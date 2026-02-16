#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试认证问题"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json

# 禁用警告
import urllib3
urllib3.disable_warnings()

BASE_URL = "http://127.0.0.1:8000"

# 1. 获取token
print("=== 步骤1: 获取Token ===")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2)}")

if response.status_code != 200:
    print("❌ 登录失败")
    sys.exit(1)

token = response.json()["access_token"]
print(f"\n✅ Token获取成功: {token[:50]}...")

# 2. 测试/auth/me
print("\n=== 步骤2: 测试 GET /api/v1/auth/me ===")
response = requests.get(
    f"{BASE_URL}/api/v1/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"状态码: {response.status_code}")
try:
    print(f"响应: {json.dumps(response.json(), indent=2)}")
except:
    print(f"响应 (text): {response.text}")

# 3. 检查请求头
print("\n=== 步骤3: 检查请求详情 ===")
print(f"Token: Bearer {token}")
print(f"完整URL: {BASE_URL}/api/v1/auth/me")

# 4. 尝试直接调用auth模块
print("\n=== 步骤4: 直接测试auth模块 ===")
try:
    from app.core.auth import get_current_user
    from app.models.base import get_session
    
    db = get_session()
    try:
        import asyncio
        user = asyncio.run(get_current_user(token=token, db=db))
        print(f"✅ 用户: {user.username} (ID: {user.id})")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")
    finally:
        db.close()
except Exception as e:
    print(f"❌ 导入错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查token内容
print("\n=== 步骤5: 解析Token内容 ===")
try:
    import jwt
    from app.core.config import settings
    
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    print(f"Token payload: {json.dumps(payload, indent=2)}")
except Exception as e:
    print(f"❌ 解析错误: {e}")

# 6. 检查token是否被撤销
print("\n=== 步骤6: 检查Token是否被撤销 ===")
try:
    from app.core.auth import is_token_revoked
    
    revoked = is_token_revoked(token)
    print(f"Token是否被撤销: {revoked}")
except Exception as e:
    print(f"❌ 检查错误: {e}")
