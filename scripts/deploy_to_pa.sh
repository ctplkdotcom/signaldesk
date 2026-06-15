#!/usr/bin/env bash
# Deploy helper for PythonAnywhere — run this from a PA Bash console.
# Usage:  bash scripts/deploy_to_pa.sh
set -euo pipefail

REPO_DIR="$HOME/fp"
DOMAIN="${USER}.pythonanywhere.com"

echo "=== Signal Desk — PythonAnywhere Deploy ==="
echo "  Repo:  $REPO_DIR"
echo "  User:  $USER"
echo "  Domain: $DOMAIN"

# 1. Pull latest code
echo ""
echo "--- Pulling latest code ---"
cd "$REPO_DIR"
git pull

# 2. Install / update deps
echo ""
echo "--- Installing Python dependencies ---"
cd "$REPO_DIR/backend"
source venv/bin/activate
pip install -r requirements.txt -q

# 3. Run migrations if using real DB (optional)
if [ "${USE_REAL_APP:-false}" = "true" ]; then
    echo ""
    echo "--- Running DB migrations ---"
    alembic upgrade head
fi

# 4. Reload the ASGI web app
echo ""
echo "--- Reloading web app ---"
pa website reload --domain "$DOMAIN"

echo ""
echo "=== Done! Site should be live at https://$DOMAIN ==="