
const state = {
  industry: 'Telecom',
  mode: 'backend',
  analysis: null,
  filteredCustomers: [],
  activeRow: null,
  searchMode: 'row',
};

const els = {
  industryButtons: [...document.querySelectorAll('#industryButtons button')],
  modeButtons: [...document.querySelectorAll('#modeButtons button')],
  uploadWrap: document.getElementById('uploadWrap'),
  fileInput: document.getElementById('fileInput'),
  fileNameText: document.getElementById('fileNameText'),
  validateBtn: document.getElementById('validateBtn'),
  trainBtn: document.getElementById('trainBtn'),
  analyzeBtn: document.getElementById('analyzeBtn'),
  reportBtn: document.getElementById('reportBtn'),
  datasetMetrics: document.getElementById('datasetMetrics'),
  schemaBox: document.getElementById('schemaBox'),
  featureBox: document.getElementById('featureBox'),
  validPill: document.getElementById('validPill'),
  trainPill: document.getElementById('trainPill'),
  trainSummary: document.getElementById('trainSummary'),
  trainExplain: document.getElementById('trainExplain'),
  perfGrid: document.getElementById('perfGrid'),
  summaryGrid: document.getElementById('summaryGrid'),
  driverList: document.getElementById('driverList'),
  issuesBox: document.getElementById('issuesBox'),
  segmentGrid: document.getElementById('segmentGrid'),
  scenarioBox: document.getElementById('scenarioBox'),
  recBox: document.getElementById('recBox'),
  customerSpotlight: document.getElementById('customerSpotlight'),
  customerRows: document.getElementById('customerRows'),
  browserCount: document.getElementById('browserCount'),
  searchInput: document.getElementById('searchInput'),
  searchBtn: document.getElementById('searchBtn'),
  searchModeButtons: [...document.querySelectorAll('#searchModeButtons button')],
  statusPill: document.getElementById('statusPill'),
};

let driverChart = null;
let segmentChart = null;

const normalize = (v) => String(v ?? '').toLowerCase().trim().replace(/\s+/g, ' ');

