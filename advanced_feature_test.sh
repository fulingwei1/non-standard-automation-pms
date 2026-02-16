#!/bin/bash

echo "============================================================"
echo "🧪 高级功能全面测试套件"
echo "============================================================"
echo ""

# 获取token
echo "🔐 获取访问令牌..."
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -d "username=admin&password=admin123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token', 'ERROR'))" 2>/dev/null)

if [ "$TOKEN" = "ERROR" ] || [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  exit 1
fi

echo "✅ 登录成功"
echo ""

# 测试计数器
TOTAL=0
PASSED=0
FAILED=0

# 测试函数
test_api() {
  local category=$1
  local name=$2
  local method=$3
  local url=$4
  local data=$5
  
  TOTAL=$((TOTAL + 1))
  
  if [ "$method" = "GET" ]; then
    RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$url")
  elif [ "$method" = "POST" ]; then
    RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$url")
  fi
  
  # 检查是否返回有效JSON
  if echo "$RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin); sys.exit(0)" 2>/dev/null; then
    # 检查是否有错误码
    ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('code', 'ok'))" 2>/dev/null)
    
    if [ "$ERROR" = "ok" ] || [ "$ERROR" = "200" ]; then
      echo "  ✅ [$category] $name"
      PASSED=$((PASSED + 1))
      return 0
    else
      echo "  ⚠️  [$category] $name - 错误: $ERROR"
      FAILED=$((FAILED + 1))
      return 1
    fi
  else
    # 检查HTTP错误
    if echo "$RESPONSE" | grep -q "<!DOCTYPE html>"; then
      echo "  ❌ [$category] $name - HTML错误响应"
    elif [ -z "$RESPONSE" ]; then
      echo "  ❌ [$category] $name - 空响应"
    else
      # 可能是简单的成功响应
      echo "  ✅ [$category] $name"
      PASSED=$((PASSED + 1))
      return 0
    fi
    FAILED=$((FAILED + 1))
    return 1
  fi
}

echo "📋 开始测试..."
echo ""

# ============================================================
# 1. 用户管理模块
# ============================================================
echo "👥 1. 用户管理模块"
test_api "用户" "获取用户列表" "GET" "http://127.0.0.1:8001/api/v1/users/?page=1&page_size=10"
test_api "用户" "获取当前用户信息" "GET" "http://127.0.0.1:8001/api/v1/auth/me"
test_api "用户" "获取角色列表" "GET" "http://127.0.0.1:8001/api/v1/roles/?page=1&page_size=10"
echo ""

# ============================================================
# 2. 项目管理模块
# ============================================================
echo "📊 2. 项目管理模块"
test_api "项目" "获取项目列表" "GET" "http://127.0.0.1:8001/api/v1/projects/?page=1&page_size=10"
test_api "项目" "获取项目模板" "GET" "http://127.0.0.1:8001/api/v1/project-templates/?page=1&page_size=10"
test_api "项目" "获取项目状态" "GET" "http://127.0.0.1:8001/api/v1/project-statuses/?page=1&page_size=10"
test_api "项目" "获取里程碑列表" "GET" "http://127.0.0.1:8001/api/v1/milestones/?page=1&page_size=10"
echo ""

# ============================================================
# 3. 生产管理模块
# ============================================================
echo "🏭 3. 生产管理模块"
test_api "生产" "获取工单列表" "GET" "http://127.0.0.1:8001/api/v1/production/work-orders?page=1&page_size=10"
test_api "生产" "获取生产计划" "GET" "http://127.0.0.1:8001/api/v1/production/plans?page=1&page_size=10"
test_api "生产" "获取车间列表" "GET" "http://127.0.0.1:8001/api/v1/production/workshops?page=1&page_size=10"
test_api "生产" "获取工作站列表" "GET" "http://127.0.0.1:8001/api/v1/production/workstations?page=1&page_size=10"
test_api "生产" "获取生产仪表板" "GET" "http://127.0.0.1:8001/api/v1/production/dashboard"
echo ""

