#!/bin/bash
# 销售模块 API 测试脚本（Bash版本）
# 使用方法: bash test_sales_apis.sh

BASE_URL="http://127.0.0.1:8000/api/v1"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务器
check_server() {
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务器运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 服务器未运行！${NC}"
        echo "   请先启动服务器："
        echo "   cd 非标自动化项目管理系统"
        echo "   uvicorn app.main:app --reload"
        return 1
    fi
}

# 登录获取Token
get_token() {
    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123" | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        echo -e "${YELLOW}⚠️  登录失败，请检查用户名密码${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 登录成功${NC}"
        echo "$TOKEN"
        return 0
    fi
}

# 测试API
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local need_auth=${5:-true}
    
    echo ""
    echo "============================================================"
    echo -e "${BLUE}ℹ️  测试: $description${NC}"
    echo "请求: $method $endpoint"
    
    TOKEN=$(get_token)
    if [ "$need_auth" = "true" ] && [ -z "$TOKEN" ]; then
        echo -e "${YELLOW}⚠️  需要先登录获取Token${NC}"
        return 1
    fi
    
    if [ "$method" = "GET" ]; then
        if [ -n "$TOKEN" ] && [ "$need_auth" = "true" ]; then
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -H "Authorization: Bearer $TOKEN" \
                "$BASE_URL$endpoint")
        else
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                "$BASE_URL$endpoint")
        fi
    elif [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        if [ -n "$TOKEN" ] && [ "$need_auth" = "true" ]; then
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X $method \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $TOKEN" \
                -d "$data" \
                "$BASE_URL$endpoint")
        else
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X $method \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$BASE_URL$endpoint")
        fi
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
    
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo -e "${GREEN}✅ 成功 (HTTP $HTTP_CODE)${NC}"
        echo "响应: $BODY" | python3 -m json.tool 2>/dev/null || echo "响应: $BODY"
    else
        echo -e "${RED}❌ 失败 (HTTP $HTTP_CODE)${NC}"
        echo "响应: $BODY"
    fi
}

# 主流程
main() {
    echo "============================================================"
    echo "销售模块 API 测试"
    echo "============================================================"
    
    # 检查服务器
    if ! check_server; then
        exit 1
    fi
    
    # 登录
    TOKEN=$(get_token)
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}无法获取Token，测试终止${NC}"
        exit 1
    fi
    
    # 1. 线索管理测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}1. 线索管理测试${NC}"
    echo "============================================================"
    
    test_api "POST" "/sales/leads" \
        '{"customer_name":"测试客户A","source":"展会","contact_name":"张三","contact_phone":"13800138000","demand_summary":"需要自动化测试设备"}' \
        "创建线索"
    
    test_api "GET" "/sales/leads?page=1&page_size=10" "" "获取线索列表"
    
    # 2. 商机管理测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}2. 商机管理测试${NC}"
    echo "============================================================"
    
    # 先获取一个客户ID（这里假设客户ID为1，实际应该从API获取）
    test_api "GET" "/customers?page=1&page_size=1" "" "获取客户列表"
    
    test_api "GET" "/sales/opportunities?page=1&page_size=10" "" "获取商机列表"
    
    # 3. 报价管理测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}3. 报价管理测试${NC}"
    echo "============================================================"
    
    test_api "GET" "/sales/quotes?page=1&page_size=10" "" "获取报价列表"
    
    # 4. 合同管理测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}4. 合同管理测试${NC}"
    echo "============================================================"
    
    test_api "GET" "/sales/contracts?page=1&page_size=10" "" "获取合同列表"
    
    # 5. 发票管理测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}5. 发票管理测试${NC}"
    echo "============================================================"
    
    test_api "GET" "/sales/invoices?page=1&page_size=10" "" "获取发票列表"
    
    # 6. 统计报表测试
    echo ""
    echo "============================================================"
    echo -e "${BLUE}6. 统计报表测试${NC}"
    echo "============================================================"
    
    test_api "GET" "/sales/statistics/funnel" "" "销售漏斗统计"
    test_api "GET" "/sales/statistics/opportunities-by-stage" "" "按阶段统计商机"
    test_api "GET" "/sales/statistics/revenue-forecast?months=3" "" "收入预测"
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✅ 测试完成！${NC}"
    echo "============================================================"
    echo ""
    echo "提示："
    echo "  - 可以通过 API 文档查看详细接口：http://127.0.0.1:8000/docs"
    echo "  - 建议使用 Python 版本测试脚本进行完整测试：python3 test_sales_apis.py"
}

main



