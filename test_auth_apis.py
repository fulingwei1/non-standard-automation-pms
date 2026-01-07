#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证与权限 API 测试脚本（Python版本）
使用方法: python3 test_auth_apis.py
"""

import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8000/api/v1"


class Colors:
    """终端颜色"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_success(msg: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")


def print_error(msg: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")


def print_warning(msg: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")


def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if response.status_code == 200:
            print_success("服务器运行正常")
            print(f"   响应: {response.json()}")
            return True
    except requests.exceptions.RequestException:
        print_error("服务器未运行！")
        print("   请先启动服务器：")
        print("   cd 非标自动化项目管理系统")
        print("   uvicorn app.main:app --reload")
        return False


def test_api(method: str, endpoint: str, token: Optional[str] = None, 
              data: Optional[dict] = None, description: str = ""):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"\n{'='*50}")
    print(f"测试: {description}")
    print(f"请求: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=5)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return None
        
        if response.status_code >= 200 and response.status_code < 300:
            print_success(f"成功 (HTTP {response.status_code})")
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            except:
                print(f"响应: {response.text}")
                return response.text
        else:
            print_error(f"失败 (HTTP {response.status_code})")
            print(f"响应: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"请求异常: {str(e)}")
        return None


def test_login(username: str = "admin", password: str = "admin123"):
    """测试登录"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    print(f"\n{'='*50}")
    print("测试: 用户登录")
    print(f"请求: POST /auth/login")
    
    try:
        # 使用form-data格式（OAuth2标准）
        response = requests.post(
            url,
            data=data,  # form-data格式
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            if token:
                print_success("登录成功")
                print(f"Token: {token[:50]}...")
                return token
            else:
                print_error("登录响应中未找到token")
                return None
        else:
            print_error(f"登录失败 (HTTP {response.status_code})")
            print(f"响应: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"请求异常: {str(e)}")
        return None


def main():
    """主测试函数"""
    print("="*50)
    print("用户认证与权限 API 测试脚本（Python版本）")
    print("="*50)
    
    # 1. 检查服务器
    if not check_server():
        return
    
    # 2. 登录
    print("\n" + "="*50)
    print("2. 认证相关 API 测试")
    print("="*50)
    
    username = input("\n请输入用户名（默认: admin）: ").strip() or "admin"
    password = input("请输入密码（默认: admin123）: ").strip() or "admin123"
    
    token = test_login(username, password)
    if not token:
        print("\n提示: 如果数据库中没有用户，请先运行:")
        print("  python3 init_db.py")
        return
    
    # 3. 测试认证API
    test_api("GET", "/auth/me", token, description="获取当前用户信息")
    test_api("POST", "/auth/refresh", token, description="刷新Token")
    
    # 4. 测试用户管理API
    print("\n" + "="*50)
    print("3. 用户管理 API 测试")
    print("="*50)
    
    test_api("GET", "/users?page=1&page_size=10", token, 
             description="获取用户列表（分页）")
    test_api("GET", "/users?keyword=admin&page=1&page_size=10", token,
             description="搜索用户（关键词）")
    test_api("GET", "/users?is_active=true&page=1&page_size=10", token,
             description="筛选用户（启用状态）")
    
    # 创建测试用户
    create_user_data = {
        "username": f"test_user_{hash(username) % 10000}",
        "password": "test123456",
        "email": "test@example.com",
        "real_name": "测试用户",
        "employee_no": "EMP001",
        "department": "测试部门",
        "position": "测试职位"
    }
    create_result = test_api("POST", "/users", token, create_user_data,
                             description="创建新用户")
    
    # 5. 测试角色管理API
    print("\n" + "="*50)
    print("4. 角色管理 API 测试")
    print("="*50)
    
    test_api("GET", "/roles?page=1&page_size=10", token,
             description="获取角色列表（分页）")
    test_api("GET", "/roles/permissions", token,
             description="获取所有权限列表")
    
    # 创建测试角色
    create_role_data = {
        "role_code": f"TEST_ROLE_{hash(username) % 10000}",
        "role_name": "测试角色",
        "description": "这是一个测试角色",
        "data_scope": "OWN"
    }
    create_role_result = test_api("POST", "/roles", token, create_role_data,
                                  description="创建新角色")
    
    # 6. 测试完成
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    print("\n提示:")
    print("1. 可以访问 http://127.0.0.1:8000/docs 查看API文档")
    print("2. 可以访问 http://127.0.0.1:8000/redoc 查看ReDoc文档")
    print("3. 使用 bash test_auth_apis.sh 运行完整测试脚本")


if __name__ == "__main__":
    main()



