#!/usr/bin/env python3
"""
快速拆分 report_center.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/report_center.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/report_center')

    print("📖 读取 report_center.py (1401行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-39，到第一个section之前）
    imports = ''.join(lines[0:39])

    # 根据章节注释定义模块
    modules = [
        {'name': 'configs.py', 'start': 41, 'end': 105, 'prefix': '/report-center/configs', 'routes': '报表配置'},
        {'name': 'generate.py', 'start': 106, 'end': 571, 'prefix': '/report-center/generate', 'routes': '报表生成'},
        {'name': 'templates.py', 'start': 572, 'end': 686, 'prefix': '/report-center/templates', 'routes': '报表模板'},
        {'name': 'rd_expense.py', 'start': 687, 'end': 1047, 'prefix': '/report-center/rd-expense', 'routes': '研发费用报表'},
        {'name': 'bi.py', 'start': 1048, 'end': 1401, 'prefix': '/report-center/bi', 'routes': 'BI 报表'},
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
从 report_center.py 拆分
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
报表中心 API - 模块化结构
"""

from fastapi import APIRouter

from .configs import router as configs_router
from .generate import router as generate_router
from .templates import router as templates_router
from .rd_expense import router as rd_expense_router
from .bi import router as bi_router

router = APIRouter()

router.include_router(configs_router)
router.include_router(generate_router)
router.include_router(templates_router)
router.include_router(rd_expense_router)
router.include_router(bi_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ report_center.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
