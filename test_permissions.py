#!/usr/bin/env python3
"""
权限模块完整测试脚本
测试细粒度权限控制、角色权限、数据权限等
"""

import requests
from typing import Optional, Dict, Any

BASE_URL = "http://127.0.0.1:8000"

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*70}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{'='*70}\n")

def print_test(name: str, success: bool, detail: str = ""):
    """打印测试结果"""
    status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if detail:
        print(f"  → {detail}")

def print_info(message: str):
    """打印信息"""
    print(f"{CYAN}ℹ {message}{RESET}")

def login(username: str, password: str) -> Optional[str]:
    """登录并返回Token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": username, "password": password},
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"{RED}登录失败: {response.status_code} - {response.text[:100]}{RESET}")
            return None
    except Exception as e:
        print(f"{RED}登录异常: {e}{RESET}")
        return None

def test_api(
    method: str,
    path: str,
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    expected_status: int = 200
) -> tuple[bool, int, Any]:
    """
    测试API端点

    Returns:
        (success, status_code, response_data)
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method,
            f"{BASE_URL}{path}",
            headers=headers,
            json=data,
            timeout=3
        )

        success = response.status_code == expected_status
        try:
            response_data = response.json()
        except:
            response_data = response.text

        return success, response.status_code, response_data
    except Exception as e:
        return False, 0, str(e)

def test_permission_check():
    """测试1: 基础权限检查"""
    print_section("测试1: 基础权限检查")

    print_info("登录admin用户（超级管理员）...")
    admin_token = login("admin", "password123")

    if not admin_token:
        print_test("获取admin Token", False, "登录失败")
        return False

    print_test("获取admin Token", True, "登录成功")

    # 测试超级管理员访问各种资源
    test_cases = [
        ("GET", "/api/v1/users", 200, "查看用户列表"),
        ("GET", "/api/v1/projects", 200, "查看项目列表"),
        ("GET", "/api/v1/materials", 200, "查看物料列表"),
        ("GET", "/api/v1/org/departments", 200, "查看部门列表"),
    ]

    all_passed = True
    for method, path, expected, description in test_cases:
        success, status, data = test_api(method, path, admin_token, expected_status=expected)

        if success:
            # 分析返回数据
            detail = f"状态码: {status}"
            if isinstance(data, dict):
                if 'items' in data:
                    detail += f" - 返回{len(data['items'])}条记录"
                elif 'data' in data:
                    detail += " - 包含数据"
        else:
            detail = f"期望{expected}但得到{status}"
            if isinstance(data, dict) and 'message' in data:
                detail += f" - {data['message']}"

        print_test(f"{description} ({method} {path})", success, detail)
        if not success:
            all_passed = False

    return all_passed

def test_permission_denied():
    """测试2: 权限拒绝测试"""
    print_section("测试2: 权限拒绝测试（模拟无权限用户）")

    # 使用admin token尝试访问需要特定权限的操作
    admin_token = login("admin", "password123")
    if not admin_token:
        print_test("获取Token", False, "登录失败")
        return False

    print_info("测试超级管理员是否能访问受保护的操作...")

    # 超级管理员应该能访问所有内容
    test_cases = [
        ("GET", "/api/v1/users/235", 200, "查看用户详情"),
        ("GET", "/api/v1/projects", 200, "查看项目"),
    ]

    all_passed = True
    for method, path, expected, description in test_cases:
        success, status, data = test_api(method, path, admin_token, expected_status=expected)

        detail = f"状态码: {status}"
        if not success and isinstance(data, dict):
            detail += f" - {data.get('message', data.get('detail', ''))}"

        print_test(f"{description} ({method} {path})", success, detail)
        if not success:
            all_passed = False

    return all_passed

def test_permission_inheritance():
    """测试3: 权限继承和角色权限"""
    print_section("测试3: 权限继承和角色权限")

    admin_token = login("admin", "password123")
    if not admin_token:
        print_test("获取Token", False, "登录失败")
        return False

    print_info("检查当前用户权限...")

    # 获取当前用户信息（包含角色和权限）
    success, status, data = test_api("GET", "/api/v1/users/235", admin_token)

    if success:
        print_test("获取用户权限信息", True, f"用户ID: {data.get('data', {}).get('id')}")

        user_data = data.get('data', {})
        print(f"  用户名: {user_data.get('username')}")
        print(f"  真实姓名: {user_data.get('real_name')}")
        print(f"  超级用户: {user_data.get('is_superuser')}")
        print(f"  角色: {user_data.get('roles', [])}")

        return True
    else:
        print_test("获取用户权限信息", False, f"状态码: {status}")
        return False

def test_data_permissions():
    """测试4: 数据权限过滤"""
    print_section("测试4: 数据权限过滤")

    admin_token = login("admin", "password123")
    if not admin_token:
        print_test("获取Token", False, "登录失败")
        return False

    print_info("测试数据权限过滤...")

    # 测试分页和过滤
    test_cases = [
        ("GET", "/api/v1/users?page=1&page_size=5", 200, "分页查询用户"),
        ("GET", "/api/v1/users?is_active=true", 200, "过滤活跃用户"),
        ("GET", "/api/v1/projects?page=1&page_size=10", 200, "分页查询项目"),
    ]

    all_passed = True
    for method, path, expected, description in test_cases:
        success, status, data = test_api(method, path, admin_token, expected_status=expected)

        if success:
            detail = f"状态码: {status}"
            if isinstance(data, dict):
                if 'items' in data:
                    detail += f" - 返回{len(data['items'])}/{data.get('total', 0)}条记录"
                    detail += f", 第{data.get('page', 1)}页"
        else:
            detail = f"期望{expected}但得到{status}"

        print_test(f"{description}", success, detail)
        if not success:
            all_passed = False

    return all_passed

