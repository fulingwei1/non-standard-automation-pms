#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECN变更管理模块API测试脚本
测试ECN基础管理、评估、审批、执行、受影响物料/订单、类型配置等API
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests

if "pytest" in sys.modules:
    import pytest

    pytest.skip("Manual API script; run with `python3 tests/test_ecn_apis.py`", allow_module_level=True)

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
                if isinstance(result, dict) and len(result) < 10:
                    print("响应:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
            except:
                print(f"响应: {response.text[:200]}")
                return response.text
        else:
            print_error(f"失败 (HTTP {response.status_code})")
            print(f"响应: {response.text[:500]}")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"请求异常: {str(e)}")
        return None

def test_login(username: str = USERNAME, password: str = PASSWORD):
    """测试登录"""
    print()
    print("=" * 60)
    print_info("测试登录")
    data = {
        "username": username,
        "password": password
    }
    result = test_api("POST", "/auth/login", data=data, description="用户登录")
    if result and "access_token" in result:
        return result["access_token"]
    return None

def test_ecn_basic_operations(token: str):
    """测试ECN基础操作"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN基础管理功能")
    print_info("=" * 80)

    # 1. 获取项目列表（用于创建ECN）
    print()
    projects_result = test_api("GET", "/projects?page_size=10", token=token, description="获取项目列表")
    project_id = None
    if projects_result and "items" in projects_result and len(projects_result["items"]) > 0:
        project_id = projects_result["items"][0]["id"]
        print_success(f"使用项目ID: {project_id}")
    else:
        print_warning("未找到项目，将使用project_id=1")
        project_id = 1

    # 2. 创建ECN
    print()
    ecn_data = {
        "ecn_title": f"测试ECN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "ecn_type": "DESIGN",
        "project_id": project_id,
        "priority": "MEDIUM",
        "urgency": "NORMAL",
        "change_reason": "测试变更原因",
        "change_description": "这是一个测试ECN，用于验证系统功能",
        "change_scope": "PARTIAL",
        "source_type": "MANUAL"
    }
    ecn_result = test_api("POST", "/ecns", token=token, data=ecn_data, description="创建ECN")
    if not ecn_result or "id" not in ecn_result:
        print_error("创建ECN失败，无法继续测试")
        return None
    ecn_id = ecn_result["id"]
    ecn_no = ecn_result.get("ecn_no", "")
    print_success(f"ECN创建成功: ID={ecn_id}, NO={ecn_no}")

    # 3. 获取ECN详情
    print()
    test_api("GET", f"/ecns/{ecn_id}", token=token, description="获取ECN详情")

    # 4. 更新ECN（草稿状态）
    print()
    update_data = {
        "ecn_title": f"更新后的ECN标题-{datetime.now().strftime('%H%M%S')}",
        "change_description": "更新后的变更描述"
    }
    test_api("PUT", f"/ecns/{ecn_id}", token=token, data=update_data, description="更新ECN")

    # 5. 获取ECN列表
    print()
    test_api("GET", "/ecns?page=1&page_size=10", token=token, description="获取ECN列表")

    return ecn_id, ecn_no

def test_affected_materials(token: str, ecn_id: int):
    """测试受影响物料管理"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试受影响物料管理功能")
    print_info("=" * 80)

    # 1. 获取物料列表（用于选择物料）
    print()
    materials_result = test_api("GET", "/materials/?page_size=5", token=token, description="获取物料列表")
    material_id = None
    material_code = "TEST-MAT-001"
    material_name = "测试物料"
    if materials_result and "items" in materials_result and len(materials_result["items"]) > 0:
        material_id = materials_result["items"][0]["id"]
        material_code = materials_result["items"][0].get("material_code", material_code)
        material_name = materials_result["items"][0].get("material_name", material_name)
        print_success(f"使用物料ID: {material_id}, 编码: {material_code}")

    # 2. 添加受影响物料
    print()
    material_data = {
        "material_id": material_id,
        "material_code": material_code,
        "material_name": material_name,
        "specification": "测试规格",
        "change_type": "UPDATE",
        "old_quantity": 10,
        "old_specification": "旧规格",
        "new_quantity": 20,
        "new_specification": "新规格",
        "cost_impact": 1000.00,
        "remark": "测试备注"
    }
    mat_result = test_api("POST", f"/ecns/{ecn_id}/affected-materials", token=token,
                         data=material_data, description="添加受影响物料")
    if not mat_result or "id" not in mat_result:
        print_error("添加受影响物料失败")
        return None
    mat_id = mat_result["id"]
    print_success(f"受影响物料添加成功: ID={mat_id}")

    # 3. 获取受影响物料列表
    print()
    test_api("GET", f"/ecns/{ecn_id}/affected-materials", token=token, description="获取受影响物料列表")

    # 4. 更新受影响物料
    print()
    update_mat_data = {
        "cost_impact": 1500.00,
        "remark": "更新后的备注"
    }
    test_api("PUT", f"/ecns/{ecn_id}/affected-materials/{mat_id}", token=token,
             data=update_mat_data, description="更新受影响物料")

    # 5. 删除受影响物料
    print()
    test_api("DELETE", f"/ecns/{ecn_id}/affected-materials/{mat_id}", token=token,
             description="删除受影响物料")

    return mat_id

