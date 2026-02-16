#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试核心业务API
识别Schema相关问题
"""

import requests
import json
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8000"

def get_token() -> str:
    """获取认证Token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]

def test_api(token: str, method: str, endpoint: str, params: dict = None) -> Tuple[bool, str, dict]:
    """
    测试单个API
    
    Returns:
        (success, error_message, response_data)
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=params, timeout=5)
        else:
            return False, f"不支持的方法: {method}", {}
        
        # 处理307重定向
        if response.status_code == 307:
            redirect_url = response.headers.get("location")
            if redirect_url:
                response = requests.get(redirect_url, headers=headers, timeout=5)
        
        # 检查响应
        if response.status_code == 200:
            try:
                data = response.json()
                return True, "", data
            except:
                return True, "", {"raw": response.text[:100]}
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", error_data.get("message", response.text[:200]))
            except:
                error_msg = response.text[:200]
            return False, f"HTTP {response.status_code}: {error_msg}", {}
    
    except requests.exceptions.Timeout:
        return False, "请求超时 (5秒)", {}
    except Exception as e:
        return False, f"异常: {str(e)[:200]}", {}

def main():
    print("=" * 80)
    print("全面API测试 - 识别Schema问题")
    print("=" * 80)
    print()
    
    # 获取Token
    print("🔐 获取认证Token...")
    try:
        token = get_token()
        print("✅ Token获取成功\n")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 定义测试用例
    test_cases = [
        # 1. 认证系统
        ("认证系统", [
            ("GET", "/api/v1/auth/me", None, "获取当前用户"),
        ]),
        
        # 2. 用户管理
        ("用户管理", [
            ("GET", "/api/v1/users/", {"page": 1, "page_size": 5}, "用户列表"),
        ]),
        
        # 3. 项目管理
        ("项目管理", [
            ("GET", "/api/v1/projects/", None, "项目列表"),
            ("GET", "/api/v1/projects/statistics", None, "项目统计"),
            ("GET", "/api/v1/projects/progress/summary", None, "进度汇总"),
        ]),
        
        # 4. 生产管理
        ("生产管理", [
            ("GET", "/api/v1/production/work-orders/", {"page": 1, "page_size": 5}, "工单列表"),
            ("GET", "/api/v1/production/dashboard", None, "生产看板"),
            ("GET", "/api/v1/production/quality/statistics", None, "质量统计"),
        ]),
        
        # 5. 销售管理
        ("销售管理", [
            ("GET", "/api/v1/sales/opportunities/", None, "销售机会列表"),
            ("GET", "/api/v1/sales/contracts/", None, "合同列表"),
            ("GET", "/api/v1/sales/customers/", None, "客户列表"),
        ]),
        
        # 6. 采购管理
        ("采购管理", [
            ("GET", "/api/v1/purchase/suppliers/", None, "供应商列表"),
            ("GET", "/api/v1/purchase/orders/", None, "采购订单列表"),
        ]),
        
        # 7. 库存管理
        ("库存管理", [
            ("GET", "/api/v1/inventory/materials/", None, "物料库存列表"),
            ("GET", "/api/v1/inventory/shortage-alerts/", None, "缺料预警列表"),
        ]),
        
        # 8. 工时管理
        ("工时管理", [
            ("GET", "/api/v1/timesheet/records/", None, "工时记录列表"),
            ("GET", "/api/v1/timesheet/monthly/", None, "月度工时统计"),
        ]),
        
        # 9. 预售管理
        ("预售管理", [
            ("GET", "/api/v1/presale/tickets/", None, "预售工单列表"),
            ("GET", "/api/v1/presale/solutions/", None, "解决方案列表"),
        ]),
        
        # 10. 角色权限
        ("角色权限", [
            ("GET", "/api/v1/roles/", None, "角色列表"),
            ("GET", "/api/v1/permissions/", None, "权限列表"),
        ]),
    ]
    
    # 执行测试
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    schema_errors = []
    
    for module_name, apis in test_cases:
        print(f"\n{'='*80}")
        print(f"📦 {module_name}")
        print(f"{'='*80}")
        
        for method, endpoint, params, description in apis:
            total_tests += 1
            success, error_msg, data = test_api(token, method, endpoint, params)
            
            if success:
                passed_tests += 1
                # 显示数据摘要
                if isinstance(data, dict):
                    if "total" in data:
                        print(f"  ✅ {description}: 返回 {data['total']} 条记录")
                    elif "items" in data:
                        print(f"  ✅ {description}: 返回 {len(data['items'])} 条记录")
                    elif "username" in data:
                        print(f"  ✅ {description}: {data['username']}")
                    else:
                        print(f"  ✅ {description}: 成功")
                else:
                    print(f"  ✅ {description}: 成功")
            else:
                failed_tests += 1
                print(f"  ❌ {description}")
                print(f"     错误: {error_msg}")
                
                # 识别Schema相关错误
                if any(keyword in error_msg.lower() for keyword in [
                    "no such column", "attributeerror", "missing", 
                    "does not have", "column", "field required"
                ]):
                    schema_errors.append({
                        "module": module_name,
                        "api": f"{method} {endpoint}",
                        "description": description,
                        "error": error_msg
                    })
    
    # 生成测试报告
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    print(f"总测试数: {total_tests}")
    print(f"✅ 通过: {passed_tests} ({passed_tests*100//total_tests}%)")
    print(f"❌ 失败: {failed_tests} ({failed_tests*100//total_tests}%)")
    print()
    
    # Schema错误详情
    if schema_errors:
        print("=" * 80)
        print("🔴 Schema相关错误 (需要修复)")
        print("=" * 80)
        for i, error in enumerate(schema_errors, 1):
            print(f"\n{i}. {error['module']} - {error['description']}")
            print(f"   API: {error['api']}")
            print(f"   错误: {error['error'][:150]}")
        print()
        print(f"🔴 发现 {len(schema_errors)} 个Schema相关问题")
    else:
        print("✅ 未发现Schema相关错误")
    
    # 保存详细报告
    report = {
        "timestamp": "2026-02-17T00:15:00+08:00",
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": f"{passed_tests*100//total_tests}%"
        },
        "schema_errors": schema_errors
    }
    
    with open("api_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: api_test_report.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
