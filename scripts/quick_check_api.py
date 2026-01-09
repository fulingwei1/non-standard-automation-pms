#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查API端点是否正常工作
"""

import sys
import os
import requests
import json

def check_api_endpoint(base_url, endpoint, token=None):
    """检查API端点"""
    url = f"{base_url}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"\n{endpoint}:")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  ✅ 成功: 返回 {len(data)} 条数据")
            elif isinstance(data, dict):
                print(f"  ✅ 成功: 返回数据")
                if 'items' in data:
                    print(f"    项目数: {len(data.get('items', []))}")
            else:
                print(f"  ✅ 成功: 返回数据")
        else:
            print(f"  ❌ 失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  错误信息: {error_data.get('detail', '未知错误')}")
            except:
                print(f"  响应内容: {response.text[:200]}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"\n{endpoint}:")
        print(f"  ❌ 连接失败: 后端服务可能未启动")
        print(f"  请确认后端服务运行在 {base_url}")
        return False
    except Exception as e:
        print(f"\n{endpoint}:")
        print(f"  ❌ 请求失败: {e}")
        return False

def main():
    """主函数"""
    base_url = "http://localhost:8000/api/v1"
    
    print("=" * 60)
    print("API端点快速检查")
    print("=" * 60)
    print(f"\n检查后端服务: {base_url}")
    
    # 1. 检查健康状态
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print(f"⚠️  后端服务响应异常: {response.status_code}")
    except:
        print("❌ 后端服务未启动或无法连接")
        print("\n请先启动后端服务:")
        print("  uvicorn app.main:app --reload")
        return
    
    # 2. 尝试登录获取token
    print("\n尝试登录...")
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            data={"username": "admin", "password": "admin"},
            timeout=5
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("✅ 登录成功")
        else:
            print(f"⚠️  登录失败: {login_response.status_code}")
            token = None
    except Exception as e:
        print(f"⚠️  登录请求失败: {e}")
        token = None
    
    # 3. 检查各个端点
    print("\n" + "=" * 60)
    print("检查API端点")
    print("=" * 60)
    
    endpoints = [
        "/roles/permissions",
        "/roles/",
        "/roles/my/nav-groups",
    ]
    
    results = []
    for endpoint in endpoints:
        success = check_api_endpoint(base_url, endpoint, token)
        results.append((endpoint, success))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    for endpoint, success in results:
        status = "✅ 正常" if success else "❌ 失败"
        print(f"  {endpoint:30} {status}")
    
    if all(success for _, success in results):
        print("\n✅ 所有端点正常！")
    else:
        print("\n⚠️  部分端点失败，请查看后端日志获取详细信息")

if __name__ == "__main__":
    main()
