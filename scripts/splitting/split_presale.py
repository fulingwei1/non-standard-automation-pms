#!/usr/bin/env python3
"""
快速拆分 presale.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/presale.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/presale')

    print("📖 读取 presale.py (1798行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-86，到第一个section之前）
    imports = ''.join(lines[0:86])

    # 根据章节注释定义模块
    modules = [
        {'name': 'tickets.py', 'start': 88, 'end': 519, 'prefix': '/presale/tickets', 'routes': '支持工单管理'},
        {'name': 'proposals.py', 'start': 520, 'end': 892, 'prefix': '/presale/proposals', 'routes': '技术方案管理'},
        {'name': 'templates.py', 'start': 893, 'end': 1190, 'prefix': '/presale/templates', 'routes': '方案模板库'},
        {'name': 'bids.py', 'start': 1191, 'end': 1517, 'prefix': '/presale/bids', 'routes': '投标管理'},
        {'name': 'statistics.py', 'start': 1518, 'end': 1798, 'prefix': '/presale/statistics', 'routes': '售前统计'},
    ]

    output_dir.mkdir(parents=True, exist_ok=True)

    for module in modules:
        print(f"📝 生成 {module['name']}...")

        start = module['start'] - 1
        end = min(module['end'], len(lines))

        module_code = ''.join(lines[start:end])
        routes = len(re.findall(r'@router\.', module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过: 没有找到路由")
            continue

        module_content = f'''# -*- coding: utf-8 -*-
"""
{module['routes']} - 自动生成
从 presale.py 拆分
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

        output_path = output_dir / module['name']
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(module_content)

        print(f"  ✅ {module['name']}: {routes} 个路由")

    # 创建__init__.py
    init_content = '''# -*- coding: utf-8 -*-
"""
售前管理 API - 模块化结构
"""

from fastapi import APIRouter

from .tickets import router as tickets_router
from .proposals import router as proposals_router
from .templates import router as templates_router
from .bids import router as bids_router
from .statistics import router as statistics_router

router = APIRouter()

router.include_router(tickets_router)
router.include_router(proposals_router)
router.include_router(templates_router)
router.include_router(bids_router)
router.include_router(statistics_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ presale.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
