#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销售模块 API 测试脚本
使用方法: python3 test_sales_apis.py
"""

import sys

# NOTE: This file is a manual script (uses live HTTP requests), not a pytest suite.
if "pytest" in sys.modules:
    import pytest

    pytest.skip("Manual API script; run with `python3 tests/test_sales_apis.py`", allow_module_level=True)

import json
from datetime import date, datetime
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
                # 只打印关键信息，避免输出过长
                if isinstance(result, dict):
                    if "items" in result:
                        print(f"返回 {len(result.get('items', []))} 条记录，共 {result.get('total', 0)} 条")
                    elif "id" in result:
                        print(f"ID: {result.get('id')}, 编码: {result.get('lead_code') or result.get('opp_code') or result.get('quote_code') or result.get('contract_code') or result.get('invoice_code', 'N/A')}")
                    else:
                        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                else:
                    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                return result
            except:
                print(f"响应: {response.text[:500]}")
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
    print(f"\n{'='*60}")
    print_info("开始登录测试")
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(url, data=data, headers=headers, timeout=5)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print_success(f"登录成功，用户: {username}")
            return token
        else:
            print_error(f"登录失败: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"登录请求异常: {str(e)}")
        return None


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("销售模块 API 测试")
    print("="*60)

    # 检查服务器
    if not check_server():
        return

    # 登录获取Token
    token = test_login()
    if not token:
        print_error("无法获取Token，测试终止")
        return

    # 存储测试过程中创建的ID
    test_data = {
        "lead_id": None,
        "opportunity_id": None,
        "quote_id": None,
        "contract_id": None,
        "invoice_id": None,
        "customer_id": None,
    }

    # ==================== 1. 线索管理测试 ====================
    print(f"\n{'='*60}")
    print_info("1. 线索管理测试")
    print("="*60)

    # 1.1 创建线索（自动生成编码）
    lead_data = {
        "customer_name": "测试客户A",
        "source": "展会",
        "industry": "电子制造",
        "contact_name": "张三",
        "contact_phone": "13800138000",
        "demand_summary": "需要自动化测试设备，节拍要求1秒/件",
        "status": "NEW"
    }
    result = test_api("POST", "/sales/leads", token, lead_data, "创建线索（自动生成编码）")
    if result and isinstance(result, dict):
        test_data["lead_id"] = result.get("id")

    # 1.2 获取线索列表
    test_api("GET", "/sales/leads", token, {"page": 1, "page_size": 10}, "获取线索列表")

    # 1.3 获取线索详情
    if test_data["lead_id"]:
        test_api("GET", f"/sales/leads/{test_data['lead_id']}", token, None, "获取线索详情")

    # ==================== 2. 商机管理测试 ====================
    print(f"\n{'='*60}")
    print_info("2. 商机管理测试")
    print("="*60)

    # 2.1 创建客户（如果不存在）
    print_info("检查测试客户是否存在...")
    customers_result = test_api("GET", "/customers", token, {"page": 1, "page_size": 10}, "获取客户列表")
    if customers_result and isinstance(customers_result, dict):
        items = customers_result.get("items", [])
        if items:
            test_data["customer_id"] = items[0].get("id")
            print_info(f"使用现有客户 ID: {test_data['customer_id']}")
        else:
            # 创建测试客户
            customer_data = {
                "customer_code": "C00001",
                "customer_name": "测试客户A",
                "industry": "电子制造",
                "contact_person": "张三",
                "contact_phone": "13800138000"
            }
            customer_result = test_api("POST", "/customers", token, customer_data, "创建测试客户")
            if customer_result and isinstance(customer_result, dict):
                test_data["customer_id"] = customer_result.get("id")

    # 2.2 创建商机（自动生成编码）
    if test_data["customer_id"]:
        opp_data = {
            "customer_id": test_data["customer_id"],
            "opp_name": "测试客户A - 自动化测试设备项目",
            "project_type": "单机",
            "equipment_type": "FCT",
            "stage": "DISCOVERY",
            "est_amount": 100000,
            "est_margin": 30,
            "budget_range": "80-120万",
            "requirement": {
                "product_object": "PCB板",
                "ct_seconds": 1,
                "interface_desc": "RS232/以太网",
                "acceptance_criteria": "节拍≤1秒，良率≥99.5%"
            }
        }
        result = test_api("POST", "/sales/opportunities", token, opp_data, "创建商机（自动生成编码）")
        if result and isinstance(result, dict):
            test_data["opportunity_id"] = result.get("id")

    # 2.3 获取商机列表
    test_api("GET", "/sales/opportunities", token, {"page": 1, "page_size": 10}, "获取商机列表")

    # 2.4 提交阶段门
    if test_data["opportunity_id"]:
        gate_data = {
            "gate_status": "PASS",
            "remark": "需求明确，预算充足，通过G1阶段门"
        }
        test_api("POST", f"/sales/opportunities/{test_data['opportunity_id']}/gate", token, gate_data, "提交阶段门（G1通过）")

    # ==================== 3. 报价管理测试 ====================
    print(f"\n{'='*60}")
    print_info("3. 报价管理测试")
    print("="*60)

    # 3.1 创建报价（自动生成编码）
    if test_data["opportunity_id"] and test_data["customer_id"]:
        quote_data = {
            "opportunity_id": test_data["opportunity_id"],
            "customer_id": test_data["customer_id"],
            "status": "DRAFT",
            "valid_until": str(date.today().replace(month=date.today().month + 1)),
            "version": {
                "version_no": "V1",
                "total_price": 100000,
                "cost_total": 70000,
                "gross_margin": 30,
                "lead_time_days": 90,
                "delivery_date": str(date.today().replace(month=date.today().month + 3)),
                "items": [
                    {
                        "item_type": "MODULE",
                        "item_name": "测试模块",
                        "qty": 1,
                        "unit_price": 50000,
                        "cost": 35000,
                        "lead_time_days": 60
                    },
                    {
                        "item_type": "LABOR",
                        "item_name": "设计工时",
                        "qty": 200,
                        "unit_price": 200,
                        "cost": 150,
                        "lead_time_days": 30
                    }
                ]
            }
        }
        result = test_api("POST", "/sales/quotes", token, quote_data, "创建报价（自动生成编码）")
        if result and isinstance(result, dict):
            test_data["quote_id"] = result.get("id")

    # 3.2 获取报价列表
    test_api("GET", "/sales/quotes", token, {"page": 1, "page_size": 10}, "获取报价列表")

    # 3.3 审批报价
    if test_data["quote_id"]:
        approve_data = {
            "approved": True,
            "remark": "报价合理，毛利率符合要求，审批通过"
        }
        test_api("POST", f"/sales/quotes/{test_data['quote_id']}/approve", token, approve_data, "审批报价")

    # ==================== 4. 合同管理测试 ====================
    print(f"\n{'='*60}")
    print_info("4. 合同管理测试")
    print("="*60)

    # 4.1 创建合同（自动生成编码）
    if test_data["opportunity_id"] and test_data["customer_id"]:
        contract_data = {
            "opportunity_id": test_data["opportunity_id"],
            "customer_id": test_data["customer_id"],
            "contract_amount": 100000,
            "status": "DRAFT",
            "payment_terms_summary": "预付款30%，发货款40%，验收款20%，质保款10%",
            "acceptance_summary": "节拍≤1秒，良率≥99.5%",
            "deliverables": [
                {
                    "deliverable_name": "FAT报告",
                    "deliverable_type": "验收报告",
                    "required_for_payment": True
                },
                {
                    "deliverable_name": "发货单",
                    "deliverable_type": "物流单据",
                    "required_for_payment": True
                }
            ]
        }
        result = test_api("POST", "/sales/contracts", token, contract_data, "创建合同（自动生成编码）")
        if result and isinstance(result, dict):
            test_data["contract_id"] = result.get("id")

    # 4.2 获取合同列表
    test_api("GET", "/sales/contracts", token, {"page": 1, "page_size": 10}, "获取合同列表")

    # 4.3 合同签订
    if test_data["contract_id"]:
        sign_data = {
            "signed_date": str(date.today()),
            "remark": "合同已签订"
        }
        test_api("POST", f"/sales/contracts/{test_data['contract_id']}/sign", token, sign_data, "合同签订")

    # ==================== 5. 发票管理测试 ====================
    print(f"\n{'='*60}")
    print_info("5. 发票管理测试")
    print("="*60)

    # 5.1 创建发票（自动生成编码）
    if test_data["contract_id"]:
        invoice_data = {
            "contract_id": test_data["contract_id"],
            "invoice_type": "SPECIAL",
            "amount": 30000,
            "tax_rate": 13,
            "status": "DRAFT",
            "buyer_name": "测试客户A",
            "buyer_tax_no": "91110000MA01234567"
        }
        result = test_api("POST", "/sales/invoices", token, invoice_data, "创建发票（自动生成编码）")
        if result and isinstance(result, dict):
            test_data["invoice_id"] = result.get("id")

    # 5.2 获取发票列表
    test_api("GET", "/sales/invoices", token, {"page": 1, "page_size": 10}, "获取发票列表")

    # 5.3 开票
    if test_data["invoice_id"]:
        issue_data = {
            "issue_date": str(date.today()),
            "remark": "发票已开具"
        }
        test_api("POST", f"/sales/invoices/{test_data['invoice_id']}/issue", token, issue_data, "开票")

    # ==================== 6. 统计报表测试 ====================
    print(f"\n{'='*60}")
    print_info("6. 统计报表测试")
    print("="*60)

    # 6.1 销售漏斗统计
    test_api("GET", "/sales/statistics/funnel", token, None, "销售漏斗统计")

    # 6.2 按阶段统计商机
    test_api("GET", "/sales/statistics/opportunities-by-stage", token, None, "按阶段统计商机")

    # 6.3 收入预测
    test_api("GET", "/sales/statistics/revenue-forecast", token, {"months": 3}, "收入预测（3个月）")

    # ==================== 测试总结 ====================
    print(f"\n{'='*60}")
    print_success("测试完成！")
    print("="*60)
    print("\n测试数据ID汇总：")
    for key, value in test_data.items():
        if value:
            print(f"  {key}: {value}")

    print("\n提示：")
    print("  - 可以通过 API 文档查看详细接口：http://127.0.0.1:8000/docs")
    print("  - 可以使用创建的ID进行更多测试")


if __name__ == "__main__":
    main()


