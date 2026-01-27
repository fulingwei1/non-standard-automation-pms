#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复测试文件中的不必要 try-except 导入块
移除 "Service dependencies not available" 的跳过逻辑，并修复缩进
"""

import re
from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 使用正则表达式匹配并替换 try-except 块
        # 模式：try: ... except Exception as e: pytest.skip("Service dependencies not available")
        
        # 匹配 try: 后面跟着导入语句，然后是代码，最后是 except Exception as e: pytest.skip
        pattern = r'(\s+)try:\s*\n(\s+)(from\s+app\.services\.[^\n]+)\s*\n((?:\s+[^\n]+\n)*?)(\s+)except\s+Exception\s+as\s+e:\s*\n(\s+)pytest\.skip\(f?["\']Service\s+dependencies\s+not\s+available[^"\']*["\']\)'
        
        def replace_block(match):
            func_indent = match.group(1)  # 函数缩进（try 的缩进）
            import_indent = match.group(2)  # 导入语句的缩进
            import_stmt = match.group(3)  # 导入语句
            code_block = match.group(4)  # try 块内的代码
            
            # 计算代码块需要的缩进（相对于函数）
            # 导入语句应该在函数体内，使用函数缩进 + 4 个空格
            new_indent = func_indent + '        '  # 8个空格（函数体缩进）
            
            # 修复代码块的缩进
            fixed_code_lines = []
            for line in code_block.split('\n'):
                if line.strip():  # 非空行
                    # 移除原来的缩进，添加新的缩进
                    stripped = line.lstrip()
                    fixed_code_lines.append(new_indent + stripped)
                else:
                    fixed_code_lines.append('')
            
            # 组合：导入语句 + 修复后的代码
            result = new_indent + import_stmt + '\n'
            if fixed_code_lines:
                result += '\n'.join(fixed_code_lines)
                if not result.endswith('\n'):
                    result += '\n'
            
            return result
        
        # 执行替换
        new_content = re.sub(pattern, replace_block, content, flags=re.MULTILINE)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    tests_dir = Path('tests/unit')
    fixed_count = 0
    total_count = 0
    
    # 先统计需要处理的文件
    test_files = []
    for test_file in tests_dir.rglob('*.py'):
        try:
            content = test_file.read_text(encoding='utf-8')
            if 'Service dependencies not available' in content:
                test_files.append(test_file)
        except:
            pass
    
    print(f"找到 {len(test_files)} 个需要处理的文件\n")
    
    for test_file in test_files:
        total_count += 1
        rel_path = str(test_file).replace(str(Path.cwd()) + '/', '')
        print(f"[{total_count}/{len(test_files)}] 处理: {rel_path}")
        if fix_test_file(str(test_file)):
            fixed_count += 1
            print("  ✓ 已修复")
        else:
            print("  - 无需修改或处理失败")
    
    print(f"\n总结: 处理了 {total_count} 个文件，修复了 {fixed_count} 个文件")

if __name__ == '__main__':
    main()
