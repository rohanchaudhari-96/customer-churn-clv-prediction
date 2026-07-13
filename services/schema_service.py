from .config import SCHEMA_HINTS


def _norm(s: str) -> str:
    return s.strip().lower().replace(' ', '').replace('_', '')


def detect_schema(df, industry: str):
    cols = { _norm(c): c for c in df.columns }
    hints = SCHEMA_HINTS[industry]
    def pick(cands):
        for c in cands:
            if _norm(c) in cols:
                return cols[_norm(c)]
        return None
    target = pick(hints['target'])
    customer_id = pick(hints['id'])
    customer_name = pick(['name','customername','fullname'])
    return {
        'target': target,
        'customer_id': customer_id,
        'customer_name': customer_name,
        'formula': hints['clv_formula'],
    }
