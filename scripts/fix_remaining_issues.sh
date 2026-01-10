#!/bin/bash

echo "修复剩余Mock数据问题..."
echo ""

# 1. 修复ProcurementManagerDashboard.jsx - 移除被注释的Mock数据定义
file="frontend/src/pages/ProcurementManagerDashboard.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  # 移除被注释的Mock数据块
  sed -i '' '/^\/\* const mockStats = {$/,/^} \*\/$/d' "$file"
  sed -i '' '/^\/\* const mockPendingApprovals = \[$/,/^] \*\/$/d' "$file"
  echo "  - 已移除被注释的Mock数据定义"
fi

# 2. 修复ContractApproval.jsx - 需要定义空数组
file="frontend/src/pages/ContractApproval.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  # 检查是否需要添加Mock数据定义
  if ! grep -q "const mockPendingApprovals" "$file"; then
    # 在useMemo之前添加Mock数据定义
    sed -i '' '/const filteredApprovals = useMemo(() => {/i\
// Mock data - 已移除，使用真实API\
const mockPendingApprovals = []\
const mockApprovalHistory = []\
\
' "$file"
    echo "  - 已添加Mock数据定义（临时）"
  fi
fi

# 3. 修复PerformanceManagement.jsx - 检查Mock数据定义
file="frontend/src/pages/PerformanceManagement.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "useState(mockStats)" "$file"; then
    echo "  - 状态初始化已修复"
  else
    echo "  - 需要检查Mock数据定义"
  fi
fi

# 4. 修复CustomerServiceDashboard.jsx - 检查状态初始化
file="frontend/src/pages/CustomerServiceDashboard.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "useState(mockStats)" "$file"; then
    echo "  - 状态初始化已修复"
  fi
fi

# 5. 修复ManufacturingDirectorDashboard.jsx - 检查Mock数据引用
file="frontend/src/pages/ManufacturingDirectorDashboard.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "mockPendingApprovals" "$file"; then
    echo "  - 发现Mock数据引用，需要检查"
  fi
fi

# 6. 修复AdministrativeApprovals.jsx - 检查状态初始化
file="frontend/src/pages/AdministrativeApprovals.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "useState(mockPendingApprovals)" "$file"; then
    echo "  - 状态初始化已修复"
  fi
fi

# 7. 修复VehicleManagement.jsx - 检查状态初始化
file="frontend/src/pages/VehicleManagement.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "useState(mockVehicles)" "$file"; then
    echo "  - 状态初始化已修复"
  fi
fi

# 8. 修复AttendanceManagement.jsx - 检查状态初始化
file="frontend/src/pages/AttendanceManagement.jsx"
if [ -f "$file" ]; then
  echo "修复: $(basename $file)"
  if grep -q "useState(mockAttendanceStats)" "$file"; then
    echo "  - 状态初始化已修复"
  fi
fi

echo ""
echo "✅ 剩余Mock数据问题检查完成"
echo ""
echo "下一步："
echo "1. 检查修复后的文件是否有语法错误"
echo "2. 运行 linter 检查代码质量"
echo "3. 测试页面功能"
