#!/usr/bin/env python3
import requests

BASE_URL = "http://127.0.0.1:8001"

# 1. 登录
print("🔐 登录 (端口8001)...")
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

# 2. 测试关键路由
modules = {
    "角色": "/api/v1/roles/",
    "权限": "/api/v1/permissions/",
    "库存": "/api/v1/inventory/",
    "缺料": "/api/v1/shortage/alerts",
    "研发": "/api/v1/rd-projects/",
    "审批": "/api/v1/approvals/",
    "预售": "/api/v1/presale/tickets",
}

print("=" * 60)
loaded, not_loaded = [], []

for name, path in modules.items():
    response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
    status = response.status_code
    
    if status == 404:
        print(f"❌ {name:6s} - 404")
        not_loaded.append(name)
    else:
        print(f"✅ {name:6s} - {status}")
        loaded.append(name)

print("=" * 60)
print(f"\n📊 {len(loaded)}/{len(modules)} 模块可用")
if loaded:
    print(f"✅ 已加载: {', '.join(loaded)}")
if not_loaded:
    print(f"❌ 未加载: {', '.join(not_loaded)}")
