import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _canonicalize_columns(df: pd.DataFrame, industry: str) -> pd.DataFrame:
    d = df.copy()
    if industry == 'Banking':
        rename_map = {
            'CustomerId': 'customer_id',
            'CreditScore': 'credit_score',
            'Geography': 'country',
            'NumOfProducts': 'products_number',
            'HasCrCard': 'credit_card',
            'IsActiveMember': 'active_member',
            'EstimatedSalary': 'estimated_salary',
            'Exited': 'churn',
            'Balance': 'balance',
            'Tenure': 'tenure',
            'Gender': 'gender',
            'Age': 'age',
        }
        d = d.rename(columns={k: v for k, v in rename_map.items() if k in d.columns})
    elif industry == 'Telecom':
        # keep original telecom names but normalize TotalCharges into numeric later
        pass
    elif industry == 'E-Commerce':
        rename_map = {
            'CustomerID': 'CustomerID',
            'PreferedOrderCat': 'PreferedOrderCat',
            'PreferredPaymentMode': 'PreferredPaymentMode',
            'PreferredLoginDevice': 'PreferredLoginDevice',
        }
        d = d.rename(columns=rename_map)
    return d


def clean_dataframe(df: pd.DataFrame, industry: str) -> pd.DataFrame:
    d = _canonicalize_columns(df, industry).copy().drop_duplicates()

    # trim object text
    for col in d.select_dtypes(include='object').columns:
        d[col] = d[col].astype(str).str.strip()
        d[col] = d[col].replace({'': pd.NA, 'nan': pd.NA, 'None': pd.NA})

    if industry == 'Telecom':
        if 'TotalCharges' in d.columns:
            d['TotalCharges'] = pd.to_numeric(d['TotalCharges'], errors='coerce')
        if 'MonthlyCharges' in d.columns:
            d['MonthlyCharges'] = pd.to_numeric(d['MonthlyCharges'], errors='coerce')
        if 'tenure' in d.columns:
            d['tenure'] = pd.to_numeric(d['tenure'], errors='coerce')

    if industry == 'Banking':
        for col in ['credit_score', 'age', 'tenure', 'balance', 'products_number', 'credit_card', 'active_member', 'estimated_salary', 'churn']:
            if col in d.columns:
                d[col] = pd.to_numeric(d[col], errors='coerce')

    if industry == 'E-Commerce':
        replacements = {'CC': 'Credit Card', 'COD': 'Cash on Delivery', 'E wallet': 'E-Wallet'}
        if 'PreferredPaymentMode' in d.columns:
            d['PreferredPaymentMode'] = d['PreferredPaymentMode'].replace(replacements)
        numeric_cols = [
            'Churn', 'Tenure', 'CityTier', 'WarehouseToHome', 'HourSpendOnApp',
            'NumberOfDeviceRegistered', 'SatisfactionScore', 'NumberOfAddress',
            'Complain', 'OrderAmountHikeFromlastYear', 'CouponUsed', 'OrderCount',
            'DaySinceLastOrder', 'CashbackAmount'
        ]
        for col in numeric_cols:
            if col in d.columns:
                d[col] = pd.to_numeric(d[col], errors='coerce')

    # fill numeric missing with median
    for col in d.select_dtypes(include='number').columns:
        if d[col].isna().any():
            d[col] = d[col].fillna(d[col].median())

    # fill categorical missing with most frequent or Unknown
    for col in d.select_dtypes(exclude='number').columns:
        if d[col].isna().any():
            mode = d[col].mode(dropna=True)
            d[col] = d[col].fillna(mode.iloc[0] if not mode.empty else 'Unknown')

    return d


def build_clv(df: pd.DataFrame, industry: str) -> pd.Series:
    d = clean_dataframe(df, industry)
    if industry == 'Telecom':
        if 'TotalCharges' in d.columns:
            vals = pd.to_numeric(d['TotalCharges'], errors='coerce')
            if vals.notna().sum() > 0:
                fallback = pd.to_numeric(d.get('MonthlyCharges', 0), errors='coerce').fillna(0) * pd.to_numeric(d.get('tenure', 1), errors='coerce').fillna(1).clip(lower=1)
                return vals.fillna(fallback)
        return pd.to_numeric(d.get('MonthlyCharges', 0), errors='coerce').fillna(0) * pd.to_numeric(d.get('tenure', 1), errors='coerce').fillna(1).clip(lower=1)
    if industry == 'Banking':
        return (
            0.65 * pd.to_numeric(d.get('balance', 0), errors='coerce').fillna(0)
            + 0.25 * pd.to_numeric(d.get('estimated_salary', 0), errors='coerce').fillna(0)
            + 500 * pd.to_numeric(d.get('tenure', 0), errors='coerce').fillna(0)
            + 1500 * pd.to_numeric(d.get('products_number', 0), errors='coerce').fillna(0)
            + 2000 * pd.to_numeric(d.get('active_member', 0), errors='coerce').fillna(0)
        )
    return (
        18 * pd.to_numeric(d.get('OrderCount', 0), errors='coerce').fillna(0)
        + 1.2 * pd.to_numeric(d.get('CashbackAmount', 0), errors='coerce').fillna(0)
        + 4 * pd.to_numeric(d.get('CouponUsed', 0), errors='coerce').fillna(0)
        + 2.5 * pd.to_numeric(d.get('OrderAmountHikeFromlastYear', 0), errors='coerce').fillna(0)
        - 2 * pd.to_numeric(d.get('DaySinceLastOrder', 0), errors='coerce').fillna(0)
        + 10 * pd.to_numeric(d.get('SatisfactionScore', 0), errors='coerce').fillna(0)
        + 3 * pd.to_numeric(d.get('Tenure', 0), errors='coerce').fillna(0)
        + 2 * (5 - pd.to_numeric(d.get('Complain', 0), errors='coerce').fillna(0))
    )


def prepare_xy(df: pd.DataFrame, schema: dict, industry: str):
    d = clean_dataframe(df, industry)
    y = d[schema['target']].copy()
    if y.dtype == object:
        y = y.astype(str).str.strip().str.lower().map({'yes':1,'no':0,'true':1,'false':0,'1':1,'0':0}).fillna(0).astype(int)
    else:
        y = pd.to_numeric(y, errors='coerce').fillna(0).astype(int)
    clv = build_clv(d, industry)
    drop_cols = [c for c in [schema['target']] if c in d.columns]
    X = d.drop(columns=drop_cols)
    numeric_features = X.select_dtypes(include=['number']).columns.tolist()
    categorical_features = [c for c in X.columns if c not in numeric_features]
    preprocessor = ColumnTransformer([
        ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), numeric_features),
        ('cat', Pipeline([('imp', SimpleImputer(strategy='most_frequent')), ('oh', OneHotEncoder(handle_unknown='ignore'))]), categorical_features),
    ])
    return X, y, clv, preprocessor, numeric_features, categorical_features
