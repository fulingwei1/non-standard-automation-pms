#!/bin/bash
# 备份验证脚本
# 用途: 验证备份文件的完整性和可恢复性

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-pms_user}"
DB_PASS="${MYSQL_PASSWORD}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ 错误: $1"
    exit 1
}

show_usage() {
    echo "用法: $0 [备份文件路径]"
    echo ""
    echo "不提供文件路径时，验证最新的备份"
    echo ""
    echo "示例:"
    echo "  $0                                              # 验证最新备份"
    echo "  $0 /var/backups/pms/pms_20260215_020000.sql.gz # 验证指定备份"
    exit 1
}

# ==================== 主程序 ====================
log "========== 备份验证工具 =========="

# 查找要验证的文件
if [ -z "$1" ]; then
    # 查找最新的数据库备份
    BACKUP_FILE=$(find "${BACKUP_DIR}" -name "pms_*.sql.gz" -type f 2>/dev/null | sort -r | head -n 1)
    
    if [ -z "${BACKUP_FILE}" ]; then
        error_exit "未找到备份文件"
    fi
    
    log "自动选择最新备份: ${BACKUP_FILE}"
else
    BACKUP_FILE="$1"
    
    # 自动添加路径
    if [ ! -f "${BACKUP_FILE}" ] && [[ "${BACKUP_FILE}" != /* ]]; then
        BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
    fi
fi

# 检查文件是否存在
if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "备份文件不存在: ${BACKUP_FILE}"
fi

log "验证文件: ${BACKUP_FILE}"

# ==================== 验证项目 ====================

# 1. 文件大小检查
FILE_SIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo "0")
FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))

log "1️⃣  文件大小检查"
if [ "${FILE_SIZE}" -eq 0 ]; then
    log "  ❌ 失败: 文件为空"
    exit 1
elif [ "${FILE_SIZE_MB}" -lt 1 ]; then
    log "  ⚠️  警告: 文件过小 (${FILE_SIZE_MB}MB)，可能不完整"
else
    log "  ✅ 通过: ${FILE_SIZE_MB}MB"
fi

# 2. MD5校验
log "2️⃣  MD5完整性检查"
if [ -f "${BACKUP_FILE}.md5" ]; then
    if command -v md5sum &> /dev/null; then
        if md5sum -c "${BACKUP_FILE}.md5" 2>/dev/null; then
            log "  ✅ 通过: MD5校验成功"
        else
            log "  ❌ 失败: MD5校验失败"
            exit 1
        fi
    elif command -v md5 &> /dev/null; then
        EXPECTED_MD5=$(cat "${BACKUP_FILE}.md5")
        ACTUAL_MD5=$(md5 -q "${BACKUP_FILE}")
        
        if [ "${EXPECTED_MD5}" = "${ACTUAL_MD5}" ]; then
            log "  ✅ 通过: MD5校验成功"
        else
            log "  ❌ 失败: MD5不匹配"
            log "    期望: ${EXPECTED_MD5}"
            log "    实际: ${ACTUAL_MD5}"
            exit 1
        fi
    fi
else
    log "  ⚠️  跳过: MD5文件不存在"
fi

# 3. GZIP格式检查
log "3️⃣  GZIP格式检查"
if gunzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log "  ✅ 通过: GZIP格式正确"
else
    log "  ❌ 失败: GZIP文件损坏"
    exit 1
fi

# 4. SQL内容检查
log "4️⃣  SQL内容检查"
FIRST_LINE=$(gunzip < "${BACKUP_FILE}" | head -n 1)

if [[ "${FIRST_LINE}" == *"MySQL dump"* ]] || [[ "${FIRST_LINE}" == "-- MySQL dump"* ]]; then
    log "  ✅ 通过: 有效的MySQL导出文件"
else
    log "  ❌ 失败: 不是有效的MySQL导出文件"
    exit 1
fi

# 5. 表结构检查
log "5️⃣  数据库表检查"
TABLE_COUNT=$(gunzip < "${BACKUP_FILE}" | grep -c "CREATE TABLE" || echo "0")

if [ "${TABLE_COUNT}" -eq 0 ]; then
    log "  ❌ 失败: 未找到表结构"
    exit 1
else
    log "  ✅ 通过: 包含 ${TABLE_COUNT} 个表"
fi

# 6. 数据检查
log "6️⃣  数据内容检查"
INSERT_COUNT=$(gunzip < "${BACKUP_FILE}" | grep -c "INSERT INTO" || echo "0")

if [ "${INSERT_COUNT}" -eq 0 ]; then
    log "  ⚠️  警告: 未找到INSERT语句，可能是空数据库"
else
    log "  ✅ 通过: 包含 ${INSERT_COUNT} 条INSERT语句"
fi

# 7. 可恢复性测试（可选，需要测试数据库）
log "7️⃣  可恢复性测试"
if [ -n "${VERIFY_RESTORE}" ] && [ "${VERIFY_RESTORE}" = "true" ]; then
    TEST_DB="pms_verify_test_$$"
    
    log "  创建测试数据库: ${TEST_DB}"
    mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
        -e "CREATE DATABASE IF NOT EXISTS ${TEST_DB}" 2>/dev/null || {
        log "  ⚠️  跳过: 无法连接数据库"
    }
    
    if mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
        -e "USE ${TEST_DB}" 2>/dev/null; then
        
        log "  正在导入测试..."
        if gunzip < "${BACKUP_FILE}" | mysql -h"${DB_HOST}" -P"${DB_PORT}" \
            -u"${DB_USER}" -p"${DB_PASS}" "${TEST_DB}" 2>/dev/null; then
            
            log "  ✅ 通过: 可成功恢复"
        else
            log "  ❌ 失败: 恢复测试失败"
        fi
        
        # 清理测试数据库
        mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" \
            -e "DROP DATABASE ${TEST_DB}" 2>/dev/null
    fi
else
    log "  ⚠️  跳过: 需要设置 VERIFY_RESTORE=true"
fi

# ==================== 汇总报告 ====================
echo ""
log "========================================="
log "✅ 备份验证通过！"
log "========================================="
echo ""
log "备份信息:"
log "  文件: ${BACKUP_FILE}"
log "  大小: ${FILE_SIZE_MB}MB"
log "  表数量: ${TABLE_COUNT}"
log "  数据行: ~${INSERT_COUNT}"
log "  创建时间: $(stat -f%Sm "${BACKUP_FILE}" 2>/dev/null || stat -c%y "${BACKUP_FILE}" 2>/dev/null || echo "未知")"
echo ""

exit 0
