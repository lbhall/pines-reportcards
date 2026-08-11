#!/usr/bin/env bash
# Nightly sqlite backup for pines-reportcards. Install on the server with:
#   crontab -e   →   15 2 * * * bash /var/www/reportcards.emcfunleague.com/source/backup.sh
# Keeps 30 days of gzipped backups in ../backups.
set -euo pipefail

SOURCE_DIR="/var/www/reportcards.emcfunleague.com/source"
VENV="$SOURCE_DIR/../venv/bin"
BACKUP_DIR="$SOURCE_DIR/../backups"
DB_PATH="${DJANGO_DB_PATH:-$SOURCE_DIR/../data/db.sqlite3}"
if [[ ! -f "$DB_PATH" ]]; then
    DB_PATH="$SOURCE_DIR/db.sqlite3"
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y-%m-%d)"
OUT="$BACKUP_DIR/db-$STAMP.sqlite3"

# sqlite's online-backup API is safe against concurrent writes (plain cp is not).
"$VENV/python" - "$DB_PATH" "$OUT" <<'PY'
import sqlite3
import sys

src_path, dest_path = sys.argv[1], sys.argv[2]
src = sqlite3.connect(src_path)
dest = sqlite3.connect(dest_path)
with dest:
    src.backup(dest)
dest.close()
src.close()
PY

gzip -f "$OUT"
find "$BACKUP_DIR" -name 'db-*.sqlite3.gz' -mtime +30 -delete

echo "Backed up $DB_PATH -> $OUT.gz"
