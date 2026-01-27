#!/usr/bin/env python3
"""
测试部门API序列化修复
验证 /api/v1/org/departments 返回正确的Pydantic模型
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_test(name: str, success: bool, detail: str = ""):
    """打印测试结果"""
    status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if detail:
        print(f"  → {detail}")

def login() -> str:
    """登录获取Token"""
    print(f"{BLUE}正在登录...{RESET}")

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin", "password": "password123"},
        timeout=3
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"{GREEN}✓ 登录成功{RESET}")
        return token
    elif response.status_code == 429:
        print(f"{YELLOW}⚠ 触发速率限制，等待60秒...{RESET}")
        time.sleep(60)
        return login()
    else:
        print(f"{RED}✗ 登录失败: {response.status_code}{RESET}")
        return None

def test_department_api(token: str):
    """测试部门API"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}测试部门API序列化修复{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    headers = {"Authorization": f"Bearer {token}"}

    # 测试1: GET /api/v1/org/departments
    print("测试1: 获取部门列表")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/org/departments",
            headers=headers,
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()

            # 检查响应格式
            if "items" in data:
                items = data["items"]
                print_test(
                    "获取部门列表",
                    True,
                    f"返回{len(items)}条部门记录"
                )

                # 检查第一条记录的结构
                if items:
                    dept = items[0]
                    required_fields = ["id", "dept_name", "dept_code"]
                    has_all_fields = all(field in dept for field in required_fields)

                    print_test(
                        "响应包含必需字段",
                        has_all_fields,
                        f"字段: {', '.join(dept.keys())}"
                    )

                    # 打印第一条记录
                    print("\n  第一条记录示例:")
                    print(f"    ID: {dept.get('id')}")
                    print(f"    部门名称: {dept.get('dept_name')}")
                    print(f"    部门编码: {dept.get('dept_code')}")
                    print(f"    是否启用: {dept.get('is_active')}")
                else:
                    print_test("响应包含必需字段", True, "无部门数据")
            else:
                print_test("获取部门列表", False, f"响应格式错误: {data}")
        else:
            print_test(
                "获取部门列表",
                False,
                f"状态码: {response.status_code}, 错误: {response.text[:200]}"
            )
    except Exception as e:
        print_test("获取部门列表", False, f"异常: {e}")

    # 测试2: GET /api/v1/org/departments/tree
    print("\n测试2: 获取部门树")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/org/departments/tree",
            headers=headers,
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                print_test(
                    "获取部门树",
                    True,
                    f"返回{len(data['items'])}个顶级部门"
                )
            else:
                print_test("获取部门树", False, "响应格式错误")
        else:
            print_test(
                "获取部门树",
                False,
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("获取部门树", False, f"异常: {e}")

    # 测试3: GET /api/v1/org/departments/statistics
    print("\n测试3: 获取部门统计")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/org/departments/statistics",
            headers=headers,
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            if "data" in data and "departments" in data["data"]:
                dept_stats = data["data"]["departments"]
                print_test(
                    "获取部门统计",
                    True,
                    f"返回{len(dept_stats)}个部门的统计数据"
                )
            else:
                print_test("获取部门统计", False, "响应格式错误")
        else:
            print_test(
                "获取部门统计",
                False,
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("获取部门统计", False, f"异常: {e}")

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}部门API修复验证测试{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # 检查服务
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"{GREEN}✓ 服务正在运行{RESET}\n")
    except:
        print(f"{RED}✗ 服务未运行！{RESET}\n")
        return

    # 登录
    token = login()
    if not token:
        print(f"{RED}无法获取Token，测试终止{RESET}")
        return

    # 测试API
    test_department_api(token)

    # 总结
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{GREEN}✅ 部门API序列化修复验证完成{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    main()
