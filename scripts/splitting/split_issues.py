#!/usr/bin/env python3
"""
快速拆分 issues.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/issues.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/issues")

    print("📖 读取 issues.py (2419行)...")
    lines = read_file_lines(source_file)

    # 提取导入
    imports = []
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            imports.append(line)
        elif line.strip().startswith('"""') or line.strip().startswith("'''"):
            if imports:
                break
    imports_str = "\n".join(imports)

    # 根据章节注释定义模块
    modules = [
        {"name": "crud.py", "start": 191, "end": 1230, "prefix": "", "routes": "CRUD操作"},
        {"name": "batch.py", "start": 1233, "end": 1385, "prefix": "/batch", "routes": "批量操作"},
        {
            "name": "import_export.py",
            "start": 1386,
            "end": 1573,
            "prefix": "",
            "routes": "导入导出",
        },
        {"name": "board.py", "start": 1574, "end": 1629, "prefix": "/board", "routes": "看板数据"},
        {
            "name": "statistics.py",
            "start": 1630,
            "end": 1921,
            "prefix": "/statistics",
            "routes": "统计分析",
        },
        {"name": "related.py", "start": 1814, "end": 1921, "prefix": "", "routes": "关联问题"},
        {
            "name": "templates.py",
            "start": 2120,
            "end": 2419,
            "prefix": "/templates",
            "routes": "问题模板",
        },
    ]

    output_dir.mkdir(exist_ok=True)

    for module in modules:
        print(f"📝 生成 {module['name']}...")

        start = module["start"] - 1
        end = min(module["end"], len(lines))

        module_code = "".join(lines[start:end])
        routes = len(re.findall(r"@router\.", module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过: 没有找到路由")
            continue

        module_content = f'''# -*- coding: utf-8 -*-
"""
{module['routes']} - 自动生成
从 issues.py 拆分
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

        print(f"  ✅ {module['name']}: {routes} 个路由")

    print("\n✅ issues.py 拆分完成！")


if __name__ == "__main__":
    main()