def test_affected_orders(token: str, ecn_id: int):
    """测试受影响订单管理"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试受影响订单管理功能")
    print_info("=" * 80)

    # 1. 获取采购订单列表（用于选择订单）
    print()
    orders_result = test_api("GET", "/purchase-orders?page_size=5", token=token, description="获取采购订单列表")
    order_id = None
    order_no = "TEST-PO-001"
    if orders_result and "items" in orders_result and len(orders_result["items"]) > 0:
        order_id = orders_result["items"][0]["id"]
        order_no = orders_result["items"][0].get("po_no", order_no)
        print_success(f"使用订单ID: {order_id}, 订单号: {order_no}")

    # 2. 添加受影响订单
    print()
    order_data = {
        "order_type": "PURCHASE",
        "order_id": order_id,
        "order_no": order_no,
        "impact_description": "测试影响描述",
        "action_type": "MODIFY",
        "action_description": "需要修改订单"
    }
    order_result = test_api("POST", f"/ecns/{ecn_id}/affected-orders", token=token,
                          data=order_data, description="添加受影响订单")
    if not order_result or "id" not in order_result:
        print_error("添加受影响订单失败")
        return None
    affected_order_id = order_result["id"]
    print_success(f"受影响订单添加成功: ID={affected_order_id}")

    # 3. 获取受影响订单列表
    print()
    test_api("GET", f"/ecns/{ecn_id}/affected-orders", token=token, description="获取受影响订单列表")

    # 4. 更新受影响订单
    print()
    update_order_data = {
        "action_type": "CANCEL",
        "action_description": "需要取消订单"
    }
    test_api("PUT", f"/ecns/{ecn_id}/affected-orders/{affected_order_id}", token=token,
             data=update_order_data, description="更新受影响订单")

    # 5. 删除受影响订单
    print()
    test_api("DELETE", f"/ecns/{ecn_id}/affected-orders/{affected_order_id}", token=token,
             description="删除受影响订单")

    return affected_order_id

def test_ecn_types(token: str):
    """测试ECN类型配置管理"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN类型配置管理功能")
    print_info("=" * 80)

    # 1. 获取ECN类型列表
    print()
    test_api("GET", "/ecn-types", token=token, description="获取ECN类型列表")

    # 2. 创建ECN类型
    print()
    type_data = {
        "type_code": "TEST",
        "type_name": "测试类型",
        "description": "这是一个测试ECN类型",
        "required_depts": ["机械部", "电气部"],
        "optional_depts": ["软件部"],
        "approval_matrix": {
            "cost_threshold": 10000,
            "schedule_threshold": 7
        },
        "is_active": True
    }
    type_result = test_api("POST", "/ecn-types", token=token, data=type_data, description="创建ECN类型")
    if not type_result or "id" not in type_result:
        print_error("创建ECN类型失败")
        return None
    type_id = type_result["id"]
    print_success(f"ECN类型创建成功: ID={type_id}")

    # 3. 获取ECN类型详情
    print()
    test_api("GET", f"/ecn-types/{type_id}", token=token, description="获取ECN类型详情")

    # 4. 更新ECN类型
    print()
    update_type_data = {
        "type_name": "更新后的测试类型",
        "required_depts": ["机械部", "电气部", "采购部"]
    }
    test_api("PUT", f"/ecn-types/{type_id}", token=token, data=update_type_data, description="更新ECN类型")

    # 5. 删除ECN类型
    print()
    test_api("DELETE", f"/ecn-types/{type_id}", token=token, description="删除ECN类型")

    return type_id

