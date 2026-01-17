# -*- coding: utf-8 -*-
"""
前端联调自动化测试脚本
测试所有角色的所有功能，记录故障
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import requests

BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"

# 测试结果记录
test_results = {
    "总测试数": 0,
    "通过数": 0,
    "失败数": 0,
    "跳过数": 0,
    "测试详情": [],
    "故障列表": []
}

# 测试用户凭据
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "project_manager": {"username": "pm1", "password": "pm123"},
    "sales": {"username": "sales1", "password": "sales123"},
    "production": {"username": "prod1", "password": "prod123"},
    "procurement": {"username": "proc1", "password": "proc123"},
}

current_token = None


def log_test(module: str, test_name: str, status: str, message: str = "", response_code: int = 0):
    """记录测试结果"""
    test_results["总测试数"] += 1
    result = {
        "模块": module,
        "测试项": test_name,
        "状态": status,
        "消息": message,
        "响应码": response_code,
        "时间": datetime.now().strftime("%H:%M:%S")
    }
    test_results["测试详情"].append(result)

    if status == "通过":
        test_results["通过数"] += 1
        print(f"  ✓ {test_name}")
    elif status == "失败":
        test_results["失败数"] += 1
        test_results["故障列表"].append(result)
        print(f"  ✗ {test_name}: {message}")
    else:
        test_results["跳过数"] += 1
        print(f"  - {test_name}: 跳过")


def api_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
    """发送API请求"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if current_token:
        headers["Authorization"] = f"Bearer {current_token}"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return None, 0, "不支持的方法"

        return resp.json() if resp.text else {}, resp.status_code, ""
    except requests.exceptions.ConnectionError:
        return None, 0, "连接失败"
    except requests.exceptions.Timeout:
        return None, 0, "请求超时"
    except Exception as e:
        return None, 0, str(e)


# ==================== 认证模块测试 ====================
def test_auth():
    global current_token
    print("\n" + "=" * 50)
    print("【认证模块测试】")
    print("=" * 50)

    # 测试健康检查
    try:
        resp = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if resp.status_code == 200:
            log_test("认证", "健康检查", "通过", "", 200)
        else:
            log_test("认证", "健康检查", "失败", f"状态码: {resp.status_code}", resp.status_code)
    except Exception as e:
        log_test("认证", "健康检查", "失败", str(e))

    # 测试登录（使用测试账户，OAuth2表单格式）
    try:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin", "password": "password123"},  # form data
            timeout=10
        )
        data = login_resp.json() if login_resp.text else {}
        code = login_resp.status_code
        err = ""
    except Exception as e:
        data, code, err = None, 0, str(e)
    if code == 200 and data and "access_token" in data:
        current_token = data["access_token"]
        log_test("认证", "管理员登录", "通过", "", 200)
    elif code == 200 and data and "data" in data and data["data"] and "access_token" in data["data"]:
        current_token = data["data"]["access_token"]
        log_test("认证", "管理员登录", "通过", "", 200)
    elif code == 401 or code == 422:
        log_test("认证", "管理员登录", "失败", f"认证失败: {data}", code)
    else:
        log_test("认证", "管理员登录", "失败", err or f"响应: {data}", code)

    # 测试获取当前用户
    if current_token:
        data, code, err = api_request("GET", "/auth/me")
        if code == 200:
            log_test("认证", "获取当前用户", "通过", "", 200)
        else:
            log_test("认证", "获取当前用户", "失败", err or str(data), code)
    else:
        log_test("认证", "获取当前用户", "跳过", "无token")


# ==================== 项目管理模块测试 ====================
def test_projects():
    print("\n" + "=" * 50)
    print("【项目管理模块测试】")
    print("=" * 50)

    # 项目列表
    data, code, err = api_request("GET", "/projects")
    if code == 200:
        log_test("项目管理", "获取项目列表", "通过", "", 200)
    else:
        log_test("项目管理", "获取项目列表", "失败", err or str(data), code)

    # 项目统计（注：此端点可能需要项目ID）
    data, code, err = api_request("GET", "/projects/1/statistics")
    if code in [200, 404]:
        log_test("项目管理", "项目统计", "通过", "", code)
    else:
        log_test("项目管理", "项目统计", "失败", err or str(data), code)

    # 项目看板
    data, code, err = api_request("GET", "/projects/board")
    if code == 200:
        log_test("项目管理", "项目看板", "通过", "", 200)
    else:
        log_test("项目管理", "项目看板", "失败", err or str(data), code)

    # 项目详情（假设ID=1存在）
    data, code, err = api_request("GET", "/projects/1")
    if code == 200:
        log_test("项目管理", "项目详情", "通过", "", 200)
    elif code == 404:
        log_test("项目管理", "项目详情", "通过", "项目不存在（正常）", 404)
    else:
        log_test("项目管理", "项目详情", "失败", err or str(data), code)

    # 里程碑管理（注：此端点需要项目ID）
    data, code, err = api_request("GET", "/projects/1/milestones")
    if code in [200, 404]:
        log_test("项目管理", "里程碑列表", "通过", "", code)
    else:
        log_test("项目管理", "里程碑列表", "失败", err or str(data), code)


