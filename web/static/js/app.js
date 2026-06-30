/**
 * app.js — ScreenMaker main application logic.
 *
 * Manages application state, wires up UI events, and communicates with the
 * Flask API. Depends on preview.js being loaded first.
 */

// ── State ──────────────────────────────────────────────────────────────────────

const state = {
  /** @type {object[]} Screen dicts loaded from the server */
  screens: [],
  /** @type {number|null} ID of the currently selected screen */
  activeScreenId: null,
  /** @type {object[]} LED tile repository entries */
  tiles: [],
  /** @type {string|null} Active generation job ID */
  currentJobId: null,
  /** @type {number|null} setInterval handle for job polling */
  pollInterval: null,
};

const preview = new ScreenPreview('previewCanvas');

// ── Utilities ──────────────────────────────────────────────────────────────────

function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

async function apiFetch(url, options = {}) {
  const r = await fetch(url, options);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `${options.method || 'GET'} ${url} → ${r.status}`);
  return data;
}

const apiGet  = (url)       => apiFetch(url);
const apiPost = (url, body) => apiFetch(url, {
  method: 'POST',
  headers: body ? { 'Content-Type': 'application/json' } : {},
  body: body ? JSON.stringify(body) : undefined,
});
const apiPatch = (url, body) => apiFetch(url, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Initialization ─────────────────────────────────────────────────────────────

async function init() {
  // Tile changes from canvas → debounced PATCH
  preview.onTilesChanged = debounce(async (enabledArray) => {
    if (state.activeScreenId === null) return;
    try {
      await apiPatch(`/api/screens/${state.activeScreenId}/tiles`, { enabled_array: enabledArray });
      const s = state.screens.find(s => s.id === state.activeScreenId);
      if (s) s.enabled_array = enabledArray;
    } catch (e) {
      console.error('Failed to save tile state:', e);
    }
  }, 350);

  // Nav actions
  document.getElementById('csvUpload').addEventListener('change', handleCSVUpload);
  document.getElementById('btnGenerate').addEventListener('click', handleGenerate);
  document.getElementById('btnExportCSV').addEventListener('click', () => { window.location.href = '/api/export-csv'; });
  document.getElementById('btnClearAll').addEventListener('click', handleClearAll);

  // Add Screen
  document.getElementById('btnAddScreen').addEventListener('click', openAddScreenModal);
  document.getElementById('btnAddScreenConfirm').addEventListener('click', handleAddScreen);
  document.getElementById('newScreenTileRepo').addEventListener('change', handleNewScreenTileRepoSelect);

  // Enter key submits add-screen modal
  document.getElementById('addScreenModal').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleAddScreen();
  });

  // Properties panel
  document.getElementById('propTileRepo').addEventListener('change', handleTileRepoSelect);
  document.getElementById('btnResetTiles').addEventListener('click', handleResetTiles);

  const debouncedProps = debounce(handlePropertiesChange, 400);
  ['propName', 'propTileW', 'propTileH', 'propTilesW', 'propTilesH'].forEach(id => {
    document.getElementById(id).addEventListener('input', debouncedProps);
  });

  await Promise.all([loadScreens(), loadTiles()]);
}

// ── Data loading ───────────────────────────────────────────────────────────────

async function loadScreens() {
  try {
    state.screens = await apiGet('/api/screens');
    renderScreenList();
    setButtonStates();
    if (state.screens.length > 0) selectScreen(state.screens[0].id);
  } catch (e) {
    console.error('Failed to load screens:', e);
  }
}

async function loadTiles() {
  try {
    state.tiles = await apiGet('/api/tiles');
    renderTileRepo('propTileRepo');
    renderTileRepo('newScreenTileRepo');
  } catch (e) {
    console.error('Failed to load tile repository:', e);
  }
}

// ── Rendering ──────────────────────────────────────────────────────────────────

function renderScreenList() {
  const list = document.getElementById('screenList');
  document.getElementById('screenCount').textContent = state.screens.length;

  if (state.screens.length === 0) {
    list.innerHTML = '<li style="padding:12px 14px; color:var(--text-3); font-size:11px;">No screens yet</li>';
    return;
  }

  list.innerHTML = state.screens.map(s => {
    const color = `hsl(${s.color_hue}, 65%, 52%)`;
    const active = s.id === state.activeScreenId ? ' active' : '';
    return `
      <li class="sm-screen-item${active}" data-id="${s.id}" onclick="selectScreen(${s.id})">
        <span class="sm-screen-swatch" style="background:${color};"></span>
        <span class="sm-screen-name" title="${escHtml(s.name)}">${escHtml(s.name)}</span>
      </li>`;
  }).join('');
}

