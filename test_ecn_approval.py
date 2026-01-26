#!/usr/bin/env python3
"""
ECN审批流程和委托审批功能测试脚本
Phase 1 Migration Test Script

测试范围：
1. ECN审批提交
2. 审批通过
3. 审批驳回
4. 审批委托（新增功能）
5. 审批撤回
6. 审批历史查询
"""

import requests
import json
from datetime import datetime
from typing import Any

# API配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
API_BASE = f"{BASE_URL}/approvals"

# 测试配置（使用mock数据）
TEST_CONFIG = {
    "ecn_id": 1,  # 假设ECN ID为1
    "submitter": {"id": 1, "name": "测试用户1"},
    "approver1": {"id": 2, "name": "测试经理"},
    "approver2": {"id": 3, "name": "测试总监"},
    "delegate_to": {"id": 4, "name": "被委托人"},
}

# 测试结果记录
test_results = []


def log_test(test_name: str, status: str, details: str, data: Any = None):
    """记录测试结果"""
    test_results.append(
        {
            "test_name": test_name,
            "status": status,  # PASS, FAIL, SKIP
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
    )

    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"\n{status_symbol} {test_name}")
    print(f"  状态: {status}")
    print(f"  详情: {details}")


def test_health_check():
    """测试1：健康检查"""
    try:
        response = requests.get(
            f"{BASE_URL.replace('/api/v1/approvals', '')}/health", timeout=5
        )
        if response.status_code == 200:
            log_test("健康检查", "PASS", f"服务器运行正常，响应: {response.json()}")
            return True
        else:
            log_test("健康检查", "FAIL", f"服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        log_test("健康检查", "FAIL", f"连接失败: {str(e)}")
        return False


def test_submit_ecn_approval():
    """测试2：提交ECN审批"""
    try:
        payload = {
            "entity_type": "ECN",
            "entity_id": TEST_CONFIG["ecn_id"],
            "title": f"ECN审批测试 - {datetime.now().strftime('%H:%M:%S')}",
            "summary": "自动化测试：验证ECN审批提交功能",
            "urgency": "NORMAL",
            "cc_user_ids": [],
        }

        response = requests.post(f"{API_BASE}/submit", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                instance_id = data.get("data", {}).get("instance_id")
                log_test(
                    "提交ECN审批",
                    "PASS",
                    f"审批实例创建成功，ID: {instance_id}",
                    data=data,
                )
                return instance_id
            else:
                log_test(
                    "提交ECN审批",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return None
        else:
            log_test(
                "提交ECN审批",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return None

    except Exception as e:
        log_test("提交ECN审批", "FAIL", f"请求失败: {str(e)}")
        return None


def test_approve_approval(instance_id: int):
    """测试3：通过审批"""
    if not instance_id:
        log_test("通过审批", "SKIP", "缺少审批实例ID")
        return False

    try:
        payload = {"decision": "APPROVE", "comment": "自动化测试：批准此ECN变更"}

        response = requests.post(
            f"{API_BASE}/{instance_id}/approve", json=payload, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                log_test("通过审批", "PASS", "审批已批准", data=data)
                return True
            else:
                log_test(
                    "通过审批",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return False
        else:
            log_test(
                "通过审批",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return False

    except Exception as e:
        log_test("通过审批", "FAIL", f"请求失败: {str(e)}")
        return False


def test_reject_approval(instance_id: int):
    """测试4：驳回审批"""
    # 需要先创建一个新的审批实例
    try:
        # 创建新实例用于驳回测试
        instance_id = test_submit_ecn_approval()
        if not instance_id:
            log_test("驳回审批", "SKIP", "无法创建审批实例")
            return False

        payload = {
            "decision": "REJECT",
            "comment": "自动化测试：驳回此ECN变更，原因：需要补充更多信息",
        }

        response = requests.post(f"{API_BASE}/submit", json=payload, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                log_test("驳回审批", "PASS", "审批已驳回", data=data)
                return True
            else:
                log_test(
                    "驳回审批",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return False
        else:
            log_test(
                "驳回审批",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return False

    except Exception as e:
        log_test("驳回审批", "FAIL", f"请求失败: {str(e)}")
        return False


def test_delegate_approval(instance_id: int):
    """测试5：委托审批（新功能）"""
    if not instance_id:
        log_test("委托审批", "SKIP", "缺少审批实例ID")
        return False

    try:
        payload = {
            "decision": "DELEGATE",
            "delegate_to_id": TEST_CONFIG["delegate_to"]["id"],
            "comment": f"自动化测试：委托给 {TEST_CONFIG['delegate_to']['name']}",
        }

        response = requests.post(
            f"{API_BASE}/{instance_id}/delegate", json=payload, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                log_test(
                    "委托审批",
                    "PASS",
                    f"审批已委托给 {TEST_CONFIG['delegate_to']['name']}",
                    data=data,
                )
                return True
            else:
                log_test(
                    "委托审批",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return False
        else:
            log_test(
                "委托审批",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return False

    except Exception as e:
        log_test("委托审批", "FAIL", f"请求失败: {str(e)}")
        return False


def test_withdraw_approval(instance_id: int):
    """测试6：撤回审批"""
    if not instance_id:
        log_test("撤回审批", "SKIP", "缺少审批实例ID")
        return False

    try:
        payload = {"decision": "WITHDRAW", "comment": "自动化测试：撤回审批"}

        response = requests.post(
            f"{API_BASE}/{instance_id}/withdraw", json=payload, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                log_test("撤回审批", "PASS", "审批已撤回", data=data)
                return True
            else:
                log_test(
                    "撤回审批",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return False
        else:
            log_test(
                "撤回审批",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return False

    except Exception as e:
        log_test("撤回审批", "FAIL", f"请求失败: {str(e)}")
        return False


def test_get_approval_history(instance_id: int):
    """测试7：查询审批历史"""
    if not instance_id:
        log_test("查询审批历史", "SKIP", "缺少审批实例ID")
        return None

    try:
        response = requests.get(f"{API_BASE}/{instance_id}/history", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                history = data.get("data", {}).get("history", [])
                log_test(
                    "查询审批历史",
                    "PASS",
                    f"查询到 {len(history)} 条历史记录",
                    data=data,
                )
                return history
            else:
                log_test(
                    "查询审批历史",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return None
        else:
            log_test(
                "查询审批历史",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return None

    except Exception as e:
        log_test("查询审批历史", "FAIL", f"请求失败: {str(e)}")
        return None


def test_get_approval_detail(instance_id: int):
    """测试8：查询审批详情"""
    if not instance_id:
        log_test("查询审批详情", "SKIP", "缺少审批实例ID")
        return None

    try:
        response = requests.get(f"{API_BASE}/{instance_id}/detail", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                log_test("查询审批详情", "PASS", "查询成功", data=data)
                return data.get("data")
            else:
                log_test(
                    "查询审批详情",
                    "FAIL",
                    f"API返回错误: {data.get('message', 'Unknown error')}",
                    data=data,
                )
                return None
        else:
            log_test(
                "查询审批详情",
                "FAIL",
                f"HTTP错误: {response.status_code}",
                data=response.text,
            )
            return None

    except Exception as e:
        log_test("查询审批详情", "FAIL", f"请求失败: {str(e)}")
        return None


def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 80)
    print("测试报告 - ECN审批流程和委托审批功能")
    print("=" * 80)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试总数: {len(test_results)}")

    # 统计结果
    passed = sum(1 for t in test_results if t["status"] == "PASS")
    failed = sum(1 for t in test_results if t["status"] == "FAIL")
    skipped = sum(1 for t in test_results if t["status"] == "SKIP")

    print(f"\n通过: {passed}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print(f"通过率: {passed / (len(test_results) - skipped) * 100:.1f}%")

    # 详细结果
    print("\n" + "=" * 80)
    print("详细测试结果:")
    print("=" * 80)

    for i, result in enumerate(test_results, 1):
        print(f"\n{i}. {result['test_name']}")
        print(f"   状态: {result['status']}")
        print(f"   详情: {result['details']}")
        if result.get("data"):
            print(
                f"   数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)[:200]}"
            )

    # 保存到文件
    report_file = (
        "/Users/flw/non-standard-automation-pm/docs/ecn_approval_test_report.json"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "test_time": datetime.now().isoformat(),
                "total_tests": len(test_results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": passed / (len(test_results) - skipped) * 100
                if (len(test_results) - skipped) > 0
                else 0,
                "results": test_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n\n✅ 测试报告已保存到: {report_file}")


def main():
    """主测试函数"""
    print("=" * 80)
    print("ECN审批流程和委托审批功能测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_BASE}")
    print("=" * 80)

    # 测试实例ID
    instance_id = None

    # 执行测试
    # 测试1: 健康检查
    if not test_health_check():
        print("\n❌ 服务器未运行，测试终止")
        return

    # 测试2: 提交ECN审批
    instance_id = test_submit_ecn_approval()

    # 测试3: 查询审批历史（查询但不使用）
    _ = test_get_approval_history(instance_id)

    # 测试4: 查询审批详情（查询但不使用）
    _ = test_get_approval_detail(instance_id)

    # 测试5: 委托审批（新功能）
    delegate_result = test_delegate_approval(instance_id)

    # 测试6: 撤回审批
    withdraw_result = test_withdraw_approval(instance_id)

    # 测试7: 驳回审批（需要新实例）
    reject_result = test_reject_approval(instance_id)

    # 测试8: 通过审批（需要新实例）
    approve_result = test_approve_approval(instance_id)

    # 生成测试报告
    generate_test_report()

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
