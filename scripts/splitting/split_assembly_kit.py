#!/usr/bin/env python3
"""
快速拆分 assembly_kit.py 为模块化结构
"""
import re
from pathlib import Path

def read_file_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    source_file = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/assembly_kit.py')
    output_dir = Path('/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/assembly_kit')

    print("📖 读取 assembly_kit.py (1632行)...")
    lines = read_file_lines(source_file)

    # 提取导入（行1-58，到第一个section之前）
    imports = ''.join(lines[0:58])

    # 根据章节注释定义模块
    modules = [
        {'name': 'stages.py', 'start': 60, 'end': 106, 'prefix': '/assembly-kit/stages', 'routes': '装配阶段管理'},
        {'name': 'material_mapping.py', 'start': 107, 'end': 202, 'prefix': '/assembly-kit/material-mapping', 'routes': '物料分类映射'},
        {'name': 'bom_attributes.py', 'start': 203, 'end': 598, 'prefix': '/assembly-kit/bom-attributes', 'routes': 'BOM装配属性'},
        {'name': 'kit_analysis.py', 'start': 599, 'end': 1052, 'prefix': '/assembly-kit/kit-analysis', 'routes': '齐套分析'},
        {'name': 'shortage_alerts.py', 'start': 1053, 'end': 1143, 'prefix': '/assembly-kit/shortage-alerts', 'routes': '缺料预警'},
        {'name': 'alert_rules.py', 'start': 1144, 'end': 1212, 'prefix': '/assembly-kit/alert-rules', 'routes': '预警规则'},
        {'name': 'wechat_config.py', 'start': 1213, 'end': 1268, 'prefix': '/assembly-kit/wechat-config', 'routes': '企业微信配置'},
        {'name': 'scheduling.py', 'start': 1269, 'end': 1387, 'prefix': '/assembly-kit/scheduling', 'routes': '排产建议'},
        {'name': 'dashboard.py', 'start': 1388, 'end': 1543, 'prefix': '/assembly-kit/dashboard', 'routes': '看板'},
        {'name': 'templates.py', 'start': 1544, 'end': 1632, 'prefix': '/assembly-kit/templates', 'routes': '装配模板管理'},
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
从 assembly_kit.py 拆分
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
装配套件 API - 模块化结构
"""

from fastapi import APIRouter

from .stages import router as stages_router
from .material_mapping import router as material_mapping_router
from .bom_attributes import router as bom_attributes_router
from .kit_analysis import router as kit_analysis_router
from .shortage_alerts import router as shortage_alerts_router
from .alert_rules import router as alert_rules_router
from .wechat_config import router as wechat_config_router
from .scheduling import router as scheduling_router
from .dashboard import router as dashboard_router
from .templates import router as templates_router

router = APIRouter()

router.include_router(stages_router)
router.include_router(material_mapping_router)
router.include_router(bom_attributes_router)
router.include_router(kit_analysis_router)
router.include_router(shortage_alerts_router)
router.include_router(alert_rules_router)
router.include_router(wechat_config_router)
router.include_router(scheduling_router)
router.include_router(dashboard_router)
router.include_router(templates_router)

__all__ = ['router']
'''

    with open(output_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    print("\n✅ assembly_kit.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")

if __name__ == '__main__':
    main()
