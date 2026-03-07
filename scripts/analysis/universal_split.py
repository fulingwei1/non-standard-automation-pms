#!/usr/bin/env python3
"""
通用拆分脚本 - 可用于任何大文件
"""
import re
import sys
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_imports(lines):
    imports = []
    docstring = False
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            docstring = not docstring
        elif line.strip().startswith("from ") or line.strip().startswith("import "):
            if not docstring:
                imports.append(line)
        elif imports and i > len(imports) + 20:
            break
    return "\n".join(imports)


def auto_split_file(file_path_str, output_dir_str, modules_config):
    """
    自动拆分文件

    Args:
        file_path_str: 源文件路径
        output_dir_str: 输出目录路径
        modules_config: 模块配置列表，每个配置包含 name, start, end, prefix
    """
    source_file = Path(file_path_str)
    output_dir = Path(output_dir_str)

    print(f"📖 读取 {source_file.name}...")
    lines = read_file_lines(source_file)
    total_lines = len(lines)
    print(f"   总行数: {total_lines}")

    # 提取导入
    imports_str = extract_imports(lines)

    output_dir.mkdir(parents=True, exist_ok=True)

    total_routes = 0
    successful_modules = 0

    for module in modules_config:
        print(f"📝 生成 {module['name']}...")

        start = module["start"] - 1
        end = min(module["end"], total_lines)

        if start >= total_lines:
            print(f"  ⚠️ 跳过: 起始行超出范围")
            continue

        module_code = "".join(lines[start:end])
        routes = len(re.findall(r"@router\.", module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过: 没有找到路由")
            continue

        module_content = f'''# -*- coding: utf-8 -*-
"""
{module.get('description', module['name'].replace('.py', '').upper())} - 自动生成
"""
{imports_str}

from fastapi import APIRouter

router = APIRouter(
    prefix="{module['prefix']}",
    tags=["{module['name'].replace('.py', '')}"]
)

# 共 {routes} 个路由

{module_code}
'''

        output_path = output_dir / module["name"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(module_content)

        print(f"  ✅ {module['name']}: {routes} 个路由 ({end-start}行)")
        total_routes += routes
        successful_modules += 1

    print(f"\n✅ {source_file.name} 拆分完成！")
    print(f"   模块数: {successful_modules}")
    print(f"   总路由: {total_routes}")

    return successful_modules, total_routes


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 universal_split.py <source_file> <output_dir>")
        sys.exit(1)

    source_file = sys.argv[1]
    output_dir = sys.argv[2]

    # 这里可以配置模块，或者从配置文件读取
    # 示例配置...
    print("请提供模块配置...")
