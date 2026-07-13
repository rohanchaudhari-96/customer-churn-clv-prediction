import json
import joblib
import pandas as pd
from .config import MODEL_DIR, INDUSTRY_KEYS
from .data_service import read_dataset
from .schema_service import detect_schema
from .preprocessing_service import clean_dataframe, build_clv
from .segmentation_service import build_segments
from .issue_detection_service import detect_issues
from .scenario_service import build_scenarios
from .recommendation_service import final_recommendation


def _folder(industry):
    return MODEL_DIR / INDUSTRY_KEYS[industry]


def run_analysis(industry, path):
    folder = _folder(industry)
    model = joblib.load(folder/'churn_model.pkl')
    metadata = json.loads((folder/'metadata.json').read_text())
    metrics = json.loads((folder/'metrics.json').read_text())
    df = clean_dataframe(read_dataset(path), industry)
    schema = detect_schema(df, industry)
    X = df.drop(columns=[schema['target']])
    proba = model.predict_proba(X)[:,1] if hasattr(model.named_steps['model'],'predict_proba') else model.predict(X).astype(float)
    threshold = float(metadata.get('threshold', 0.5))
    churn_label = (proba >= threshold).astype(int)
    clv = build_clv(df, industry)

    customer_name_col = schema.get('customer_name')
    if customer_name_col and customer_name_col in df.columns:
        customer_name = df[customer_name_col].astype(str)
    else:
        customer_name = df[schema['customer_id']].astype(str).apply(lambda x: f'Customer {x}')

    actual = pd.to_numeric(df[schema['target']], errors='coerce')
    if actual.isna().all():
        actual = df[schema['target']].astype(str).str.lower().map({'yes':1,'no':0,'true':1,'false':0,'1':1,'0':0})
    actual = actual.fillna(0).astype(int)

    out = pd.DataFrame({
        'row_no': range(1, len(df)+1),
        'customer_id': df[schema['customer_id']].astype(str),
        'customer_name': customer_name,
        'actual_churn': actual,
        'churn_probability': proba,
        'predicted_clv': clv,
        'will_leave': churn_label,
    })
    details_payload = df.copy()
    details_payload.insert(0, 'row_no', range(1, len(df)+1))
    out, seg_counts = build_segments(out)

    prep = model.named_steps['prep']
    mod = model.named_steps['model']
    feats = prep.get_feature_names_out()
    importances = getattr(mod, 'feature_importances_', None)
    if importances is None and hasattr(mod, 'coef_'):
        import numpy as np
        importances = np.abs(mod.coef_[0])
    if importances is None:
        top_features = feats[:5].tolist()
        top_values = [1, 0.8, 0.6, 0.5, 0.4]
    else:
        order = importances.argsort()[::-1][:5]
        top_features = [str(feats[i]) for i in order]
        top_values = [float(importances[i]) for i in order]

    issues = detect_issues(industry, top_features, {'threshold': threshold, 'avg_churn': float(proba.mean())})
    summary = {
        'total_customers': int(len(out)),
        'estimated_churners': int(out['will_leave'].sum()),
        'avg_churn_probability': float(out['churn_probability'].mean()),
        'total_predicted_clv': float(out['predicted_clv'].sum()),
        'avg_predicted_clv': float(out['predicted_clv'].mean()),
        'churn_threshold': threshold,
    }
    scenarios = build_scenarios(industry, issues, summary)
    recommendation = final_recommendation(summary, issues, scenarios)

    ordered_out = out.sort_values('row_no', ascending=True).reset_index(drop=True)
    details_payload = details_payload.set_index('row_no')

    spotlight_row = ordered_out.iloc[0].to_dict()
    spotlight_row['formula'] = metadata['clv_formula']
    spotlight_row['why'] = [f'{f} influenced the model (importance {v:.3f})' for f, v in zip(top_features, top_values)]
    spotlight_row['details'] = {k: ('' if pd.isna(v) else str(v)) for k, v in details_payload.loc[int(spotlight_row['row_no'])].to_dict().items()}

    out_records = ordered_out.to_dict(orient='records')
    for rec in out_records:
        rec['formula'] = metadata['clv_formula']
        rec['why'] = [f'{f} influenced the model (importance {v:.3f})' for f, v in zip(top_features[:3], top_values[:3])]
        rec['details'] = {k: ('' if pd.isna(v) else str(v)) for k, v in details_payload.loc[int(rec['row_no'])].to_dict().items()}

    return {
        'summary': summary,
        'metrics': metrics,
        'metadata': metadata,
        'segments': seg_counts,
        'drivers': [{'feature': f, 'importance': round(v, 4)} for f, v in zip(top_features, top_values)],
        'issues': issues,
        'scenarios': scenarios,
        'recommendation': recommendation,
        'customer_spotlight': spotlight_row,
        'customers': out_records,
        'top_customers': out_records[:40],
    }
