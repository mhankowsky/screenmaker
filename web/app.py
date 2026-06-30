"""ScreenMaker Flask web application."""

import sys
import os
import uuid
import csv
import math
import zipfile
import tempfile
import threading
import shutil
import io
from pathlib import Path
from functools import wraps

# Make src/ importable
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from flask import (
    Flask, request, session, jsonify, send_file,
    render_template, redirect, url_for,
)
import session_store
from screens import Screen, ScreenList, ScreenDrawer
from database import DatabaseManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['PERMANENT_SESSION_LIFETIME'] = 7 * 24 * 3600  # 7 days
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

PASSWORD = os.environ.get('SCREENMAKER_PASSWORD', 'screenmaker')

# In-process job store  { job_id: {status, progress, total, zip_path, error} }
_jobs: dict = {}
_jobs_lock = threading.Lock()

session_store.init()


# ── Helpers ────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


def screen_to_dict(screen: Screen) -> dict:
    return {
        'id': screen.num,
        'name': screen.name,
        'tile_width': screen.tile_width,
        'tile_height': screen.tile_height,
        'tiles_w': screen.tiles_w,
        'tiles_h': screen.tiles_h,
        'enabled_array': screen.enabled_array,
        'color_hue': screen.colorBGHue,
        'width_px': screen.width,
        'height_px': screen.height,
    }


def dict_to_screen(d: dict) -> Screen:
    screen = Screen(
        name=d['name'],
        tile_width=d['tile_width'],
        tile_height=d['tile_height'],
        tiles_w=d['tiles_w'],
        tiles_h=d['tiles_h'],
        num=d['id'],
        enabled_array=d['enabled_array'],
    )
    screen.colorBGHue = d.get('color_hue', 0)
    return screen


def resize_enabled_array(old_array: list, new_rows: int, new_cols: int) -> list:
    """Grow or shrink enabled_array; new cells default to True."""
    result = []
    for r in range(new_rows):
        row = []
        for c in range(new_cols):
            if r < len(old_array) and c < len(old_array[r]):
                row.append(old_array[r][c])
            else:
                row.append(True)
        result.append(row)
    return result


def _get_session_screens() -> list:
    sid = session.get('session_id')
    if not sid:
        return []
    return session_store.get(sid).get('screens', [])


def _save_session_screens(screens: list):
    sid = session.get('session_id')
    if not sid:
        return
    data = session_store.get(sid)
    data['screens'] = screens
    session_store.save(sid, data)