def test_ecn_evaluation(token: str, ecn_id: int):
    """测试ECN评估功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN评估功能")
    print_info("=" * 80)

    # 1. 提交ECN（进入评估阶段）
    print()
    test_api("PUT", f"/ecns/{ecn_id}/submit", token=token, data={}, description="提交ECN")

    # 2. 创建评估
    print()
    eval_data = {
        "eval_dept": "机械部",
        "impact_analysis": "影响分析：需要修改机械结构",
        "cost_estimate": 5000.00,
        "schedule_estimate": 3,
        "resource_requirement": "需要2名机械工程师",
        "risk_assessment": "风险较低",
        "eval_result": "APPROVED",
        "eval_opinion": "同意变更",
        "conditions": "无附加条件"
    }
    eval_result = test_api("POST", f"/ecns/{ecn_id}/evaluations", token=token,
                           data=eval_data, description="创建评估")
    if not eval_result or "id" not in eval_result:
        print_error("创建评估失败")
        return None
    eval_id = eval_result["id"]
    print_success(f"评估创建成功: ID={eval_id}")

    # 3. 获取评估列表
    print()
    test_api("GET", f"/ecns/{ecn_id}/evaluations", token=token, description="获取评估列表")

    # 4. 获取评估详情
    print()
    test_api("GET", f"/ecn-evaluations/{eval_id}", token=token, description="获取评估详情")

    # 5. 提交评估
    print()
    test_api("PUT", f"/ecn-evaluations/{eval_id}/submit", token=token, description="提交评估")

    # 6. 获取评估汇总
    print()
    test_api("GET", f"/ecns/{ecn_id}/evaluation-summary", token=token, description="获取评估汇总")

    return eval_id

def test_ecn_approval(token: str, ecn_id: int):
    """测试ECN审批功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN审批功能")
    print_info("=" * 80)

    # 1. 创建审批记录
    print()
    approval_data = {
        "approval_level": 1,
        "approval_role": "项目经理",
        "due_date": (datetime.now() + timedelta(days=3)).isoformat()
    }
    approval_result = test_api("POST", f"/ecns/{ecn_id}/approvals", token=token,
                             data=approval_data, description="创建审批记录")
    if not approval_result or "id" not in approval_result:
        print_error("创建审批记录失败")
        return None
    approval_id = approval_result["id"]
    print_success(f"审批记录创建成功: ID={approval_id}")

    # 2. 获取审批列表
    print()
    test_api("GET", f"/ecns/{ecn_id}/approvals", token=token, description="获取审批列表")

    # 3. 获取审批详情
    print()
    test_api("GET", f"/ecn-approvals/{approval_id}", token=token, description="获取审批详情")

    # 4. 审批通过
    print()
    test_api("PUT", f"/ecn-approvals/{approval_id}/approve?approval_comment=同意", token=token,
             description="审批通过")

    return approval_id

