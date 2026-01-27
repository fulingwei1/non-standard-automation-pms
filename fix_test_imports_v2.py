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
            lines = f.readlines()
        
        new_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是 try: 行
            if line.rstrip().endswith('try:'):
                # 检查下一行是否是服务导入
                if i + 1 < len(lines) and ('from app.services.' in lines[i + 1] or 'from app.services import' in lines[i + 1]):
                    # 收集 try 块的内容
                    try_indent = len(line) - len(line.lstrip())
                    try_block = [lines[i + 1]]  # 包含导入行
                    j = i + 2
                    found_except = False
                    
                    # 查找 try 块的内容和对应的 except
                    while j < len(lines):
                        current = lines[j]
                        current_indent = len(current) - len(current.lstrip())
                        
                        # 如果缩进相同或更小，且是 except Exception as e:
                        if current.strip().startswith('except Exception as e:'):
                            if current_indent == try_indent:
                                # 检查下一行是否是 pytest.skip with "Service dependencies not available"
                                if j + 1 < len(lines):
                                    skip_line = lines[j + 1]
                                    if 'Service dependencies not available' in skip_line:
                                        # 找到匹配的 except，移除 try 和 except，保留 try 块内容
                                        new_lines.extend(try_block)
                                        # 跳过 try:、except 和 pytest.skip 行
                                        i = j + 2
                                        modified = True
                                        found_except = True
                                        break
                        
                        # 如果缩进回到 try 的级别或更小，且不是空行或注释，try 块结束
                        if current_indent <= try_indent and current.strip() and not current.strip().startswith('#'):
                            if not found_except:
                                # 没有找到匹配的 except，保留原样
                                new_lines.append(line)
                                new_lines.extend(try_block)
                                i = j
                                break
                        
                        # 仍在 try 块内
                        if current_indent > try_indent or not current.strip() or current.strip().startswith('#'):
                            try_block.append(current)
                            j += 1
                        else:
                            # try 块结束，但没有找到匹配的 except
                            new_lines.append(line)
                            new_lines.extend(try_block)
                            i = j
                            break
                    else:
                        # 到达文件末尾
                        if not found_except:
                            new_lines.append(line)
                            new_lines.extend(try_block)
                        i = j
                    continue
            
            new_lines.append(line)
            i += 1
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
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
