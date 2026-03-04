#!/usr/bin/env python3
"""
快速拆分 management_rhythm.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/management_rhythm.py"
    )
    output_dir = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/management_rhythm"
    )

    print("📖 读取 management_rhythm.py (1993行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-48，到router = APIRouter()为止）
    imports = "".join(lines[0:48])

    # 根据章节注释定义模块
    modules = [
        {
            "name": "configs.py",
            "start": 50,
            "end": 277,
            "prefix": "/management-rhythm/configs",
            "routes": "管理节律配置",
        },
        {
            "name": "meetings.py",
            "start": 278,
            "end": 635,
            "prefix": "/management-rhythm/meetings",
            "routes": "战略会议",
        },
        {
            "name": "action_items.py",
            "start": 636,
            "end": 779,
            "prefix": "/management-rhythm/action-items",
            "routes": "会议行动项",
        },
        {
            "name": "dashboard.py",
            "start": 780,
            "end": 941,
            "prefix": "/management-rhythm/dashboard",
            "routes": "节律仪表盘",
        },
        {
            "name": "meeting_map.py",
            "start": 942,
            "end": 1173,
            "prefix": "/management-rhythm/meeting-map",
            "routes": "会议地图",
        },
        {
            "name": "integrations.py",
            "start": 1174,
            "end": 1276,
            "prefix": "/management-rhythm/integrations",
            "routes": "数据集成",
        },
        {
            "name": "report_configs.py",
            "start": 1345,
            "end": 1567,
            "prefix": "/management-rhythm/report-configs",
            "routes": "报告配置管理",
        },
        {
            "name": "metrics.py",
            "start": 1568,
            "end": 1739,
            "prefix": "/management-rhythm/metrics",
            "routes": "指标定义管理",
        },
        {
            "name": "reports.py",
            "start": 1740,
            "end": 1993,
            "prefix": "/management-rhythm/reports",
            "routes": "会议报告",
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
从 management_rhythm.py 拆分
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
管理节律 API - 模块化结构
"""

from fastapi import APIRouter

from .configs import router as configs_router
from .meetings import router as meetings_router
from .action_items import router as action_items_router
from .dashboard import router as dashboard_router
from .meeting_map import router as meeting_map_router
from .integrations import router as integrations_router
from .report_configs import router as report_configs_router
from .metrics import router as metrics_router
from .reports import router as reports_router

router = APIRouter()

router.include_router(configs_router)
router.include_router(meetings_router)
router.include_router(action_items_router)
router.include_router(dashboard_router)
router.include_router(meeting_map_router)
router.include_router(integrations_router)
router.include_router(report_configs_router)
router.include_router(metrics_router)
router.include_router(reports_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ management_rhythm.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
