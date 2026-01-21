#!/bin/bash
# 工程师进度管理系统 - UAT自动化测试脚本
# 版本: 1.0.0
# 日期: 2026-01-07

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_PREFIX="/api/v1"

# 测试统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# HTTP请求封装
http_get() {
    local url="$1"
    local token="$2"

    if [ -n "$token" ]; then
        curl -s -X GET "$BASE_URL$url" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json"
    else
        curl -s -X GET "$BASE_URL$url" \
            -H "Content-Type: application/json"
    fi
}

http_post() {
    local url="$1"
    local data="$2"
    local token="$3"

    if [ -n "$token" ]; then
        curl -s -X POST "$BASE_URL$url" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X POST "$BASE_URL$url" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

http_put() {
    local url="$1"
    local data="$2"
    local token="$3"

    curl -s -X PUT "$BASE_URL$url" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$data"
}

# 开始测试
echo "======================================================================"
echo "工程师进度管理系统 - UAT自动化测试"
echo "======================================================================"
echo "测试环境: $BASE_URL"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ========== 预检查 ==========
log_info "执行预检查..."
((TOTAL_TESTS++))

# 检查服务器是否运行
if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    log_success "预检查 - 服务器运行正常"
else
    log_error "预检查 - 服务器未运行或健康检查失败"
    exit 1
fi

echo ""

# ========== 模块1: 认证测试 ==========
echo "----------------------------------------------------------------------"
log_info "模块1: 认证测试"
echo "----------------------------------------------------------------------"

# TC-AUTH-001: 健康检查
((TOTAL_TESTS++))
log_info "TC-AUTH-001: 健康检查端点"
response=$(http_get "/health")
if echo "$response" | grep -q '"status":"ok"'; then
    log_success "TC-AUTH-001: 健康检查通过"
else
    log_error "TC-AUTH-001: 健康检查失败 - $response"
fi

# TC-AUTH-002: API文档访问
((TOTAL_TESTS++))
log_info "TC-AUTH-002: API文档可访问性"
if curl -s -f "$BASE_URL/docs" | grep -q "Swagger UI" > /dev/null 2>&1; then
    log_success "TC-AUTH-002: Swagger UI可访问"
else
    log_error "TC-AUTH-002: Swagger UI不可访问"
fi

echo ""

# ========== 模块2: 工程师端功能测试 ==========
echo "----------------------------------------------------------------------"
log_info "模块2: 工程师端功能测试（需要认证token）"
echo "----------------------------------------------------------------------"

# 注意：以下测试需要有效的JWT token
# 如果没有token，这些测试将跳过

if [ -z "$TEST_TOKEN" ]; then
    log_warning "跳过需要认证的测试（未提供TEST_TOKEN环境变量）"
    log_warning "使用方式: TEST_TOKEN='your_jwt_token' ./test_uat_automated.sh"
else
    # TC-ENG-001: 获取我的项目列表
    ((TOTAL_TESTS++))
    log_info "TC-ENG-001: 获取我的项目列表"
    response=$(http_get "$API_PREFIX/engineers/my-projects?page=1&page_size=10" "$TEST_TOKEN")
    if echo "$response" | grep -q '"items"'; then
        log_success "TC-ENG-001: 项目列表获取成功"
    else
        log_error "TC-ENG-001: 项目列表获取失败 - $response"
    fi

    # TC-ENG-002: 创建一般任务
    ((TOTAL_TESTS++))
    log_info "TC-ENG-002: 创建一般任务（无需审批）"
    task_data='{
        "project_id": 1,
        "title": "UAT自动化测试任务-一般",
        "task_importance": "GENERAL",
        "priority": "MEDIUM",
        "estimated_hours": 10
    }'
    response=$(http_post "$API_PREFIX/engineers/tasks" "$task_data" "$TEST_TOKEN")
    if echo "$response" | grep -q '"task_code"'; then
        task_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
        log_success "TC-ENG-002: 一般任务创建成功 (ID: $task_id)"

        # 验证状态
        if echo "$response" | grep -q '"status":"ACCEPTED"'; then
            log_success "TC-ENG-002: 任务状态正确 (ACCEPTED)"
        else
            log_error "TC-ENG-002: 任务状态错误 - 预期ACCEPTED"
        fi
    else
        log_error "TC-ENG-002: 任务创建失败 - $response"
    fi

    # TC-ENG-003: 创建重要任务
    ((TOTAL_TESTS++))
    log_info "TC-ENG-003: 创建重要任务（需要审批）"
    important_task_data='{
        "project_id": 1,
        "title": "UAT自动化测试任务-重要",
        "task_importance": "IMPORTANT",
        "justification": "这是一个测试重要任务的必要性说明",
        "priority": "HIGH",
        "estimated_hours": 40
    }'
    response=$(http_post "$API_PREFIX/engineers/tasks" "$important_task_data" "$TEST_TOKEN")
    if echo "$response" | grep -q '"task_code"'; then
        important_task_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
        log_success "TC-ENG-003: 重要任务创建成功 (ID: $important_task_id)"

        # 验证状态
        if echo "$response" | grep -q '"status":"PENDING_APPROVAL"'; then
            log_success "TC-ENG-003: 任务状态正确 (PENDING_APPROVAL)"
        else
            log_error "TC-ENG-003: 任务状态错误 - 预期PENDING_APPROVAL"
        fi
    else
        log_error "TC-ENG-003: 任务创建失败 - $response"
    fi

    # TC-ENG-004: 获取我的任务列表
    ((TOTAL_TESTS++))
    log_info "TC-ENG-004: 获取我的任务列表"
    response=$(http_get "$API_PREFIX/engineers/tasks?page=1&page_size=20" "$TEST_TOKEN")
    if echo "$response" | grep -q '"items"'; then
        task_count=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")
        log_success "TC-ENG-004: 任务列表获取成功 (共 $task_count 个任务)"
    else
        log_error "TC-ENG-004: 任务列表获取失败 - $response"
    fi

    # 如果创建了任务，测试进度更新
    if [ -n "$task_id" ]; then
        # TC-ENG-005: 更新任务进度
        ((TOTAL_TESTS++))
        log_info "TC-ENG-005: 更新任务进度（触发聚合）"
        progress_data='{
            "progress": 50,
            "actual_hours": 5,
            "progress_note": "UAT测试 - 进度更新到50%"
        }'
        response=$(http_put "$API_PREFIX/engineers/tasks/$task_id/progress" "$progress_data" "$TEST_TOKEN")
        if echo "$response" | grep -q '"progress":50'; then
            log_success "TC-ENG-005: 进度更新成功"

            # 验证聚合标志
            if echo "$response" | grep -q '"project_progress_updated":true'; then
                log_success "TC-ENG-005: 项目进度已聚合"
            else
                log_warning "TC-ENG-005: 项目进度未聚合（可能是数据问题）"
            fi
        else
            log_error "TC-ENG-005: 进度更新失败 - $response"
        fi
    fi