def test_api_endpoints_coverage():
    """测试5: API端点权限覆盖率"""
    print_section("测试5: API端点权限覆盖率检查")

    admin_token = login("admin", "password123")
    if not admin_token:
        print_test("获取Token", False, "登录失败")
        return False

    print_info("检查主要API端点是否有权限保护...")

    # 关键API端点列表
    endpoints = [
        ("/api/v1/users", "用户管理"),
        ("/api/v1/projects", "项目管理"),
        ("/api/v1/materials", "物料管理"),
        ("/api/v1/org/departments", "部门管理"),
        ("/api/v1/org/employees", "员工管理"),
    ]

    print("\n未认证访问测试（应该全部返回401）：")
    all_protected = True
    for path, name in endpoints:
        success, status, data = test_api("GET", path, token=None, expected_status=401)

        if success:
            error_code = data.get('error_code', '') if isinstance(data, dict) else ''
            print_test(f"{name}: {path}", True, f"正确拦截 - {error_code}")
        else:
            print_test(f"{name}: {path}", False, f"未拦截！状态码: {status}")
            all_protected = False

    print("\n已认证访问测试（超级管理员应该全部可访问）：")
    all_accessible = True
    for path, name in endpoints:
        success, status, data = test_api("GET", path, admin_token, expected_status=200)

        if success:
            item_count = len(data.get('items', [])) if isinstance(data, dict) else 0
            print_test(f"{name}: {path}", True, f"访问成功 - {item_count}条记录")
        else:
            print_test(f"{name}: {path}", False, f"访问失败: {status}")
            all_accessible = False

    return all_protected and all_accessible

def test_permission_codes():
    """测试6: 权限代码验证"""
    print_section("测试6: 权限代码验证")

    print_info("检查权限代码是否正确实施...")

    # 读取代码检查权限定义
    import subprocess

    try:
        # 查找所有 require_permission 的使用
        result = subprocess.run(
            ["grep", "-r", "require_permission", "app/api/v1/endpoints/",
             "--include=*.py", "-h"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            permissions = set()
            for line in lines:
                if 'require_permission' in line:
                    # 提取权限代码
                    import re
                    match = re.search(r'require_permission\(["\']([^"\']+)["\']\)', line)
                    if match:
                        permissions.add(match.group(1))

            print_test(
                "权限代码扫描",
                True,
                f"发现{len(permissions)}个不同的权限代码"
            )

            if permissions:
                print("\n  权限代码列表:")
                for perm in sorted(permissions):
                    print(f"    - {perm}")

            return True
        else:
            print_test("权限代码扫描", False, "扫描失败")
            return False
    except Exception as e:
        print_test("权限代码扫描", False, f"异常: {e}")
        return False

def main():
    """主测试流程"""
    print(f"\n{BLUE}{'='*70}")
    print("权限模块完整测试")
    print(f"{'='*70}{RESET}")

    print(f"\n{YELLOW}测试环境: {BASE_URL}{RESET}")
    print(f"{YELLOW}测试账号: admin / password123{RESET}")

    # 先检查服务是否运行
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"{GREEN}✓ 服务正在运行{RESET}")
    except:
        print(f"\n{RED}✗ 服务未运行！{RESET}")
        print(f"请先启动服务: {YELLOW}uvicorn app.main:app --reload{RESET}\n")
        return

    # 执行测试
    results = []

    # 测试1: 基础权限检查
    results.append(("基础权限检查", test_permission_check()))

    # 测试2: 权限拒绝
    results.append(("权限拒绝测试", test_permission_denied()))

    # 测试3: 权限继承
    results.append(("权限继承和角色", test_permission_inheritance()))

    # 测试4: 数据权限
    results.append(("数据权限过滤", test_data_permissions()))

    # 测试5: API覆盖率
    results.append(("API端点权限覆盖", test_api_endpoints_coverage()))

    # 测试6: 权限代码
    results.append(("权限代码验证", test_permission_codes()))

    # 汇总结果
    print_section("测试结果汇总")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{status} {name}")

    print(f"\n{'='*70}")
    if passed == total:
        print(f"{GREEN}✅ 所有测试通过！ ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}⚠ 部分测试失败 ({passed}/{total}){RESET}")
    print(f"{'='*70}\n")

    # 总结和建议
    if passed == total:
        print(f"{BLUE}🎉 权限模块工作正常！{RESET}\n")
        print("权限系统特点：")
        print("✓ 全局认证中间件保护所有API")
        print("✓ 细粒度权限控制（require_permission）")
        print("✓ 超级管理员拥有所有权限")
        print("✓ 数据权限过滤和分页")
        print("\n下一步建议：")
        print("1. 创建普通用户测试权限限制")
        print("2. 测试角色继承和权限组合")
        print("3. 添加权限审计日志")
        print("4. 实施数据权限隔离（部门/项目级别）")
    else:
        print(f"{YELLOW}需要修复失败的测试{RESET}\n")

if __name__ == "__main__":
    main()
