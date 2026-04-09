#!/usr/bin/env python
"""导入所有app模块"""
import sys
import os
import importlib

sys.path.insert(0, '.')

modules = []

# 收集所有app模块
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            mod = path.replace('/', '.').replace('.py', '')
            modules.append(mod)

print(f'Total: {len(modules)}')

for mod in modules:
    try:
        importlib.import_module(mod)
    except Exception:
        pass

print('Done')