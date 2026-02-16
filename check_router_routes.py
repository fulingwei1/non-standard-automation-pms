#!/usr/bin/env python3
"""检查各模块router是否有路由"""

import sys
sys.path.insert(0, '.')

modules_to_check = [
    ("库存", "app.api.v1.endpoints.inventory.inventory_router", "router"),
    ("缺料", "app.api.v1.endpoints.shortage", "router"),
    ("研发", "app.api.v1.endpoints.rd_project", "router"),
    ("审批", "app.api.v1.endpoints.approvals", "router"),
    ("预售", "app.api.v1.endpoints.presale", "router"),
]

print("检查各模块router的路由数量:")
print("=" * 60)

for name, module_path, attr_name in modules_to_check:
    try:
        module = __import__(module_path, fromlist=[attr_name])
        router = getattr(module, attr_name)
        route_count = len(router.routes)
        
        if route_count > 0:
            print(f"✅ {name:6s} - {route_count:3d} 个路由")
            # 打印前3个路由
            for route in router.routes[:3]:
                if hasattr(route, 'path'):
                    print(f"   └─ {route.path}")
        else:
            print(f"❌ {name:6s} - 0 个路由 (router是空的!)")
    except Exception as e:
        print(f"❌ {name:6s} - 导入失败: {str(e)[:50]}")

