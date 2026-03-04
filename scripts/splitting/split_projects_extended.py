#!/usr/bin/env python3
"""
拆分 projects/extended.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    """读取文件所有行"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_imports(lines):
    """提取导入语句"""
    imports = []
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            imports.append(line)
        elif imports and i > len(imports) + 10:
            break
    return "\n".join(imports)


def main():
    source_file = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/extended.py"
    )
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects")

    print("📖 读取 projects/extended.py...")
    lines = read_file_lines(source_file)

    # 提取导入
    imports = extract_imports(lines)

    # 定义各个模块（基于文件结构分析）
    modules = {
        "reviews.py": {"start": 64, "end": 500, "prefix": "/project-reviews", "name": "项目复盘"},
        "lessons.py": {"start": 500, "end": 900, "prefix": "/project-lessons", "name": "经验教训"},
        "best_practices.py": {
            "start": 900,
            "end": 1200,
            "prefix": "/best-practices",
            "name": "最佳实践",
        },
        "costs.py": {"start": 1200, "end": 1500, "prefix": "/financial-costs", "name": "财务成本"},
        "resources.py": {"start": 1500, "end": 1700, "prefix": "/resources", "name": "资源管理"},
        "relations.py": {"start": 1700, "end": 1850, "prefix": "/relations", "name": "关联分析"},
        "risks.py": {"start": 1850, "end": 1993, "prefix": "/risks", "name": "风险管理"},
    }

    # 创建输出目录
    output_dir.mkdir(exist_ok=True)

    # 为每个模块创建文件
    for module_name, config in modules.items():
        print(f"📝 生成 {module_name}...")

        start = config["start"] - 1
        end = min(config["end"], len(lines))

        if start >= len(lines):
            print(f"  ⚠️ 跳过 {module_name}")
            continue

        # 提取模块代码
        module_code = "".join(lines[start:end])

        # 统计路由数量
        routes = len(re.findall(r"@router\.", module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过 {module_name}: 没有找到路由")
            continue

        # 生成模块文件内容
        module_content = f'''# -*- coding: utf-8 -*-
"""
{config['name']} API
从 projects/extended.py 拆分
"""

{imports}

from fastapi import APIRouter

router = APIRouter(
    prefix="{config['prefix']}",
    tags=["{module_name.replace('.py', '')}"]
)

# ==================== 路由定义 ====================
# 共 {routes} 个路由

{module_code}
'''

        # 写入文件
        output_path = output_dir / f"ext_{module_name}"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(module_content)

        print(f"  ✅ ext_{module_name}: {routes} 个路由")

    print("\n✅ 拆分完成！")


if __name__ == "__main__":
    main()
