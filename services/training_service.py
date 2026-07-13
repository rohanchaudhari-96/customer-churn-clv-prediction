import json, time
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from .config import MODEL_DIR, INDUSTRY_KEYS
from .data_service import read_dataset
from .schema_service import detect_schema
from .preprocessing_service import prepare_xy


def _folder(industry):
    f = MODEL_DIR / INDUSTRY_KEYS[industry]
    f.mkdir(parents=True, exist_ok=True)
    return f


def _best_threshold(y_true, proba):
    precision, recall, thresholds = precision_recall_curve(y_true, proba)
    if len(thresholds) == 0:
        return 0.5
    f1 = (2 * precision[:-1] * recall[:-1]) / np.clip(precision[:-1] + recall[:-1], 1e-9, None)
    idx = int(np.nanargmax(f1))
    thresh = float(thresholds[idx])
    return round(max(0.25, min(0.75, thresh)), 3)


def train_and_save(industry, path):
    df = read_dataset(path)
    schema = detect_schema(df, industry)
    X, y, clv, preprocessor, numf, catf = prepare_xy(df, schema, industry)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    candidates = {
        'LogisticRegression': LogisticRegression(max_iter=900, class_weight='balanced'),
        'RandomForestClassifier': RandomForestClassifier(n_estimators=260, class_weight='balanced', random_state=42, min_samples_leaf=2),
        'GradientBoostingClassifier': GradientBoostingClassifier(random_state=42, n_estimators=200, learning_rate=0.05),
    }
    best_name = None
    best_score = -1
    best_pipe = None
    best_metrics = None
    best_threshold_value = 0.5
    started = time.time()
    for name, model in candidates.items():
        pipe = Pipeline([('prep', preprocessor), ('model', model)])
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:,1] if hasattr(pipe.named_steps['model'],'predict_proba') else pipe.predict(X_test).astype(float)
        threshold = _best_threshold(y_test, proba)
        pred = (proba >= threshold).astype(int)
        metrics = {
            'accuracy': round(float(accuracy_score(y_test, pred)), 3),
            'precision': round(float(precision_score(y_test, pred, zero_division=0)), 3),
            'recall': round(float(recall_score(y_test, pred, zero_division=0)), 3),
            'f1': round(float(f1_score(y_test, pred, zero_division=0)), 3),
            'roc_auc': round(float(roc_auc_score(y_test, proba)), 3),
            'threshold': threshold,
        }
        score = 0.40*metrics['roc_auc'] + 0.35*metrics['f1'] + 0.25*metrics['recall']
        if score > best_score:
            best_score = score
            best_name = name
            best_pipe = pipe
            best_metrics = metrics
            best_threshold_value = threshold
    folder = _folder(industry)
    run_count = 1
    meta_path = folder/'metadata.json'
    if meta_path.exists():
        try:
            old = json.loads(meta_path.read_text())
            run_count = int(old.get('run_count',0)) + 1
        except Exception:
            run_count = 1
    version = f'v{run_count}'
    joblib.dump(best_pipe, folder/'churn_model.pkl')
    metadata = {
        'industry': industry,
        'version': version,
        'run_count': run_count,
        'rows': int(len(df)),
        'features': int(X.shape[1]),
        'training_time_sec': round(time.time()-started,3),
        'best_churn_model': best_name,
        'schema': schema,
        'numeric_features': numf,
        'categorical_features': catf,
        'clv_formula': schema['formula'],
        'threshold': best_threshold_value,
        'train_test_split': '80/20',
    }
    metrics_payload = {'churn_metrics': best_metrics}
    (folder/'metadata.json').write_text(json.dumps(metadata, indent=2))
    (folder/'metrics.json').write_text(json.dumps(metrics_payload, indent=2))
    return {'metadata': metadata, 'metrics': metrics_payload}


def model_status(industry):
    folder = _folder(industry)
    meta = folder/'metadata.json'
    met = folder/'metrics.json'
    model = folder/'churn_model.pkl'
    trained = meta.exists() and met.exists() and model.exists()
    out = {'trained': trained, 'metadata': {}, 'metrics': {}}
    if meta.exists():
        out['metadata'] = json.loads(meta.read_text())
    if met.exists():
        out['metrics'] = json.loads(met.read_text())
    return out
