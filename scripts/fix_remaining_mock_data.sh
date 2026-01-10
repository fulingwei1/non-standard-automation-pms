#!/bin/bash

echo "修复剩余Mock数据..."
echo ""

# 批量修复状态初始化
for file in frontend/src/pages/PerformanceManagement.jsx frontend/src/pages/CustomerServiceDashboard.jsx; do
  if [ -f "$file" ]; then
    echo "修复: $(basename $file)"
    # 将 useState(mockData) 改为 useState({})
    sed -i '' 's/useState(mockStats)/useState({})/g' "$file"
    sed -i '' 's/useState(mockPendingTasks)/useState([])/g' "$file"
    sed -i '' 's/useState(mockRecentResults)/useState([])/g' "$file"
    sed -i '' 's/useState(mockDepartmentPerformance)/useState([])/g' "$file"
    sed -i '' 's/useState(mockCurrentPeriod)/useState({})/g' "$file"
  fi
done

# 批量修复Mock数据引用
for file in frontend/src/pages/ContractApproval.jsx frontend/src/pages/AdministrativeApprovals.jsx frontend/src/pages/VehicleManagement.jsx frontend/src/pages/AttendanceManagement.jsx; do
  if [ -f "$file" ]; then
    echo "修复: $(basename $file)"
    # 移除 useState(mockPendingApprovals) 等的初始化
    sed -i '' 's/useState(mockPendingApprovals)/useState([])/g' "$file"
    sed -i '' 's/useState(mockApprovalHistory)/useState([])/g' "$file"
    sed -i '' 's/useState(mockAttendanceStats)/useState([])/g' "$file"
    sed -i '' 's/useState(mockVehicles)/useState([])/g' "$file"
  fi
done

echo ""
echo "✅ 状态初始化修复完成"
