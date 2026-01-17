#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务工单API测试脚本（带数据检查）
先检查数据库中是否有项目、客户和用户数据，如果没有则提示
"""

import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual live-HTTP script (not a pytest test module)",
        allow_module_level=True,
    )

import json
from typing import Optional

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    NC = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

def get_token():
    """获取Token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except:
        pass
    return None

def check_data(token: str):
    """检查数据库中是否有必要的数据"""
    print()
    print("=" * 60)
    print_info("检查数据库数据")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    # 检查项目
    try:
        response = requests.get(f"{BASE_URL}/projects?page=1&page_size=1", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("total", 0) > 0:
                project = data.get("items", [{}])[0]
                print_success(f"找到项目: {project.get('project_name', 'N/A')} (ID: {project.get('id', 'N/A')})")
                return project.get("id"), None, None
            else:
                print_warning("数据库中没有项目数据")
        else:
            print_warning("无法获取项目列表")
    except Exception as e:
        print_warning(f"检查项目时出错: {e}")

    # 检查客户
    try:
        response = requests.get(f"{BASE_URL}/customers?page=1&page_size=1", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("total", 0) > 0:
                customer = data.get("items", [{}])[0]
                print_success(f"找到客户: {customer.get('customer_name', 'N/A')} (ID: {customer.get('id', 'N/A')})")
                return None, customer.get("id"), None
            else:
                print_warning("数据库中没有客户数据")
        else:
            print_warning("无法获取客户列表")
    except Exception as e:
        print_warning(f"检查客户时出错: {e}")

    # 检查用户
    try:
        response = requests.get(f"{BASE_URL}/users?page=1&page_size=1", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("total", 0) > 0:
                user = data.get("items", [{}])[0]
                print_success(f"找到用户: {user.get('name', user.get('username', 'N/A'))} (ID: {user.get('id', 'N/A')})")
                return None, None, user.get("id")
            else:
                print_warning("数据库中没有用户数据")
        else:
            print_warning("无法获取用户列表")
    except Exception as e:
        print_warning(f"检查用户时出错: {e}")

    return None, None, None

def test_api(method: str, endpoint: str, token: str, data: Optional[dict] = None, description: str = ""):
    """测试API"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    print()
    print("=" * 60)
    print_info(f"测试: {description}")
    print(f"请求: {method} {url}")
    if data:
        print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return None

        if response.status_code >= 200 and response.status_code < 300:
            print_success(f"成功 (HTTP {response.status_code})")
            try:
                result = response.json()
                print("响应:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
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

def main():
    """主测试流程"""
    print("=" * 60)
    print_info("服务工单API测试（带数据检查）")
    print("=" * 60)

    # 获取Token
    token = get_token()
    if not token:
        print_error("无法获取Token，请检查服务器和登录信息")
        sys.exit(1)
    print_success("登录成功")

    # 检查数据
    project_id, customer_id, user_id = check_data(token)

    # 如果数据不存在，提示用户
    if not project_id or not customer_id or not user_id:
        print()
        print_warning("数据库中没有足够的数据进行完整测试")
        print_warning("建议：")
        print("1. 先创建项目数据")
        print("2. 先创建客户数据")
        print("3. 确保有用户数据")
        print()
        print_info("继续测试基础API（不创建数据）...")

    # 测试基础API（不需要数据）
    print()
    print("=" * 60)
    print_info("测试基础API")
    print("=" * 60)

    # 获取服务工单列表
    test_api("GET", "/service/service-tickets?page=1&page_size=10", token,
             description="获取服务工单列表")

    # 获取服务工单统计
    test_api("GET", "/service/service-tickets/statistics", token,
             description="获取服务工单统计")

    # 获取服务记录列表
    test_api("GET", "/service/service-records?page=1&page_size=10", token,
             description="获取服务记录列表")

    # 获取服务记录统计
    test_api("GET", "/service/service-records/statistics", token,
             description="获取服务记录统计")

    # 如果有数据，测试创建功能
    if project_id and customer_id and user_id:
        print()
        print("=" * 60)
        print_info("测试创建功能（使用找到的数据）")
        print("=" * 60)

        # 创建服务工单
        ticket_data = {
            "project_id": project_id,
            "customer_id": customer_id,
            "problem_type": "SOFTWARE",
            "problem_desc": "测试问题描述",
            "urgency": "MEDIUM",
            "reported_by": "测试用户",
            "reported_time": "2026-01-06T10:00:00"
        }
        ticket_result = test_api("POST", "/service/service-tickets", token, ticket_data,
                                description="创建服务工单")

        ticket_id = None
        if ticket_result and isinstance(ticket_result, dict) and "id" in ticket_result:
            ticket_id = ticket_result["id"]
            print_success(f"创建的服务工单ID: {ticket_id}")

            # 获取详情
            test_api("GET", f"/service/service-tickets/{ticket_id}", token,
                    description="获取服务工单详情")

        # 创建服务记录
        record_data = {
            "service_type": "INSTALLATION",
            "project_id": project_id,
            "customer_id": customer_id,
            "service_date": "2026-01-06",
            "service_engineer_id": user_id,
            "service_content": "测试服务内容"
        }
        record_result = test_api("POST", "/service/service-records", token, record_data,
                               description="创建服务记录")

        record_id = None
        if record_result and isinstance(record_result, dict) and "id" in record_result:
            record_id = record_result["id"]
            print_success(f"创建的服务记录ID: {record_id}")

            # 获取详情
            test_api("GET", f"/service/service-records/{record_id}", token,
                    description="获取服务记录详情")

    print()
    print("=" * 60)
    print_success("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()


