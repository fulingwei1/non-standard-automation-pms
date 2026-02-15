#!/bin/bash
# 数据库恢复脚本
# 用途: 从备份文件恢复MySQL数据库

set -e

# ==================== 配置区域 ====================
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-pms}"
DB_USER="${DB_USER:-pms_user}"
DB_PASS="${MYSQL_PASSWORD}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"

# ==================== 函数定义 ====================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ 错误: $1"
    exit 1
}

show_usage() {
    echo "用法: $0 <备份文件路径>"
    echo ""
    echo "示例:"
    echo "  $0 /var/backups/pms/pms_20260215_020000.sql.gz"
    echo "  $0 pms_20260215_020000.sql.gz  # 自动从备份目录查找"
    echo ""
    echo "列出可用备份:"
    echo "  ls -lh ${BACKUP_DIR}/pms_*.sql.gz"
    exit 1
}

# ==================== 参数检查 ====================
if [ -z "$1" ]; then
    show_usage
fi

BACKUP_FILE="$1"

# 如果只提供文件名，自动添加路径
if [ ! -f "${BACKUP_FILE}" ] && [[ "${BACKUP_FILE}" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# 检查备份文件是否存在
if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "备份文件不存在: ${BACKUP_FILE}"
fi

# 检查文件大小
FILE_SIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo "0")
if [ "${FILE_SIZE}" -eq 0 ]; then
    error_exit "备份文件为空: ${BACKUP_FILE}"
fi

# ==================== 主程序 ====================
log "========== 数据库恢复 =========="
log "备份文件: ${BACKUP_FILE}"
log "文件大小: $(du -h "${BACKUP_FILE}" | awk '{print $1}')"

# 验证MD5校验和
if [ -f "${BACKUP_FILE}.md5" ]; then
    log "验证备份文件完整性..."
    
    if command -v md5sum &> /dev/null; then
        if md5sum -c "${BACKUP_FILE}.md5" 2>/dev/null; then
            log "✅ 备份文件完整性验证通过"
        else
            error_exit "备份文件MD5校验失败，文件可能已损坏"
        fi
    elif command -v md5 &> /dev/null; then
        EXPECTED_MD5=$(cat "${BACKUP_FILE}.md5")
        ACTUAL_MD5=$(md5 -q "${BACKUP_FILE}")
        if [ "${EXPECTED_MD5}" = "${ACTUAL_MD5}" ]; then
            log "✅ 备份文件完整性验证通过"
        else
            error_exit "备份文件MD5校验失败，文件可能已损坏"
        fi
    fi
else
    log "⚠️  警告: MD5校验文件不存在，跳过完整性验证"
fi

# 确认恢复操作
echo ""
echo "⚠️⚠️⚠️  警告  ⚠️⚠️⚠️"
echo "此操作将恢复数据库，可能覆盖当前数据！"
echo "数据库: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "备份文件: ${BACKUP_FILE}"
echo ""
read -p "确认要恢复数据库吗？(输入 yes 继续): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "❌ 恢复已取消"
    exit 0
fi

# 检查数据库连接
log "测试数据库连接..."
if ! mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" -e "SELECT 1" &>/dev/null; then
    error_exit "无法连接到数据库，请检查配置"
fi
log "✅ 数据库连接正常"

# 备份当前数据库（以防万一）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_BACKUP="${BACKUP_DIR}/before_restore_${TIMESTAMP}.sql.gz"

log "备份当前数据库到: ${CURRENT_BACKUP}"
mkdir -p "${BACKUP_DIR}"

mysqldump \
    -h"${DB_HOST}" \
    -P"${DB_PORT}" \
    -u"${DB_USER}" \
    -p"${DB_PASS}" \
    --single-transaction \
    --databases "${DB_NAME}" \
    2>/dev/null | gzip > "${CURRENT_BACKUP}" || log "⚠️  当前数据库备份失败"

if [ -f "${CURRENT_BACKUP}" ]; then
    CURRENT_SIZE=$(du -h "${CURRENT_BACKUP}" | awk '{print $1}')
    log "✅ 当前数据库已备份: ${CURRENT_SIZE}"
fi

# 恢复数据库
log "开始恢复数据库..."
log "这可能需要几分钟，请耐心等待..."

if gunzip < "${BACKUP_FILE}" | mysql \
    -h"${DB_HOST}" \
    -P"${DB_PORT}" \
    -u"${DB_USER}" \
    -p"${DB_PASS}" 2>/dev/null; then
    
    log "✅ 数据库恢复完成"
    log "  备份文件: ${BACKUP_FILE}"
    log "  当前数据备份至: ${CURRENT_BACKUP}"
    
    # 验证恢复
    log "验证数据库恢复..."
    TABLE_COUNT=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
        -D"${DB_NAME}" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}'" 2>/dev/null || echo "0")
    
    log "✅ 数据库表数量: ${TABLE_COUNT}"
    
    echo ""
    echo "========================================="
    echo "✅ 数据库恢复成功！"
    echo "========================================="
    echo ""
    echo "重要提示:"
    echo "1. 请立即测试应用功能"
    echo "2. 如有问题，可从以下文件恢复:"
    echo "   ${CURRENT_BACKUP}"
    echo ""
else
    error_exit "数据库恢复失败"
fi

log "========== 恢复流程完成 =========="
exit 0
