#!/bin/bash
# 数据库备份脚本
# 用途: 自动备份MySQL数据库并上传到远程存储

set -e

# ==================== 配置区域 ====================
BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-pms}"
DB_USER="${DB_USER:-pms_user}"
DB_PASS="${MYSQL_PASSWORD}"  # 从环境变量读取
RETENTION_DAYS="${RETENTION_DAYS:-7}"
OSS_BUCKET="${OSS_BUCKET:-pms-backups}"  # 阿里云OSS存储桶
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"  # 企业微信webhook

# ==================== 函数定义 ====================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ 错误: $1"
    # 发送失败通知
    if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
        curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{
                \"msgtype\": \"text\",
                \"text\": {
                    \"content\": \"❌ PMS数据库备份失败\n时间: $(date)\n错误: $1\"
                }
            }" > /dev/null 2>&1
    fi
    exit 1
}

# ==================== 主程序 ====================
log "========== 开始数据库备份 =========="

# 检查必需环境变量
if [ -z "${DB_PASS}" ]; then
    error_exit "MYSQL_PASSWORD 环境变量未设置"
fi

# 创建备份目录
mkdir -p "${BACKUP_DIR}" || error_exit "无法创建备份目录: ${BACKUP_DIR}"

# 备份文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pms_${TIMESTAMP}.sql.gz"

log "数据库: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log "备份文件: ${BACKUP_FILE}"

# 检查mysqldump是否存在
if ! command -v mysqldump &> /dev/null; then
    error_exit "mysqldump 命令不存在，请安装 MySQL 客户端"
fi

# 执行mysqldump并压缩
log "正在执行数据库导出..."
mysqldump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --password="${DB_PASS}" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --databases "${DB_NAME}" \
    2>/dev/null | gzip > "${BACKUP_FILE}" || error_exit "数据库备份失败"

# 检查备份文件是否创建成功
if [ ! -f "${BACKUP_FILE}" ] || [ ! -s "${BACKUP_FILE}" ]; then
    error_exit "备份文件创建失败或为空"
fi

# 计算MD5校验和
log "计算MD5校验和..."
if command -v md5sum &> /dev/null; then
    MD5SUM=$(md5sum "${BACKUP_FILE}" | awk '{print $1}')
elif command -v md5 &> /dev/null; then
    # macOS 使用 md5 命令
    MD5SUM=$(md5 -q "${BACKUP_FILE}")
else
    log "⚠️  警告: 无法计算MD5校验和（md5sum/md5 命令不存在）"
    MD5SUM="N/A"
fi

if [ "${MD5SUM}" != "N/A" ]; then
    echo "${MD5SUM}" > "${BACKUP_FILE}.md5"
    log "MD5校验和: ${MD5SUM}"
fi

# 获取备份大小
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | awk '{print $1}')
BACKUP_SIZE_BYTES=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo "0")

log "✅ 数据库备份完成"
log "  文件: ${BACKUP_FILE}"
log "  大小: ${BACKUP_SIZE} (${BACKUP_SIZE_BYTES} bytes)"
log "  MD5: ${MD5SUM}"

# 上传到阿里云OSS（可选）
if command -v ossutil &> /dev/null && [ -n "${OSS_BUCKET}" ]; then
    log "开始上传到阿里云OSS..."
    if ossutil cp "${BACKUP_FILE}" "oss://${OSS_BUCKET}/database/" --force 2>/dev/null; then
        log "✅ 数据库文件上传成功"
    else
        log "⚠️  警告: OSS上传失败，但本地备份已完成"
    fi
    
    if [ "${MD5SUM}" != "N/A" ]; then
        ossutil cp "${BACKUP_FILE}.md5" "oss://${OSS_BUCKET}/database/" --force 2>/dev/null
    fi
else
    log "跳过OSS上传（ossutil未安装或OSS_BUCKET未配置）"
fi

# 删除旧备份（保留指定天数）
log "清理旧备份（保留${RETENTION_DAYS}天）..."
OLD_COUNT=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -mtime +${RETENTION_DAYS} 2>/dev/null | wc -l | tr -d ' ')
if [ "${OLD_COUNT}" -gt 0 ]; then
    find "${BACKUP_DIR}" -name "pms_*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
    find "${BACKUP_DIR}" -name "pms_*.sql.gz.md5" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
    log "✅ 删除了 ${OLD_COUNT} 个旧备份文件"
else
    log "无旧备份需要清理"
fi

# 发送成功通知（企业微信/钉钉）
if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
    log "发送通知..."
    curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{
            \"msgtype\": \"text\",
            \"text\": {
                \"content\": \"✅ PMS数据库备份成功\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n大小: ${BACKUP_SIZE}\nMD5: ${MD5SUM}\"
            }
        }" > /dev/null 2>&1 && log "✅ 通知发送成功" || log "⚠️  通知发送失败"
fi

log "========== 备份流程完成 =========="
exit 0
