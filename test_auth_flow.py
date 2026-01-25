#!/usr/bin/env python3
"""
完整认证流程测试脚本
测试从登录到访问受保护资源的完整流程
"""

import requests
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
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

def test_whitelist_access():
    """测试1: 白名单路径无需认证"""
    print_section("测试1: 白名单路径访问")

    whitelist_paths = [
        ("/health", "健康检查"),
        ("/", "根路径"),
        ("/docs", "API文档"),
        ("/openapi.json", "OpenAPI Schema"),
    ]

    all_passed = True
    for path, description in whitelist_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=3)
            success = response.status_code in [200, 307]  # 307 是重定向
            print_test(
                f"{description} ({path})",
                success,
                f"状态码: {response.status_code}"
            )
            if not success:
                all_passed = False
        except Exception as e:
            print_test(f"{description} ({path})", False, f"错误: {e}")
            all_passed = False

    return all_passed

def test_unauthorized_access():
    """测试2: 未认证访问应被拦截"""
    print_section("测试2: 未认证访问拦截")

    protected_paths = [
        "/api/v1/projects",
        "/api/v1/users",
        "/api/v1/materials",
    ]

    all_passed = True
    for path in protected_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=3)
            success = response.status_code == 401

            if success:
                data = response.json()
                detail = f"错误码: {data.get('error_code')} - {data.get('message')}"
            else:
                detail = f"期望401但得到{response.status_code}"

            print_test(f"拦截 {path}", success, detail)
            if not success:
                all_passed = False
        except Exception as e:
            print_test(f"拦截 {path}", False, f"错误: {e}")
            all_passed = False

    return all_passed

def test_login() -> Optional[str]:
    """测试3: 登录获取Token"""
    print_section("测试3: 登录流程")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "password123"
            },
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")

            print_test(
                "登录成功",
                True,
                f"获取到Token: {token[:30]}..."
            )

            # 显示Token信息
            print(f"\n  Token类型: {data.get('token_type')}")
            print(f"  用户ID: {data.get('user', {}).get('id')}")
            print(f"  用户名: {data.get('user', {}).get('username')}")
            print(f"  真实姓名: {data.get('user', {}).get('real_name')}")

            return token
        else:
            print_test(
                "登录失败",
                False,
                f"状态码: {response.status_code} - {response.text[:200]}"
            )
            return None
    except Exception as e:
        print_test("登录失败", False, f"错误: {e}")
        return None

def test_authenticated_access(token: str):
    """测试4: 使用Token访问受保护资源"""
    print_section("测试4: Token访问受保护资源")

    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        ("/api/v1/projects", "GET", "项目列表"),
        ("/api/v1/users/me", "GET", "当前用户信息"),
        ("/api/v1/materials", "GET", "物料列表"),
    ]

    all_passed = True
    for path, method, description in test_cases:
        try:
            response = requests.request(
                method,
                f"{BASE_URL}{path}",
                headers=headers,
                timeout=3
            )

            success = response.status_code in [200, 404]  # 404也算正常（资源不存在）

            if success:
                detail = f"状态码: {response.status_code}"
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'data' in data:
                            detail += f" - 返回{len(data.get('data', []))}条记录"
                        elif isinstance(data, list):
                            detail += f" - 返回{len(data)}条记录"
                    except:
                        pass
            else:
                detail = f"期望200/404但得到{response.status_code} - {response.text[:100]}"

            print_test(f"{description} ({method} {path})", success, detail)
            if not success:
                all_passed = False
        except Exception as e:
            print_test(f"{description} ({method} {path})", False, f"错误: {e}")
            all_passed = False

    return all_passed

def test_invalid_token():
    """测试5: 无效Token应被拒绝"""
    print_section("测试5: 无效Token拒绝")

    invalid_tokens = [
        ("invalid.token.here", "格式错误的Token"),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U", "伪造的Token"),
    ]

    all_passed = True
    for token, description in invalid_tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/projects",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3
            )

            success = response.status_code == 401

            if success:
                data = response.json()
                detail = f"正确拦截 - {data.get('error_code')}"
            else:
                detail = f"期望401但得到{response.status_code}"

            print_test(description, success, detail)
            if not success:
                all_passed = False
        except Exception as e:
            print_test(description, False, f"错误: {e}")
            all_passed = False

    return all_passed

def main():
    """主测试流程"""
    print(f"\n{BLUE}{'='*70}")
    print("全局认证中间件 - 完整流程测试")
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

    # 测试1: 白名单
    results.append(("白名单路径访问", test_whitelist_access()))

    # 测试2: 未认证拦截
    results.append(("未认证访问拦截", test_unauthorized_access()))

    # 测试3: 登录
    token = test_login()
    results.append(("登录流程", token is not None))

    # 测试4: 认证访问
    if token:
        results.append(("Token访问", test_authenticated_access(token)))
    else:
        print(f"\n{YELLOW}⚠ 跳过Token访问测试（登录失败）{RESET}")
        results.append(("Token访问", False))

    # 测试5: 无效Token
    results.append(("无效Token拒绝", test_invalid_token()))

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

    # 下一步建议
    if passed == total:
        print(f"{BLUE}🎉 恭喜！全局认证中间件工作正常！{RESET}\n")
        print("下一步建议：")
        print("1. 为敏感操作添加细粒度权限（删除、审批等）")
        print("2. 根据业务需求调整白名单")
        print("3. 添加前端Token自动刷新机制")
        print("4. 建立权限审计机制")
    else:
        print(f"{YELLOW}请检查失败的测试并修复问题{RESET}\n")

if __name__ == "__main__":
    main()
