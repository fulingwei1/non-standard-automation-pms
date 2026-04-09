#!/usr/bin/env python
"""直接运行测试以累积覆盖率"""
import sys
import importlib
import traceback

sys.path.insert(0, '.')

# 导入并运行测试模块
test_modules = [
    'tests.unit.test_acceptance_service_auto',
    'tests.unit.test_project_services_auto',
    'tests.unit.test_customer_service_auto',
    'tests.unit.test_kpi_services_auto',
]

for mod in test_modules:
    try:
        imported = importlib.import_module(mod)
        print(f'Imported: {mod}')

        # 尝试运行测试类
        for name in dir(imported):
            if name.startswith('Test'):
                cls = getattr(imported, name)
                print(f'  Class: {name}')
    except Exception as e:
        print(f'FAIL: {mod} - {e}')
        traceback.print_exc()