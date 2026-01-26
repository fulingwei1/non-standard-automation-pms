#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
循环依赖分析工具
分析 app/ 目录下的 Python 文件，检测潜在的循环导入
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class ImportVisitor(ast.NodeVisitor):
    """AST 访问器，用于提取导入语句"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.imports: List[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.startswith("app."):
                self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith("app"):
            self.imports.append(node.module)
        self.generic_visit(node)


def get_module_name(file_path: Path, base_path: Path) -> str:
    """将文件路径转换为模块名"""
    relative = file_path.relative_to(base_path)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def analyze_imports(base_path: Path) -> Dict[str, Set[str]]:
    """分析所有 Python 文件的导入关系"""
    imports_map = defaultdict(set)

    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or "migrations" in str(py_file):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            module_name = get_module_name(py_file, base_path.parent)
            visitor = ImportVisitor(module_name)
            visitor.visit(tree)

            for imp in visitor.imports:
                imports_map[module_name].add(imp)

        except Exception as e:
            print(f"警告: 无法解析 {py_file}: {e}")
            continue

    return imports_map


def find_cycles(imports_map: Dict[str, Set[str]]) -> List[List[str]]:
    """使用 DFS 查找循环依赖"""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in imports_map.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # 发现循环
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if len(cycle) > 2:  # 忽略自引用
                    cycles.append(cycle)

        rec_stack.remove(node)

    for node in imports_map:
        if node not in visited:
            dfs(node, [])

    return cycles


def main():
    base_path = Path("app")
    if not base_path.exists():
        print("错误: app/ 目录不存在")
        return

    print("正在分析导入关系...")
    imports_map = analyze_imports(base_path)
    print(f"已分析 {len(imports_map)} 个模块")

    print("\n正在检测循环依赖...")
    cycles = find_cycles(imports_map)

    if not cycles:
        print("✅ 未发现循环依赖")
        return

    print(f"\n⚠️ 发现 {len(cycles)} 个循环依赖:\n")

    # 去重和排序
    unique_cycles = []
    seen = set()
    for cycle in cycles:
        cycle_key = tuple(sorted(cycle))
        if cycle_key not in seen:
            seen.add(cycle_key)
            unique_cycles.append(cycle)

    for i, cycle in enumerate(unique_cycles[:20], 1):  # 只显示前 20 个
        print(f"{i}. 循环依赖 (长度 {len(cycle) - 1}):")
        for j, module in enumerate(cycle):
            if j < len(cycle) - 1:
                print(f"   {module}")
                print("     ↓")
            else:
                print(f"   {module} (回到起点)")
        print()

    if len(unique_cycles) > 20:
        print(f"... 还有 {len(unique_cycles) - 20} 个循环依赖未显示\n")

    # 统计最常出现在循环中的模块
    module_freq = defaultdict(int)
    for cycle in unique_cycles:
        for module in set(cycle):
            module_freq[module] += 1

    print("\n最常出现在循环依赖中的模块 (Top 10):")
    for module, count in sorted(module_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {count}x - {module}")


if __name__ == "__main__":
    main()