function renderTileRepo(selectId) {
  const sel = document.getElementById(selectId);
  const first = sel.options[0].text; // keep placeholder
  sel.innerHTML = `<option value="">${first}</option>`;
  state.tiles.forEach(t => {
    const opt = new Option(t.name, t.id);
    opt.dataset.pixelWidth  = t.pixel_width;
    opt.dataset.pixelHeight = t.pixel_height;
    sel.appendChild(opt);
  });
}

function setButtonStates() {
  const has = state.screens.length > 0;
  document.getElementById('btnGenerate').disabled = !has;
  document.getElementById('btnExportCSV').disabled = !has;
}

// ── Screen selection ───────────────────────────────────────────────────────────

function selectScreen(id) {
  const screen = state.screens.find(s => s.id === id);
  if (!screen) return;
  state.activeScreenId = id;

  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('previewCanvas').style.display = 'block';
  document.getElementById('propertiesPanel').style.display = 'block';

  preview.setScreen(screen);
  populateProperties(screen);
  renderScreenList();
}

function populateProperties(screen) {
  document.getElementById('propName').value     = screen.name;
  document.getElementById('propTileW').value    = screen.tile_width;
  document.getElementById('propTileH').value    = screen.tile_height;
  document.getElementById('propTilesW').value   = screen.tiles_w;
  document.getElementById('propTilesH').value   = screen.tiles_h;
  document.getElementById('propResolution').textContent = `${screen.width_px} × ${screen.height_px}`;
  document.getElementById('propTileRepo').value = '';
}

// ── CSV upload ─────────────────────────────────────────────────────────────────

async function handleCSVUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = '';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const data = await apiFetch('/api/upload-csv', { method: 'POST', body: formData });
    state.screens = data.screens;
    state.activeScreenId = null;
    renderScreenList();
    setButtonStates();
    if (state.screens.length > 0) selectScreen(state.screens[0].id);
  } catch (e) {
    alert('CSV upload failed: ' + e.message);
  }
}

// ── Add Screen modal ───────────────────────────────────────────────────────────

function openAddScreenModal() {
  document.getElementById('newScreenName').value  = '';
  document.getElementById('newScreenTileW').value = 60;
  document.getElementById('newScreenTileH').value = 60;
  document.getElementById('newScreenTilesW').value = 8;
  document.getElementById('newScreenTilesH').value = 6;
  document.getElementById('newScreenTileRepo').value = '';
  document.getElementById('addScreenError').classList.add('d-none');

  const modal = new bootstrap.Modal(document.getElementById('addScreenModal'));
  modal.show();
  setTimeout(() => document.getElementById('newScreenName').focus(), 300);
}

async function handleAddScreen() {
  const name    = document.getElementById('newScreenName').value.trim();
  const tileW   = parseFloat(document.getElementById('newScreenTileW').value);
  const tileH   = parseFloat(document.getElementById('newScreenTileH').value);
  const tilesW  = parseFloat(document.getElementById('newScreenTilesW').value);
  const tilesH  = parseFloat(document.getElementById('newScreenTilesH').value);

  const errEl = document.getElementById('addScreenError');
  if (!name) {
    errEl.textContent = 'Screen name is required.';
    errEl.classList.remove('d-none');
    document.getElementById('newScreenName').focus();
    return;
  }
  if ([tileW, tileH, tilesW, tilesH].some(v => isNaN(v) || v <= 0)) {
    errEl.textContent = 'All dimensions must be positive numbers.';
    errEl.classList.remove('d-none');
    return;
  }

  try {
    const result = await apiPost('/api/screens', {
      name,
      tile_width: tileW, tile_height: tileH,
      tiles_w: tilesW, tiles_h: tilesH,
    });

    bootstrap.Modal.getInstance(document.getElementById('addScreenModal')).hide();

    state.screens = result.screens;
    renderScreenList();
    setButtonStates();
    selectScreen(result.new_id);
  } catch (e) {
    errEl.textContent = e.message;
    errEl.classList.remove('d-none');
  }
}

function handleNewScreenTileRepoSelect() {
  const sel = document.getElementById('newScreenTileRepo');
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !opt.dataset.pixelWidth) return;
  document.getElementById('newScreenTileW').value = opt.dataset.pixelWidth;
  document.getElementById('newScreenTileH').value = opt.dataset.pixelHeight;
}

// ── Properties panel ───────────────────────────────────────────────────────────

