#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整服务API测试脚本
测试所有服务相关API：工单、记录、沟通、满意度、知识库
"""

import json
import sys
from typing import Optional

import requests

if "pytest" in sys.modules:
    import pytest

    pytest.skip("Manual API script; run with `python3 tests/test_all_service_apis.py`", allow_module_level=True)

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
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return None

        if response.status_code >= 200 and response.status_code < 300:
            print_success(f"成功 (HTTP {response.status_code})")
            try:
                result = response.json()
                if isinstance(result, dict) and len(str(result)) < 500:
                    print("响应:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    print(f"响应: {type(result).__name__} (数据已返回)")
                return result
            except:
                print(f"响应: {response.text[:200]}")
                return response.text
        else:
            print_error(f"失败 (HTTP {response.status_code})")
            print(f"响应: {response.text[:200]}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"请求异常: {str(e)}")
        return None

def main():
    """主测试流程"""
    print("=" * 60)
    print_info("完整服务API测试")
    print("=" * 60)

    # 获取Token
    token = get_token()
    if not token:
        print_error("无法获取Token，请检查服务器和登录信息")
        sys.exit(1)
    print_success("登录成功")

    # ==================== 服务工单API ====================
    print()
    print("=" * 60)
    print_info("1. 服务工单API测试")
    print("=" * 60)

    test_api("GET", "/service/service-tickets?page=1&page_size=5", token,
             description="获取服务工单列表")
    test_api("GET", "/service/service-tickets/statistics", token,
             description="获取服务工单统计")

    # ==================== 现场服务记录API ====================
    print()
    print("=" * 60)
    print_info("2. 现场服务记录API测试")
    print("=" * 60)

    test_api("GET", "/service/service-records?page=1&page_size=5", token,
             description="获取服务记录列表")
    test_api("GET", "/service/service-records/statistics", token,
             description="获取服务记录统计")

    # ==================== 客户沟通API ====================
    print()
    print("=" * 60)
    print_info("3. 客户沟通API测试")
    print("=" * 60)

    test_api("GET", "/service/customer-communications?page=1&page_size=5", token,
             description="获取客户沟通记录列表")
    test_api("GET", "/service/customer-communications/statistics", token,
             description="获取客户沟通统计")

    # 创建沟通记录
    comm_data = {
        "communication_type": "PHONE",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "topic": "技术支持",
        "subject": "测试沟通主题",
        "content": "这是一条测试沟通记录",
        "communication_date": "2026-01-06",
        "importance": "中"
    }
    comm_result = test_api("POST", "/service/customer-communications", token, comm_data,
                          description="创建客户沟通记录")

    comm_id = None
    if comm_result and isinstance(comm_result, dict) and "id" in comm_result:
        comm_id = comm_result["id"]
        test_api("GET", f"/service/customer-communications/{comm_id}", token,
                description="获取客户沟通记录详情")

    # ==================== 满意度调查API ====================
    print()
    print("=" * 60)
    print_info("4. 满意度调查API测试")
    print("=" * 60)

    test_api("GET", "/service/customer-satisfactions?page=1&page_size=5", token,
             description="获取满意度调查列表")
    test_api("GET", "/service/customer-satisfactions/statistics", token,
             description="获取满意度调查统计")

    # 创建满意度调查
    survey_data = {
        "survey_type": "PROJECT",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "survey_date": "2026-01-06",
        "send_method": "EMAIL"
    }
    survey_result = test_api("POST", "/service/customer-satisfactions", token, survey_data,
                            description="创建满意度调查")

    survey_id = None
    if survey_result and isinstance(survey_result, dict) and "id" in survey_result:
        survey_id = survey_result["id"]
        test_api("GET", f"/service/customer-satisfactions/{survey_id}", token,
                description="获取满意度调查详情")

        # 发送调查
        test_api("POST", f"/service/customer-satisfactions/{survey_id}/send", token,
                description="发送满意度调查")

    # ==================== 知识库API ====================
    print()
    print("=" * 60)
    print_info("5. 知识库API测试")
    print("=" * 60)

    test_api("GET", "/service/knowledge-base?page=1&page_size=5", token,
             description="获取知识库文章列表")
    test_api("GET", "/service/knowledge-base/statistics", token,
             description="获取知识库统计")

    # 创建知识库文章
    article_data = {
        "title": "测试文章标题",
        "category": "故障处理",
        "content": "这是测试文章内容",
        "tags": ["测试", "FAQ"],
        "is_faq": True,
        "status": "已发布"
    }
    article_result = test_api("POST", "/service/knowledge-base", token, article_data,
                            description="创建知识库文章")

    article_id = None
    if article_result and isinstance(article_result, dict) and "id" in article_result:
        article_id = article_result["id"]
        test_api("GET", f"/service/knowledge-base/{article_id}", token,
                description="获取知识库文章详情（会增加浏览量）")

        # 点赞
        test_api("POST", f"/service/knowledge-base/{article_id}/like", token,
                description="点赞知识库文章")

        # 标记有用
        test_api("POST", f"/service/knowledge-base/{article_id}/helpful", token,
                description="标记知识库文章为有用")

    print()
    print("=" * 60)
    print_success("所有API测试完成！")
    print("=" * 60)
    print()
    print_info("提示：")
    print("1. 可以访问 http://127.0.0.1:8000/docs 查看完整的API文档")
    print("2. 在Swagger UI中可以直接测试所有API")
    print("3. 部分创建功能需要数据库中有对应的关联数据")

if __name__ == "__main__":
    main()


