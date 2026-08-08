#!/usr/bin/env bash
# Deploy pines-reportcards on the production server.
# Run as: bash /var/www/reportcards.emcfunleague.com/source/deploy.sh
set -euo pipefail

SOURCE_DIR="/var/www/reportcards.emcfunleague.com/source"
VENV="$SOURCE_DIR/../venv/bin"

export DEBUG="false"
export ALLOWED_HOSTS="reportcards.emcfunleague.com"

cd "$SOURCE_DIR"

echo "==> Pulling latest code"
git pull

echo "==> Installing dependencies"
"$VENV/pip" install -r requirements.txt --quiet

echo "==> Running migrations"
"$VENV/python" manage.py migrate --noinput

echo "==> Collecting static files"
"$VENV/python" manage.py collectstatic --noinput

echo "==> Restarting gunicorn"
sudo systemctl restart gunicorn.reportcards

echo "==> Deploy complete"
