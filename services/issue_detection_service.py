def detect_issues(industry, top_features, summary):
    features_lower = ' '.join([f.lower() for f in top_features])
    issues = []
    if industry == 'Telecom':
        if 'techsupport' in features_lower or 'onlinesecurity' in features_lower:
            issues.append({'issue':'Support / service issue','how_found':'Support-related fields were among the strongest churn drivers.'})
        if 'paymentmethod' in features_lower or 'monthlycharges' in features_lower:
            issues.append({'issue':'Pricing / payment friction','how_found':'Payment method or charge-related fields strongly influenced churn.'})
        if 'contract' in features_lower:
            issues.append({'issue':'Contract risk','how_found':'Short contract type increased churn probability.'})
    elif industry == 'Banking':
        if 'active_member' in features_lower:
            issues.append({'issue':'Low engagement','how_found':'Inactive membership was a strong churn signal.'})
        if 'balance' in features_lower or 'products_number' in features_lower:
            issues.append({'issue':'Value and product mismatch','how_found':'Balance or low product count influenced leaving behavior.'})
        if 'credit_score' in features_lower:
            issues.append({'issue':'Risk profile pressure','how_found':'Credit-score related pattern appeared in churn ranking.'})
    else:
        if 'complain' in features_lower:
            issues.append({'issue':'Complaint friction','how_found':'Complaint flag strongly contributed to churn prediction.'})
        if 'preferredpaymentmode' in features_lower or 'cashbackamount' in features_lower:
            issues.append({'issue':'Payment / incentive friction','how_found':'Payment and incentive behavior affected customer risk.'})
        if 'satisfactionscore' in features_lower or 'daysincelastorder' in features_lower:
            issues.append({'issue':'Engagement drop','how_found':'Low satisfaction or long inactivity signaled churn.'})
    if not issues:
        issues.append({'issue':'General churn pressure','how_found':'Model signals show moderate churn pressure across the dataset.'})
    return issues