async function handlePropertiesChange() {
  if (state.activeScreenId === null) return;

  const name   = document.getElementById('propName').value.trim();
  const tileW  = parseFloat(document.getElementById('propTileW').value);
  const tileH  = parseFloat(document.getElementById('propTileH').value);
  const tilesW = parseFloat(document.getElementById('propTilesW').value);
  const tilesH = parseFloat(document.getElementById('propTilesH').value);

  if (!name || [tileW, tileH, tilesW, tilesH].some(v => isNaN(v) || v <= 0)) return;

  try {
    const updated = await apiPatch(`/api/screens/${state.activeScreenId}`, {
      name, tile_width: tileW, tile_height: tileH, tiles_w: tilesW, tiles_h: tilesH,
    });

    const idx = state.screens.findIndex(s => s.id === state.activeScreenId);
    if (idx !== -1) state.screens[idx] = updated;

    document.getElementById('propResolution').textContent = `${updated.width_px} × ${updated.height_px}`;
    preview.setScreen(updated);
    renderScreenList();
  } catch (e) {
    console.error('Properties update failed:', e);
  }
}

function handleTileRepoSelect() {
  const sel = document.getElementById('propTileRepo');
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !opt.dataset.pixelWidth) return;
  document.getElementById('propTileW').value = opt.dataset.pixelWidth;
  document.getElementById('propTileH').value = opt.dataset.pixelHeight;
  handlePropertiesChange();
}

async function handleResetTiles() {
  if (state.activeScreenId === null) return;
  const screen = state.screens.find(s => s.id === state.activeScreenId);
  if (!screen) return;

  const rows = Math.ceil(screen.tiles_h);
  const cols = Math.ceil(screen.tiles_w);
  const enabledArray = Array.from({ length: rows }, () => Array(cols).fill(true));

  try {
    await apiPatch(`/api/screens/${state.activeScreenId}/tiles`, { enabled_array: enabledArray });
    screen.enabled_array = enabledArray;
    preview.updateEnabledArray(enabledArray);
  } catch (e) {
    console.error('Reset tiles failed:', e);
  }
}

async function handleClearAll() {
  if (!confirm('Clear all screens? This cannot be undone.')) return;
  try {
    await apiPost('/api/clear');
    state.screens = [];
    state.activeScreenId = null;
    renderScreenList();
    setButtonStates();
    document.getElementById('previewCanvas').style.display = 'none';
    document.getElementById('propertiesPanel').style.display = 'none';
    document.getElementById('emptyState').style.display = 'block';
  } catch (e) {
    alert('Failed to clear screens: ' + e.message);
  }
}

// ── Generation ─────────────────────────────────────────────────────────────────

async function handleGenerate() {
  const modalEl = document.getElementById('generateModal');
  const modal   = new bootstrap.Modal(modalEl);

  document.getElementById('generateStatus').textContent = 'Starting…';
  const bar = document.getElementById('generateProgressBar');
  bar.style.width = '0%';
  bar.classList.add('animated');
  document.getElementById('generateError').classList.add('d-none');
  document.getElementById('btnDownloadZip').classList.add('d-none');
  document.getElementById('btnCloseModal').classList.add('d-none');

  modal.show();

  try {
    const { job_id } = await apiPost('/api/generate');
    state.currentJobId = job_id;
    _pollJobStatus(job_id, modal);
  } catch (e) {
    _showGenerateError(e.message);
  }
}

function _pollJobStatus(jobId, modal) {
  if (state.pollInterval) clearInterval(state.pollInterval);

  state.pollInterval = setInterval(async () => {
    try {
      const job = await apiGet(`/api/generate/${jobId}/status`);
      const pct = job.total > 0 ? Math.round((job.progress / job.total) * 100) : 0;
      const bar = document.getElementById('generateProgressBar');
      bar.style.width = `${pct}%`;

      document.getElementById('generateStatus').textContent =
        `${job.progress} / ${job.total} screen${job.total !== 1 ? 's' : ''} complete`;

      if (job.status === 'complete') {
        clearInterval(state.pollInterval);
        bar.classList.remove('animated');
        bar.style.width = '100%';
        document.getElementById('generateStatus').textContent = 'Done — ready to download.';
        document.getElementById('btnDownloadZip').classList.remove('d-none');
        document.getElementById('btnCloseModal').classList.remove('d-none');

        document.getElementById('btnDownloadZip').onclick = () => {
          window.location.href = `/api/generate/${jobId}/download`;
          setTimeout(() => modal.hide(), 1200);
        };
      } else if (job.status === 'error') {
        clearInterval(state.pollInterval);
        _showGenerateError(job.error || 'An unknown error occurred.');
      }
    } catch (e) {
      clearInterval(state.pollInterval);
      _showGenerateError(e.message);
    }
  }, 1000);
}

function _showGenerateError(message) {
  document.getElementById('generateError').textContent = message;
  document.getElementById('generateError').classList.remove('d-none');
  document.getElementById('generateProgressBar').classList.remove('animated');
  document.getElementById('btnCloseModal').classList.remove('d-none');
}

// ── Boot ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
