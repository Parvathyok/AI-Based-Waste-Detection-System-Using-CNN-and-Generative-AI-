/**
 * app.js — WasteWise AI Frontend Logic
 * Handles: drag-and-drop, file preview, POST /predict, result rendering
 */

const dropZone      = document.getElementById('drop-zone');
const dropZoneInner = document.getElementById('drop-zone-inner');
const imgPreviewWrap= document.getElementById('image-preview-wrap');
const imgPreview    = document.getElementById('image-preview');
const fileInput     = document.getElementById('file-input');
const browseBtn     = document.getElementById('browse-btn');
const changeImgBtn  = document.getElementById('change-img-btn');
const analyzeBtn    = document.getElementById('analyze-btn');
const btnText       = analyzeBtn.querySelector('.btn-text');
const btnLoader     = analyzeBtn.querySelector('.btn-loader');
const errorBox      = document.getElementById('error-box');
const errorMsg      = document.getElementById('error-msg');
const emptyState    = document.getElementById('empty-state');
const resultsContent= document.getElementById('results-content');

let selectedFile = null;

// ── File Selection ──────────────────────────────────────────────────────────
browseBtn.addEventListener('click', () => fileInput.click());
changeImgBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

// ── Drag & Drop ─────────────────────────────────────────────────────────────
dropZone.addEventListener('click', () => { if (!selectedFile) fileInput.click(); });
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// ── Handle selected file ─────────────────────────────────────────────────────
function handleFile(file) {
  const allowed = ['image/png','image/jpeg','image/jpg','image/webp','image/gif','image/bmp'];
  if (!allowed.includes(file.type)) {
    showError('Unsupported file type. Please upload PNG, JPG, or WEBP.');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError('File too large. Maximum size is 10 MB.');
    return;
  }
  hideError();
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    imgPreview.src = e.target.result;
    dropZoneInner.style.display = 'none';
    imgPreviewWrap.style.display = 'block';
    analyzeBtn.disabled = false;
  };
  reader.readAsDataURL(file);
}

// ── Analyze Button ───────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  setLoading(true);
  hideError();
  hideResults();

  const formData = new FormData();
  formData.append('image', selectedFile);

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      showError(data.error || 'Server error. Please try again.');
      return;
    }

    renderResults(data);
  } catch (err) {
    showError('Network error. Is the server running?');
    console.error(err);
  } finally {
    setLoading(false);
  }
});

// ── Render Results ───────────────────────────────────────────────────────────
function renderResults(d) {
  // Classification card
  document.getElementById('res-icon').textContent       = d.icon || '♻️';
  document.getElementById('res-label').textContent      = d.label;
  document.getElementById('res-class').textContent      = d.class_name;
  document.getElementById('res-confidence').textContent = d.confidence_pct;

  // Confidence bar (animated)
  const fill = document.getElementById('confidence-fill');
  fill.style.width = '0%';
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      fill.style.width = (d.confidence * 100).toFixed(1) + '%';
    });
  });

  // Badges
  const recycBadge = document.getElementById('recyclable-badge');
  if (d.recyclable) {
    recycBadge.textContent = '♻️ Recyclable';
    recycBadge.className = 'badge';
  } else {
    recycBadge.textContent = '🚫 Not Recyclable';
    recycBadge.className = 'badge not-recyclable';
  }
  document.getElementById('bin-badge').textContent = '🗑️ ' + d.bin_color + ' Bin';

  // GenAI explanation cards
  document.getElementById('res-explanation').textContent    = d.explanation    || '—';
  document.getElementById('res-disposal').textContent       = d.disposal_method|| '—';
  document.getElementById('res-recyclability').textContent  = d.recyclability  || '—';
  document.getElementById('res-impact').textContent         = d.environmental_impact || '—';
  document.getElementById('res-reuse').textContent          = d.reuse_tips     || '—';
  document.getElementById('res-sdg').textContent            = d.sdg_contribution || '—';

  // All-scores bars
  renderScoreBars(d.all_scores, d.class_name);

  // Processing time
  document.getElementById('processing-time').textContent =
    `⚡ Processed in ${d.processing_time_ms} ms`;

  // Show
  emptyState.style.display    = 'none';
  resultsContent.style.display= 'block';
  resultsContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function renderScoreBars(scores, topClass) {
  const container = document.getElementById('scores-bars');
  container.innerHTML = '';

  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  sorted.forEach(([cls, score]) => {
    const isTop = cls === topClass;
    const pct   = (score * 100).toFixed(1);
    const label = cls.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    const row = document.createElement('div');
    row.className = 'score-row';
    row.innerHTML = `
      <div class="score-label">${label}</div>
      <div class="score-bar-wrap">
        <div class="score-bar-fill${isTop ? '' : ' dim'}" data-pct="${pct}"></div>
      </div>
      <div class="score-pct">${pct}%</div>
    `;
    container.appendChild(row);
  });

  // Animate bars
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      container.querySelectorAll('.score-bar-fill').forEach(el => {
        el.style.width = el.dataset.pct + '%';
      });
    });
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function setLoading(loading) {
  analyzeBtn.disabled = loading;
  btnText.style.display   = loading ? 'none'   : 'inline';
  btnLoader.style.display = loading ? 'inline-flex' : 'none';
}

function showError(msg) {
  errorMsg.textContent     = msg;
  errorBox.style.display   = 'flex';
}
function hideError() { errorBox.style.display = 'none'; }

function hideResults() {
  resultsContent.style.display = 'none';
  emptyState.style.display     = 'block';
}
