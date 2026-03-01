#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试认证token是否有效
"""

import sys

import requests


def test_auth():
    """测试认证流程"""
    base_url = "http://localhost:8000/api/v1"
    token = None

    print("=" * 60)
    print("测试认证Token")
    print("=" * 60)

    # 1. 尝试登录
    print("\n1. 尝试登录...")
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            data={"username": "admin", "password": "admin"},
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            if token:
                print(f"✅ 登录成功，获取到token (长度: {len(token)})")
            else:
                print("❌ 登录成功但未获取到token")
                print(f"响应: {login_response.json()}")
                return False
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应: {login_response.text}")
            return False
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False

    if not token:
        return False

    # 2. 使用token访问权限列表
    print("\n2. 使用token访问权限列表...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        perm_response = requests.get(
            f"{base_url}/roles/permissions", headers=headers, timeout=5
        )
        print(f"状态码: {perm_response.status_code}")
        if perm_response.status_code == 200:
            data = perm_response.json()
            print(f"✅ 成功: 返回 {len(data)} 条权限")
            return True
        else:
            print(f"❌ 失败: {perm_response.status_code}")
            print(f"响应: {perm_response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


if __name__ == "__main__":
    success = test_auth()
    sys.exit(0 if success else 1)
