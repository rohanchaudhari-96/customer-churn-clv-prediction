from .data_service import read_dataset, basic_profile
from .schema_service import detect_schema


def validate_dataset(path, industry):
    df = read_dataset(path)
    profile = basic_profile(df)
    schema = detect_schema(df, industry)
    return {
        'profile': profile,
        'schema': schema,
        'valid': bool(schema['target'] and schema['customer_id']),
        'message': 'Dataset checked successfully.' if schema['target'] and schema['customer_id'] else 'Target or customer ID column not detected.',
    }
