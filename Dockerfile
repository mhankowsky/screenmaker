# ScreenMaker web app, containerised for Cloud Run (basecamp mode).
#
# Only the Flask app ships here. The desktop/PySide6 side of the repo (Main.py,
# ScreenMaker.spec, the pyinstaller deps in the root requirements.txt) is
# deliberately left out — web/requirements.txt is the web app's real dependency
# set, and pulling PySide6 in would add ~400 MB for nothing.
#
# src/ and lib/ still have to be present: web/app.py puts ../src on sys.path,
# and src/screens.py loads lib/font/RobotoMono-Light.ttf at import time (via
# root_dir = <repo root>), so the repo layout must be preserved inside /app.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY web/requirements.txt /app/web/requirements.txt
RUN pip install --no-cache-dir -r /app/web/requirements.txt gunicorn==23.0.0

COPY src/ /app/src/
COPY lib/ /app/lib/
COPY web/ /app/web/

# Saved screens live in session_store's SESSIONS_DIR, which is hardcoded to
# <web>/sessions with no env override. Cloud Run's container filesystem is
# ephemeral, so point that path at the mounted GCS volume instead. The tile
# database is redirected the same way but via env (APPDATA, read by
# DatabaseManager) — see the service's APPDATA=/data.
RUN rm -rf /app/web/sessions && ln -s /data/sessions /app/web/sessions

WORKDIR /app/web

# The mkdir is load-bearing: session_store.init() calls
# SESSIONS_DIR.mkdir(exist_ok=True), and on a *dangling* symlink that raises
# FileExistsError rather than passing (pathlib only swallows the error when the
# path is already a directory). So the symlink target has to exist before the
# app is imported.
#
# One worker, many threads, on purpose. Generation jobs live in an in-process
# dict (_jobs) and are polled by job_id, so a second worker would answer status
# and download requests it has never heard of. Keep this at -w 1 and keep the
# service at --max-instances=1 for the same reason.
CMD exec sh -c 'mkdir -p /data/sessions && exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 600 app:app'
