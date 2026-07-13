def build_scenarios(industry, issues, summary):
    base = summary['avg_churn_probability']
    scen = []
    def add(name, why, delta, clv):
        scen.append({'name':name,'why':why,'expected_churn_after':round(max(0, base+delta),3),'expected_clv_impact_pct':clv})
    issue_names = ' '.join(i['issue'].lower() for i in issues)
    if 'support' in issue_names or 'service' in issue_names or 'complaint' in issue_names:
        add('Improve support experience','Support-related signals are high.',-0.08,6)
    if 'payment' in issue_names or 'pricing' in issue_names:
        add('Reduce pricing friction','Payment or charge-related friction appears in model drivers.',-0.06,4)
    add('Launch loyalty campaign','Useful for medium-risk customers and long-term retention.',-0.04,8)
    add('Targeted discount','Use only for high-value risky segment.',-0.05,3)
    return scen[:4]
