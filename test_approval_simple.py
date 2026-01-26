#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 ECN 审批测试脚本
测试 Phase 1 核心功能
"""

import sys
import os
import json

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


def print_result(test_name, response):
    """打印测试结果"""
    print(f"\n{'=' * 60}")
    print(f"测试: {test_name}")
    print(f"{'=' * 60}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"响应: {response.text}")


def test_health():
    """测试服务器健康状态"""
    response = requests.get("http://127.0.0.1:8000/health", timeout=10)
    print_result("服务器健康检查", response)
    return response.status_code == 200


def test_approval_endpoints():
    """测试所有审批端点是否可用"""
    endpoints = [
        ("POST", "/approvals/instances/submit"),
        ("POST", "/approvals/tasks/{task_id}/approve"),
        ("POST", "/approvals/tasks/{task_id}/reject"),
        ("POST", "/approvals/instances/{instance_id}/delegate"),  # Phase 1 新增
        ("GET", "/approvals/pending/my-tasks"),
        ("GET", "/approvals/instances/{instance_id}/detail"),
        ("GET", "/approvals/instances/{instance_id}/history"),
        ("GET", "/approvals/templates"),
    ]

    print(f"\n{'=' * 60}")
    print("检查所有审批端点")
    print(f"{'=' * 60}")

    for method, path in endpoints:
        # Check if route exists by trying OPTIONS
        try:
            response = requests.options(f"{API_BASE_URL}{path}", timeout=5)
            status = "✅" if response.status_code in [200, 405] else "❌"
            print(f"{status} {method:6s} {path}")
        except Exception as e:
            print(f"❌ {method:6s} {path} - {e}")


def test_submit_approval():
    """测试提交审批"""
    print(f"\n{'=' * 60}")
    print("测试: 提交 ECN 审批")
    print(f"{'=' * 60}")

    payload = {
        "entity_type": "ECN",
        "entity_id": 1,  # 测试 ECN ID
    }

    print(f"请求体: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            f"{API_BASE_URL}/approvals/instances/submit", json=payload, timeout=30
        )
        print_result("提交审批", response)

        if response.status_code == 200:
            data = response.json()
            # 提交审批返回的是 instance，不是 task
            instance_id = data.get("id")
            print("\n✅ 审批实例创建成功！")
            print(f"   实例 ID: {instance_id}")
            print(f"   状态: {data.get('status')}")
            return instance_id
        else:
            print("\n❌ 提交审批失败")
            return None
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时（30秒）")
        print("提示: 可能需要增加超时时间或检查网络连接")
        return None
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None


def test_query_approval_instance(approval_id):
    """查询审批实例详情"""
    if not approval_id:
        print("\n⚠️ 跳过查询审批实例（没有审批ID）")
        return

    try:
        response = requests.get(
            f"{API_BASE_URL}/approvals/{approval_id}/detail", timeout=30
        )
        print_result("查询审批详情", response)
    except Exception as e:
        print(f"\n❌ 查询异常: {e}")


def test_query_approval_history(approval_id):
    """查询审批历史"""
    if not approval_id:
        print("\n⚠️ 跳过查询审批历史（没有审批ID）")
        return

    try:
        response = requests.get(
            f"{API_BASE_URL}/approvals/{approval_id}/history", timeout=30
        )
        print_result("查询审批历史", response)
    except Exception as e:
        print(f"\n❌ 查询异常: {e}")


def test_query_my_tasks():
    """查询我的待办任务"""
    try:
        response = requests.get(f"{API_BASE_URL}/approvals/my-tasks", timeout=30)
        print_result("查询待办任务", response)
    except Exception as e:
        print(f"\n❌ 查询异常: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 ECN 审批功能测试")
    print("=" * 60)

    # 1. 健康检查
    if not test_health():
        print("\n❌ 服务器未就绪，终止测试")
        sys.exit(1)

    # 2. 检查端点
    test_approval_endpoints()

    # 3. 提交审批
    instance_id = test_submit_approval()

    # 4. 查询审批实例
    test_query_approval_instance(instance_id)

    # 5. 查询审批历史
    test_query_approval_history(instance_id)

    # 6. 查询待办任务
    test_query_my_tasks()

    print(f"\n{'=' * 60}")
    print("测试完成")
    print(f"{'=' * 60}")
    print("\n📝 下一步测试建议:")
    if instance_id:
        print(f"1. 查询审批任务: GET /approvals/instances/{instance_id}/detail")
        print("2. 查询待办任务: GET /approvals/pending/my-tasks")
        print("3. 测试任务审批: POST /approvals/tasks/{task_id}/approve")
        print("4. 测试任务拒绝: POST /approvals/tasks/{task_id}/reject")
        print(f"5. 测试委托审批: POST /approvals/instances/{instance_id}/delegate")
    else:
        print("审批实例创建失败，请检查错误日志")
