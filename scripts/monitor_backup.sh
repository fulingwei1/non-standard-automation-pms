#!/bin/bash
# 备份监控脚本
# 用途: 监控备份状态，检查备份健康度

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"
MAX_AGE_HOURS="${MAX_AGE_HOURS:-26}"  # 最新备份的最大年龄（小时）
MIN_SIZE_MB="${MIN_SIZE_MB:-10}"      # 最小备份大小（MB）

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

send_alert() {
    local message="$1"
    log "🚨 告警: ${message}"
    
    if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
        curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{
                \"msgtype\": \"text\",
                \"text\": {
                    \"content\": \"🚨 PMS备份告警\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n${message}\"
                }
            }" > /dev/null 2>&1
    fi
}

log "========== 备份监控检查 =========="

# 初始化告警计数
ALERT_COUNT=0
WARNINGS=()
ALERTS=()

# 1. 检查备份目录是否存在
log "1️⃣  检查备份目录"
if [ ! -d "${BACKUP_DIR}" ]; then
    ALERTS+=("备份目录不存在: ${BACKUP_DIR}")
    ((ALERT_COUNT++))
else
    log "  ✅ 备份目录正常"
fi

# 2. 检查最新数据库备份
log "2️⃣  检查数据库备份"
LATEST_DB_BACKUP=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -type f 2>/dev/null | sort -r | head -n 1)

if [ -z "${LATEST_DB_BACKUP}" ]; then
    ALERTS+=("未找到数据库备份文件")
    ((ALERT_COUNT++))
else
    # 检查备份年龄
    if [ -f "${LATEST_DB_BACKUP}" ]; then
        BACKUP_TIME=$(stat -f%m "${LATEST_DB_BACKUP}" 2>/dev/null || stat -c%Y "${LATEST_DB_BACKUP}" 2>/dev/null || echo "0")
        CURRENT_TIME=$(date +%s)
        AGE_HOURS=$(( (CURRENT_TIME - BACKUP_TIME) / 3600 ))
        
        if [ "${AGE_HOURS}" -gt "${MAX_AGE_HOURS}" ]; then
            ALERTS+=("最新数据库备份过旧: ${AGE_HOURS}小时前")
            ((ALERT_COUNT++))
        else
            log "  ✅ 最新备份: ${AGE_HOURS}小时前"
        fi
        
        # 检查备份大小
        FILE_SIZE=$(stat -f%z "${LATEST_DB_BACKUP}" 2>/dev/null || stat -c%s "${LATEST_DB_BACKUP}" 2>/dev/null || echo "0")
        FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))
        
        if [ "${FILE_SIZE_MB}" -lt "${MIN_SIZE_MB}" ]; then
            WARNINGS+=("数据库备份文件过小: ${FILE_SIZE_MB}MB")
        else
            log "  ✅ 备份大小正常: ${FILE_SIZE_MB}MB"
        fi
        
        # 检查MD5文件
        if [ ! -f "${LATEST_DB_BACKUP}.md5" ]; then
            WARNINGS+=("MD5校验文件缺失")
        fi
    fi
fi

# 3. 检查文件备份
log "3️⃣  检查文件备份"
LATEST_FILES_BACKUP=$(find "${BACKUP_DIR}" -name "uploads_*.tar.gz" -type f 2>/dev/null | sort -r | head -n 1)

if [ -z "${LATEST_FILES_BACKUP}" ]; then
    WARNINGS+=("未找到文件备份")
else
    BACKUP_TIME=$(stat -f%m "${LATEST_FILES_BACKUP}" 2>/dev/null || stat -c%Y "${LATEST_FILES_BACKUP}" 2>/dev/null || echo "0")
    CURRENT_TIME=$(date +%s)
    AGE_HOURS=$(( (CURRENT_TIME - BACKUP_TIME) / 3600 ))
    
    if [ "${AGE_HOURS}" -gt "${MAX_AGE_HOURS}" ]; then
        WARNINGS+=("文件备份过旧: ${AGE_HOURS}小时前")
    else
        log "  ✅ 文件备份正常: ${AGE_HOURS}小时前"
    fi
fi

