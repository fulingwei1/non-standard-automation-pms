#!/usr/bin/env python3
"""检查当前加载的API模块"""

import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. 获取Token
print("🔐 登录...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"❌ 登录失败: {response.text}")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Token: {token[:20]}...\n")

headers = {"Authorization": f"Bearer {token}"}

# 2. 测试各模块的关键API
modules = {
    "认证": "/api/v1/auth/me",
    "用户": "/api/v1/users/",
    "角色": "/api/v1/roles/",
    "权限": "/api/v1/permissions/",
    "项目": "/api/v1/projects/",
    "生产": "/api/v1/production/work-orders",
    "销售": "/api/v1/sales/opportunities",
    "客户": "/api/v1/customers/",
    "供应商": "/api/v1/suppliers/",
    "物料": "/api/v1/materials/",
    "采购订单": "/api/v1/purchase-orders/",
    "库存": "/api/v1/inventory/",
    "缺料": "/api/v1/shortage/alerts",
    "工时": "/api/v1/timesheet/records",
    "研发项目": "/api/v1/rd-projects/",
    "审批": "/api/v1/approvals/",
    "预售": "/api/v1/presale/tickets",
}

loaded = []
not_loaded = []

print("=" * 60)
print("模块加载状态检查")
print("=" * 60)

for name, path in modules.items():
    response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
    status = response.status_code
    
    if status == 404:
        print(f"❌ {name:12s} - 404 (路由未加载)")
        not_loaded.append(name)
    elif status in [200, 422]:
        print(f"✅ {name:12s} - {status} (已加载)")
        loaded.append(name)
    else:
        print(f"⚠️  {name:12s} - {status}")
        loaded.append(name)  # 可能已加载但有其他问题

print("\n" + "=" * 60)
print(f"📊 统计: {len(loaded)}/{len(modules)} 模块已加载 ({len(loaded)*100//len(modules)}%)")
print("=" * 60)

print(f"\n✅ 已加载 ({len(loaded)}): {', '.join(loaded)}")
print(f"\n❌ 未加载 ({len(not_loaded)}): {', '.join(not_loaded)}")
