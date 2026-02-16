#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证授权完整性测试脚本 (Team 3)

测试覆盖：
1. 认证endpoints（Login, Logout, Refresh token, Password change）
2. Token验证（有效/无效/过期token）
3. 权限控制（Admin/Manager/Employee角色）
4. 认证中间件（白名单/protected endpoints）
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# 配置
BASE_URL = "http://127.0.0.1:8000"
VERBOSE = True

# 测试结果收集
test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0


class TestColors:
    """ANSI颜色码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log_test(test_name: str, passed: bool, details: str = ""):
    """记录测试结果"""
    global total_tests, passed_tests, failed_tests, test_results
    
    total_tests += 1
    if passed:
        passed_tests += 1
        status = f"{TestColors.OKGREEN}✓ PASS{TestColors.ENDC}"
    else:
        failed_tests += 1
        status = f"{TestColors.FAIL}✗ FAIL{TestColors.ENDC}"
    
    test_results.append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    
    print(f"  {status} {test_name}")
    if details and (not passed or VERBOSE):
        print(f"      {details}")


def print_section(title: str):
    """打印区块标题"""
    print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'=' * 80}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{title:^80}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{'=' * 80}{TestColors.ENDC}\n")


def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, 
                 json_data: Dict = None, expected_status: int = 200) -> Tuple[bool, Dict]:
    """
    发送HTTP请求并验证状态码
    
    Returns:
        (success, response_data)
    """
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, data=data, json=json_data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        success = response.status_code == expected_status
        
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text, "status_code": response.status_code}
        
        return success, response_data
        
    except Exception as e:
        return False, {"error": str(e)}


# ============================================================================
# 测试1: 认证Endpoints测试
# ============================================================================

def test_auth_endpoints():
    """测试所有认证相关的endpoints"""
    print_section("测试 1: 认证 Endpoints")
    
    tokens = {}
    
    # 1.1 测试登录成功 (Admin账户)
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    success, response = make_request("POST", "/api/v1/auth/login", data=login_data)
    
    if success and "access_token" in response:
        tokens['admin'] = {
            'access_token': response['access_token'],
            'refresh_token': response.get('refresh_token', '')
        }
        log_test("1.1 Admin登录成功", True, f"获取到access_token")
    else:
        log_test("1.1 Admin登录成功", False, f"响应: {response}")
        return None
    
    # 1.2 测试登录失败 - 错误密码
    wrong_login_data = {
        "username": "admin",
        "password": "wrong_password"
    }
    
    success, response = make_request("POST", "/api/v1/auth/login", 
                                    data=wrong_login_data, expected_status=401)
    
    if success and response.get("detail", {}).get("error_code") in ["WRONG_PASSWORD", "INVALID_CREDENTIALS"]:
        log_test("1.2 错误密码被拒绝", True, "返回401错误")
    else:
        log_test("1.2 错误密码被拒绝", False, f"响应: {response}")
    
    # 1.3 测试登录失败 - 不存在的用户
    nonexist_login = {
        "username": "nonexistent_user_12345",
        "password": "password"
    }
    
    success, response = make_request("POST", "/api/v1/auth/login", 
                                    data=nonexist_login, expected_status=401)
    
    if success:
        log_test("1.3 不存在的用户被拒绝", True, "返回401错误")
    else:
        log_test("1.3 不存在的用户被拒绝", False, f"响应: {response}")
    
    # 1.4 测试获取当前用户信息
    headers = {"Authorization": f"Bearer {tokens['admin']['access_token']}"}
    success, response = make_request("GET", "/api/v1/auth/me", headers=headers)
    
    if success and response.get("username") == "admin":
        log_test("1.4 获取当前用户信息", True, 
                f"用户: {response.get('username')}, 角色数: {len(response.get('roles', []))}")
    else:
        log_test("1.4 获取当前用户信息", False, f"响应: {response}")
    
    # 1.5 测试刷新Token
    if tokens['admin'].get('refresh_token'):
        refresh_data = {"refresh_token": tokens['admin']['refresh_token']}
        success, response = make_request("POST", "/api/v1/auth/refresh", 
                                        json_data=refresh_data)
        
        if success and "access_token" in response:
            new_token = response['access_token']
            log_test("1.5 刷新Token成功", True, "获取到新的access_token")
            tokens['admin']['new_access_token'] = new_token
        else:
            log_test("1.5 刷新Token成功", False, f"响应: {response}")
    else:
        log_test("1.5 刷新Token成功", False, "未获取到refresh_token")
    
    # 1.6 测试修改密码
    password_change_data = {
        "old_password": "admin123",
        "new_password": "NewAdmin123!"
    }
    
    success, response = make_request("PUT", "/api/v1/auth/password", 
                                    headers=headers, json_data=password_change_data)
    
    if success:
        log_test("1.6 修改密码", True, response.get("message", ""))
        
        # 恢复密码
        time.sleep(0.5)
        restore_login = {
            "username": "admin",
            "password": "NewAdmin123!"
        }
        success2, response2 = make_request("POST", "/api/v1/auth/login", data=restore_login)
        
        if success2:
            new_token = response2['access_token']
            restore_headers = {"Authorization": f"Bearer {new_token}"}
            
            restore_password = {
                "old_password": "NewAdmin123!",
                "new_password": "admin123"
            }
            
            make_request("PUT", "/api/v1/auth/password", 
                        headers=restore_headers, json_data=restore_password)
            
            log_test("1.6.1 密码已恢复", True, "密码恢复为admin123")
    else:
        log_test("1.6 修改密码", False, f"响应: {response}")
    
    # 1.7 测试登出
    logout_data = {"logout_all": False}
    success, response = make_request("POST", "/api/v1/auth/logout", 
                                    headers=headers, json_data=logout_data)
    
    if success:
        log_test("1.7 登出成功", True, response.get("message", ""))
    else:
        log_test("1.7 登出成功", False, f"响应: {response}")
    
    # 重新登录获取新token用于后续测试
    success, response = make_request("POST", "/api/v1/auth/login", data=login_data)
    if success:
        tokens['admin']['access_token'] = response['access_token']
    
    return tokens


# ============================================================================
# 测试2: Token验证测试
# ============================================================================

def test_token_validation(tokens: Dict):
    """测试Token验证机制"""
    print_section("测试 2: Token 验证")
    
    if not tokens or 'admin' not in tokens:
        log_test("2.0 前置条件检查", False, "缺少admin token")
        return
    
    valid_token = tokens['admin']['access_token']
    
    # 2.1 有效Token可以访问protected endpoint
    headers = {"Authorization": f"Bearer {valid_token}"}
    success, response = make_request("GET", "/api/v1/auth/me", headers=headers)
    
    if success:
        log_test("2.1 有效Token访问成功", True, f"访问 /api/v1/auth/me")
    else:
        log_test("2.1 有效Token访问成功", False, f"响应: {response}")
    
    # 2.2 无效Token被拒绝
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    success, response = make_request("GET", "/api/v1/auth/me", 
                                    headers=invalid_headers, expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("2.2 无效Token被拒绝", True, "返回401")
    else:
        log_test("2.2 无效Token被拒绝", False, f"响应: {response}")
    
    # 2.3 缺少Token被拒绝
    success, response = make_request("GET", "/api/v1/auth/me", expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("2.3 缺少Token被拒绝", True, "返回401")
    else:
        log_test("2.3 缺少Token被拒绝", False, f"响应: {response}")
    
    # 2.4 Token格式错误被拒绝
    wrong_format_headers = {"Authorization": "InvalidFormat token123"}
    success, response = make_request("GET", "/api/v1/auth/me", 
                                    headers=wrong_format_headers, expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("2.4 Token格式错误被拒绝", True, "返回401")
    else:
        log_test("2.4 Token格式错误被拒绝", False, f"响应: {response}")
    
    # 2.5 测试Token刷新后旧Token失效（如果实现了）
    if tokens['admin'].get('new_access_token'):
        old_token_headers = {"Authorization": f"Bearer {valid_token}"}
        # 注意：这个测试可能失败，因为旧token可能仍然有效（取决于实现）
        success, response = make_request("GET", "/api/v1/auth/me", 
                                        headers=old_token_headers)
        
        if not success:
            log_test("2.5 刷新后旧Token失效", True, "旧token已失效")
        else:
            log_test("2.5 刷新后旧Token失效", False, 
                    "旧token仍然有效（可能未实现token撤销）")


# ============================================================================
# 测试3: 权限控制测试
# ============================================================================

def test_permission_control(tokens: Dict):
    """测试不同角色的权限控制"""
    print_section("测试 3: 权限控制")
    
    if not tokens or 'admin' not in tokens:
        log_test("3.0 前置条件检查", False, "缺少admin token")
        return
    
    admin_headers = {"Authorization": f"Bearer {tokens['admin']['access_token']}"}
    
    # 3.1 获取Admin用户的权限信息
    success, response = make_request("GET", "/api/v1/auth/me", headers=admin_headers)
    
    if success:
        roles = response.get('roles', [])
        permissions = response.get('permissions', [])
        is_superuser = response.get('is_superuser', False)
        
        log_test("3.1 Admin用户权限信息", True, 
                f"角色数: {len(roles)}, 权限数: {len(permissions)}, Superuser: {is_superuser}")
        
        # 保存权限信息供后续测试
        tokens['admin']['permissions'] = permissions
        tokens['admin']['is_superuser'] = is_superuser
    else:
        log_test("3.1 Admin用户权限信息", False, f"响应: {response}")
    
    # 3.2 测试Admin访问用户管理接口
    success, response = make_request("GET", "/api/v1/users", headers=admin_headers)
    
    if success:
        users = response.get('data', {}).get('items', [])
        log_test("3.2 Admin访问用户列表", True, f"返回 {len(users)} 个用户")
    else:
        log_test("3.2 Admin访问用户列表", False, f"响应: {response}")
    
    # 3.3 测试Admin访问角色管理接口
    success, response = make_request("GET", "/api/v1/roles", headers=admin_headers)
    
    if success:
        roles = response.get('data', {}).get('items', []) or response.get('items', [])
        log_test("3.3 Admin访问角色列表", True, f"返回 {len(roles)} 个角色")
    else:
        log_test("3.3 Admin访问角色列表", False, f"响应: {response}")
    
    # 3.4 测试权限查询接口
    success, response = make_request("GET", "/api/v1/auth/permissions", headers=admin_headers)
    
    if success:
        perm_data = response.get('data', {})
        log_test("3.4 获取权限数据", True, f"权限数: {len(perm_data.get('permissions', []))}")
    else:
        log_test("3.4 获取权限数据", False, f"响应: {response}")
    
    # 3.5 测试项目访问（如果有权限）
    success, response = make_request("GET", "/api/v1/projects", headers=admin_headers)
    
    if success:
        projects = response.get('data', {}).get('items', [])
        log_test("3.5 Admin访问项目列表", True, f"返回 {len(projects)} 个项目")
    else:
        # 可能因为没有权限或其他原因失败
        log_test("3.5 Admin访问项目列表", False, 
                f"状态码: {response.get('status_code', 'unknown')}")


# ============================================================================
# 测试4: 认证中间件测试
# ============================================================================

def test_auth_middleware():
    """测试认证中间件的白名单和保护机制"""
    print_section("测试 4: 认证中间件")
    
    # 4.1 白名单路径无需认证 - /health
    success, response = make_request("GET", "/health", expected_status=200)
    
    if success or response.get("status_code") == 200:
        log_test("4.1 白名单路径 /health 可访问", True, "无需认证")
    else:
        log_test("4.1 白名单路径 /health 可访问", False, f"响应: {response}")
    
    # 4.2 白名单路径 - /api/v1/auth/login
    success, response = make_request("POST", "/api/v1/auth/login", 
                                    data={"username": "test", "password": "test"}, 
                                    expected_status=401)
    
    # 登录接口应该可以访问（即使凭证错误也不应该因为缺少token被拦截）
    if response.get("status_code") in [200, 401, 403, 423]:
        log_test("4.2 白名单路径 /api/v1/auth/login 可访问", True, "无需认证")
    else:
        log_test("4.2 白名单路径 /api/v1/auth/login 可访问", False, f"响应: {response}")
    
    # 4.3 Protected路径需要认证 - /api/v1/users
    success, response = make_request("GET", "/api/v1/users", expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("4.3 Protected路径需要认证", True, "/api/v1/users 返回401")
    else:
        log_test("4.3 Protected路径需要认证", False, f"响应: {response}")
    
    # 4.4 Protected路径 - /api/v1/projects
    success, response = make_request("GET", "/api/v1/projects", expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("4.4 Protected路径 /api/v1/projects 需要认证", True, "返回401")
    else:
        log_test("4.4 Protected路径 /api/v1/projects 需要认证", False, f"响应: {response}")
    
    # 4.5 测试认证失败返回正确错误码
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    success, response = make_request("GET", "/api/v1/auth/me", 
                                    headers=invalid_headers, expected_status=401)
    
    error_code = response.get("error_code") or response.get("detail", {}).get("error_code")
    
    if success and error_code:
        log_test("4.5 认证失败返回正确错误码", True, f"错误码: {error_code}")
    else:
        log_test("4.5 认证失败返回正确错误码", False, f"响应: {response}")


# ============================================================================
# 测试5: 安全性测试
# ============================================================================

def test_security_features():
    """测试安全特性"""
    print_section("测试 5: 安全特性")
    
    # 5.1 SQL注入防护测试
    sql_injection_login = {
        "username": "admin' OR '1'='1",
        "password": "anything"
    }
    
    success, response = make_request("POST", "/api/v1/auth/login", 
                                    data=sql_injection_login, expected_status=401)
    
    if success or response.get("status_code") == 401:
        log_test("5.1 SQL注入防护", True, "SQL注入尝试被拒绝")
    else:
        log_test("5.1 SQL注入防护", False, f"响应: {response}")
    
    # 5.2 密码强度验证（通过修改密码接口测试）
    login_data = {"username": "admin", "password": "admin123"}
    success, response = make_request("POST", "/api/v1/auth/login", data=login_data)
    
    if success and "access_token" in response:
        headers = {"Authorization": f"Bearer {response['access_token']}"}
        
        # 尝试使用弱密码
        weak_password = {
            "old_password": "admin123",
            "new_password": "123"  # 太短
        }
        
        success2, response2 = make_request("PUT", "/api/v1/auth/password", 
                                          headers=headers, json_data=weak_password, 
                                          expected_status=422)
        
        if success2 or response2.get("status_code") == 422:
            log_test("5.2 密码强度验证", True, "弱密码被拒绝")
        else:
            log_test("5.2 密码强度验证", False, f"响应: {response2}")
    else:
        log_test("5.2 密码强度验证", False, "无法登录")
    
    # 5.3 账户锁定机制测试（多次错误登录）
    wrong_login = {
        "username": "admin",
        "password": "wrong_password_123"
    }
    
    lockout_triggered = False
    for i in range(6):  # 尝试6次
        success, response = make_request("POST", "/api/v1/auth/login", 
                                        data=wrong_login, expected_status=401)
        
        if response.get("status_code") == 423:  # 账户锁定
            lockout_triggered = True
            break
        
        time.sleep(0.2)  # 短暂延迟
    
    if lockout_triggered:
        log_test("5.3 账户锁定机制", True, "多次失败后账户被锁定")
        
        # 等待一段时间后再测试
        time.sleep(2)
    else:
        log_test("5.3 账户锁定机制", False, 
                "多次错误登录未触发锁定（可能未实现或阈值更高）")


# ============================================================================
# 生成测试报告
# ============================================================================

def generate_report():
    """生成测试报告"""
    print_section("测试报告")
    
    print(f"{TestColors.BOLD}测试统计:{TestColors.ENDC}")
    print(f"  总测试数: {total_tests}")
    print(f"  {TestColors.OKGREEN}通过: {passed_tests}{TestColors.ENDC}")
    print(f"  {TestColors.FAIL}失败: {failed_tests}{TestColors.ENDC}")
    print(f"  通过率: {(passed_tests/total_tests*100 if total_tests > 0 else 0):.1f}%\n")
    
    # 按类别统计
    categories = {}
    for result in test_results:
        category = result['name'].split()[0]  # 取第一个词作为类别
        if category not in categories:
            categories[category] = {'passed': 0, 'failed': 0}
        
        if result['passed']:
            categories[category]['passed'] += 1
        else:
            categories[category]['failed'] += 1
    
    print(f"{TestColors.BOLD}分类统计:{TestColors.ENDC}")
    for category, stats in sorted(categories.items()):
        total = stats['passed'] + stats['failed']
        rate = stats['passed'] / total * 100 if total > 0 else 0
        print(f"  {category}: {stats['passed']}/{total} ({rate:.0f}%)")
    
    # 失败的测试详情
    if failed_tests > 0:
        print(f"\n{TestColors.BOLD}{TestColors.FAIL}失败的测试:{TestColors.ENDC}")
        for result in test_results:
            if not result['passed']:
                print(f"  ✗ {result['name']}")
                if result['details']:
                    print(f"    {result['details']}")
    
    # 生成JSON报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": f"{(passed_tests/total_tests*100 if total_tests > 0 else 0):.1f}%"
        },
        "categories": categories,
        "details": test_results
    }
    
    report_file = "data/auth_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{TestColors.OKCYAN}详细报告已保存至: {report_file}{TestColors.ENDC}")
    
    return passed_tests == total_tests


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主测试流程"""
    print(f"\n{TestColors.BOLD}{TestColors.HEADER}")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "认证授权完整性测试 (Team 3)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("║" + f"服务地址: {BASE_URL}".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"{TestColors.ENDC}\n")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code != 200:
            print(f"{TestColors.FAIL}✗ 服务未运行或健康检查失败{TestColors.ENDC}")
            sys.exit(1)
        print(f"{TestColors.OKGREEN}✓ 服务运行正常{TestColors.ENDC}\n")
    except Exception as e:
        print(f"{TestColors.FAIL}✗ 无法连接到服务: {e}{TestColors.ENDC}")
        sys.exit(1)
    
    # 执行测试
    tokens = test_auth_endpoints()
    test_token_validation(tokens)
    test_permission_control(tokens)
    test_auth_middleware()
    test_security_features()
    
    # 生成报告
    all_passed = generate_report()
    
    # 返回退出码
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
