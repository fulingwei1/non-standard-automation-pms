#!/usr/bin/env python
"""导入更多app模块"""
import sys
import os
import importlib

sys.path.insert(0, '.')

# 高覆盖率模块
modules = [
    'app.api.deps',
    'app.api.v1.endpoints.production.work_orders.assignment',
    'app.api.v1.endpoints.production.work_orders.crud',
    'app.api.v1.endpoints.production.work_orders.progress',
    'app.api.v1.endpoints.production.work_orders.utils',
    'app.api.v1.endpoints.production.workers',
    'app.api.v1.endpoints.production.workshops',
    'app.api.v1.endpoints.production.plans',
    'app.api.v1.endpoints.production.exceptions',
    'app.api.v1.endpoints.production.exception_enhancement',
    'app.api.v1.endpoints.production.capacity.dashboard',
    'app.api.v1.endpoints.production.capacity.calculation',
    'app.api.v1.endpoints.acceptance.order_approval',
    'app.api.v1.endpoints.acceptance.issues.follow_ups',
    'app.api.v1.endpoints.acceptance.templates.items',
    'app.api.v1.endpoints.alerts.exceptions',
    'app.api.v1.endpoints.alerts.notifications',
    'app.common.context',
    'app.common.pagination',
    'app.common.crud.types',
    'app.common.crud.exceptions',
    'app.common.dashboard.base',
    'app.core.exceptions',
]

success = 0
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f'OK: {mod}')
        success += 1
    except Exception as e:
        print(f'FAIL: {mod}')

print(f'\nSuccess: {success}/{len(modules)}')