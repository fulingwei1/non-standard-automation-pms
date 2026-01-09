#!/usr/bin/env python3
"""
分析代码库中最长的函数
"""
import ast
import os
from pathlib import Path
from typing import List, Tuple

def analyze_python_file(file_path: Path) -> List[Tuple[str, int, int, str]]:
    """分析Python文件中的函数"""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算函数行数
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                line_count = end_line - start_line + 1
                
                # 获取函数名和类型
                func_name = node.name
                func_type = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                
                functions.append((str(file_path), line_count, start_line, f"{func_type} {func_name}"))
    except Exception as e:
        pass  # 忽略无法解析的文件
    
    return functions

def analyze_jsx_file(file_path: Path) -> List[Tuple[str, int, int, str]]:
    """分析JSX/JS文件中的函数"""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_function = False
        function_start = 0
        function_name = ""
        brace_count = 0
        paren_count = 0
        
        for i, line in enumerate(lines, 1):
            # 检测函数定义
            if 'function ' in line or 'const ' in line and '= (' in line or '= async (' in line:
                # 简单检测函数开始
                if 'function ' in line:
                    func_match = line.split('function')
                    if len(func_match) > 1:
                        func_part = func_match[1].strip()
                        if '(' in func_part:
                            function_name = func_part.split('(')[0].strip()
                            in_function = True
                            function_start = i
                            brace_count = 0
                            paren_count = line.count('(') - line.count(')')
                elif '= (' in line or '= async (' in line:
                    # 箭头函数或const函数
                    if '=' in line:
                        func_part = line.split('=')[0].strip()
                        if func_part.startswith('const '):
                            function_name = func_part.replace('const ', '').strip()
                        else:
                            function_name = func_part.strip()
                        in_function = True
                        function_start = i
                        brace_count = 0
                        paren_count = line.count('(') - line.count(')')
            
            if in_function:
                brace_count += line.count('{') - line.count('}')
                paren_count += line.count('(') - line.count(')')
                
                # 函数结束
                if brace_count == 0 and paren_count == 0 and (';' in line or line.strip().endswith(')')):
                    line_count = i - function_start + 1
                    functions.append((str(file_path), line_count, function_start, f"function {function_name}"))
                    in_function = False
                    function_name = ""
    except Exception as e:
        pass
    
    return functions

def main():
    project_root = Path(__file__).parent.parent
    all_functions = []
    
    # 分析Python文件
    python_files = list(project_root.rglob('*.py'))
    print(f"分析 {len(python_files)} 个Python文件...")
    
    for py_file in python_files:
        # 跳过虚拟环境和缓存
        if 'venv' in str(py_file) or '__pycache__' in str(py_file) or '.pyc' in str(py_file):
            continue
        functions = analyze_python_file(py_file)
        all_functions.extend(functions)
    
    # 分析JSX/JS文件
    jsx_files = list(project_root.rglob('*.jsx')) + list(project_root.rglob('*.js'))
    print(f"分析 {len(jsx_files)} 个JS/JSX文件...")
    
    for jsx_file in jsx_files:
        # 跳过node_modules
        if 'node_modules' in str(jsx_file):
            continue
        functions = analyze_jsx_file(jsx_file)
        all_functions.extend(functions)
    
    # 按行数排序
    all_functions.sort(key=lambda x: x[1], reverse=True)
    
    # 输出Top 20
    print("\n" + "="*80)
    print("最长的函数 Top 20:")
    print("="*80)
    print(f"{'排名':<6} {'行数':<8} {'文件':<50} {'函数':<30}")
    print("-"*80)
    
    for i, (file_path, line_count, start_line, func_name) in enumerate(all_functions[:20], 1):
        # 简化文件路径
        rel_path = os.path.relpath(file_path, project_root)
        if len(rel_path) > 47:
            rel_path = "..." + rel_path[-44:]
        
        print(f"{i:<6} {line_count:<8} {rel_path:<50} {func_name:<30} (第{start_line}行)")
    
    if all_functions:
        longest = all_functions[0]
        print("\n" + "="*80)
        print(f"最长的函数:")
        print(f"  文件: {longest[0]}")
        print(f"  函数: {longest[3]}")
        print(f"  行数: {longest[1]} 行")
        print(f"  起始行: {longest[2]}")
        print("="*80)

if __name__ == '__main__':
    main()
