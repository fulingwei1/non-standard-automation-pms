#!/usr/bin/env python3
"""
快速拆分 task_center.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/task_center.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/task_center")

    print("📖 读取 task_center.py (1391行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-73，到第一个section之前）
    imports = "".join(lines[0:73])

    # 根据章节注释定义模块
    modules = [
        {
            "name": "overview.py",
            "start": 75,
            "end": 173,
            "prefix": "/task-center/overview",
            "routes": "任务概览",
        },
        {
            "name": "my_tasks.py",
            "start": 174,
            "end": 327,
            "prefix": "/task-center/my-tasks",
            "routes": "我的任务列表",
        },
        {
            "name": "detail.py",
            "start": 328,
            "end": 390,
            "prefix": "/task-center/detail",
            "routes": "任务详情",
        },
        {
            "name": "create.py",
            "start": 391,
            "end": 452,
            "prefix": "/task-center/create",
            "routes": "创建个人任务",
        },
        {
            "name": "update.py",
            "start": 453,
            "end": 506,
            "prefix": "/task-center/update",
            "routes": "更新任务进度",
        },
        {
            "name": "complete.py",
            "start": 507,
            "end": 548,
            "prefix": "/task-center/complete",
            "routes": "完成任务",
        },
        {
            "name": "transfer.py",
            "start": 549,
            "end": 628,
            "prefix": "/task-center/transfer",
            "routes": "任务转办",
        },
        {
            "name": "reject.py",
            "start": 629,
            "end": 737,
            "prefix": "/task-center/reject",
            "routes": "接收/拒绝转办任务",
        },
        {
            "name": "comments.py",
            "start": 738,
            "end": 870,
            "prefix": "/task-center/comments",
            "routes": "任务评论",
        },
        {
            "name": "batch.py",
            "start": 871,
            "end": 1391,
            "prefix": "/task-center/batch",
            "routes": "批量操作",
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
从 task_center.py 拆分
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
任务中心 API - 模块化结构
"""

from fastapi import APIRouter

from .overview import router as overview_router
from .my_tasks import router as my_tasks_router
from .detail import router as detail_router
from .create import router as create_router
from .update import router as update_router
from .complete import router as complete_router
from .transfer import router as transfer_router
from .reject import router as reject_router
from .comments import router as comments_router
from .batch import router as batch_router

router = APIRouter()

router.include_router(overview_router)
router.include_router(my_tasks_router)
router.include_router(detail_router)
router.include_router(create_router)
router.include_router(update_router)
router.include_router(complete_router)
router.include_router(transfer_router)
router.include_router(reject_router)
router.include_router(comments_router)
router.include_router(batch_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ task_center.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