function fmt(n) {
  const num = Number(n);
  if (!Number.isFinite(num)) return '-';
  return num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function pct(v) {
  return `${(Number(v) * 100).toFixed(1)}%`;
}

function tag(text) { return `<span class='tag'>${text}</span>`; }

function setSearchMode(mode) {
  state.searchMode = mode;
  els.searchModeButtons.forEach(b => b.classList.toggle('active', b.dataset.search === mode));
  const placeholderMap = {
    row: 'Search by row number, e.g. 3210',
    id: 'Search by customer ID, e.g. 8149-RSOUN',
    name: 'Search by customer name, e.g. Customer 8149-RSOUN'
  };
  els.searchInput.placeholder = placeholderMap[mode] || 'Search customers';
}

function formData() {
  const fd = new FormData();
  fd.append('industry', state.industry);
  fd.append('mode', state.mode);
  if (state.mode === 'upload' && els.fileInput.files[0]) fd.append('file', els.fileInput.files[0]);
  return fd;
}

function setIndustry(ind) {
  state.industry = ind;
  els.industryButtons.forEach(b => b.classList.toggle('active', b.dataset.ind === ind));
  loadStatus();
}

function setMode(mode) {
  state.mode = mode;
  els.modeButtons.forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  els.uploadWrap.classList.toggle('hidden', mode !== 'upload');
}

async function post(url) {
  const res = await fetch(url, { method: 'POST', body: formData() });
  return res.json();
}

async function loadStatus() {
  const res = await fetch(`/api/model-status?industry=${encodeURIComponent(state.industry)}`);
  const data = await res.json();
  if (data.trained) {
    els.trainPill.textContent = `Trained ${data.metadata.version || ''}`;
    renderTrain(data);
  } else {
    els.trainPill.textContent = 'Not Trained';
    els.trainSummary.innerHTML = '';
    els.perfGrid.innerHTML = '';
    els.trainExplain.innerHTML = 'Train once and the strongest churn model will be saved permanently for the selected industry.';
  }
}

function renderValidation(d) {
  const p = d.profile;
  const s = d.schema;
  els.validPill.textContent = d.valid ? 'Validated' : 'Check';
  els.datasetMetrics.innerHTML = [
    ['Total Rows', fmt(p.rows)], ['Total Columns', p.columns], ['Missing %', `${p.missing_pct}%`], ['Quality', p.quality],
  ].map(x => `<div class='metric'><div class='label'>${x[0]}</div><div class='value'>${x[1]}</div></div>`).join('');
  els.schemaBox.innerHTML = [
    tag(`Target: ${s.target || 'Not found'}`), tag(`Customer ID: ${s.customer_id || 'Not found'}`),
    tag(`Name: ${s.customer_name || 'Generated from ID'}`), tag(`CLV Formula: ${s.formula}`),
  ].join('');
  els.featureBox.innerHTML = (p.features || []).slice(0, 24).map(f => tag(f)).join('');
}

function renderTrain(d) {
  const m = d.metadata || {};
  const cm = (d.metrics || {}).churn_metrics || {};
  els.trainSummary.innerHTML = [
    tag(`Industry: ${m.industry || state.industry}`), tag(`Rows: ${m.rows || '-'}`), tag(`Features: ${m.features || '-'}`),
    tag(`Training Time: ${m.training_time_sec || '-'}s`), tag(`Run Count: ${m.run_count || '-'}`), tag(`Version: ${m.version || '-'}`),
    tag(`Best Churn Model: ${m.best_churn_model || '-'}`), tag(`Threshold: ${m.threshold || '-'}`),
  ].join('');
  els.trainExplain.innerHTML = `<strong>Simple Training Explanation</strong><br>The system automatically compared churn models and saved the strongest one for ${state.industry}. CLV is calculated using this formula: <strong>${m.clv_formula || '-'}</strong>`;
  els.perfGrid.innerHTML = [
    ['Accuracy', cm.accuracy], ['Precision', cm.precision], ['Recall', cm.recall], ['F1', cm.f1], ['ROC-AUC', cm.roc_auc],
  ].map(x => `<div class='metric'><div class='label'>${x[0]}</div><div class='value'>${x[1] ?? '-'}</div></div>`).join('');
}

function renderAnalysis(d) {
  state.analysis = d;
  state.filteredCustomers = [...(d.customers || [])].sort((a,b)=>a.row_no-b.row_no);
  const s = d.summary;
  els.summaryGrid.innerHTML = [
    ['Total Customers', fmt(s.total_customers)], ['Estimated Churners', fmt(s.estimated_churners)], ['Average Churn %', pct(s.avg_churn_probability)],
    ['Total Predicted CLV', fmt(s.total_predicted_clv)], ['Average Predicted CLV', fmt(s.avg_predicted_clv)], ['Churn Threshold', s.churn_threshold],
  ].map(x => `<div class='metric'><div class='label'>${x[0]}</div><div class='value'>${x[1]}</div></div>`).join('');

  els.driverList.innerHTML = d.drivers.map((x, i) => `<div class='subcard'><strong>#${i + 1} ${x.feature}</strong><br>Importance: ${x.importance}</div>`).join('');

  if (driverChart) driverChart.destroy();
  driverChart = new Chart(document.getElementById('driverChart'), {
    type: 'bar',
    data: { labels: d.drivers.map(x => x.feature), datasets: [{ data: d.drivers.map(x => x.importance), backgroundColor: '#2d7df7', borderRadius: 8 }] },
    options: { indexAxis: 'y', plugins: { legend: { display: false } }, maintainAspectRatio: false, responsive: true,
      scales: { x: { ticks: { color: '#a9c0de' } }, y: { ticks: { color: '#dbe8ff' } } } }
  });

  els.issuesBox.innerHTML = d.issues.map(x => `<div class='subcard'><strong>${x.issue}</strong><br>${x.how_found}</div>`).join('');

  const orderedSegments = ['High Risk + High Value', 'High Risk + Low Value', 'Low Risk + High Value', 'Low Risk + Low Value'];
  const segmentData = orderedSegments.map(k => d.segments[k] || 0);
  els.segmentGrid.innerHTML = orderedSegments.map((k, idx) => `<div class='metric'><div class='label'>${k}</div><div class='value'>${fmt(segmentData[idx])}</div></div>`).join('');

  if (segmentChart) segmentChart.destroy();
  segmentChart = new Chart(document.getElementById('segmentChart'), {
    type: 'doughnut',
    data: { labels: orderedSegments, datasets: [{ data: segmentData, backgroundColor: ['#4f8eed', '#2d6bcb', '#2cc4a4', '#173a65'], borderColor: '#f3f7ff', borderWidth: 2 }] },
    options: { maintainAspectRatio: false, responsive: true, plugins: { legend: { labels: { color: '#dbe8ff', boxWidth: 18 }, position: 'top' } } }
  });

  els.scenarioBox.innerHTML = d.scenarios.map(x => `<div class='subcard'><strong>${x.name}</strong><br>${x.why}<br>Expected churn after action: <strong>${pct(x.expected_churn_after)}</strong><br>Expected CLV impact: <strong>${x.expected_clv_impact_pct}%</strong></div>`).join('');
  els.recBox.innerHTML = `<strong>${d.recommendation.title}</strong><br>${d.recommendation.summary}<br><br><strong>Secondary:</strong> ${d.recommendation.secondary}<br><strong>Avoid:</strong> ${d.recommendation.avoid}`;

  renderCustomerRows(state.filteredCustomers);
  spotlight(d.customer_spotlight || state.filteredCustomers[0]);
}

function rowHtml(r) {
  return `
    <tr class='${state.activeRow === r.row_no ? 'active' : ''}' data-row='${r.row_no}'>
      <td>${r.row_no}</td>
      <td>${r.customer_id}</td>
      <td>${r.customer_name || '-'}</td>
      <td><span class='small-badge'>${r.actual_churn}</span></td>
      <td><span class='small-badge'>${r.will_leave}</span></td>
      <td>${pct(r.churn_probability)}</td>
      <td>${fmt(r.predicted_clv)}</td>
      <td>${r.segment}</td>
    </tr>`;
}

function renderCustomerRows(rows) {
  const list = [...(rows || [])].sort((a,b)=>a.row_no-b.row_no);
  els.browserCount.textContent = `${list.length} records`;
  els.customerRows.innerHTML = list.map(rowHtml).join('');
  [...els.customerRows.querySelectorAll('tr')].forEach(tr => {
    tr.onclick = () => {
      const row = Number(tr.dataset.row);
      const found = (state.filteredCustomers.length ? state.filteredCustomers : state.analysis?.customers || []).find(x => x.row_no === row)
        || (state.analysis?.customers || []).find(x => x.row_no === row);
      if (found) spotlight(found);
    };
  });
}

function spotlight(c) {
  if (!c) return;
  state.activeRow = c.row_no;
  renderCustomerRows(state.filteredCustomers.length ? state.filteredCustomers : (state.analysis?.customers || []));
  const why = (c.why || []).map(x => `<li>${x}</li>`).join('');
  const detailEntries = Object.entries(c.details || {}).slice(0, 20).map(([k,v]) => `
      <div class='detail-item'><span class='detail-key'>${k}</span>${v || '-'}</div>
  `).join('');
  els.customerSpotlight.innerHTML = `
    <strong>Customer Spotlight</strong>
    <div class='inline-kv'>
      <div><span class='muted'>Row</span><br>${c.row_no}</div>
      <div><span class='muted'>Customer ID</span><br>${c.customer_id}</div>
      <div><span class='muted'>Name</span><br>${c.customer_name || '-'}</div>
      <div><span class='muted'>Actual Churn</span><br>${c.actual_churn ?? '-'}</div>
      <div><span class='muted'>Predicted Leave</span><br>${c.will_leave}</div>
      <div><span class='muted'>Churn Probability</span><br>${pct(c.churn_probability)}</div>
      <div><span class='muted'>Predicted CLV</span><br>${fmt(c.predicted_clv)}</div>
      <div><span class='muted'>Segment</span><br>${c.segment}</div>
    </div>
    <br><strong>CLV Formula Used:</strong> ${c.formula || state.analysis.metadata.clv_formula}
    <br><strong>Why this customer was scored this way</strong>
    <ul>${why}</ul>
    <br><strong>Customer Data Snapshot</strong>
    <div class='detail-grid'>${detailEntries}</div>
  `;
}

function searchCustomer() {
  if (!state.analysis) return;
  const q = normalize(els.searchInput.value);
  const all = [...(state.analysis.customers || [])].sort((a,b)=>a.row_no-b.row_no);

  if (!q) {
    state.filteredCustomers = all;
    renderCustomerRows(all);
    if (all.length) spotlight(all[0]);
    return;
  }

  state.filteredCustomers = all.filter(r => {
    if (state.searchMode === 'row') {
      return String(r.row_no) === q || String(r.row_no).startsWith(q);
    }
    if (state.searchMode === 'id') {
      return normalize(r.customer_id).includes(q);
    }
    return normalize(r.customer_name).includes(q);
  }).sort((a,b)=>a.row_no-b.row_no);

  renderCustomerRows(state.filteredCustomers);
  if (state.filteredCustomers.length) {
    spotlight(state.filteredCustomers[0]);
  } else {
    els.browserCount.textContent = '0 records';
    els.customerRows.innerHTML = '';
    els.customerSpotlight.innerHTML = `Customer not found for <strong>${state.searchMode}</strong> search. Try another value.`;
  }
}

els.industryButtons.forEach(b => b.onclick = () => setIndustry(b.dataset.ind));
els.modeButtons.forEach(b => b.onclick = () => setMode(b.dataset.mode));
els.fileInput.addEventListener('change', () => { els.fileNameText.textContent = els.fileInput.files[0]?.name || 'No file selected'; });
els.validateBtn.onclick = async () => { const d = await post('/api/validate'); renderValidation(d); };
els.trainBtn.onclick = async () => { els.statusPill.textContent = 'Training...'; const d = await post('/api/train'); renderTrain(d); els.statusPill.textContent = 'Trained'; };
els.analyzeBtn.onclick = async () => { els.statusPill.textContent = 'Analyzing...'; const d = await post('/api/analyze'); renderAnalysis(d); els.statusPill.textContent = 'Ready'; };
els.reportBtn.onclick = () => window.open(`/api/report?industry=${encodeURIComponent(state.industry)}`, '_blank');
els.searchModeButtons.forEach(b => b.onclick = () => setSearchMode(b.dataset.search));
els.searchBtn.onclick = () => searchCustomer();
els.searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') searchCustomer(); });
els.searchInput.addEventListener('input', () => { if (state.analysis) searchCustomer(); });

setIndustry('Telecom');
setMode('backend');
setSearchMode('row');
