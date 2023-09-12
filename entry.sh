#!/bin/sh
set -e
exec gunicorn app:app --workers 4 --timeout 150 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT &
exec python3 ./app_admin.py
# exec python3 ./app.py &