import pandas as pd

def build_segments(df: pd.DataFrame):
    churn_thr = 0.5
    clv_thr = df['predicted_clv'].median() if len(df) else 0
    def seg(r):
        hr = r['churn_probability'] >= churn_thr
        hv = r['predicted_clv'] >= clv_thr
        if hr and hv: return 'High Risk + High Value'
        if hr and not hv: return 'High Risk + Low Value'
        if not hr and hv: return 'Low Risk + High Value'
        return 'Low Risk + Low Value'
    df = df.copy()
    df['segment'] = df.apply(seg, axis=1)
    counts = df['segment'].value_counts().to_dict()
    return df, counts