def _cleanup_job(job_id: str, zip_path: str):
    try:
        os.unlink(zip_path)
    except Exception:
        pass
    with _jobs_lock:
        _jobs.pop(job_id, None)


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if session.get('authenticated'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        if request.form.get('password', '') == PASSWORD:
            session.permanent = True
            session['authenticated'] = True
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            return redirect(url_for('index'))
        error = 'Incorrect password.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


# ── Screen API ─────────────────────────────────────────────────────────────────

def _recalculate_hues(screens: list):
    """Evenly distribute HSV hues across all screens."""
    n = len(screens)
    if n == 0:
        return
    offset = int(360 / n)
    for i, s in enumerate(screens):
        s['color_hue'] = i * offset


@app.route('/api/screens', methods=['GET'])
@login_required
def get_screens():
    return jsonify(_get_session_screens())


@app.route('/api/screens', methods=['POST'])
@login_required
def create_screen():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400

    try:
        tile_width = float(data.get('tile_width', 60))
        tile_height = float(data.get('tile_height', 60))
        tiles_w = float(data.get('tiles_w', 8))
        tiles_h = float(data.get('tiles_h', 6))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid numeric values'}), 400

    screens = _get_session_screens()
    new_id = max((s['id'] for s in screens), default=-1) + 1

    screen = Screen(
        name=name,
        tile_width=tile_width,
        tile_height=tile_height,
        tiles_w=tiles_w,
        tiles_h=tiles_h,
        num=new_id,
    )
    screen_dict = screen_to_dict(screen)
    screens.append(screen_dict)
    _recalculate_hues(screens)
    _save_session_screens(screens)

    return jsonify({'screens': screens, 'new_id': new_id}), 201


@app.route('/api/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    f = request.files['file']
    if not f.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a .csv'}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            f.save(tmp)
            tmp_path = tmp.name

        screen_list = ScreenList(tmp_path)
        if not screen_list.screens:
            return jsonify({
                'error': (
                    'Could not parse CSV. '
                    'Required columns: WALL, Tile_Px_Width, Tile_Px_Height, '
                    'Tiles_Wide, Tiles_High'
                )
            }), 400

        screens_data = [screen_to_dict(s) for s in screen_list.screens]
        _save_session_screens(screens_data)
        return jsonify({'screens': screens_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.route('/api/screens/<int:screen_id>', methods=['PATCH'])
@login_required
def update_screen(screen_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    screens = _get_session_screens()
    screen_dict = next((s for s in screens if s['id'] == screen_id), None)
    if screen_dict is None:
        return jsonify({'error': 'Screen not found'}), 404

    for key in ('name', 'tile_width', 'tile_height', 'tiles_w', 'tiles_h'):
        if key in data:
            screen_dict[key] = data[key]

    # Recalculate pixel dimensions
    screen_dict['width_px'] = int(screen_dict['tile_width'] * screen_dict['tiles_w'])
    screen_dict['height_px'] = int(screen_dict['tile_height'] * screen_dict['tiles_h'])

    # Resize enabled_array if tile counts changed
    new_rows = math.ceil(screen_dict['tiles_h'])
    new_cols = math.ceil(screen_dict['tiles_w'])
    old_array = screen_dict['enabled_array']
    if new_rows != len(old_array) or new_cols != (len(old_array[0]) if old_array else 0):
        screen_dict['enabled_array'] = resize_enabled_array(old_array, new_rows, new_cols)

    _save_session_screens(screens)
    return jsonify(screen_dict)


@app.route('/api/screens/<int:screen_id>/tiles', methods=['PATCH'])
@login_required
def update_tiles(screen_id):
    data = request.get_json()
    if not data or 'enabled_array' not in data:
        return jsonify({'error': 'enabled_array required'}), 400

    screens = _get_session_screens()
    screen_dict = next((s for s in screens if s['id'] == screen_id), None)
    if screen_dict is None:
        return jsonify({'error': 'Screen not found'}), 404

    screen_dict['enabled_array'] = data['enabled_array']
    _save_session_screens(screens)
    return jsonify({'ok': True})


@app.route('/api/clear', methods=['POST'])
@login_required
def clear_all():
    sid = session.get('session_id')
    if sid:
        session_store.clear_screens(sid)
    return jsonify({'ok': True})


@app.route('/api/export-csv')
@login_required
def export_csv():
    screens = _get_session_screens()
    if not screens:
        return jsonify({'error': 'No screens to export'}), 400

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['WALL', 'Tile_Px_Width', 'Tile_Px_Height', 'Tiles_Wide', 'Tiles_High', 'Enabled_Array'])
    for s in screens:
        enabled_str = ';'.join(
            ''.join(str(int(v)) for v in row)
            for row in s['enabled_array']
        )
        writer.writerow([
            s['name'], s['tile_width'], s['tile_height'],
            s['tiles_w'], s['tiles_h'], enabled_str,
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='screens.csv',
    )


# ── LED Tile Repository ────────────────────────────────────────────────────────

@app.route('/api/tiles', methods=['GET'])
@login_required
def get_tiles():
    return jsonify(DatabaseManager().get_all_tiles())


@app.route('/api/tiles', methods=['POST'])
@login_required
def add_tile():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name required'}), 400
    tile_id = DatabaseManager().add_tile(data)
    return jsonify({'id': tile_id}), 201


# ── Image Generation ───────────────────────────────────────────────────────────

def _run_generation(job_id: str, screens: list):
    """Background worker: generate PNGs for all screens and zip the results."""
    tmp_dir = None
    try:
        with _jobs_lock:
            _jobs[job_id]['status'] = 'running'

        tmp_dir = tempfile.mkdtemp(prefix='screenmaker_')
        output_path = Path(tmp_dir)
        for subdir in ('01_Content_Blocks', '02_Eng_Blocks', '03_Stealth_Blocks'):
            (output_path / subdir).mkdir()

        for i, screen in enumerate(screens):
            drawer = ScreenDrawer(screen, output_path)
            drawer.draw_content()
            drawer.draw_eng()
            drawer.draw_stealth()
            with _jobs_lock:
                _jobs[job_id]['progress'] = i + 1

        # Build ZIP from generated PNGs
        zip_fd, zip_path = tempfile.mkstemp(suffix='.zip', prefix='screenmaker_out_')
        os.close(zip_fd)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for png in sorted(output_path.rglob('*.png')):
                zf.write(png, png.relative_to(output_path))

        with _jobs_lock:
            _jobs[job_id]['status'] = 'complete'
            _jobs[job_id]['zip_path'] = zip_path

    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]['status'] = 'error'
            _jobs[job_id]['error'] = str(e)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@app.route('/api/generate', methods=['POST'])
@login_required
def generate():
    screens_data = _get_session_screens()
    if not screens_data:
        return jsonify({'error': 'No screens loaded'}), 400

    screens = [dict_to_screen(s) for s in screens_data]
    job_id = str(uuid.uuid4())

    with _jobs_lock:
        _jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'total': len(screens),
            'zip_path': None,
            'error': None,
        }

    thread = threading.Thread(target=_run_generation, args=(job_id, screens), daemon=True)
    thread.start()
    return jsonify({'job_id': job_id})


@app.route('/api/generate/<job_id>/status')
@login_required
def job_status(job_id):
    with _jobs_lock:
        job = dict(_jobs.get(job_id, {}))
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    # Don't send the local filesystem path to the client
    job.pop('zip_path', None)
    return jsonify(job)


@app.route('/api/generate/<job_id>/download')
@login_required
def download_zip(job_id):
    with _jobs_lock:
        job = dict(_jobs.get(job_id, {}))

    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if job.get('status') != 'complete':
        return jsonify({'error': 'Job not complete'}), 400

    zip_path = job.get('zip_path')
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({'error': 'Output file not found'}), 404

    # Schedule cleanup 60 s after the response is sent
    timer = threading.Timer(60, _cleanup_job, args=[job_id, zip_path])
    timer.daemon = True
    timer.start()

    return send_file(zip_path, as_attachment=True, download_name='screenmaker_output.zip')


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8088))
    app.run(debug=True, host='0.0.0.0', port=port)
