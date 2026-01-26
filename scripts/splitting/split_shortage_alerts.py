#!/usr/bin/env python3
"""
拆分 shortage_alerts.py 为模块化结构
"""
import re
from pathlib import Path

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/shortage_alerts.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints')

    print("📖 读取 shortage_alerts.py (2161行)...")
    lines = open(source_file, 'r', encoding='utf-8').readlines()

    # 提取导入
    imports = []
    for i, line in enumerate(lines[:60]):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            imports.append(line)
    imports_str = '\n'.join(imports)

    # 定义模块（基于章节注释）
    modules = [
        {'name': 'alerts_crud.py', 'start': 36, 'end': 773, 'prefix': '', 'routes': '预警CRUD'},
        {'name': 'statistics.py', 'start': 430, 'end': 773, 'prefix': '/statistics', 'routes': '统计仪表板'},
        {'name': 'reports.py', 'start': 792, 'end': 1050, 'prefix': '/reports', 'routes': '缺料上报'},
        {'name': 'arrivals.py', 'start': 1069, 'end': 1344, 'prefix': '/arrivals', 'routes': '到货跟踪'},
        {'name': 'substitutions.py', 'start': 1363, 'end': 1693, 'prefix': '/substitutions', 'routes': '物料替代'},
        {'name': 'transfers.py', 'start': 1712, 'end': 2161, 'prefix': '/transfers', 'routes': '物料调拨'},
    ]

    output_dir.mkdir(exist_ok=True)

    for module in modules:
        print(f"📝 生成 {module['name']}...")

        start = module['start'] - 1
        end = min(module['end'], len(lines))

        module_code = ''.join(lines[start:end])
        routes = len(re.findall(r'@router\.', module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过: 没有找到路由")
            continue

        # 创建shortage_alerts子目录
        module_output_dir = output_dir / 'shortage_alerts'
        module_output_dir.mkdir(exist_ok=True)

        module_content = f'''# -*- coding: utf-8 -*-
"""
{module['routes']} - 自动生成
从 shortage_alerts.py 拆分
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

        output_path = module_output_dir / module['name']
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(module_content)

        print(f"  ✅ {module['name']}: {routes} 个路由")

    # 创建__init__.py
    init_content = '''# -*- coding: utf-8 -*-
"""
短缺预警 API - 模块化结构
"""

from fastapi import APIRouter

from .alerts_crud import router as alerts_router
from .statistics import router as statistics_router
from .reports import router as reports_router
from .arrivals import router as arrivals_router
from .substitutions import router as substitutions_router
from .transfers import router as transfers_router

router = APIRouter()

router.include_router(alerts_router)
router.include_router(statistics_router)
router.include_router(reports_router)
router.include_router(arrivals_router)
router.include_router(substitutions_router)
router.include_router(transfers_router)

__all__ = ['router']
'''

    with open(module_output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ shortage_alerts.py 拆分完成！")
    print(f"注意: 文件已创建到 shortage_alerts/ 目录")

if __name__ == '__main__':
    main()
