#!/usr/bin/env python
"""批量导入所有服务模块以累积覆盖率"""
import sys
import os
import importlib

sys.path.insert(0, '.')

# 动态收集所有服务模块路径
services_dir = 'app/services'
modules = []

for root, dirs, files in os.walk(services_dir):
    for f in files:
        if f.endswith('.py') and not f.startswith('__'):
            path = os.path.join(root, f)
            # 转换为模块路径
            mod_path = path.replace('/', '.').replace('.py', '')
            modules.append(mod_path)

# 添加 __init__ 模块
for root, dirs, files in os.walk(services_dir):
    if '__init__.py' in files:
        path = os.path.join(root, '__init__.py')
        mod_path = path.replace('/', '.').replace('.py', '')
        if mod_path not in modules:
            modules.append(mod_path)

print(f'Total modules to import: {len(modules)}')

success = 0
failed = 0

for mod in sorted(modules):
    try:
        importlib.import_module(mod)
        success += 1
    except Exception as e:
        failed += 1
        if failed <= 20:  # 只显示前20个失败
            print(f'FAIL: {mod}')

print(f'\nSuccess: {success}, Failed: {failed}')