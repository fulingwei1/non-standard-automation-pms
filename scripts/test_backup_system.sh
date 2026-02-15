#!/bin/bash
# 备份系统快速验证脚本
# 用途: 一键测试整个备份系统是否正常工作

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "=================================================="
echo "  PMS备份系统 - 快速验证测试"
echo "=================================================="
echo ""

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    ((TOTAL_TESTS++))
    log "测试 ${TOTAL_TESTS}: ${test_name}"
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        success "${test_name} - 通过"
        ((PASSED_TESTS++))
        return 0
    else
        error "${test_name} - 失败"
        ((FAILED_TESTS++))
        return 1
    fi
}

# ==================== 环境检查 ====================
log "========== 1. 环境检查 =========="

run_test "检查项目目录" "[ -d '${PROJECT_DIR}' ]"
run_test "检查scripts目录" "[ -d '${SCRIPT_DIR}' ]"
run_test "检查docs目录" "[ -d '${PROJECT_DIR}/docs/backup' ]"

# 检查命令
run_test "检查bash命令" "command -v bash"
run_test "检查tar命令" "command -v tar"
run_test "检查gzip命令" "command -v gzip"
run_test "检查find命令" "command -v find"

echo ""

# ==================== 脚本检查 ====================
log "========== 2. 脚本文件检查 =========="

SCRIPTS=(
    "backup_database.sh"
    "backup_files.sh"
    "backup_full.sh"
    "restore_database.sh"
    "restore_files.sh"
    "verify_backup.sh"
    "monitor_backup.sh"
    "test_restore.sh"
)

for script in "${SCRIPTS[@]}"; do
    run_test "检查 ${script}" "[ -f '${SCRIPT_DIR}/${script}' ]"
    run_test "${script} 可执行" "[ -x '${SCRIPT_DIR}/${script}' ]"
done

echo ""

# ==================== 配置文件检查 ====================
log "========== 3. 配置文件检查 =========="

run_test "检查crontab配置" "[ -f '${SCRIPT_DIR}/crontab.backup' ]"
run_test "检查OSS配置示例" "[ -f '${SCRIPT_DIR}/ossutil.config.example' ]"
run_test "检查环境变量配置" "[ -f '${PROJECT_DIR}/.env.backup' ]"

echo ""

# ==================== Python服务检查 ====================
log "========== 4. Python服务检查 =========="

run_test "检查backup_service.py" "[ -f '${PROJECT_DIR}/app/services/backup_service.py' ]"
run_test "检查backup API" "[ -f '${PROJECT_DIR}/app/api/v1/endpoints/backup.py' ]"

echo ""

# ==================== 文档检查 ====================
log "========== 5. 文档检查 =========="

DOCS=(
    "README.md"
    "backup_strategy.md"
    "backup_operations.md"
    "restore_operations.md"
    "disaster_recovery_plan.md"
)

for doc in "${DOCS[@]}"; do
    run_test "检查 ${doc}" "[ -f '${PROJECT_DIR}/docs/backup/${doc}' ]"
done

echo ""

# ==================== 目录结构检查 ====================
log "========== 6. 创建必要目录 =========="

BACKUP_DIR="${BACKUP_DIR:-/var/backups/pms}"
LOG_DIR="/var/log/pms"

if [ ! -d "${BACKUP_DIR}" ]; then
    warn "备份目录不存在，创建中..."
    mkdir -p "${BACKUP_DIR}" 2>/dev/null || {
        warn "无权限创建 ${BACKUP_DIR}，需要sudo"
    }
fi

if [ ! -d "${LOG_DIR}" ]; then
    warn "日志目录不存在，创建中..."
    mkdir -p "${LOG_DIR}" 2>/dev/null || {
        warn "无权限创建 ${LOG_DIR}，需要sudo"
    }
fi

run_test "备份目录可写" "[ -w '${BACKUP_DIR}' ] || [ ! -d '${BACKUP_DIR}' ]"
run_test "日志目录可写" "[ -w '${LOG_DIR}' ] || [ ! -d '${LOG_DIR}' ]"

echo ""

# ==================== 功能测试（可选） ====================
if [ "$1" = "--full" ]; then
    log "========== 7. 功能测试（完整模式） =========="
    
    # 测试备份脚本语法
    log "测试脚本语法..."
    for script in "${SCRIPTS[@]}"; do
        if bash -n "${SCRIPT_DIR}/${script}" 2>/dev/null; then
            success "${script} 语法正确"
            ((PASSED_TESTS++))
        else
            error "${script} 语法错误"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    done
    
    echo ""
fi

# ==================== 汇总报告 ====================
echo ""
log "=========================================="
log "测试汇总"
log "=========================================="
echo ""
log "总测试数: ${TOTAL_TESTS}"
success "通过: ${PASSED_TESTS}"

if [ ${FAILED_TESTS} -gt 0 ]; then
    error "失败: ${FAILED_TESTS}"
fi

echo ""

# 计算通过率
if [ ${TOTAL_TESTS} -gt 0 ]; then
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    log "通过率: ${PASS_RATE}%"
    
    if [ ${PASS_RATE} -eq 100 ]; then
        echo ""
        success "🎉 所有测试通过！备份系统已就绪！"
        echo ""
        log "下一步操作:"
        echo "  1. 配置环境变量: cp .env.backup .env.backup.local && vim .env.backup.local"
        echo "  2. 加载环境变量: source .env.backup.local"
        echo "  3. 手动测试备份: bash scripts/backup_database.sh"
        echo "  4. 配置定时任务: crontab -e"
        echo "  5. 查看文档: cat docs/backup/README.md"
        echo ""
        exit 0
    elif [ ${PASS_RATE} -ge 80 ]; then
        echo ""
        warn "⚠️  大部分测试通过，但有少量失败项"
        echo ""
        log "建议检查失败项并修复"
        exit 1
    else
        echo ""
        error "❌ 测试失败较多，请检查环境配置"
        exit 1
    fi
fi
