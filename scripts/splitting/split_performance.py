#!/usr/bin/env python3
"""
快速拆分 performance.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/performance.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/performance')

    print("📖 读取 performance.py (1594行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-194，到第一个section之前）
    imports = ''.join(lines[0:194])

    # 根据章节注释定义模块
    modules = [
        {'name': 'individual.py', 'start': 196, 'end': 482, 'prefix': '/performance/individual', 'routes': '个人绩效'},
        {'name': 'team.py', 'start': 483, 'end': 749, 'prefix': '/performance/team', 'routes': '团队/部门绩效'},
        {'name': 'project.py', 'start': 750, 'end': 962, 'prefix': '/performance/project', 'routes': '项目绩效'},
        {'name': 'employee_api.py', 'start': 963, 'end': 1208, 'prefix': '/performance/new/employee', 'routes': '新绩效-员工端'},
        {'name': 'manager_api.py', 'start': 1209, 'end': 1446, 'prefix': '/performance/new/manager', 'routes': '新绩效-经理端'},
        {'name': 'hr_api.py', 'start': 1447, 'end': 1519, 'prefix': '/performance/new/hr', 'routes': '新绩效-HR端'},
        {'name': 'integration.py', 'start': 1520, 'end': 1594, 'prefix': '/performance/integration', 'routes': '绩效融合'},
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
从 performance.py 拆分
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
绩效管理 API - 模块化结构
"""

from fastapi import APIRouter

from .individual import router as individual_router
from .team import router as team_router
from .project import router as project_router
from .employee_api import router as employee_api_router
from .manager_api import router as manager_api_router
from .hr_api import router as hr_api_router
from .integration import router as integration_router

router = APIRouter()

router.include_router(individual_router)
router.include_router(team_router)
router.include_router(project_router)
router.include_router(employee_api_router)
router.include_router(manager_api_router)
router.include_router(hr_api_router)
router.include_router(integration_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ performance.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
