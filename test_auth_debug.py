#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证功能调试脚本
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_refresh_token():
    """测试refresh token功能"""
    print("=" * 60)
    print("测试 Refresh Token")
    print("=" * 60)
    
    # 先登录
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    print(f"登录状态码: {response.status_code}")
    print(f"登录响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    if response.status_code == 200:
        data = response.json()
        refresh_token = data.get('refresh_token')
        
        if refresh_token:
            print(f"✓ 获取到refresh_token: {refresh_token[:50]}...\n")
            
            # 尝试刷新token
            refresh_data = {"refresh_token": refresh_token}
            time.sleep(1)
            
            response2 = requests.post(f"{BASE_URL}/api/v1/auth/refresh", 
                                     json=refresh_data)
            
            print(f"刷新Token状态码: {response2.status_code}")
            print(f"刷新Token响应: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")
        else:
            print("✗ 登录响应中没有refresh_token")


def test_password_change():
    """测试修改密码功能"""
    print("\n" + "=" * 60)
    print("测试 修改密码")
    print("=" * 60)
    
    # 先登录
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "admin123",
            "new_password": "NewAdmin123!"
        }
        
        time.sleep(1)
        response2 = requests.put(f"{BASE_URL}/api/v1/auth/password", 
                                headers=headers, json=password_data)
        
        print(f"修改密码状态码: {response2.status_code}")
        print(f"修改密码响应: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")


def test_logout():
    """测试登出功能"""
    print("\n" + "=" * 60)
    print("测试 登出")
    print("=" * 60)
    
    # 先登录
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        
        headers = {"Authorization": f"Bearer {token}"}
        logout_data = {"logout_all": False}
        
        time.sleep(1)
        response2 = requests.post(f"{BASE_URL}/api/v1/auth/logout", 
                                 headers=headers, json=logout_data)
        
        print(f"登出状态码: {response2.status_code}")
        print(f"登出响应: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    test_refresh_token()
    test_password_change()
    test_logout()
