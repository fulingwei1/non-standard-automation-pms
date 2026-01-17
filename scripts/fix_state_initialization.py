#!/usr/bin/env python3
"""
修复状态初始化问题 - 将 useState(mockData) 改为 useState([])
"""

import re
import sys
from pathlib import Path

FILES_TO_FIX = [
    'frontend/src/pages/AdministrativeApprovals.jsx',
    'frontend/src/pages/AttendanceManagement.jsx',
    'frontend/src/pages/PerformanceManagement.jsx',
    'frontend/src/pages/VehicleManagement.jsx',
    'frontend/src/pages/CustomerServiceDashboard.jsx',
]

def fix_state_initialization(file_path: Path) -> bool:
    """修复状态初始化"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 替换 useState(mockPendingApprovals) -> useState([])
        content = re.sub(r'state=\[setApprovals\]\s*=\s*useState\(mockPendingApprovals\)',
                       r'state={[setApprovals]} = useState([])', content)

        content = re.sub(r'state=\[setApprovals\]\s*=\s*useState\(mockApprovalHistory\)',
                       r'state={[setApprovals]} = useState([])', content)

        content = re.sub(r'state=\[setAttendanceStats\]\s*=\s*useState\(mockAttendanceStats\)',
                       r'state={[setAttendanceStats]} = useState([])', content)

        content = re.sub(r'state=\[setVehicles\]\s*=\s*useState\(mockVehicles\)',
                       r'state={[setVehicles]} = useState([])', content)

        content = re.sub(r'state=\[setStats\]\s*=\s*useState\(mockStats\)',
                       r'state={[setStats]} = useState({})', content)

        # 如果有修改，保存文件
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True

        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    base_path = Path("/Users/flw/non-standard-automation-pm")

    fixed = 0
    for filename in FILES_TO_FIX:
        file_path = base_path / filename
        if file_path.exists():
            if fix_state_initialization(file_path):
                print(f"✅ 已修复: {filename}")
                fixed += 1
            else:
                print(f"⏭️  无需修复: {filename}")
        else:
            print(f"❌ 文件不存在: {filename}")

    print(f"\n总计: 修复了 {fixed} 个文件")
