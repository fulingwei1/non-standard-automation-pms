#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复测试文件中的不必要 try-except 导入块
移除 "Service dependencies not available" 的跳过逻辑
"""

from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 模式1: 简单的 try-except 导入块
        # try:
        #     from app.services.xxx import YYY
        #     ...测试代码...
        # except Exception as e:
        #     pytest.skip(f"Service dependencies not available: {e}")
        
        # 匹配 try-except 块，其中 except 包含 "Service dependencies not available"
        pattern = r'(\s+)try:\s*\n(\s+)from\s+app\.services\.\S+\s+import\s+\S+\s*\n(\s+)(.*?)\n(\s+)except\s+Exception\s+as\s+e:\s*\n(\s+)pytest\.skip\(f?["\']Service\s+dependencies\s+not\s+available:\s+\{e\}["\']\)'
        
        def replace_try_except(match):
            indent = match.group(1)
            import_indent = match.group(2)
            code_indent = match.group(3)
            code = match.group(4)
            # 移除 try-except，直接保留导入和代码
            return f"{import_indent}from {match.group(0).split('from ')[1].split(' import')[0]} import {match.group(0).split(' import ')[1].split('\\n')[0]}\n{code_indent}{code}"
        
        # 更精确的模式：匹配完整的 try-except 块
        # 先处理简单的单行导入情况
        lines = content.split('\n')
        new_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是 try: 行，且下一行是导入语句
            if line.strip() == 'try:' and i + 1 < len(lines):
                next_line = lines[i + 1]
                # 检查是否是服务导入
                if 'from app.services.' in next_line or 'from app.services import' in next_line:
                    # 查找对应的 except 块
                    try_indent = len(line) - len(line.lstrip())
                    try_block_lines = [line]
                    j = i + 1
                    except_found = False
                    
                    while j < len(lines):
                        current_line = lines[j]
                        current_indent = len(current_line) - len(current_line.lstrip())
                        
                        # 如果缩进回到 try 的级别或更小，且是 except，检查是否是我们要找的
                        if current_line.strip().startswith('except Exception as e:'):
                            if current_indent == try_indent:
                                # 检查下一行是否是 pytest.skip
                                if j + 1 < len(lines):
                                    skip_line = lines[j + 1]
                                    if 'Service dependencies not available' in skip_line:
                                        # 找到完整的 try-except 块，移除 try 和 except
                                        # 保留 try 块内的内容
                                        try_block_lines.pop(0)  # 移除 try:
                                        try_block_lines.pop()  # 移除 except 行（如果有的话）
                                        new_lines.extend(try_block_lines)
                                        j += 2  # 跳过 except 和 pytest.skip 行
                                        i = j
                                        modified = True
                                        except_found = True
                                        break
                        
                        # 如果缩进小于 try，说明 try 块结束了
                        if current_indent <= try_indent and current_line.strip() and not current_line.strip().startswith('#'):
                            if not except_found:
                                # 没有找到对应的 except，保留原样
                                new_lines.extend(try_block_lines)
                                i = j
                                break
                        
                        try_block_lines.append(current_line)
                        j += 1
                    
                    if not except_found:
                        # 没有找到匹配的 except，保留原样
                        new_lines.extend(try_block_lines)
                        i = j
                    continue
            
            new_lines.append(line)
            i += 1
        
        if modified:
            new_content = '\n'.join(new_lines)
            # 验证修改后的代码仍然有效
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    tests_dir = Path('tests/unit')
    fixed_count = 0
    total_count = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if 'Service dependencies not available' in test_file.read_text(encoding='utf-8'):
            total_count += 1
            print(f"Processing: {test_file}")
            if fix_test_file(str(test_file)):
                fixed_count += 1
                print(f"  ✓ Fixed: {test_file}")
            else:
                print(f"  - No changes needed or error: {test_file}")
    
    print(f"\n总结: 处理了 {total_count} 个文件，修复了 {fixed_count} 个文件")

if __name__ == '__main__':
    main()
