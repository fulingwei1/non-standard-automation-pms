#!/bin/bash
# Database backup script for the active SQLite database.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
DATABASE_URL="${DATABASE_URL:-sqlite:///data/app.db}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OSS_BUCKET="${OSS_BUCKET:-}"
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
        curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"PMS database backup failed: $1\"}}" \
            > /dev/null 2>&1 || true
    fi
    exit 1
}

log "========== Starting SQLite database backup =========="

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    error_exit "Python executable not found: ${PYTHON_BIN}"
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

mkdir -p "${BACKUP_DIR}" || error_exit "Unable to create backup dir: ${BACKUP_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pms_${TIMESTAMP}.sql.gz"

log "Database file: ${DB_PATH}"
log "Backup file: ${BACKUP_FILE}"

if ! MD5SUM=$("${PYTHON_BIN}" - "${DB_PATH}" "${BACKUP_FILE}" <<'PY'
import gzip
import hashlib
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
backup_file = Path(sys.argv[2])

if not db_path.exists():
    print(f"SQLite database does not exist: {db_path}", file=sys.stderr)
    sys.exit(1)

backup_file.parent.mkdir(parents=True, exist_ok=True)
source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
try:
    with gzip.open(backup_file, "wt", encoding="utf-8") as fh:
        for line in source.iterdump():
            fh.write(f"{line}\n")
finally:
    source.close()

digest = hashlib.md5(backup_file.read_bytes()).hexdigest()
Path(str(backup_file) + ".md5").write_text(digest, encoding="utf-8")
print(digest)
PY
); then
    error_exit "SQLite dump failed"
fi

if [ ! -s "${BACKUP_FILE}" ]; then
    error_exit "Backup file was not created or is empty"
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | awk '{print $1}')
BACKUP_SIZE_BYTES=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo "0")

log "SQLite database backup completed"
log "  file: ${BACKUP_FILE}"
log "  size: ${BACKUP_SIZE} (${BACKUP_SIZE_BYTES} bytes)"
log "  md5: ${MD5SUM}"

if command -v ossutil >/dev/null 2>&1 && [ -n "${OSS_BUCKET}" ]; then
    log "Uploading backup to OSS bucket ${OSS_BUCKET}"
    ossutil cp "${BACKUP_FILE}" "oss://${OSS_BUCKET}/database/" --force 2>/dev/null || \
        log "WARN: OSS upload failed, local backup remains available"
    ossutil cp "${BACKUP_FILE}.md5" "oss://${OSS_BUCKET}/database/" --force 2>/dev/null || true
else
    log "Skipping OSS upload"
fi

log "Cleaning old backups older than ${RETENTION_DAYS} days"
find "${BACKUP_DIR}" -name "pms_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "pms_*.sql.gz.md5" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true

if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
    curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"PMS SQLite backup succeeded: ${BACKUP_SIZE}\"}}" \
        > /dev/null 2>&1 || true
fi

log "========== Backup completed =========="
exit 0
