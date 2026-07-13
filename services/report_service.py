from datetime import datetime
from .config import REPORT_DIR


def write_report(industry, payload):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = REPORT_DIR / f'{industry.lower().replace("-", "_")}_report_{ts}.html'
    top = payload['top_customers'][:10]
    rows = ''.join(
        f"<tr><td>{r['row_no']}</td><td>{r['customer_id']}</td><td>{r.get('customer_name','')}</td><td>{r['actual_churn']}</td><td>{r['will_leave']}</td><td>{r['churn_probability']:.3f}</td><td>{r['predicted_clv']:.2f}</td><td>{r['segment']}</td></tr>"
        for r in top
    )
    issues = ''.join(f"<li><strong>{i['issue']}</strong>: {i['how_found']}</li>" for i in payload['issues'])
    spot = payload['customer_spotlight']
    html = f"""
    <html><body style='font-family:Arial;padding:24px'>
    <h1>{industry} Customer Intelligence Report</h1>
    <p><b>Total customers:</b> {payload['summary']['total_customers']} | <b>Total CLV:</b> {payload['summary']['total_predicted_clv']:.2f} | <b>Estimated churners:</b> {payload['summary']['estimated_churners']}</p>
    <h2>Recommendation</h2><p>{payload['recommendation']['summary']}</p>
    <h2>Individual Customer Spotlight</h2>
    <p><b>Row:</b> {spot['row_no']} | <b>ID:</b> {spot['customer_id']} | <b>Name:</b> {spot.get('customer_name','')}<br>
    <b>Actual Churn:</b> {spot['actual_churn']} | <b>Predicted Leave:</b> {spot['will_leave']} | <b>Churn Probability:</b> {spot['churn_probability']:.3f}<br>
    <b>Predicted CLV:</b> {spot['predicted_clv']:.2f}<br><b>CLV Formula:</b> {spot.get('formula','')}</p>
    <h2>Issues</h2><ul>{issues}</ul>
    <h2>Top Customers</h2><table border='1' cellpadding='6' cellspacing='0'><tr><th>Row</th><th>ID</th><th>Name</th><th>Actual</th><th>Leave?</th><th>Churn Prob</th><th>CLV</th><th>Segment</th></tr>{rows}</table>
    </body></html>
    """
    path.write_text(html, encoding='utf-8')
    return path