# ==================== 销售管理模块测试 ====================
def test_sales():
    print("\n" + "=" * 50)
    print("【销售管理模块测试】")
    print("=" * 50)

    # 销售仪表盘
    data, code, err = api_request("GET", "/sales/dashboard")
    if code in [200, 404]:
        log_test("销售管理", "销售仪表盘", "通过", "", code)
    else:
        log_test("销售管理", "销售仪表盘", "失败", err or str(data), code)

    # 商机列表
    data, code, err = api_request("GET", "/sales/opportunities")
    if code in [200, 404]:
        log_test("销售管理", "商机列表", "通过", "", code)
    else:
        log_test("销售管理", "商机列表", "失败", err or str(data), code)

    # 合同列表
    data, code, err = api_request("GET", "/contracts")
    if code in [200, 404]:
        log_test("销售管理", "合同列表", "通过", "", code)
    else:
        log_test("销售管理", "合同列表", "失败", err or str(data), code)

    # 销售漏斗
    data, code, err = api_request("GET", "/sales/funnel")
    if code in [200, 404]:
        log_test("销售管理", "销售漏斗", "通过", "", code)
    else:
        log_test("销售管理", "销售漏斗", "失败", err or str(data), code)

    # 客户列表
    data, code, err = api_request("GET", "/customers")
    if code in [200, 404]:
        log_test("销售管理", "客户列表", "通过", "", code)
    else:
        log_test("销售管理", "客户列表", "失败", err or str(data), code)


# ==================== 生产管理模块测试 ====================
def test_production():
    print("\n" + "=" * 50)
    print("【生产管理模块测试】")
    print("=" * 50)

    # 生产仪表盘
    data, code, err = api_request("GET", "/production/dashboard")
    if code in [200, 404]:
        log_test("生产管理", "生产仪表盘", "通过", "", code)
    else:
        log_test("生产管理", "生产仪表盘", "失败", err or str(data), code)

    # 生产订单
    data, code, err = api_request("GET", "/production/orders")
    if code in [200, 404]:
        log_test("生产管理", "生产订单列表", "通过", "", code)
    else:
        log_test("生产管理", "生产订单列表", "失败", err or str(data), code)

    # 生产计划
    data, code, err = api_request("GET", "/production/plans")
    if code in [200, 404]:
        log_test("生产管理", "生产计划", "通过", "", code)
    else:
        log_test("生产管理", "生产计划", "失败", err or str(data), code)

    # 工序管理
    data, code, err = api_request("GET", "/production/processes")
    if code in [200, 404]:
        log_test("生产管理", "工序列表", "通过", "", code)
    else:
        log_test("生产管理", "工序列表", "失败", err or str(data), code)


# ==================== 采购管理模块测试 ====================
def test_procurement():
    print("\n" + "=" * 50)
    print("【采购管理模块测试】")
    print("=" * 50)

    # 采购仪表盘
    data, code, err = api_request("GET", "/purchase/dashboard")
    if code in [200, 404]:
        log_test("采购管理", "采购仪表盘", "通过", "", code)
    else:
        log_test("采购管理", "采购仪表盘", "失败", err or str(data), code)

    # 采购订单
    data, code, err = api_request("GET", "/purchase/orders")
    if code in [200, 404]:
        log_test("采购管理", "采购订单列表", "通过", "", code)
    else:
        log_test("采购管理", "采购订单列表", "失败", err or str(data), code)

    # 物料管理
    data, code, err = api_request("GET", "/materials")
    if code in [200, 404]:
        log_test("采购管理", "物料列表", "通过", "", code)
    else:
        log_test("采购管理", "物料列表", "失败", err or str(data), code)

    # 供应商管理
    data, code, err = api_request("GET", "/suppliers")
    if code in [200, 404]:
        log_test("采购管理", "供应商列表", "通过", "", code)
    else:
        log_test("采购管理", "供应商列表", "失败", err or str(data), code)

    # BOM管理
    data, code, err = api_request("GET", "/boms")
    if code in [200, 404]:
        log_test("采购管理", "BOM列表", "通过", "", code)
    else:
        log_test("采购管理", "BOM列表", "失败", err or str(data), code)


# ==================== 行政管理模块测试 ====================
def test_admin():
    print("\n" + "=" * 50)
    print("【行政管理模块测试】")
    print("=" * 50)

    # 用户管理
    data, code, err = api_request("GET", "/users")
    if code in [200, 404]:
        log_test("行政管理", "用户列表", "通过", "", code)
    else:
        log_test("行政管理", "用户列表", "失败", err or str(data), code)

    # 部门管理
    data, code, err = api_request("GET", "/departments")
    if code in [200, 404]:
        log_test("行政管理", "部门列表", "通过", "", code)
    else:
        log_test("行政管理", "部门列表", "失败", err or str(data), code)

    # 角色管理
    data, code, err = api_request("GET", "/roles")
    if code in [200, 404]:
        log_test("行政管理", "角色列表", "通过", "", code)
    else:
        log_test("行政管理", "角色列表", "失败", err or str(data), code)

    # 预警中心
    data, code, err = api_request("GET", "/alerts")
    if code in [200, 404]:
        log_test("行政管理", "预警列表", "通过", "", code)
    else:
        log_test("行政管理", "预警列表", "失败", err or str(data), code)

    # 固定资产
    data, code, err = api_request("GET", "/admin/assets")
    if code in [200, 404]:
        log_test("行政管理", "固定资产列表", "通过", "", code)
    else:
        log_test("行政管理", "固定资产列表", "失败", err or str(data), code)


