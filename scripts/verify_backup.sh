#!/bin/bash
# Verify a compressed SQLite SQL dump.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

show_usage() {
    echo "Usage: $0 [backup_file]"
    echo "Without a file, the latest ${BACKUP_DIR}/pms_*.sql.gz is verified."
    exit 1
}

log "========== SQLite backup verification =========="

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    error_exit "Python executable not found: ${PYTHON_BIN}"
fi

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    show_usage
fi

if [ -z "${1:-}" ]; then
    BACKUP_FILE=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -type f 2>/dev/null | sort -r | head -n 1)
    if [ -z "${BACKUP_FILE}" ]; then
        error_exit "No backup file found"
    fi
else
    BACKUP_FILE="$1"
    if [ ! -f "${BACKUP_FILE}" ] && [[ "${BACKUP_FILE}" != /* ]]; then
        BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
    fi
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "Backup file does not exist: ${BACKUP_FILE}"
fi

if [ ! -s "${BACKUP_FILE}" ]; then
    error_exit "Backup file is empty: ${BACKUP_FILE}"
fi

log "Verifying file: ${BACKUP_FILE}"

if ! VERIFY_OUTPUT=$("${PYTHON_BIN}" - "${BACKUP_FILE}" <<'PY'
import gzip
import hashlib
import sqlite3
import sys
from pathlib import Path

backup_file = Path(sys.argv[1])
md5_file = Path(str(backup_file) + ".md5")

if not md5_file.exists():
    print(f"Missing checksum file: {md5_file}", file=sys.stderr)
    sys.exit(1)

checksum_parts = md5_file.read_text(encoding="utf-8").strip().split()
expected = checksum_parts[0] if checksum_parts else ""
if not expected:
    print(f"Empty checksum file: {md5_file}", file=sys.stderr)
    sys.exit(1)

actual = hashlib.md5(backup_file.read_bytes()).hexdigest()
if expected != actual:
    print(f"MD5 mismatch: expected {expected}, actual {actual}", file=sys.stderr)
    sys.exit(1)

try:
    with gzip.open(backup_file, "rt", encoding="utf-8") as fh:
        sql_dump = fh.read()
except Exception as exc:
    print(f"Invalid gzip or text dump: {exc}", file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(":memory:")
try:
    conn.executescript(sql_dump)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        print(f"SQLite integrity_check failed: {integrity}", file=sys.stderr)
        sys.exit(1)
    table_count = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
finally:
    conn.close()

insert_count = sql_dump.count("INSERT INTO")
print(f"SQLite backup OK; tables={table_count}; inserts={insert_count}")
PY
); then
    error_exit "${VERIFY_OUTPUT:-SQLite backup verification failed}"
fi

log "${VERIFY_OUTPUT}"
log "========== Verification passed =========="
exit 0
