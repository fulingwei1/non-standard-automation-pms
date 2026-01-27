#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复测试文件的缩进问题 - 完整版本"""

from pathlib import Path

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped:  # 空行
            new_lines.append(line)
            continue
        
        if stripped.startswith('#'):  # 注释行
            new_lines.append(line)
            continue
        
        leading_spaces = len(line) - len(stripped)
        
        # 如果缩进是12、16、20等（try块内的代码），减少到8个空格
        if leading_spaces >= 12:
            # 计算应该的缩进：函数体内应该是8个空格
            new_lines.append('        ' + stripped)
        else:
            new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

# 修复所有被 v2 脚本处理过的文件
test_dir = Path('tests/unit')
for test_file in test_dir.rglob('*.py'):
    content = test_file.read_text(encoding='utf-8')
    # 检查是否有缩进问题（12个或更多空格的行）
    has_issue = False
    for line in content.split('\n'):
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            leading = len(line) - len(stripped)
            if leading >= 12:
                has_issue = True
                break
    
    if has_issue:
        print(f"修复: {test_file}")
        fix_file(str(test_file))

print("完成")