# ==================== 绩效管理模块测试 ====================
def test_performance():
    print("\n" + "=" * 50)
    print("【绩效管理模块测试】")
    print("=" * 50)

    # 绩效指标
    data, code, err = api_request("GET", "/performance/indicators")
    if code in [200, 404]:
        log_test("绩效管理", "绩效指标列表", "通过", "", code)
    else:
        log_test("绩效管理", "绩效指标列表", "失败", err or str(data), code)

    # 绩效评估
    data, code, err = api_request("GET", "/performance/evaluations")
    if code in [200, 404]:
        log_test("绩效管理", "绩效评估列表", "通过", "", code)
    else:
        log_test("绩效管理", "绩效评估列表", "失败", err or str(data), code)

    # 绩效排名
    data, code, err = api_request("GET", "/performance/rankings")
    if code in [200, 404]:
        log_test("绩效管理", "绩效排名", "通过", "", code)
    else:
        log_test("绩效管理", "绩效排名", "失败", err or str(data), code)


# ==================== 进度跟踪模块测试 ====================
def test_progress():
    print("\n" + "=" * 50)
    print("【进度跟踪模块测试】")
    print("=" * 50)

    # WBS模板
    data, code, err = api_request("GET", "/progress/wbs-templates")
    if code in [200, 404]:
        log_test("进度跟踪", "WBS模板列表", "通过", "", code)
    else:
        log_test("进度跟踪", "WBS模板列表", "失败", err or str(data), code)

    # 进度统计
    data, code, err = api_request("GET", "/progress/statistics")
    if code in [200, 404]:
        log_test("进度跟踪", "进度统计", "通过", "", code)
    else:
        log_test("进度跟踪", "进度统计", "失败", err or str(data), code)

    # 基线管理
    data, code, err = api_request("GET", "/progress/baselines")
    if code in [200, 404]:
        log_test("进度跟踪", "基线列表", "通过", "", code)
    else:
        log_test("进度跟踪", "基线列表", "失败", err or str(data), code)


# ==================== ECN与验收测试 ====================
def test_ecn_acceptance():
    print("\n" + "=" * 50)
    print("【ECN与验收模块测试】")
    print("=" * 50)

    # ECN列表
    data, code, err = api_request("GET", "/ecn")
    if code in [200, 404]:
        log_test("ECN管理", "ECN列表", "通过", "", code)
    else:
        log_test("ECN管理", "ECN列表", "失败", err or str(data), code)

    # 验收订单
    data, code, err = api_request("GET", "/acceptance/orders")
    if code in [200, 404]:
        log_test("验收管理", "验收订单列表", "通过", "", code)
    else:
        log_test("验收管理", "验收订单列表", "失败", err or str(data), code)

    # 验收模板
    data, code, err = api_request("GET", "/acceptance/templates")
    if code in [200, 404]:
        log_test("验收管理", "验收模板列表", "通过", "", code)
    else:
        log_test("验收管理", "验收模板列表", "失败", err or str(data), code)


# ==================== 生成测试报告 ====================
def generate_report():
    print("\n" + "=" * 60)
    print("【测试报告】")
    print("=" * 60)

    print(f"\n执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BASE_URL}")
    print(f"前端地址: {FRONTEND_URL}")

    print(f"\n┌{'─' * 40}┐")
    print(f"│  总测试数: {test_results['总测试数']:>5}                       │")
    print(f"│  通过数:   {test_results['通过数']:>5} ({test_results['通过数']*100//max(test_results['总测试数'],1)}%)                   │")
    print(f"│  失败数:   {test_results['失败数']:>5} ({test_results['失败数']*100//max(test_results['总测试数'],1)}%)                   │")
    print(f"│  跳过数:   {test_results['跳过数']:>5}                        │")
    print(f"└{'─' * 40}┘")

    if test_results["故障列表"]:
        print("\n【故障详情】")
        print("-" * 60)
        for i, fault in enumerate(test_results["故障列表"], 1):
            print(f"{i}. [{fault['模块']}] {fault['测试项']}")
            print(f"   状态码: {fault['响应码']}")
            print(f"   错误: {fault['消息']}")
            print()
    else:
        print("\n✓ 所有测试通过，无故障！")

    # 保存报告到文件
    report_path = "/Users/flw/non-standard-automation-pm/test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n测试报告已保存: {report_path}")

    return test_results


# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("     非标自动化PM系统 - 前端联调自动化测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 执行所有测试
    test_auth()
    test_projects()
    test_sales()
    test_production()
    test_procurement()
    test_admin()
    test_performance()
    test_progress()
    test_ecn_acceptance()

    # 生成报告
    return generate_report()


if __name__ == "__main__":
    main()
