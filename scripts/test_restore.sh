#!/bin/bash
# 恢复测试脚本
# 用途: 定期测试备份恢复能力（每周执行）

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
TEST_DB="pms_restore_test"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-pms_user}"
DB_PASS="${MYSQL_PASSWORD}"
WECHAT_WEBHOOK_URL="${WECHAT_WEBHOOK_URL:-}"

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
                    \"content\": \"❌ PMS备份恢复测试失败\n时间: $(date)\n错误: $1\"
                }
            }" > /dev/null 2>&1
    fi
    
    exit 1
}

cleanup() {
    log "清理测试环境..."
    
    # 删除测试数据库
    if [ -n "${TEST_DB}" ]; then
        mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
            -e "DROP DATABASE IF EXISTS ${TEST_DB}" 2>/dev/null || true
    fi
    
    log "✅ 清理完成"
}

# 设置退出清理
trap cleanup EXIT

# ==================== 主程序 ====================
log "========== 备份恢复测试 =========="

# 检查数据库连接
log "1️⃣  测试数据库连接"
if ! mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
    -e "SELECT 1" &>/dev/null; then
    error_exit "无法连接到数据库"
fi
log "  ✅ 数据库连接正常"

# 查找最新的备份文件
log "2️⃣  查找最新备份"
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -type f 2>/dev/null | sort -r | head -n 1)

if [ -z "${LATEST_BACKUP}" ]; then
    error_exit "未找到备份文件"
fi

FILE_SIZE=$(stat -f%z "${LATEST_BACKUP}" 2>/dev/null || stat -c%s "${LATEST_BACKUP}" 2>/dev/null || echo "0")
FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))

log "  备份文件: ${LATEST_BACKUP}"
log "  文件大小: ${FILE_SIZE_MB}MB"

# 验证备份完整性
log "3️⃣  验证备份完整性"

# MD5校验
if [ -f "${LATEST_BACKUP}.md5" ]; then
    if command -v md5sum &> /dev/null; then
        if md5sum -c "${LATEST_BACKUP}.md5" 2>/dev/null; then
            log "  ✅ MD5校验通过"
        else
            error_exit "MD5校验失败"
        fi
    elif command -v md5 &> /dev/null; then
        EXPECTED_MD5=$(cat "${LATEST_BACKUP}.md5")
        ACTUAL_MD5=$(md5 -q "${LATEST_BACKUP}")
        
        if [ "${EXPECTED_MD5}" = "${ACTUAL_MD5}" ]; then
            log "  ✅ MD5校验通过"
        else
            error_exit "MD5校验失败"
        fi
    fi
else
    log "  ⚠️  警告: MD5文件不存在"
fi

# GZIP完整性
if gunzip -t "${LATEST_BACKUP}" 2>/dev/null; then
    log "  ✅ GZIP格式正确"
else
    error_exit "GZIP文件损坏"
fi

# 创建测试数据库
log "4️⃣  创建测试数据库"
mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
    -e "DROP DATABASE IF EXISTS ${TEST_DB}" 2>/dev/null

mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
    -e "CREATE DATABASE ${TEST_DB}" 2>/dev/null || error_exit "无法创建测试数据库"

log "  ✅ 测试数据库创建成功"

# 执行恢复测试
log "5️⃣  执行恢复测试"
START_TIME=$(date +%s)

if gunzip < "${LATEST_BACKUP}" | \
   sed "s/\`pms\`/\`${TEST_DB}\`/g" | \
   mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
   "${TEST_DB}" 2>/dev/null; then
    
    END_TIME=$(date +%s)
    RESTORE_TIME=$((END_TIME - START_TIME))
    
    log "  ✅ 恢复成功"
    log "  恢复耗时: ${RESTORE_TIME}秒"
else
    error_exit "数据库恢复失败"
fi

# 验证恢复结果
log "6️⃣  验证恢复结果"

# 检查表数量
TABLE_COUNT=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
    -D"${TEST_DB}" -N -e "SELECT COUNT(*) FROM information_schema.tables \
    WHERE table_schema='${TEST_DB}'" 2>/dev/null || echo "0")

log "  表数量: ${TABLE_COUNT}"

if [ "${TABLE_COUNT}" -eq 0 ]; then
    error_exit "恢复的数据库没有表"
fi

# 检查关键表（根据实际情况调整）
CRITICAL_TABLES=("users" "projects" "roles")
MISSING_TABLES=()

for table in "${CRITICAL_TABLES[@]}"; do
    if ! mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
        -D"${TEST_DB}" -e "SHOW TABLES LIKE '${table}'" 2>/dev/null | grep -q "${table}"; then
        MISSING_TABLES+=("${table}")
    fi
done

if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    log "  ⚠️  警告: 缺少关键表: ${MISSING_TABLES[*]}"
else
    log "  ✅ 关键表验证通过"
fi

# 检查数据行数（示例）
if mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
    -D"${TEST_DB}" -e "SHOW TABLES LIKE 'users'" 2>/dev/null | grep -q "users"; then
    
    USER_COUNT=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
        -D"${TEST_DB}" -N -e "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
    
    log "  用户数量: ${USER_COUNT}"
    
    if [ "${USER_COUNT}" -eq 0 ]; then
        log "  ⚠️  警告: 用户表为空"
    fi
fi

# 计算RTO（恢复时间目标）
log "7️⃣  RTO评估"
log "  实际恢复时间: ${RESTORE_TIME}秒 ($(echo "scale=2; ${RESTORE_TIME}/60" | bc)分钟)"

if [ "${RESTORE_TIME}" -lt 3600 ]; then
    log "  ✅ RTO达标 (< 1小时)"
else
    log "  ⚠️  警告: RTO超标 (> 1小时)"
fi

# ==================== 生成测试报告 ====================
echo ""
log "========================================="
log "✅ 恢复测试完成"
log "========================================="
echo ""
log "测试结果:"
log "  备份文件: $(basename ${LATEST_BACKUP})"
log "  文件大小: ${FILE_SIZE_MB}MB"
log "  恢复耗时: ${RESTORE_TIME}秒"
log "  表数量: ${TABLE_COUNT}"
log "  RTO状态: $([ ${RESTORE_TIME} -lt 3600 ] && echo '✅ 达标' || echo '⚠️ 超标')"

# 发送成功通知
if [ -n "${WECHAT_WEBHOOK_URL}" ]; then
    RTO_STATUS=$([ ${RESTORE_TIME} -lt 3600 ] && echo '✅ 达标' || echo '⚠️ 超标')
    
    curl -s -X POST "${WECHAT_WEBHOOK_URL}" \
        -H "Content-Type: application/json" \
        -d "{
            \"msgtype\": \"text\",
            \"text\": {
                \"content\": \"✅ PMS备份恢复测试成功\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n恢复耗时: ${RESTORE_TIME}秒\n表数量: ${TABLE_COUNT}\nRTO: ${RTO_STATUS}\"
            }
        }" > /dev/null 2>&1
fi

exit 0
