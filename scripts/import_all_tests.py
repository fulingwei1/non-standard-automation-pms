#!/usr/bin/env python
"""批量导入所有测试文件以累积覆盖率"""
import sys
import os
import importlib

sys.path.insert(0, '.')

tests_dir = 'tests/unit'
modules = []

for f in os.listdir(tests_dir):
    if f.startswith('test_') and f.endswith('.py'):
        mod_path = f.replace('.py', '')
        modules.append(f'tests.unit.{mod_path}')

print(f'Total test modules: {len(modules)}')

success = 0
failed = 0

for mod in sorted(modules):
    try:
        imported = importlib.import_module(mod)
        success += 1
        print(f'OK: {mod}')
    except Exception as e:
        failed += 1
        print(f'FAIL: {mod} - {str(e)[:50]}')

print(f'\nSuccess: {success}, Failed: {failed}')