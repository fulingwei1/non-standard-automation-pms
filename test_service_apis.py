#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务工单API测试脚本
测试服务工单、现场服务记录等API
"""

import requests
import json
import sys
from typing import Optional

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

def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=2)
        if response.status_code == 200:
            print_success("服务器运行正常")
            return True
    except requests.exceptions.RequestException:
        pass
    print_error("服务器未运行，请先启动服务器：uvicorn app.main:app --reload")
    return False

def test_api(method: str, endpoint: str, token: Optional[str] = None,
              data: Optional[dict] = None, description: str = ""):
    """测试API"""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
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
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
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

def test_login(username: str = USERNAME, password: str = PASSWORD):
    """测试登录"""
    print()
    print("=" * 60)
    print_info("测试登录")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            if token:
                print_success("登录成功")
                print(f"Token: {token[:50]}...")
                return token
            else:
                print_error("登录响应中没有Token")
                return None
        else:
            print_error(f"登录失败 (HTTP {response.status_code})")
            print(f"响应: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"登录请求异常: {str(e)}")
        return None

def main():
    """主测试流程"""
    print("=" * 60)
    print_info("服务工单API测试")
    print("=" * 60)
    
    # 检查服务器
    if not check_server():
        sys.exit(1)
    
    # 登录获取Token
    token = test_login()
    if not token:
        print_error("无法获取Token，测试终止")
        sys.exit(1)
    
    # 测试服务工单API
    print()
    print("=" * 60)
    print_info("开始测试服务工单API")
    print("=" * 60)
    
    # 1. 获取服务工单列表
    test_api("GET", "/service/service-tickets?page=1&page_size=10", token,
             description="获取服务工单列表")
    
    # 2. 获取服务工单统计
    test_api("GET", "/service/service-tickets/statistics", token,
             description="获取服务工单统计")
    
    # 3. 创建服务工单
    ticket_data = {
        "project_id": 1,
        "customer_id": 1,
        "problem_type": "SOFTWARE",
        "problem_desc": "设备控制软件频繁崩溃，导致测试中断。",
        "urgency": "URGENT",
        "reported_by": "测试用户",
        "reported_time": "2026-01-06T10:00:00"
    }
    ticket_result = test_api("POST", "/service/service-tickets", token, ticket_data,
                            description="创建服务工单")
    
    ticket_id = None
    if ticket_result and isinstance(ticket_result, dict) and "id" in ticket_result:
        ticket_id = ticket_result["id"]
        print_success(f"创建的服务工单ID: {ticket_id}")
    
    # 4. 获取服务工单详情
    if ticket_id:
        test_api("GET", f"/service/service-tickets/{ticket_id}", token,
                description="获取服务工单详情")
    
    # 5. 分配服务工单
    if ticket_id:
        assign_data = {
            "assignee_id": 1
        }
        test_api("PUT", f"/service/service-tickets/{ticket_id}/assign", token, assign_data,
                description="分配服务工单")
    
    # 6. 关闭服务工单
    if ticket_id:
        close_data = {
            "solution": "重新安装软件并更新到最新版本",
            "root_cause": "软件版本过旧，存在已知bug",
            "preventive_action": "定期更新软件版本",
            "satisfaction": 4,
            "feedback": "处理及时，问题已解决"
        }
        test_api("PUT", f"/service/service-tickets/{ticket_id}/close", token, close_data,
                description="关闭服务工单")
    
    # 测试现场服务记录API
    print()
    print("=" * 60)
    print_info("开始测试现场服务记录API")
    print("=" * 60)
    
    # 1. 获取服务记录列表
    test_api("GET", "/service/service-records?page=1&page_size=10", token,
             description="获取服务记录列表")
    
    # 2. 获取服务记录统计
    test_api("GET", "/service/service-records/statistics", token,
             description="获取服务记录统计")
    
    # 3. 创建服务记录
    record_data = {
        "service_type": "INSTALLATION",
        "project_id": 1,
        "machine_no": "TEST-001",
        "customer_id": 1,
        "location": "测试地点",
        "service_date": "2026-01-06",
        "start_time": "09:00",
        "end_time": "17:00",
        "duration_hours": 8.0,
        "service_engineer_id": 1,
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "service_content": "完成设备安装、接线和初步调试",
        "service_result": "设备已成功安装，待进行功能测试",
        "status": "COMPLETED"
    }
    record_result = test_api("POST", "/service/service-records", token, record_data,
                            description="创建服务记录")
    
    record_id = None
    if record_result and isinstance(record_result, dict) and "id" in record_result:
        record_id = record_result["id"]
        print_success(f"创建的服务记录ID: {record_id}")
    
    # 4. 获取服务记录详情
    if record_id:
        test_api("GET", f"/service/service-records/{record_id}", token,
                description="获取服务记录详情")
    
    print()
    print("=" * 60)
    print_success("测试完成！")
    print("=" * 60)
    print()
    print_info("提示：")
    print("1. 如果某些测试失败，可能是因为数据库中没有对应的项目或客户数据")
    print("2. 可以访问 http://127.0.0.1:8000/docs 查看完整的API文档")
    print("3. 确保数据库已初始化，运行 python3 init_db.py")

if __name__ == "__main__":
    main()



