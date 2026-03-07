#!/usr/bin/env python3
"""
快速拆分 shortage.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/shortage.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/shortage")

    print("📖 读取 shortage.py (2104行)...")
    lines = read_file_lines(source_file)

    # 提取导入和辅助函数（行1-145）
    imports_and_utils = "".join(lines[0:145])

    # 根据章节注释定义模块
    modules = [
        {
            "name": "reports.py",
            "start": 146,
            "end": 474,
            "prefix": "/shortage/reports",
            "routes": "缺料上报",
        },
        {
            "name": "arrivals.py",
            "start": 476,
            "end": 929,
            "prefix": "/shortage/arrivals",
            "routes": "到货跟踪",
        },
        {
            "name": "substitutions.py",
            "start": 932,
            "end": 1340,
            "prefix": "/shortage/substitutions",
            "routes": "物料替代",
        },
        {
            "name": "transfers.py",
            "start": 1343,
            "end": 1679,
            "prefix": "/shortage/transfers",
            "routes": "物料调拨",
        },
        {
            "name": "statistics.py",
            "start": 1682,
            "end": 2104,
            "prefix": "/shortage",
            "routes": "缺料统计",
        },
    ]

    output_dir.mkdir(parents=True, exist_ok=True)

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
从 shortage.py 拆分
"""

{imports_and_utils}

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

    # 创建__init__.py
    init_content = '''# -*- coding: utf-8 -*-
"""
缺料管理 API - 模块化结构
"""

from fastapi import APIRouter

from .reports import router as reports_router
from .arrivals import router as arrivals_router
from .substitutions import router as substitutions_router
from .transfers import router as transfers_router
from .statistics import router as statistics_router

router = APIRouter()

router.include_router(reports_router)
router.include_router(arrivals_router)
router.include_router(substitutions_router)
router.include_router(transfers_router)
router.include_router(statistics_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ shortage.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
