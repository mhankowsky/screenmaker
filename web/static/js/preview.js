/**
 * preview.js — Interactive HTML5 Canvas tile preview for ScreenMaker.
 *
 * Renders a grid of tiles for a given screen definition. Each tile can be
 * toggled enabled/disabled by clicking or click-dragging. Disabled tiles are
 * shown with a dark background and a red X; enabled tiles are gray.
 *
 * Usage:
 *   const preview = new ScreenPreview('previewCanvas');
 *   preview.onTilesChanged = (enabledArray) => { ... };
 *   preview.setScreen(screenObject);
 */
class ScreenPreview {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');

    /** @type {object|null} Current screen data (deep-copied on setScreen) */
    this.screen = null;

    /**
     * Flat list of tile layout rects:
     * [{x, y, w, h, row, col}, ...]
     */
    this.tileRects = [];
    this.scale = 1;

    this.isDragging = false;
    /** 'enable' | 'disable' | null — set on mousedown, consistent for the drag */
    this.dragMode = null;

    /**
     * Callback fired (debounced in app.js) whenever a tile is toggled.
     * Receives the full enabled_array.
     * @type {Function|null}
     */
    this.onTilesChanged = null;

    this.canvas.addEventListener('mousedown', this._onMouseDown.bind(this));
    this.canvas.addEventListener('mousemove', this._onMouseMove.bind(this));
    this.canvas.addEventListener('mouseup', this._onMouseUp.bind(this));
    this.canvas.addEventListener('mouseleave', this._onMouseUp.bind(this));
    // Prevent text selection while dragging
    this.canvas.addEventListener('selectstart', e => e.preventDefault());
  }

  /**
   * Load a new screen and re-render.
   * @param {object} screen  Plain screen dict from the API.
   */
  setScreen(screen) {
    this.screen = JSON.parse(JSON.stringify(screen)); // deep copy
    this._computeLayout();
    this.render();
  }

  /**
   * Replace just the enabled_array without re-computing layout (used for
   * external resets / server-side updates).
   * @param {boolean[][]} enabledArray
   */
  updateEnabledArray(enabledArray) {
    if (!this.screen) return;
    this.screen.enabled_array = enabledArray;
    this.render();
  }

  // ── Layout ──────────────────────────────────────────────────────────────

  _computeLayout() {
    const screen = this.screen;
    const container = this.canvas.parentElement;

    const maxW = Math.max(container.clientWidth - 40, 200);
    const maxH = Math.max(container.clientHeight - 40, 200);

    const rawW = screen.width_px;
    const rawH = screen.height_px;

    // Fit inside container, but never show tiles smaller than 12 px
    const minTilePx = 12;
    const minTileDim = Math.min(screen.tile_width, screen.tile_height);
    const scaleByContainer = Math.min(maxW / rawW, maxH / rawH);
    const scaleByMinTile = minTilePx / minTileDim;
    this.scale = Math.max(scaleByContainer, scaleByMinTile);

    this.canvas.width = Math.ceil(rawW * this.scale);
    this.canvas.height = Math.ceil(rawH * this.scale);

    // Pre-compute tile bounding boxes
    this.tileRects = [];
    const totalRows = Math.ceil(screen.tiles_h);
    const totalCols = Math.ceil(screen.tiles_w);
    let curY = 0;

    for (let i = 0; i < totalRows; i++) {
      const remainingH = screen.tiles_h - i;
      const isHalfRow = remainingH > 0 && remainingH < 1;
      const tileH = Math.round(screen.tile_height * (isHalfRow ? 0.5 : 1) * this.scale);
      let curX = 0;

      for (let j = 0; j < totalCols; j++) {
        const remainingW = screen.tiles_w - j;
        const isHalfCol = remainingW > 0 && remainingW < 1;
        const tileW = Math.round(screen.tile_width * (isHalfCol ? 0.5 : 1) * this.scale);

        this.tileRects.push({ x: curX, y: curY, w: tileW, h: tileH, row: i, col: j });
        curX += tileW;
      }
      curY += tileH;
    }
  }

  // ── Rendering ────────────────────────────────────────────────────────────

  render() {
    if (!this.screen) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (const tile of this.tileRects) {
      const enabled = this.screen.enabled_array[tile.row]?.[tile.col] ?? true;

      if (enabled) {
        // Enabled tile: medium gray with subtle border
        ctx.fillStyle = '#323232';
        ctx.fillRect(tile.x, tile.y, tile.w, tile.h);

        ctx.strokeStyle = '#484848';
        ctx.lineWidth = 1;
        ctx.strokeRect(tile.x + 0.5, tile.y + 0.5, tile.w - 1, tile.h - 1);

        // Tile coordinate label (only when tiles are large enough to read)
        if (tile.w >= 30 && tile.h >= 20) {
          const fontSize = Math.min(11, Math.floor(tile.h * 0.28));
          ctx.fillStyle = 'rgba(255,255,255,0.25)';
          ctx.font = `${fontSize}px monospace`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${tile.col + 1},${tile.row + 1}`, tile.x + tile.w / 2, tile.y + tile.h / 2);
        }
      } else {
        // Disabled tile: very dark bg + red X
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(tile.x, tile.y, tile.w, tile.h);

        ctx.strokeStyle = '#2e2e2e';
        ctx.lineWidth = 1;
        ctx.strokeRect(tile.x + 0.5, tile.y + 0.5, tile.w - 1, tile.h - 1);

        const pad = Math.max(4, Math.min(tile.w, tile.h) * 0.22);
        ctx.strokeStyle = 'rgba(220, 50, 50, 0.65)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(tile.x + pad, tile.y + pad);
        ctx.lineTo(tile.x + tile.w - pad, tile.y + tile.h - pad);
        ctx.moveTo(tile.x + tile.w - pad, tile.y + pad);
        ctx.lineTo(tile.x + pad, tile.y + tile.h - pad);
        ctx.stroke();
      }
    }
  }

  // ── Interaction ──────────────────────────────────────────────────────────

  _canvasPoint(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    // Account for CSS scaling (if the element is CSS-sized differently from canvas px)
    const scaleX = this.canvas.width / rect.width;
    const scaleY = this.canvas.height / rect.height;
    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY,
    };
  }

  _getTileAt(clientX, clientY) {
    const { x, y } = this._canvasPoint(clientX, clientY);
    return this.tileRects.find(t => x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h) ?? null;
  }

  _paintTile(row, col) {
    const current = this.screen.enabled_array[row][col];
    const desired = this.dragMode === 'enable';
    if (current === desired) return; // already in target state
    this.screen.enabled_array[row][col] = desired;
    this.render();
    if (this.onTilesChanged) {
      this.onTilesChanged(this.screen.enabled_array);
    }
  }

  _onMouseDown(e) {
    if (e.button !== 0) return;
    const tile = this._getTileAt(e.clientX, e.clientY);
    if (!tile) return;
    // Drag mode is opposite of what the tile currently is
    this.dragMode = this.screen.enabled_array[tile.row][tile.col] ? 'disable' : 'enable';
    this.isDragging = true;
    this._paintTile(tile.row, tile.col);
  }

  _onMouseMove(e) {
    if (!this.isDragging) return;
    const tile = this._getTileAt(e.clientX, e.clientY);
    if (tile) this._paintTile(tile.row, tile.col);
  }

  _onMouseUp() {
    this.isDragging = false;
    this.dragMode = null;
  }
}
