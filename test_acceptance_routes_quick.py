#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证 acceptance 路由是否正确注册"""

import os
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-with-32-chars-minimum!"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 检查路由是否注册
routes = [str(route.path) for route in app.routes]
print(f"总路由数: {len(routes)}")

acceptance_routes = [r for r in routes if 'acceptance' in r.lower()]
print(f"\nAcceptance相关路由({len(acceptance_routes)}):")
for route in sorted(acceptance_routes)[:20]:
    print(f"  - {route}")

# 检查特定路由
target_routes = [
    "/api/v1/acceptance-templates",
    "/api/v1/acceptance-orders"
]

print("\n目标路由检查:")
for target in target_routes:
    if target in routes:
        print(f"✓ {target} - 已注册")
    else:
        print(f"✗ {target} - 未找到")
