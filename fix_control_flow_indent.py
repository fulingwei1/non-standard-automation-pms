#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复控制流语句（for, if, with, try）的缩进问题"""

from pathlib import Path

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        
        # 检查是否是控制流语句
        if stripped.startswith(('for ', 'if ', 'with ', 'try:', 'elif ', 'else:')):
            # 检查下一行的缩进
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.lstrip()
                
                if next_stripped and not next_stripped.startswith('#'):
                    next_leading = len(next_line) - len(next_stripped)
                    current_leading = len(line) - len(stripped)
                    
                    # 如果下一行缩进不足（应该是当前缩进 + 4）
                    expected_indent = current_leading + 4
                    if next_leading < expected_indent:
                        # 修复缩进
                        new_lines.append(line)
                        fixed_line = ' ' * expected_indent + next_stripped + '\n'
                        new_lines.append(fixed_line)
                        i += 2
                        continue
        
        new_lines.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

# 修复有问题的文件
files_to_fix = [
    'tests/unit/test_work_log_auto_generator_service.py',
    'tests/unit/test_assembly_kit_service.py',
]

for f in files_to_fix:
    if Path(f).exists():
        print(f"修复: {f}")
        try:
            fix_file(f)
            # 验证语法
            import py_compile
            py_compile.compile(f, doraise=True)
            print("  ✓ 修复成功")
        except Exception as e:
            print(f"  ✗ 修复失败: {e}")

print("完成")
