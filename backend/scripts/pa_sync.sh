#!/usr/bin/env bash
# One-command PythonAnywhere sync & reload.
# 1. Run this from the PythonAnywhere Bash console.
# 2. It pulls latest code, installs deps, and reloads the web app.
# 3. Set PA_API_TOKEN env var in your PythonAnywhere account's
#    "Environment variables" (Web tab) before running.

set -e

APP_DIR=~/signaldesk/backend
WEBAPP="$USER.pythonanywhere.com"

echo "=== Pulling latest code ==="
cd ~/signaldesk
git pull

echo "=== Installing dependencies ==="
cd "$APP_DIR"
source venv/bin/activate
pip install -q -r requirements.txt

echo "=== Reloading web app ==="
if [ -n "$PA_API_TOKEN" ]; then
    curl -s -X POST \
        "https://www.pythonanywhere.com/api/v0/user/$USER/webapps/$WEBAPP/reload/" \
        -H "Authorization: Token $PA_API_TOKEN"
    echo ""
    echo "=== Reload triggered ==="
else
    echo "PA_API_TOKEN not set. Reload manually from the Web tab."
fi
