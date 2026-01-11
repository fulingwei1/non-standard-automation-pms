#!/bin/bash

# 快速验证和修复高优先级页面的API集成

HIGH_PRIORITY_PAGES=(
  "ChairmanWorkstation.jsx"
  "EngineerWorkstation.jsx"
  "SalesManagerWorkstation.jsx"
  "FinanceManagerDashboard.jsx"
  "CustomerServiceDashboard.jsx"
  "ProcurementManagerDashboard.jsx"
  "ProductionManagerDashboard.jsx"
  "ManufacturingDirectorDashboard.jsx"
  "PerformanceManagement.jsx"
  "ProjectBoard.jsx"
  "AdminDashboard.jsx"
  "AdministrativeManagerWorkstation.jsx"
  "SalesDirectorWorkstation.jsx"
  "GeneralManagerWorkstation.jsx"
  "PMODashboard.jsx"
)

echo "========================================="
echo "高优先级页面API集成快速验证"
echo "========================================="
echo ""

FIXED_COUNT=0
CHECKED_COUNT=0
ISSUES_FOUND=0

for file in "${HIGH_PRIORITY_PAGES[@]}"; do
  FILEPATH="frontend/src/pages/$file"
  
  if [ ! -f "$FILEPATH" ]; then
    echo "⚠️  文件不存在: $file"
    continue
  fi
  
  echo "检查: $file"
  CHECKED_COUNT=$((CHECKED_COUNT + 1))
  
  # 1. 检查是否有API导入
  if grep -q "from.*services/api" "$FILEPATH"; then
    echo "  ✅ API导入: 存在"
  else
    echo "  ❌ API导入: 缺失"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
  fi
  
  # 2. 检查是否有useState
  if grep -q "useState" "$FILEPATH"; then
    echo "  ✅ useState: 存在"
  else
    echo "  ⚠️  useState: 缺失"
  fi
  
  # 3. 检查是否有useEffect
  if grep -q "useEffect" "$FILEPATH"; then
    echo "  ✅ useEffect: 存在"
  else
    echo "  ⚠️  useEffect: 缺失"
  fi
  
  # 4. 检查是否有Mock数据残留
  MOCK_COUNT=$(grep -c "mockStats\|mockPendingApprovals\|mockData\|mockMeetings\|mockOfficeSupplies\|mockVehicles\|mockAttendanceStats\|demoStats" "$FILEPATH" 2>/dev/null || echo "0")
  if [ "$MOCK_COUNT" = "0" ]; then
    echo "  ✅ Mock数据: 无残留"
  else
    echo "  ❌ Mock数据: 发现 $MOCK_COUNT 处"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
  fi
  
  # 5. 检查是否有isDemoAccount残留
  DEMO_COUNT=$(grep -c "isDemoAccount\|demo_token_" "$FILEPATH" 2>/dev/null || echo "0")
  if [ "$DEMO_COUNT" = "0" ]; then
    echo "  ✅ Demo检查: 无残留"
  else
    echo "  ❌ Demo检查: 发现 $DEMO_COUNT 处"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
  fi
  
  if [ "$ISSUES_FOUND" = "0" ]; then
    echo "  ✅ 状态: 无需修复"
    FIXED_COUNT=$((FIXED_COUNT + 1))
  else
    echo "  ⚠️  状态: 需要修复"
  fi
  
  echo ""
done

echo "========================================="
echo "验证完成"
echo "========================================="
echo ""
echo "统计："
echo "  检查文件: $CHECKED_COUNT"
echo "  无需修复: $FIXED_COUNT"
echo "  需要修复: $((CHECKED_COUNT - FIXED_COUNT))"
echo ""
echo "下一步：对需要修复的页面进行手动修复或使用其他工具"
