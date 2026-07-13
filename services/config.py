from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'
REPORT_DIR = BASE_DIR / 'reports'
UPLOAD_DIR = DATA_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

INDUSTRY_KEYS = {
    'Telecom': 'telecom',
    'Banking': 'banking',
    'E-Commerce': 'ecommerce',
}

INDUSTRY_DATASETS = {
    'Telecom': DATA_DIR / 'telecom' / 'train.csv',
    'Banking': DATA_DIR / 'banking' / 'train.csv',
    'E-Commerce': DATA_DIR / 'ecommerce' / 'train.csv',
}

SCHEMA_HINTS = {
    'Telecom': {
        'id': ['customerid'],
        'target': ['churn'],
        'name': [],
        'clv_formula': 'CLV = TotalCharges (fallback: MonthlyCharges × max(tenure,1))',
    },
    'Banking': {
        'id': ['customer_id', 'customerid'],
        'target': ['churn', 'exited'],
        'name': [],
        'clv_formula': 'CLV = 0.65×balance + 0.25×estimated_salary + 500×tenure + 1500×products_number + 2000×active_member',
    },
    'E-Commerce': {
        'id': ['customerid', 'customer_id'],
        'target': ['churn'],
        'name': [],
        'clv_formula': 'CLV = 18×OrderCount + 1.2×CashbackAmount + 4×CouponUsed + 2.5×OrderAmountHikeFromlastYear − 2×DaySinceLastOrder + 10×SatisfactionScore',
    },
}
