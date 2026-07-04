#!/bin/bash
# Restore the active SQLite database from a compressed SQL dump.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
DATABASE_URL="${DATABASE_URL:-sqlite:///data/app.db}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIRM_RESTORE="${CONFIRM_RESTORE:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

show_usage() {
    echo "Usage: $0 <backup_file>"
    echo "Set CONFIRM_RESTORE=yes for non-interactive restore."
    exit 1
}

if [ -z "${1:-}" ]; then
    show_usage
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    error_exit "Python executable not found: ${PYTHON_BIN}"
fi

BACKUP_FILE="$1"
if [ ! -f "${BACKUP_FILE}" ] && [[ "${BACKUP_FILE}" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "Backup file does not exist: ${BACKUP_FILE}"
fi

if ! DB_PATH=$("${PYTHON_BIN}" - "${DATABASE_URL}" <<'PY'
import sys

url = sys.argv[1]
if not url.startswith("sqlite:///") or url in {"sqlite:///:memory:", "sqlite:///"}:
    print("Only file-backed sqlite:/// DATABASE_URL is supported", file=sys.stderr)
    sys.exit(1)
print(url.replace("sqlite:///", "", 1))
PY
); then
    error_exit "DATABASE_URL must be a file-backed sqlite:/// URL"
fi

log "========== SQLite database restore =========="
log "Backup file: ${BACKUP_FILE}"
log "Target database: ${DB_PATH}"

if [ "${CONFIRM_RESTORE}" != "yes" ]; then
    echo "This will replace the target SQLite database: ${DB_PATH}"
    read -r -p "Type yes to continue: " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
fi

bash "${SCRIPT_DIR}/verify_backup.sh" "${BACKUP_FILE}" >/dev/null

mkdir -p "${BACKUP_DIR}"

if ! RESTORE_OUTPUT=$("${PYTHON_BIN}" - "${BACKUP_FILE}" "${DB_PATH}" "${BACKUP_DIR}" <<'PY'
import gzip
import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

backup_file = Path(sys.argv[1])
db_path = Path(sys.argv[2])
backup_dir = Path(sys.argv[3])
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
pre_restore = None

db_path.parent.mkdir(parents=True, exist_ok=True)
backup_dir.mkdir(parents=True, exist_ok=True)

if db_path.exists() and db_path.stat().st_size > 0:
    pre_restore = backup_dir / f"before_restore_{timestamp}.sql.gz"
    source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        with gzip.open(pre_restore, "wt", encoding="utf-8") as fh:
            for line in source.iterdump():
                fh.write(f"{line}\n")
    finally:
        source.close()
    digest = hashlib.md5(pre_restore.read_bytes()).hexdigest()
    Path(str(pre_restore) + ".md5").write_text(digest, encoding="utf-8")

with gzip.open(backup_file, "rt", encoding="utf-8") as fh:
    sql_dump = fh.read()

restore_tmp = db_path.with_name(f".{db_path.name}.restore-{os.getpid()}.tmp")
if restore_tmp.exists():
    restore_tmp.unlink()

conn = sqlite3.connect(restore_tmp)
try:
    conn.executescript(sql_dump)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
finally:
    conn.close()

if integrity != "ok":
    restore_tmp.unlink(missing_ok=True)
    print(f"Restored SQLite integrity_check failed: {integrity}", file=sys.stderr)
    sys.exit(1)

for sidecar_name in (f"{db_path}-wal", f"{db_path}-shm"):
    sidecar = Path(sidecar_name)
    if sidecar.exists():
        sidecar.unlink()

os.replace(restore_tmp, db_path)
print(f"SQLite restore OK; pre_restore_backup={pre_restore or ''}")
PY
); then
    error_exit "${RESTORE_OUTPUT:-SQLite restore failed}"
fi

log "${RESTORE_OUTPUT}"
log "========== Restore completed =========="
exit 0
