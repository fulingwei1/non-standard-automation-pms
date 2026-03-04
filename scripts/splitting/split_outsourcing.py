#!/usr/bin/env python3
"""
快速拆分 outsourcing.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/outsourcing.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/outsourcing")

    print("📖 读取 outsourcing.py (1498行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-88，到第一个section之前）
    imports = "".join(lines[0:88])

    # 根据章节注释定义模块
    modules = [
        {
            "name": "suppliers.py",
            "start": 90,
            "end": 303,
            "prefix": "/outsourcing/suppliers",
            "routes": "外协供应商",
        },
        {
            "name": "orders.py",
            "start": 304,
            "end": 652,
            "prefix": "/outsourcing/orders",
            "routes": "外协订单",
        },
        {
            "name": "deliveries.py",
            "start": 653,
            "end": 800,
            "prefix": "/outsourcing/deliveries",
            "routes": "外协交付",
        },
        {
            "name": "quality.py",
            "start": 801,
            "end": 1001,
            "prefix": "/outsourcing/quality",
            "routes": "外协质检",
        },
        {
            "name": "progress.py",
            "start": 1002,
            "end": 1089,
            "prefix": "/outsourcing/progress",
            "routes": "外协进度",
        },
        {
            "name": "payments.py",
            "start": 1090,
            "end": 1498,
            "prefix": "/outsourcing/payments",
            "routes": "外协付款",
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
从 outsourcing.py 拆分
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
外协管理 API - 模块化结构
"""

from fastapi import APIRouter

from .suppliers import router as suppliers_router
from .orders import router as orders_router
from .deliveries import router as deliveries_router
from .quality import router as quality_router
from .progress import router as progress_router
from .payments import router as payments_router

router = APIRouter()

router.include_router(suppliers_router)
router.include_router(orders_router)
router.include_router(deliveries_router)
router.include_router(quality_router)
router.include_router(progress_router)
router.include_router(payments_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ outsourcing.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