# 4. 检查备份数量
log "4️⃣  检查备份数量"
DB_BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -type f 2>/dev/null | wc -l | tr -d ' ')
log "  数据库备份数量: ${DB_BACKUP_COUNT}"

if [ "${DB_BACKUP_COUNT}" -lt 3 ]; then
    WARNINGS+=("数据库备份数量过少: ${DB_BACKUP_COUNT}个")
fi

# 5. 检查磁盘空间
log "5️⃣  检查磁盘空间"
DISK_USAGE=$(df -h "${BACKUP_DIR}" | tail -1 | awk '{print $5}' | tr -d '%')
DISK_AVAIL=$(df -h "${BACKUP_DIR}" | tail -1 | awk '{print $4}')

log "  磁盘使用率: ${DISK_USAGE}%"
log "  可用空间: ${DISK_AVAIL}"

if [ "${DISK_USAGE}" -gt 90 ]; then
    ALERTS+=("磁盘空间严重不足: ${DISK_USAGE}%")
    ((ALERT_COUNT++))
elif [ "${DISK_USAGE}" -gt 80 ]; then
    WARNINGS+=("磁盘空间不足: ${DISK_USAGE}%")
fi

# 6. 检查备份完整性（抽样）
log "6️⃣  备份完整性抽样检查"
if [ -n "${LATEST_DB_BACKUP}" ] && [ -f "${LATEST_DB_BACKUP}.md5" ]; then
    if command -v md5sum &> /dev/null; then
        if md5sum -c "${LATEST_DB_BACKUP}.md5" 2>/dev/null >/dev/null; then
            log "  ✅ 最新备份完整性验证通过"
        else
            ALERTS+=("最新备份MD5校验失败")
            ((ALERT_COUNT++))
        fi
    elif command -v md5 &> /dev/null; then
        EXPECTED_MD5=$(cat "${LATEST_DB_BACKUP}.md5")
        ACTUAL_MD5=$(md5 -q "${LATEST_DB_BACKUP}")
        
        if [ "${EXPECTED_MD5}" = "${ACTUAL_MD5}" ]; then
            log "  ✅ 最新备份完整性验证通过"
        else
            ALERTS+=("最新备份MD5校验失败")
            ((ALERT_COUNT++))
        fi
    fi
fi

# 7. 检查备份日志
log "7️⃣  检查备份日志"
BACKUP_LOG="/var/log/pms/backup.log"

if [ -f "${BACKUP_LOG}" ]; then
    # 检查最近的备份是否有错误
    RECENT_ERRORS=$(tail -100 "${BACKUP_LOG}" | grep -i "error\|failed\|❌" | wc -l | tr -d ' ')
    
    if [ "${RECENT_ERRORS}" -gt 0 ]; then
        WARNINGS+=("备份日志中发现 ${RECENT_ERRORS} 个错误")
    else
        log "  ✅ 备份日志正常"
    fi
else
    log "  ⚠️  备份日志文件不存在"
fi

# ==================== 生成监控报告 ====================
echo ""
log "========================================="
log "监控报告"
log "========================================="

if [ "${ALERT_COUNT}" -gt 0 ]; then
    log "🚨 严重告警 (${ALERT_COUNT})"
    for alert in "${ALERTS[@]}"; do
        log "  - ${alert}"
        send_alert "${alert}"
    done
fi

if [ ${#WARNINGS[@]} -gt 0 ]; then
    log "⚠️  警告 (${#WARNINGS[@]})"
    for warning in "${WARNINGS[@]}"; do
        log "  - ${warning}"
    done
fi

if [ "${ALERT_COUNT}" -eq 0 ] && [ ${#WARNINGS[@]} -eq 0 ]; then
    log "✅ 所有检查通过，备份系统运行正常"
fi

# 备份统计
echo ""
log "备份统计:"
log "  数据库备份: ${DB_BACKUP_COUNT}个"
log "  最新备份: ${AGE_HOURS:-N/A}小时前"
log "  备份大小: ${FILE_SIZE_MB:-N/A}MB"
log "  磁盘使用率: ${DISK_USAGE}%"
log "  可用空间: ${DISK_AVAIL}"

# 返回状态码
if [ "${ALERT_COUNT}" -gt 0 ]; then
    exit 1
else
    exit 0
fi
