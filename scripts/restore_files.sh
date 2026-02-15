#!/bin/bash
# 文件恢复脚本
# 用途: 恢复应用文件和配置

set -e

APP_DIR="${APP_DIR:-/var/www/pms}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "❌ 错误: $1"
    exit 1
}

show_usage() {
    echo "用法: $0 <备份文件> [类型]"
    echo ""
    echo "类型:"
    echo "  uploads  - 恢复上传文件"
    echo "  configs  - 恢复配置文件"
    echo "  logs     - 恢复日志文件"
    echo "  auto     - 自动检测（默认）"
    echo ""
    echo "示例:"
    echo "  $0 uploads_20260215_030000.tar.gz"
    echo "  $0 configs_20260215_030000.tar.gz configs"
    exit 1
}

if [ -z "$1" ]; then
    show_usage
fi

BACKUP_FILE="$1"
RESTORE_TYPE="${2:-auto}"

# 自动添加路径
if [ ! -f "${BACKUP_FILE}" ] && [[ "${BACKUP_FILE}" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "备份文件不存在: ${BACKUP_FILE}"
fi

# 自动检测类型
if [ "${RESTORE_TYPE}" = "auto" ]; then
    if [[ "${BACKUP_FILE}" == *"uploads"* ]]; then
        RESTORE_TYPE="uploads"
    elif [[ "${BACKUP_FILE}" == *"configs"* ]]; then
        RESTORE_TYPE="configs"
    elif [[ "${BACKUP_FILE}" == *"logs"* ]]; then
        RESTORE_TYPE="logs"
    else
        error_exit "无法自动检测备份类型，请手动指定"
    fi
fi

log "========== 文件恢复 =========="
log "备份文件: ${BACKUP_FILE}"
log "恢复类型: ${RESTORE_TYPE}"

# 验证MD5
if [ -f "${BACKUP_FILE}.md5" ]; then
    log "验证文件完整性..."
    if command -v md5sum &> /dev/null; then
        md5sum -c "${BACKUP_FILE}.md5" 2>/dev/null || error_exit "MD5校验失败"
    fi
    log "✅ 完整性验证通过"
fi

# 确认操作
echo ""
read -p "确认要恢复 ${RESTORE_TYPE} 吗？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log "❌ 恢复已取消"
    exit 0
fi

# 执行恢复
case "${RESTORE_TYPE}" in
    uploads)
        log "恢复上传文件到: ${APP_DIR}/uploads"
        
        # 备份当前文件
        if [ -d "${APP_DIR}/uploads" ]; then
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            mv "${APP_DIR}/uploads" "${APP_DIR}/uploads.bak.${TIMESTAMP}"
            log "✅ 当前文件已备份到: uploads.bak.${TIMESTAMP}"
        fi
        
        # 解压恢复
        tar -xzf "${BACKUP_FILE}" -C "${APP_DIR}" || error_exit "解压失败"
        log "✅ 上传文件恢复完成"
        ;;
        
    configs)
        log "恢复配置文件..."
        
        # 创建临时目录
        TEMP_DIR=$(mktemp -d)
        tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}" || error_exit "解压失败"
        
        # 逐个恢复配置文件
        find "${TEMP_DIR}" -type f | while read -r file; do
            RELATIVE_PATH="${file#${TEMP_DIR}}"
            TARGET_PATH="${RELATIVE_PATH}"
            
            if [ -f "${TARGET_PATH}" ]; then
                cp "${TARGET_PATH}" "${TARGET_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
            fi
            
            mkdir -p "$(dirname "${TARGET_PATH}")"
            cp "${file}" "${TARGET_PATH}"
            log "恢复: ${TARGET_PATH}"
        done
        
        rm -rf "${TEMP_DIR}"
        log "✅ 配置文件恢复完成"
        
        echo ""
        echo "⚠️  重要提示:"
        echo "配置文件已恢复，请检查以下内容："
        echo "1. .env 文件中的密钥和密码"
        echo "2. nginx 配置是否正确"
        echo "3. 可能需要重启服务"
        ;;
        
    logs)
        log "恢复日志文件..."
        tar -xzf "${BACKUP_FILE}" -C / || error_exit "解压失败"
        log "✅ 日志文件恢复完成"
        ;;
        
    *)
        error_exit "未知的恢复类型: ${RESTORE_TYPE}"
        ;;
esac

log "========== 恢复流程完成 =========="
exit 0
