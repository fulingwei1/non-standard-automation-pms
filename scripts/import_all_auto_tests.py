#!/usr/bin/env python
"""导入所有auto测试文件"""
import sys
import os
import importlib

sys.path.insert(0, '.')

modules = []

# 收集所有auto测试文件
for f in os.listdir('tests/unit'):
    if f.endswith('_auto.py') and f.startswith('test_'):
        mod = f.replace('.py', '')
        modules.append(f'tests.unit.{mod}')

print(f'Total tests: {len(modules)}')

for mod in modules:
    try:
        importlib.import_module(mod)
        print(f'OK: {mod}')
    except SyntaxError:
        print(f'SKIP: {mod} (syntax)')
    except Exception as e:
        print(f'FAIL: {mod}')

print('Done')