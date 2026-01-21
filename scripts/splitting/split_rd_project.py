#!/usr/bin/env python3
"""
快速拆分 rd_project.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/rd_project.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/rd_project')

    print("📖 读取 rd_project.py (1270行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-85，到第一个section之前）
    imports = ''.join(lines[0:85])

    # 根据章节注释定义模块
    modules = [
        {'name': 'categories.py', 'start': 87, 'end': 114, 'prefix': '/rd-project/categories', 'routes': '研发项目分类'},
        {'name': 'initiation.py', 'start': 115, 'end': 397, 'prefix': '/rd-project/initiation', 'routes': '研发项目立项'},
        {'name': 'expense_types.py', 'start': 398, 'end': 425, 'prefix': '/rd-project/expense-types', 'routes': '研发费用类型'},
        {'name': 'expenses.py', 'start': 426, 'end': 737, 'prefix': '/rd-project/expenses', 'routes': '研发费用归集'},
        {'name': 'allocation.py', 'start': 738, 'end': 941, 'prefix': '/rd-project/allocation', 'routes': '费用分摊规则'},
        {'name': 'worklogs.py', 'start': 942, 'end': 1082, 'prefix': '/rd-project/worklogs', 'routes': '研发项目工作日志'},
        {'name': 'documents.py', 'start': 1083, 'end': 1270, 'prefix': '/rd-project/documents', 'routes': '研发项目文档管理'},
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
从 rd_project.py 拆分
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
研发项目 API - 模块化结构
"""

from fastapi import APIRouter

from .categories import router as categories_router
from .initiation import router as initiation_router
from .expense_types import router as expense_types_router
from .expenses import router as expenses_router
from .allocation import router as allocation_router
from .worklogs import router as worklogs_router
from .documents import router as documents_router

router = APIRouter()

router.include_router(categories_router)
router.include_router(initiation_router)
router.include_router(expense_types_router)
router.include_router(expenses_router)
router.include_router(allocation_router)
router.include_router(worklogs_router)
router.include_router(documents_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ rd_project.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
