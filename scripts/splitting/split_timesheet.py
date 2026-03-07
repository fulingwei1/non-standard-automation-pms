#!/usr/bin/env python3
"""
快速拆分 timesheet.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/timesheet.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/timesheet")

    print("📖 读取 timesheet.py (1570行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-101，到第一个section之前）
    imports = "".join(lines[0:101])

    # 根据章节注释定义模块
    modules = [
        {
            "name": "records.py",
            "start": 103,
            "end": 459,
            "prefix": "/timesheet/records",
            "routes": "工时记录管理",
        },
        {
            "name": "approval.py",
            "start": 460,
            "end": 668,
            "prefix": "/timesheet/approval",
            "routes": "提交与审批",
        },
        {
            "name": "weekly.py",
            "start": 669,
            "end": 762,
            "prefix": "/timesheet/weekly",
            "routes": "周工时表",
        },
        {
            "name": "monthly.py",
            "start": 763,
            "end": 844,
            "prefix": "/timesheet/monthly",
            "routes": "月度汇总",
        },
        {
            "name": "pending.py",
            "start": 845,
            "end": 939,
            "prefix": "/timesheet/pending",
            "routes": "待审核列表",
        },
        {
            "name": "statistics.py",
            "start": 940,
            "end": 1227,
            "prefix": "/timesheet/statistics",
            "routes": "工时统计分析",
        },
        {
            "name": "reports.py",
            "start": 1228,
            "end": 1570,
            "prefix": "/timesheet/reports",
            "routes": "工时汇总与报表",
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
从 timesheet.py 拆分
"""

{imports}

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
工时管理 API - 模块化结构
"""

from fastapi import APIRouter

from .records import router as records_router
from .approval import router as approval_router
from .weekly import router as weekly_router
from .monthly import router as monthly_router
from .pending import router as pending_router
from .statistics import router as statistics_router
from .reports import router as reports_router

router = APIRouter()

router.include_router(records_router)
router.include_router(approval_router)
router.include_router(weekly_router)
router.include_router(monthly_router)
router.include_router(pending_router)
router.include_router(statistics_router)
router.include_router(reports_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ timesheet.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
