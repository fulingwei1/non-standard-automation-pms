#!/usr/bin/env python3
"""
修复仪表板页面的Mock数据
"""

import re
import sys
from pathlib import Path

FILES_TO_FIX = [
    'frontend/src/pages/PerformanceManagement.jsx',
    'frontend/src/pages/ProcurementManagerDashboard.jsx',
    'frontend/src/pages/CustomerServiceDashboard.jsx',
    'frontend/src/pages/ManufacturingDirectorDashboard.jsx',
    'frontend/src/pages/ContractApproval.jsx',
    'frontend/src/pages/AdministrativeApprovals.jsx',
    'frontend/src/pages/VehicleManagement.jsx',
    'frontend/src/pages/AttendanceManagement.jsx',
]

def fix_dashboard_file(file_path: Path) -> bool:
    """修复仪表板文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 1. 移除 Mock 数据定义（更全面的模式）
        patterns = [
            # 移除 const mockXXX = {...} 或 [...]
            r'\n// Mock data.*?\nconst mock\w+\s*=\s*\{[^\}]*\}',
            r'\n// Mock data.*?\nconst mock\w+\s*=\s*\[[^\]]*\]',
            r'\n// Mock data for.*?\nconst mock\w+\s*=\s*\{[^\}]*\}',
            r'\n// Mock data for.*?\nconst mock\w+\s*=\s*\[[^\]]*\]',
            # 移除 const demoStats = {...}
            r'\n(?://\s*)?const demoStats\s*=\s*\{[^\}]*\}',
            # 移除所有 mockStats, mockXXX 的定义
            r'\nconst mock\w+\s*=\s*\{[^\}]*\}',
            r'\nconst mock\w+\s*=\s*\[[^\]]*\]',
        ]

        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

        # 2. 移除 isDemoAccount 检查
        demo_patterns = [
            r'\s*//(?:如果|检查是否).*?演示账号.*?\n\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\).*?\n\s*(?:if\s*\(\s*isDemoAccount\s*\)\s*\{[^}]*\}\s*)+',
            r'\s*const isDemoAccount\s*=\s*useMemo\(\(\)\s*=>\s*\{[^}]+\}\s*,\s*\[.*?\]\)',
            r'\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\)',
        ]

        for pattern in demo_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

        # 3. 移除错误处理中的Mock回退
        catch_demo = r'if\s*\(\s*!?isDemoAccount.*?\)\s*\{[^}]*\}'
        content = re.sub(catch_demo, '', content, flags=re.MULTILINE | re.DOTALL)

        # 4. 移除 useEffect 依赖中的 isDemoAccount
        content = re.sub(r',\s*\[isDemoAccount\]', ', []', content)
        content = re.sub(r'\[isDemoAccount\]', '[]', content)

        # 5. 移除Mock数据注释
        comment_patterns = [
            r'// Mock data.*?\n',
            r'// Mock data for demo accounts.*?\n',
            r'// 如果是演示账号，使用 mock 数据.*?\n',
        ]
        for pattern in comment_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)

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

    print("修复仪表板页面的Mock数据...")
    print()

    fixed = 0
    for filename in FILES_TO_FIX:
        file_path = base_path / filename
        if file_path.exists():
            if fix_dashboard_file(file_path):
                print(f"✅ 已修复: {filename}")
                fixed += 1
            else:
                print(f"⏭️  无需修复: {filename}")
        else:
            print(f"❌ 文件不存在: {filename}")

    print()
    print(f"总计: 修复了 {fixed} 个文件")