def test_ecn_tasks(token: str, ecn_id: int):
    """测试ECN执行任务功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN执行任务功能")
    print_info("=" * 80)

    # 1. 创建执行任务
    print()
    task_data = {
        "task_name": "测试任务",
        "task_type": "DESIGN",
        "task_dept": "机械部",
        "task_description": "这是一个测试执行任务",
        "deliverables": "完成设计图纸",
        "planned_start": datetime.now().date().isoformat(),
        "planned_end": (datetime.now() + timedelta(days=5)).date().isoformat()
    }
    task_result = test_api("POST", f"/ecns/{ecn_id}/tasks", token=token,
                          data=task_data, description="创建执行任务")
    if not task_result or "id" not in task_result:
        print_error("创建执行任务失败")
        return None
    task_id = task_result["id"]
    print_success(f"执行任务创建成功: ID={task_id}")

    # 2. 获取任务列表
    print()
    test_api("GET", f"/ecns/{ecn_id}/tasks", token=token, description="获取任务列表")

    # 3. 获取任务详情
    print()
    test_api("GET", f"/ecn-tasks/{task_id}", token=token, description="获取任务详情")

    # 4. 更新任务进度
    print()
    progress_data = {
        "progress_percent": 50,
        "progress_note": "任务进行中"
    }
    test_api("PUT", f"/ecn-tasks/{task_id}/progress", token=token,
             data=progress_data, description="更新任务进度")

    # 5. 完成任务
    print()
    complete_data = {
        "completion_note": "任务已完成"
    }
    test_api("PUT", f"/ecn-tasks/{task_id}/complete", token=token,
             data=complete_data, description="完成任务")

    return task_id

def test_ecn_logs(token: str, ecn_id: int):
    """测试ECN日志功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN日志功能")
    print_info("=" * 80)

    # 获取ECN日志
    print()
    test_api("GET", f"/ecns/{ecn_id}/logs", token=token, description="获取ECN日志")

def test_ecn_statistics(token: str):
    """测试ECN统计功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试ECN统计功能")
    print_info("=" * 80)

    # 获取ECN统计
    print()
    test_api("GET", "/ecns/statistics", token=token, description="获取ECN统计")

def test_overdue_alerts(token: str):
    """测试超时提醒功能"""
    print()
    print("=" * 80)
    print_info("=" * 80)
    print_info("测试超时提醒功能")
    print_info("=" * 80)

    # 获取超时提醒
    print()
    test_api("GET", "/ecns/overdue-alerts", token=token, description="获取超时提醒")

def main():
    """主测试函数"""
    print()
    print("=" * 80)
    print_info("ECN变更管理模块API测试")
    print_info("=" * 80)

    # 检查服务器
    if not check_server():
        sys.exit(1)

    # 登录
    token = test_login()
    if not token:
        print_error("登录失败，无法继续测试")
        sys.exit(1)

    print()
    print_success("=" * 80)
    print_success("开始测试ECN模块功能")
    print_success("=" * 80)

    try:
        # 1. ECN基础操作
        result = test_ecn_basic_operations(token)
        if not result:
            print_error("ECN基础操作测试失败")
            return
        ecn_id, ecn_no = result

        # 2. 受影响物料管理
        test_affected_materials(token, ecn_id)

        # 3. 受影响订单管理
        test_affected_orders(token, ecn_id)

        # 4. ECN类型配置管理
        test_ecn_types(token)

        # 5. ECN评估功能
        test_ecn_evaluation(token, ecn_id)

        # 6. ECN审批功能
        test_ecn_approval(token, ecn_id)

        # 7. ECN执行任务功能
        test_ecn_tasks(token, ecn_id)

        # 8. ECN日志功能
        test_ecn_logs(token, ecn_id)

        # 9. ECN统计功能
        test_ecn_statistics(token)

        # 10. 超时提醒功能
        test_overdue_alerts(token)

        print()
        print_success("=" * 80)
        print_success("所有测试完成！")
        print_success("=" * 80)
        print()
        print_info(f"测试ECN编号: {ecn_no}")
        print_info(f"测试ECN ID: {ecn_id}")
        print()

    except Exception as e:
        print_error(f"测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()





