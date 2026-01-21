#!/usr/bin/env python3
"""
快速拆分 pmo.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/pmo.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/pmo')

    print("📖 读取 pmo.py (1986行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-70，到第一个section之前）
    imports = ''.join(lines[0:70])

    # 根据章节注释定义模块
    modules = [
        {'name': 'initiation.py', 'start': 72, 'end': 428, 'prefix': '/pmo/initiation', 'routes': '立项管理'},
        {'name': 'phases.py', 'start': 429, 'end': 703, 'prefix': '/pmo/phases', 'routes': '项目阶段'},
        {'name': 'risks.py', 'start': 704, 'end': 1063, 'prefix': '/pmo/risks', 'routes': '风险管理'},
        {'name': 'closure.py', 'start': 1064, 'end': 1359, 'prefix': '/pmo/closure', 'routes': '项目结项'},
        {'name': 'cockpit.py', 'start': 1360, 'end': 1743, 'prefix': '/pmo/cockpit', 'routes': 'PMO 驾驶舱'},
        {'name': 'meetings.py', 'start': 1744, 'end': 1986, 'prefix': '/pmo/meetings', 'routes': '会议管理'},
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
从 pmo.py 拆分
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
PMO API - 模块化结构
"""

from fastapi import APIRouter

from .initiation import router as initiation_router
from .phases import router as phases_router
from .risks import router as risks_router
from .closure import router as closure_router
from .cockpit import router as cockpit_router
from .meetings import router as meetings_router

router = APIRouter()

router.include_router(initiation_router)
router.include_router(phases_router)
router.include_router(risks_router)
router.include_router(closure_router)
router.include_router(cockpit_router)
router.include_router(meetings_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ pmo.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
