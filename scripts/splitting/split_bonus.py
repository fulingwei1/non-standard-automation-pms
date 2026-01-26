#!/usr/bin/env python3
"""
快速拆分 bonus.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/bonus.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/bonus')

    print("📖 读取 bonus.py (1472行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-48，到第一个section之前）
    imports = ''.join(lines[0:48])

    # 根据章节注释定义模块
    modules = [
        {'name': 'rules.py', 'start': 50, 'end': 229, 'prefix': '/bonus/rules', 'routes': '奖金规则管理'},
        {'name': 'calculation.py', 'start': 230, 'end': 404, 'prefix': '/bonus/calculation', 'routes': '奖金计算'},
        {'name': 'sales_calc.py', 'start': 405, 'end': 624, 'prefix': '/bonus/sales-calc', 'routes': '销售奖金计算'},
        {'name': 'payment.py', 'start': 625, 'end': 771, 'prefix': '/bonus/payment', 'routes': '奖金发放'},
        {'name': 'team.py', 'start': 772, 'end': 857, 'prefix': '/bonus/team', 'routes': '团队奖金分配'},
        {'name': 'my_bonus.py', 'start': 858, 'end': 895, 'prefix': '/bonus/my', 'routes': '我的奖金'},
        {'name': 'statistics.py', 'start': 896, 'end': 971, 'prefix': '/bonus/statistics', 'routes': '奖金统计'},
        {'name': 'details.py', 'start': 972, 'end': 1472, 'prefix': '/bonus/details', 'routes': '奖金分配明细表'},
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
从 bonus.py 拆分
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
奖金管理 API - 模块化结构
"""

from fastapi import APIRouter

from .rules import router as rules_router
from .calculation import router as calculation_router
from .sales_calc import router as sales_calc_router
from .payment import router as payment_router
from .team import router as team_router
from .my_bonus import router as my_bonus_router
from .statistics import router as statistics_router
from .details import router as details_router

router = APIRouter()

router.include_router(rules_router)
router.include_router(calculation_router)
router.include_router(sales_calc_router)
router.include_router(payment_router)
router.include_router(team_router)
router.include_router(my_bonus_router)
router.include_router(statistics_router)
router.include_router(details_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ bonus.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
