from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from services.config import UPLOAD_DIR
from services.data_service import dataset_path
from services.validation_service import validate_dataset
from services.training_service import train_and_save, model_status
from services.analysis_service import run_analysis
from services.report_service import write_report

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
LAST_ANALYSIS = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.get('/api/model-status')
def api_model_status():
    industry = request.args.get('industry','Telecom')
    return jsonify(model_status(industry))


def _resolve_dataset(industry):
    mode = request.form.get('mode', 'backend')
    uploaded = request.files.get('file')
    filename = None
    if mode == 'upload' and uploaded and uploaded.filename:
        filename = uploaded.filename
        path = UPLOAD_DIR / filename
        uploaded.save(path)
        return path
    return dataset_path(industry, 'backend')

@app.post('/api/validate')
def api_validate():
    industry = request.form.get('industry','Telecom')
    path = _resolve_dataset(industry)
    return jsonify(validate_dataset(path, industry))

@app.post('/api/train')
def api_train():
    industry = request.form.get('industry','Telecom')
    path = _resolve_dataset(industry)
    return jsonify(train_and_save(industry, path))

@app.post('/api/analyze')
def api_analyze():
    industry = request.form.get('industry','Telecom')
    path = _resolve_dataset(industry)
    payload = run_analysis(industry, path)
    LAST_ANALYSIS[industry] = payload
    return jsonify(payload)

@app.get('/api/report')
def api_report():
    industry = request.args.get('industry','Telecom')
    payload = LAST_ANALYSIS.get(industry)
    if not payload:
        return jsonify({'error':'Run analysis first'}), 400
    path = write_report(industry, payload)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
