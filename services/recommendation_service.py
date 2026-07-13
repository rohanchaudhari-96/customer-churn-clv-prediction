def final_recommendation(summary, issues, scenarios):
    best = min(scenarios, key=lambda x: x['expected_churn_after']) if scenarios else None
    title = best['name'] if best else 'Balanced monitoring strategy'
    return {
        'title': title,
        'summary': f"Focus on {title.lower()} because it best reduces projected churn for the current segment mix.",
        'secondary': 'Monitor high-value low-risk customers to protect future value.',
        'avoid': 'Avoid broad untargeted offers that reduce ROI.',
    }
