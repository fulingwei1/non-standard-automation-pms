#!/usr/bin/env python3
"""
分析前端代码中最长的函数
"""
import os
import re
from pathlib import Path
from typing import List, Tuple


def find_functions_in_jsx(file_path: Path) -> List[Tuple[str, int, int, str]]:
    """分析JSX/JS文件中的函数"""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 使用正则表达式匹配函数定义
        # 匹配: function name(...) { 或 const name = (...) => { 或 const name = function(...) {
        function_patterns = [
            (r'^\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\(', 'function'),  # function name()
            (r'^\s*const\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>\s*{', 'arrow'),  # const name = () => {
            (r'^\s*const\s+(\w+)\s*=\s*(async\s+)?function\s*\(', 'const function'),  # const name = function()
            (r'^\s*(\w+)\s*:\s*(async\s+)?\([^)]*\)\s*=>\s*{', 'method'),  # name: () => {
            (r'^\s*(\w+)\s*:\s*(async\s+)?function\s*\(', 'method function'),  # name: function()
        ]

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是函数定义
            for pattern, func_type in function_patterns:
                match = re.search(pattern, line)
                if match:
                    # 提取函数名
                    if func_type == 'function':
                        func_name = match.group(3) if match.groups() else match.group(1)
                    elif func_type == 'arrow':
                        func_name = match.group(1)
                    elif func_type == 'const function':
                        func_name = match.group(1)
                    elif func_type in ['method', 'method function']:
                        func_name = match.group(1)
                    else:
                        func_name = match.group(1) if match.groups() else 'anonymous'

                    # 计算函数体长度
                    start_line = i + 1
                    brace_count = line.count('{') - line.count('}')
                    paren_count = line.count('(') - line.count(')')
                    end_line = start_line

                    # 如果第一行就闭合了，跳过
                    if brace_count == 0 and '}' in line:
                        i += 1
                        continue

                    # 查找函数结束位置
                    j = i + 1
                    while j < len(lines) and (brace_count > 0 or paren_count > 0):
                        current_line = lines[j]
                        brace_count += current_line.count('{') - current_line.count('}')
                        paren_count += current_line.count('(') - current_line.count(')')

                        # 检查是否是函数结束（大括号闭合且不在字符串中）
                        if brace_count == 0 and paren_count <= 0:
                            # 检查下一行是否是函数调用或赋值
                            if j + 1 < len(lines):
                                next_line = lines[j + 1].strip()
                                # 如果下一行是函数调用或赋值，可能不是结束
                                if next_line and not (next_line.startswith('//') or
                                                     next_line.startswith('/*') or
                                                     next_line.startswith('*') or
                                                     next_line.startswith('}') or
                                                     next_line.startswith(')') or
                                                     next_line == ''):
                                    # 检查是否是链式调用
                                    if not (next_line.startswith('.') or
                                           next_line.startswith(';') or
                                           next_line.startswith('return')):
                                        break
                            end_line = j + 1
                            break
                        j += 1

                    if j < len(lines):
                        line_count = end_line - start_line + 1
                        if line_count > 10:  # 只记录超过10行的函数
                            functions.append((
                                str(file_path),
                                line_count,
                                start_line,
                                f"{func_name} ({func_type})"
                            ))
                    break

            i += 1

    except Exception:
        pass

    return functions

def main():
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / 'frontend'

    if not frontend_dir.exists():
        print("前端目录不存在")
        return

    all_functions = []

    # 分析JSX文件
    jsx_files = list(frontend_dir.rglob('*.jsx')) + list(frontend_dir.rglob('*.js'))
    print(f"分析 {len(jsx_files)} 个前端文件...")

    for jsx_file in jsx_files:
        # 跳过node_modules和构建文件
        if 'node_modules' in str(jsx_file) or 'dist' in str(jsx_file) or '.test.' in str(jsx_file):
            continue

        functions = find_functions_in_jsx(jsx_file)
        all_functions.extend(functions)

    # 按行数排序
    all_functions.sort(key=lambda x: x[1], reverse=True)

    # 输出Top 20
    print("\n" + "="*100)
    print("前端最长的函数 Top 20:")
    print("="*100)
    print(f"{'排名':<6} {'行数':<8} {'函数名':<50} {'文件':<30}")
    print("-"*100)

    for i, (file_path, line_count, start_line, func_name) in enumerate(all_functions[:20], 1):
        # 简化文件路径
        rel_path = os.path.relpath(file_path, project_root)
        if len(rel_path) > 28:
            rel_path = "..." + rel_path[-25:]

        if len(func_name) > 48:
            func_name = func_name[:45] + "..."

        print(f"{i:<6} {line_count:<8} {func_name:<50} {rel_path:<30} (第{start_line}行)")

    if all_functions:
        longest = all_functions[0]
        print("\n" + "="*100)
        print(f"最长的函数:")
        print(f"  文件: {longest[0]}")
        print(f"  函数: {longest[3]}")
        print(f"  行数: {longest[1]} 行")
        print(f"  起始行: {longest[2]}")
        print("="*100)

if __name__ == '__main__':
    main()
