#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术评估系统 API 测试脚本
使用方法: python3 test_technical_assessment.py
"""

import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual live-HTTP script (not a pytest test module)",
        allow_module_level=True,
    )

import json
from datetime import datetime
from typing import Optional

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"


class Colors:
    """终端颜色"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
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


def print_info(msg: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")


def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if response.status_code == 200:
            print_success("服务器运行正常")
            return True
    except requests.exceptions.RequestException:
        print_error("服务器未运行！")
        print("   请先启动服务器：")
        print("   uvicorn app.main:app --reload")
        return False


def login(username: str = "admin", password: str = "admin123") -> Optional[str]:
    """登录获取token"""
    try:
        # 使用 form data 格式（OAuth2PasswordRequestForm）
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success(f"登录成功: {username}")
                return token
        print_error(f"登录失败: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print_error(f"登录异常: {e}")
        return None


def test_api(method: str, endpoint: str, token: Optional[str] = None,
              data: Optional[dict] = None, description: str = ""):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"请求: {method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return None

        if response.status_code >= 200 and response.status_code < 300:
            print_success(f"成功 (HTTP {response.status_code})")
            try:
                result = response.json()
                if isinstance(result, dict):
                    if "items" in result:
                        print(f"返回 {len(result.get('items', []))} 条记录，共 {result.get('total', 0)} 条")
                    elif "id" in result:
                        print(f"ID: {result.get('id')}")
                    elif "message" in result:
                        print(f"消息: {result.get('message')}")
                return result
            except:
                print(f"响应: {response.text[:500]}")
                return {"text": response.text}
        else:
            print_error(f"失败 (HTTP {response.status_code})")
            print(f"错误: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"请求异常: {e}")
        return None


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("技术评估系统 API 测试")
    print("="*60)

    # 检查服务器
    if not check_server():
        return

    # 登录
    token = login()
    if not token:
        print_warning("使用无token模式测试（部分API可能失败）")

    # 1. 测试评分规则管理
    print("\n" + "="*60)
    print("1. 评分规则管理")
    print("="*60)

    # 获取评分规则列表
    rules = test_api("GET", "/sales/scoring-rules", token, description="获取评分规则列表")

    # 如果没有规则，创建一个示例规则
    if not rules or len(rules) == 0:
        print_info("创建示例评分规则...")
        sample_rule = {
            "version": "2.0",
            "rules_json": json.dumps({
                "version": "2.0",
                "scales": {
                    "total_score_max": 100,
                    "decision_thresholds": [
                        {"min_score": 75, "decision": "推荐立项"},
                        {"min_score": 60, "decision": "有条件立项"},
                        {"min_score": 45, "decision": "暂缓"},
                        {"min_score": 0, "decision": "不建议立项"}
                    ]
                },
                "evaluation_criteria": {
                    "customer_nature": {
                        "name": "客户性质",
                        "field": "customerType",
                        "max_points": 10,
                        "options": [
                            {"value": "老客户成交", "points": 10},
                            {"value": "新客户", "points": 6}
                        ]
                    }
                }
            }, ensure_ascii=False),
            "description": "示例评分规则"
        }
        rule_result = test_api("POST", "/sales/scoring-rules", token, sample_rule, "创建评分规则")
        if rule_result:
            rule_id = rule_result.get("id")
            if rule_id:
                test_api("PUT", f"/sales/scoring-rules/{rule_id}/activate", token, None, "激活评分规则")

    # 2. 测试失败案例库
    print("\n" + "="*60)
    print("2. 失败案例库")
    print("="*60)

    test_api("GET", "/sales/failure-cases", token, {"page": 1, "page_size": 10}, "获取失败案例列表")

    # 创建示例失败案例
    sample_case = {
        "case_code": "FC-20260117-001",
        "project_name": "示例失败项目",
        "industry": "新能源",
        "failure_tags": json.dumps(["需求不明确", "预算不足"]),
        "core_failure_reason": "客户需求频繁变更，导致项目延期",
        "early_warning_signals": json.dumps(["需求文档不完整", "决策链不清晰"]),
        "lesson_learned": "需要在项目前期充分沟通需求，确保需求冻结",
        "keywords": json.dumps(["需求变更", "延期"])
    }
    test_api("POST", "/sales/failure-cases", token, sample_case, "创建失败案例")

    # 3. 测试线索技术评估
    print("\n" + "="*60)
    print("3. 线索技术评估")
    print("="*60)

    # 先获取一个线索
    leads = test_api("GET", "/sales/leads", token, {"page": 1, "page_size": 1}, "获取线索列表")
    lead_id = None
    if leads and "items" in leads and len(leads["items"]) > 0:
        lead_id = leads["items"][0].get("id")
        print_info(f"使用线索 ID: {lead_id}")

        # 申请技术评估
        assessment_result = test_api(
            "POST",
            f"/sales/leads/{lead_id}/assessments/apply",
            token,
            {},
            "申请技术评估（线索）"
        )

        if assessment_result:
            assessment_id = assessment_result.get("data", {}).get("assessment_id")
            if assessment_id:
                print_info(f"评估ID: {assessment_id}")

                # 获取评估列表
                test_api("GET", f"/sales/leads/{lead_id}/assessments", token, None, "获取线索的评估列表")

                # 执行评估（需要需求数据）
                requirement_data = {
                    "industry": "新能源",
                    "customerType": "新客户",
                    "budgetStatus": "明确",
                    "techRequirements": "电池测试设备",
                    "requirementMaturity": 3
                }
                test_api(
                    "POST",
                    f"/sales/assessments/{assessment_id}/evaluate",
                    token,
                    {
                        "requirement_data": requirement_data,
                        "enable_ai": False
                    },
                    "执行技术评估"
                )

                # 获取评估详情
                test_api("GET", f"/sales/assessments/{assessment_id}", token, None, "获取评估详情")
    else:
        print_warning("没有可用的线索，跳过线索评估测试")

    # 4. 测试未决事项
    print("\n" + "="*60)
    print("4. 未决事项管理")
    print("="*60)

    if lead_id:
        # 创建未决事项
        open_item = {
            "item_type": "INTERFACE",
            "description": "接口协议文档尚未提供",
            "responsible_party": "CUSTOMER",
            "due_date": "2026-02-01T00:00:00",
            "blocks_quotation": True
        }
        test_api(
            "POST",
            f"/sales/leads/{lead_id}/open-items",
            token,
            open_item,
            "创建未决事项（线索）"
        )

        # 获取未决事项列表
        test_api(
            "GET",
            "/sales/open-items",
            token,
            {
                "source_type": "LEAD",
                "source_id": lead_id,
                "page": 1,
                "page_size": 10
            },
            "获取未决事项列表"
        )

    # 5. 测试相似案例查找
    print("\n" + "="*60)
    print("5. 相似案例查找")
    print("="*60)

    test_api(
        "GET",
        "/sales/failure-cases/similar",
        token,
        {
            "industry": "新能源",
            "takt_time_s": 30
        },
        "查找相似失败案例"
    )

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
