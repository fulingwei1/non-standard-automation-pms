#!/usr/bin/env python3
"""
测试不同角色权限控制
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# 测试账号配置（需要先在数据库中创建）
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin123", "role": "系统管理员"},
    "pm": {"username": "pm001", "password": "pm123", "role": "项目经理"},
    "sales": {"username": "sales001", "password": "sales123", "role": "销售专员"},
    "engineer": {"username": "eng001", "password": "eng123", "role": "机械工程师"},
}

# 需要测试的API端点和对应的权限要求
TEST_ENDPOINTS = [
    # 全局管理功能（仅管理员）
    {"method": "GET", "path": "/api/v1/users", "name": "用户列表", "admin_only": True},
    {"method": "GET", "path": "/api/v1/roles", "name": "角色列表", "admin_only": True},
    
    # 项目管理（项目经理/管理员）
    {"method": "GET", "path": "/api/v1/projects", "name": "项目列表", "admin_only": False},
    {"method": "POST", "path": "/api/v1/projects", "name": "创建项目", "admin_only": False, 
     "data": {"project_name": "测试项目", "project_code": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"}},
    
    # 销售管理（销售/管理员）
    {"method": "GET", "path": "/api/v1/opportunities", "name": "商机列表", "admin_only": False},
    
    # 工程师功能
    {"method": "GET", "path": "/api/v1/tasks", "name": "任务列表", "admin_only": False},
]


def login(username, password):
    """登录并获取token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ 登录失败 ({username}): {response.status_code} - {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ 登录异常 ({username}): {e}")
        return None


def test_endpoint(endpoint_config, token, role_name):
    """测试API端点访问权限"""
    method = endpoint_config["method"]
    path = endpoint_config["path"]
    name = endpoint_config["name"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
        elif method == "POST":
            data = endpoint_config.get("data", {})
            response = requests.post(f"{BASE_URL}{path}", headers=headers, json=data, timeout=5)
        else:
            return f"⚠️  不支持的方法: {method}"
        
        status = response.status_code
        if status == 200:
            return f"✅ {status}"
        elif status == 403:
            return f"🚫 {status} (无权限)"
        elif status == 401:
            return f"🔒 {status} (未认证)"
        elif status == 404:
            return f"❓ {status} (端点不存在)"
        else:
            return f"⚠️  {status}"
    except requests.exceptions.Timeout:
        return "⏱️  超时"
    except Exception as e:
        return f"❌ {str(e)[:30]}"


def main():
    print("=" * 80)
    print("🔐 非标自动化项目管理系统 - 权限控制测试")
    print("=" * 80)
    print()
    
    # 登录所有测试账号
    tokens = {}
    print("📝 步骤 1: 登录测试账号")
    print("-" * 80)
    for role_key, user_info in TEST_USERS.items():
        username = user_info["username"]
        password = user_info["password"]
        role_name = user_info["role"]
        
        token = login(username, password)
        if token:
            tokens[role_key] = token
            print(f"✅ {role_name:12s} ({username:12s}) - 登录成功")
        else:
            print(f"❌ {role_name:12s} ({username:12s}) - 登录失败")
    
    print()
    
    if not tokens:
        print("❌ 没有成功登录的账号，无法继续测试")
        print()
        print("💡 提示：请先在数据库中创建测试账号，或使用以下SQL:")
        print()
        print("-- 创建测试用户（需要先hash密码）")
        print("INSERT INTO users (username, password_hash, real_name, is_active) VALUES")
        print("  ('admin', '<hash>', '系统管理员', 1),")
        print("  ('pm001', '<hash>', '项目经理张三', 1),")
        print("  ('sales001', '<hash>', '销售李四', 1),")
        print("  ('eng001', '<hash>', '工程师王五', 1);")
        print()
        print("-- 分配角色")
        print("INSERT INTO user_roles (user_id, role_id) VALUES")
        print("  ((SELECT id FROM users WHERE username='admin'), (SELECT id FROM roles WHERE role_code='ADMIN')),")
        print("  ((SELECT id FROM users WHERE username='pm001'), (SELECT id FROM roles WHERE role_code='PM')),")
        print("  ((SELECT id FROM users WHERE username='sales001'), (SELECT id FROM roles WHERE role_code='SA')),")
        print("  ((SELECT id FROM users WHERE username='eng001'), (SELECT id FROM roles WHERE role_code='ME'));")
        return
    
    # 测试各个端点
    print("📊 步骤 2: 测试API端点权限")
    print("-" * 80)
    
    # 表头
    header = f"{'端点':<25s}"
    for role_key in tokens.keys():
        role_name = TEST_USERS[role_key]["role"]
        header += f" {role_name[:10]:^15s}"
    print(header)
    print("-" * 80)
    
    # 测试每个端点
    for endpoint in TEST_ENDPOINTS:
        name = endpoint["name"]
        row = f"{name:<25s}"
        
        for role_key, token in tokens.items():
            role_name = TEST_USERS[role_key]["role"]
            result = test_endpoint(endpoint, token, role_name)
            row += f" {result:^15s}"
        
        print(row)
    
    print("=" * 80)
    print()
    print("📖 图例:")
    print("  ✅ 200    - 有权限，访问成功")
    print("  🚫 403    - 无权限，被拒绝")
    print("  🔒 401    - 未认证或token失效")
    print("  ❓ 404    - API端点不存在")
    print("  ⏱️  超时   - 请求超时")
    print()


if __name__ == "__main__":
    main()
