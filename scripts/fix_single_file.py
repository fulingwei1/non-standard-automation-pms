#!/usr/bin/env python3
"""
修复单个文件的Mock数据使用
"""

import re
import sys
from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 1. 移除 Mock 数据定义
        # 移除 const mockXXX = ... 的整个块
        patterns_to_remove = [
            r'\n// Mock data.*?\nconst mock\w+\s*=\s*\{[^\}]*\}',
            r'\n// Mock data.*?\nconst mock\w+\s*=\s*\[[^\]]*\]',
            r'\n// Mock data for.*?\nconst mock\w+\s*=\s*\[[^\]]*\]',
            r'\nconst mockPurchaseRequests\s*=\s*\[[^\]]*\]',
            r'\nconst mockPendingApprovals\s*=\s*\[[^\]]*\]',
            r'\nconst mockStats\s*=\s*\{[^\}]*\}',
            r'\nconst demoStats\s*=\s*\{[^\}]*\}',
        ]

        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

        # 2. 移除 isDemoAccount 检查块
        # 移除整个 const isDemoAccount = ... if (isDemoAccount) { ... } 块
        demo_check_pattern = r'\s*//(?:如果|检查是否).*?演示账号.*?\n\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\).*?\n\s*if\s*\(\s*isDemoAccount\s*\)\s*\{[^}]*\}'

        content = re.sub(demo_check_pattern, '', content, flags=re.MULTILINE | re.DOTALL)

        # 3. 移除 useMemo 中的 isDemoAccount
        usememo_pattern = r'\s*const isDemoAccount\s*=\s*useMemo\(\(\)\s*=>\s*\{[^}]+\}\s*,\s*\[.*?\]\)'
        content = re.sub(usememo_pattern, '', content, flags=re.MULTILINE | re.DOTALL)

        # 4. 移除错误处理中的Mock回退
        # 这里只移除 isDemoAccount 相关，保留其他错误处理
        catch_demo = r'if\s*\(\!?isDemoAccount.*?\)\s*\{[^}]*\}'
        content = re.sub(catch_demo, '', content, flags=re.MULTILINE | re.DOTALL)

        # 5. 移除 useEffect 依赖中的 isDemoAccount
        content = re.sub(r',\s*\[isDemoAccount\]', ', []', content)
        content = re.sub(r'\[isDemoAccount\]', '[]', content)

        # 6. 移除相关注释
        comment_patterns = [
            r'// 如果是演示账号，使用 mock 数据.*?\n',
            r'// 演示账号不加载数据.*?\n',
            r'// 演示账号不调用真实API.*?\n',
            r'// 检查是否是演示账号.*?\n',
            r'// Mock data for.*?\n',
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
    if len(sys.argv) < 2:
        print("Usage: fix_single_file.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    fixed = fix_file(file_path)
    sys.exit(0 if fixed else 1)
