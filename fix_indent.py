#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复测试文件的缩进问题"""

from pathlib import Path

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for i, line in enumerate(lines):
        # 如果行有16个或更多前导空格，且是代码行（不是注释），减少到8个空格
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            leading_spaces = len(line) - len(stripped)
            if leading_spaces >= 16:
                # 减少到8个空格（函数体内的标准缩进）
                new_lines.append('        ' + stripped)
                continue
        
        new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

# 修复所有被 v2 脚本处理过的文件
files_to_fix = [
    'tests/unit/test_user_sync_service.py',
    'tests/unit/test_alert_pdf_service.py',
]

for f in files_to_fix:
    if Path(f).exists():
        print(f"修复: {f}")
        fix_file(f)

print("完成")
