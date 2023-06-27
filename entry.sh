#!/bin/sh
set -e
exec python3 ./app.py &
exec python3 ./app_admin.py
