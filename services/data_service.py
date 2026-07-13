import pandas as pd
from pathlib import Path
from .config import INDUSTRY_DATASETS, UPLOAD_DIR


def dataset_path(industry: str, mode: str, uploaded_name: str | None = None) -> Path:
    if mode == 'upload' and uploaded_name:
        return UPLOAD_DIR / uploaded_name
    return INDUSTRY_DATASETS[industry]


def read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path)
    return pd.read_excel(path)


def basic_profile(df: pd.DataFrame) -> dict:
    rows, cols = df.shape
    missing_pct = round(float(df.isna().sum().sum()) / max(rows * cols, 1) * 100, 2)
    quality = 'Excellent' if missing_pct == 0 else ('Good' if missing_pct < 5 else ('Moderate' if missing_pct < 15 else 'Poor'))
    return {
        'rows': int(rows),
        'columns': int(cols),
        'missing_pct': missing_pct,
        'quality': quality,
        'features': list(df.columns),
    }
