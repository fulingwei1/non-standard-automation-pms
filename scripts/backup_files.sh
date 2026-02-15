#!/bin/bash
# 文件备份脚本（上传文件、配置文件）
# 用途: 备份应用相关的文件和配置

set -e

# ==================== 配置区域 ====================
BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
APP_DIR="${APP_DIR:-/var/www/pms}"
UPLOADS_DIR="${APP_DIR}/uploads"
OSS_BUCKET="${OSS_BUCKET:-pms-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"

# ==================== 函数定义 ====================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ 错误: $1"
    if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
        curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{
                \"msgtype\": \"text\",
                \"text\": {
                    \"content\": \"❌ PMS文件备份失败\n时间: $(date)\n错误: $1\"
                }
            }" > /dev/null 2>&1
    fi
    exit 1
}

# ==================== 主程序 ====================
log "========== 开始文件备份 =========="

# 创建备份目录
mkdir -p "${BACKUP_DIR}" || error_exit "无法创建备份目录"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. 备份上传文件
if [ -d "${UPLOADS_DIR}" ]; then
    log "备份上传文件目录: ${UPLOADS_DIR}"
    UPLOADS_BACKUP="${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"
    
    tar -czf "${UPLOADS_BACKUP}" -C "${APP_DIR}" uploads 2>/dev/null || error_exit "上传文件备份失败"
    
    UPLOADS_SIZE=$(du -h "${UPLOADS_BACKUP}" | awk '{print $1}')
    log "✅ 上传文件备份完成: ${UPLOADS_SIZE}"
    
    # 计算MD5
    if command -v md5sum &> /dev/null; then
        md5sum "${UPLOADS_BACKUP}" | awk '{print $1}' > "${UPLOADS_BACKUP}.md5"
    elif command -v md5 &> /dev/null; then
        md5 -q "${UPLOADS_BACKUP}" > "${UPLOADS_BACKUP}.md5"
    fi
else
    log "⚠️  上传文件目录不存在: ${UPLOADS_DIR}"
fi

# 2. 备份配置文件
log "备份配置文件..."
CONFIGS_BACKUP="${BACKUP_DIR}/configs_${TIMESTAMP}.tar.gz"

# 收集存在的配置文件
CONFIG_FILES=""
[ -f "${APP_DIR}/.env" ] && CONFIG_FILES="${CONFIG_FILES} ${APP_DIR}/.env"
[ -f "${APP_DIR}/docker-compose.yml" ] && CONFIG_FILES="${CONFIG_FILES} ${APP_DIR}/docker-compose.yml"
[ -f "/etc/nginx/nginx.conf" ] && CONFIG_FILES="${CONFIG_FILES} /etc/nginx/nginx.conf"
[ -d "/etc/nginx/conf.d" ] && CONFIG_FILES="${CONFIG_FILES} /etc/nginx/conf.d"

if [ -n "${CONFIG_FILES}" ]; then
    tar -czf "${CONFIGS_BACKUP}" ${CONFIG_FILES} 2>/dev/null || log "⚠️  部分配置文件备份失败"
    
    CONFIGS_SIZE=$(du -h "${CONFIGS_BACKUP}" | awk '{print $1}')
    log "✅ 配置文件备份完成: ${CONFIGS_SIZE}"
    
    # 计算MD5
    if command -v md5sum &> /dev/null; then
        md5sum "${CONFIGS_BACKUP}" | awk '{print $1}' > "${CONFIGS_BACKUP}.md5"
    elif command -v md5 &> /dev/null; then
        md5 -q "${CONFIGS_BACKUP}" > "${CONFIGS_BACKUP}.md5"
    fi
else
    log "⚠️  未找到配置文件"
fi

# 3. 备份日志文件（可选，最近7天）
if [ -d "/var/log/pms" ]; then
    log "备份日志文件..."
    LOGS_BACKUP="${BACKUP_DIR}/logs_${TIMESTAMP}.tar.gz"
    
    find /var/log/pms -type f -mtime -7 -print0 2>/dev/null | \
        tar -czf "${LOGS_BACKUP}" --null -T - 2>/dev/null || log "⚠️  日志文件备份失败"
    
    if [ -f "${LOGS_BACKUP}" ]; then
        LOGS_SIZE=$(du -h "${LOGS_BACKUP}" | awk '{print $1}')
        log "✅ 日志文件备份完成: ${LOGS_SIZE}"
    fi
fi

# 上传到OSS
if command -v ossutil &> /dev/null && [ -n "${OSS_BUCKET}" ]; then
    log "开始上传到阿里云OSS..."
    
    [ -f "${UPLOADS_BACKUP}" ] && ossutil cp "${UPLOADS_BACKUP}" "oss://${OSS_BUCKET}/files/" --force 2>/dev/null
    [ -f "${CONFIGS_BACKUP}" ] && ossutil cp "${CONFIGS_BACKUP}" "oss://${OSS_BUCKET}/configs/" --force 2>/dev/null
    [ -f "${LOGS_BACKUP}" ] && ossutil cp "${LOGS_BACKUP}" "oss://${OSS_BUCKET}/logs/" --force 2>/dev/null
    
    log "✅ OSS上传完成"
else
    log "跳过OSS上传"
fi

# 清理旧备份
log "清理旧备份（保留${RETENTION_DAYS}天）..."
find "${BACKUP_DIR}" -name "uploads_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
find "${BACKUP_DIR}" -name "configs_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
find "${BACKUP_DIR}" -name "logs_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
log "✅ 清理完成"

# 发送通知
if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
    curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{
            \"msgtype\": \"text\",
            \"text\": {
                \"content\": \"✅ PMS文件备份成功\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n上传文件: ${UPLOADS_SIZE:-N/A}\n配置文件: ${CONFIGS_SIZE:-N/A}\"
            }
        }" > /dev/null 2>&1
fi

log "========== 文件备份流程完成 =========="
exit 0