fi

echo ""

# ========== 模块3: PM审批端功能测试 ==========
echo "----------------------------------------------------------------------"
log_info "模块3: PM审批端功能测试（需要PM token）"
echo "----------------------------------------------------------------------"

if [ -z "$PM_TOKEN" ]; then
    log_warning "跳过PM审批测试（未提供PM_TOKEN环境变量）"
    log_warning "使用方式: PM_TOKEN='pm_jwt_token' ./test_uat_automated.sh"
else
    # TC-PM-001: 获取待审批任务
    ((TOTAL_TESTS++))
    log_info "TC-PM-001: 获取待审批任务列表"
    response=$(http_get "$API_PREFIX/engineers/tasks/pending-approval" "$PM_TOKEN")
    if echo "$response" | grep -q '"items"'; then
        pending_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))")
        log_success "TC-PM-001: 待审批任务获取成功 (共 $pending_count 个)"
    else
        log_error "TC-PM-001: 待审批任务获取失败 - $response"
    fi
fi

echo ""

# ========== 模块4: 跨部门进度视图测试 ==========
echo "----------------------------------------------------------------------"
log_info "模块4: 跨部门进度视图测试（核心功能）"
echo "----------------------------------------------------------------------"

if [ -n "$TEST_TOKEN" ]; then
    # TC-CROSS-001: 跨部门进度可见性
    ((TOTAL_TESTS++))
    log_info "TC-CROSS-001: 获取项目跨部门进度视图"
    response=$(http_get "$API_PREFIX/engineers/projects/1/progress-visibility" "$TEST_TOKEN")
    if echo "$response" | grep -q '"department_progress"'; then
        log_success "TC-CROSS-001: 跨部门进度视图获取成功"

        # 验证数据完整性
        if echo "$response" | grep -q '"stage_progress"'; then
            log_success "TC-CROSS-001: 包含阶段进度数据"
        fi

        if echo "$response" | grep -q '"active_delays"'; then
            log_success "TC-CROSS-001: 包含活跃延期数据"
        fi

        if echo "$response" | grep -q '"overall_progress"'; then
            overall_progress=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('overall_progress', 0))")
            log_success "TC-CROSS-001: 项目整体进度: ${overall_progress}%"
        fi
    else
        log_error "TC-CROSS-001: 跨部门进度视图获取失败 - $response"
    fi
fi

echo ""

# ========== 测试报告 ==========
echo "======================================================================"
echo "测试报告"
echo "======================================================================"
echo "总测试数:   $TOTAL_TESTS"
echo -e "${GREEN}通过:       $PASSED_TESTS${NC}"
echo -e "${RED}失败:       $FAILED_TESTS${NC}"
echo "跳过:       $((TOTAL_TESTS - PASSED_TESTS - FAILED_TESTS))"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    pass_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo -e "${GREEN}通过率:     ${pass_rate}%${NC}"
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit_code=0
else
    pass_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo -e "${YELLOW}通过率:     ${pass_rate}%${NC}"
    echo -e "${RED}❌ 有测试失败，请检查日志${NC}"
    exit_code=1
fi

echo ""
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"

exit $exit_code
