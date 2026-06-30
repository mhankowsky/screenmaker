"""Disk-backed session store for ScreenMaker web app.

Each session is stored as a JSON file in the sessions/ directory, keyed by
a UUID that is kept in the Flask signed-cookie session. An in-memory cache
speeds up repeated requests without hitting the filesystem every time.

Sessions expire after SESSION_TTL seconds (7 days) of inactivity.
"""

import json
import time
import threading
from pathlib import Path

SESSIONS_DIR = Path(__file__).parent / 'sessions'
SESSION_TTL = 7 * 24 * 3600  # 7 days in seconds

_cache: dict = {}
_lock = threading.Lock()


def init():
    """Create the sessions directory if it does not exist."""
    SESSIONS_DIR.mkdir(exist_ok=True)


def _path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def get(session_id: str) -> dict:
    """Return session data for *session_id*.

    Creates and persists a fresh empty session if none exists or if the
    existing session has expired.
    """
    with _lock:
        # Fast path: already in memory
        if session_id in _cache:
            _cache[session_id]['last_accessed'] = time.time()
            _write(session_id, _cache[session_id])
            return _cache[session_id]

        # Try loading from disk
        p = _path(session_id)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                if time.time() - data.get('last_accessed', 0) < SESSION_TTL:
                    data['last_accessed'] = time.time()
                    _cache[session_id] = data
                    _write(session_id, data)
                    return data
                # Expired — fall through to create a fresh session
                p.unlink(missing_ok=True)
            except (json.JSONDecodeError, OSError):
                pass

        # New session
        data = {'screens': [], 'last_accessed': time.time()}
        _cache[session_id] = data
        _write(session_id, data)
        return data


def save(session_id: str, data: dict):
    """Persist *data* for *session_id* to cache and disk."""
    data['last_accessed'] = time.time()
    with _lock:
        _cache[session_id] = data
        _write(session_id, data)


def clear_screens(session_id: str):
    """Remove all screens from a session without deleting the session."""
    data = get(session_id)
    data['screens'] = []
    save(session_id, data)


def _write(session_id: str, data: dict):
    _path(session_id).write_text(json.dumps(data), encoding='utf-8')


def cleanup_expired():
    """Delete session files and cache entries older than SESSION_TTL."""
    now = time.time()
    with _lock:
        for p in SESSIONS_DIR.glob('*.json'):
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                if now - data.get('last_accessed', 0) >= SESSION_TTL:
                    p.unlink(missing_ok=True)
                    _cache.pop(p.stem, None)
            except Exception:
                p.unlink(missing_ok=True)
