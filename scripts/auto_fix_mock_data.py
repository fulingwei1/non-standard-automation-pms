#!/usr/bin/env python3
"""
自动修复前端页面中的 mock 数据和 demo 账号检查
"""

import re
from pathlib import Path

FRONTEND_DIR = Path("/Users/flw/non-standard-automation-pm/frontend/src/pages")


def fix_file(file_path: Path) -> int:
    """修复单个文件，返回修改的行数"""
    content = file_path.read_text(encoding='utf-8')
    modified = False
    changes = 0

    # 1. 移除 mock 数据定义
    # 查找 "const mockXXX = [" 或 "const mockXXX = {" 这样的模式
    mock_patterns = [
        (
            r"// Mock data for demo accounts\n(?:.|\n)*?^const mock[A-Z][a-zA-Z]+ = \[\s*\n(?:.|\n)*?\n\];?\s*\n",
            "",
        ),
        (
            r"// Mock data for demo accounts\n(?:.|\n)*?^const mock[A-Z][a-zA-Z]+ = \{\s*\n(?:.|\n)*?^\};?\s*\n",
            "",
        ),
        (
            r"^const mock[A-Z][a-zA-Z]+ = \[[\s\S]*?\];?\s*\n",
            "// Mock data - 已移除，使用真实API\n",
        ),
        (
            r"^const mock[A-Z][a-zA-Z]+ = \{[\s\S]*?\};?\s*\n",
            "// Mock data - 已移除，使用真实API\n",
        ),
    ]

    for pattern, replacement in mock_patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            changes += count
            modified = True

    # 2. 移除 isDemoAccount 声明
    demo_account_patterns = [
        r'\s+// Check if demo account\s*\n\s+const isDemoAccount = useMemo\(\(\) => \{\s+const token = localStorage\.getItem\([\'"]token[\'"]\)\s+return token && token\.startsWith\([\'"]demo_token_[\'"]\)\s+\}, \[\]\)\s*\n',
        r'\s+const isDemoAccount = localStorage\.getItem\([\'"]token[\'"]\)\?\.startsWith\([\'"]demo_token_[\'"]\)\s*\n',
        r'\s+const isDemoAccount = useMemo\(\(\) => \{\s+const token = localStorage\.getItem\([\'"]token[\'"]\)\s+return token && token\.startsWith\([\'"]demo_token_[\'"]\)\s+\}, \[\]\)\s*\n',
    ]

    for pattern in demo_account_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, "", content)
            changes += 1
            modified = True

    # 3. 移除 isDemoAccount 的条件判断 (简化版本)
    # 注意：这是简化处理，实际需要更复杂的逻辑
    # 建议人工检查和修复复杂的条件逻辑

    if modified:
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✅ {file_path.name}: {changes} 处修改")

    return changes


def auto_fix_all() -> None:
    """自动修复所有文件"""
    print("🚀 开始自动修复前端 mock 数据...")

    files_to_fix = []
    for file_path in FRONTEND_DIR.glob("*.jsx"):
        content = file_path.read_text(encoding="utf-8")

        # 检查是否需要修复
        if re.search(r"isDemoAccount|demo_token_|const mock[A-Z]", content):
            files_to_fix.append(file_path)

    if not files_to_fix:
        print("✅ 没有需要修复的文件")
        return

    print(f"📊 发现 {len(files_to_fix)} 个文件需要修复\n")

    total_changes = 0
    fixed_files = 0

    for file_path in files_to_fix:
        try:
            changes = fix_file(file_path)
            if changes > 0:
                total_changes += changes
                fixed_files += 1
        except Exception as e:
            print(f"  ❌ {file_path.name}: 修复失败 - {e}")

    print(f"\n✅ 修复完成:")
    print(f"   - 修复文件: {fixed_files}/{len(files_to_fix)}")
    print(f"   - 总修改数: {total_changes}")

    if fixed_files < len(files_to_fix):
        print(f"\n⚠️  {len(files_to_fix) - fixed_files} 个文件可能需要人工检查")


if __name__ == "__main__":
    auto_fix_all()