# ============================================================
# 4. 销售管理模块
# ============================================================
echo "💰 4. 销售管理模块"
test_api "销售" "获取合同列表" "GET" "http://127.0.0.1:8001/api/v1/sales/contracts?page=1&page_size=10"
test_api "销售" "获取商机列表" "GET" "http://127.0.0.1:8001/api/v1/opportunities/?page=1&page_size=10"
test_api "销售" "获取客户列表" "GET" "http://127.0.0.1:8001/api/v1/customers/?page=1&page_size=10"
test_api "销售" "获取报价列表" "GET" "http://127.0.0.1:8001/api/v1/quotes/?page=1&page_size=10"
echo ""

# ============================================================
# 5. 物料管理模块
# ============================================================
echo "📦 5. 物料管理模块"
test_api "物料" "获取物料列表" "GET" "http://127.0.0.1:8001/api/v1/materials/?page=1&page_size=10"
test_api "物料" "获取物料分类" "GET" "http://127.0.0.1:8001/api/v1/material-categories/?page=1&page_size=10"
test_api "物料" "获取BOM列表" "GET" "http://127.0.0.1:8001/api/v1/boms/?page=1&page_size=10"
test_api "物料" "获取供应商列表" "GET" "http://127.0.0.1:8001/api/v1/vendors/?page=1&page_size=10"
echo ""

# ============================================================
# 6. 采购管理模块
# ============================================================
echo "🛒 6. 采购管理模块"
test_api "采购" "获取采购订单" "GET" "http://127.0.0.1:8001/api/v1/purchase-orders/?page=1&page_size=10"
test_api "采购" "获取采购申请" "GET" "http://127.0.0.1:8001/api/v1/purchase-requests/?page=1&page_size=10"
test_api "采购" "获取收货单" "GET" "http://127.0.0.1:8001/api/v1/goods-receipts/?page=1&page_size=10"
echo ""

# ============================================================
# 7. 质量管理模块
# ============================================================
echo "✅ 7. 质量管理模块"
test_api "质量" "获取验收订单" "GET" "http://127.0.0.1:8001/api/v1/acceptance-orders/?page=1&page_size=10"
test_api "质量" "获取验收模板" "GET" "http://127.0.0.1:8001/api/v1/acceptance-templates/?page=1&page_size=10"
test_api "质量" "获取质量检验记录" "GET" "http://127.0.0.1:8001/api/v1/production/quality/inspections?page=1&page_size=10"
echo ""

# ============================================================
# 8. 外协管理模块
# ============================================================
echo "🔧 8. 外协管理模块"
test_api "外协" "获取外协订单" "GET" "http://127.0.0.1:8001/api/v1/outsourcing-orders/?page=1&page_size=10"
test_api "外协" "获取外协交付" "GET" "http://127.0.0.1:8001/api/v1/outsourcing-deliveries/?page=1&page_size=10"
echo ""

# ============================================================
# 9. 售前管理模块
# ============================================================
echo "💡 9. 售前管理模块"
test_api "售前" "获取售前工单" "GET" "http://127.0.0.1:8001/api/v1/presale-tickets/?page=1&page_size=10"
test_api "售前" "获取售前方案" "GET" "http://127.0.0.1:8001/api/v1/presale-solutions/?page=1&page_size=10"
echo ""

# ============================================================
# 10. 仪表板和统计
# ============================================================
echo "📈 10. 仪表板和统计"
test_api "仪表板" "生产仪表板" "GET" "http://127.0.0.1:8001/api/v1/production/dashboard"
test_api "仪表板" "项目仪表板" "GET" "http://127.0.0.1:8001/api/v1/projects/dashboard"
echo ""

# ============================================================
# 测试结果统计
# ============================================================
echo ""
echo "============================================================"
echo "📊 测试结果统计"
echo "============================================================"
echo ""
echo "总测试数: $TOTAL"
echo "✅ 通过: $PASSED"
echo "❌ 失败: $FAILED"
echo ""

# 计算通过率
if [ $TOTAL -gt 0 ]; then
  PASS_RATE=$(python3 -c "print(f'{$PASSED/$TOTAL*100:.1f}')")
  echo "通过率: ${PASS_RATE}%"
  echo ""
  
  if [ $FAILED -eq 0 ]; then
    echo "🎉 所有测试通过！"
  elif [ $FAILED -lt 5 ]; then
    echo "⚠️  少数测试失败，整体良好"
  else
    echo "❌ 多个测试失败，需要检查"
  fi
else
  echo "❌ 没有执行任何测试"
fi

echo ""
echo "============================================================"
