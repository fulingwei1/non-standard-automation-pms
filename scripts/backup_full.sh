#!/bin/bash
# 完整备份脚本（数据库 + 文件）
# 用途: 每周执行完整备份

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "========== 开始完整备份（数据库 + 文件） =========="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FULL_BACKUP_DIR="${BACKUP_DIR}/full_${TIMESTAMP}"
mkdir -p "${FULL_BACKUP_DIR}"

# 1. 执行数据库备份
log "执行数据库备份..."
if bash "${SCRIPT_DIR}/backup_database.sh"; then
    log "✅ 数据库备份完成"
    DB_SUCCESS=1
else
    log "❌ 数据库备份失败"
    DB_SUCCESS=0
fi

# 2. 执行文件备份
log "执行文件备份..."
if bash "${SCRIPT_DIR}/backup_files.sh"; then
    log "✅ 文件备份完成"
    FILES_SUCCESS=1
else
    log "❌ 文件备份失败"
    FILES_SUCCESS=0
fi

# 3. 打包完整备份（可选）
log "创建完整备份归档..."
FULL_ARCHIVE="${BACKUP_DIR}/pms_full_${TIMESTAMP}.tar.gz"

tar -czf "${FULL_ARCHIVE}" \
    -C "${BACKUP_DIR}" \
    $(find "${BACKUP_DIR}" -name "*${TIMESTAMP}*" -type f -exec basename {} \;) 2>/dev/null || true

if [ -f "${FULL_ARCHIVE}" ]; then
    ARCHIVE_SIZE=$(du -h "${FULL_ARCHIVE}" | awk '{print $1}')
    log "✅ 完整归档创建完成: ${ARCHIVE_SIZE}"
    
    # 计算MD5
    if command -v md5sum &> /dev/null; then
        md5sum "${FULL_ARCHIVE}" | awk '{print $1}' > "${FULL_ARCHIVE}.md5"
    elif command -v md5 &> /dev/null; then
        md5 -q "${FULL_ARCHIVE}" > "${FULL_ARCHIVE}.md5"
    fi
    
    # 上传完整归档到OSS
    if command -v ossutil &> /dev/null && [ -n "${OSS_BUCKET}" ]; then
        ossutil cp "${FULL_ARCHIVE}" "oss://${OSS_BUCKET}/full/" --force 2>/dev/null
        log "✅ 完整归档已上传到OSS"
    fi
fi

# 发送汇总通知
if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
    STATUS="✅ 完整备份成功"
    [ $DB_SUCCESS -eq 0 ] && STATUS="⚠️ 完整备份部分失败（数据库）"
    [ $FILES_SUCCESS -eq 0 ] && STATUS="⚠️ 完整备份部分失败（文件）"
    [ $DB_SUCCESS -eq 0 ] && [ $FILES_SUCCESS -eq 0 ] && STATUS="❌ 完整备份失败"
    
    curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{
            \"msgtype\": \"text\",
            \"text\": {
                \"content\": \"${STATUS}\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n归档大小: ${ARCHIVE_SIZE:-N/A}\n数据库: $([ $DB_SUCCESS -eq 1 ] && echo '✅' || echo '❌')\n文件: $([ $FILES_SUCCESS -eq 1 ] && echo '✅' || echo '❌')\"
            }
        }" > /dev/null 2>&1
fi

log "========== 完整备份流程结束 =========="
exit 0
