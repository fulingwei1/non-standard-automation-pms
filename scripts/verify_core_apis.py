#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心API验证脚本

验证所有核心endpoints是否可访问
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
from typing import Tuple

import requests

BASE_URL = "http://127.0.0.1:8000"


def get_admin_token() -> str:
    """获取admin账户的token，带重试"""
    print("🔐 正在获取admin token...")

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )

            if response.status_code == 429:
                print(
                    f"⚠️ Rate limit exceeded, waiting {retry_delay}s before retry {attempt + 1}/{max_retries}..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            if response.status_code != 200:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"响应: {response.text}")
                if attempt < max_retries - 1:
                    print(f"等待{retry_delay}s后重试...")
                    time.sleep(retry_delay)
                    continue
                raise Exception("无法获取admin token")

            data = response.json()
            token = data.get("access_token")

            if not token:
                raise Exception("响应中没有access_token")

            print(f"✅ 成功获取token: {token[:20]}...")
            return token

        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接失败: {e}")
            if attempt < max_retries - 1:
                print(f"等待{retry_delay}s后重试...")
                time.sleep(retry_delay)
            else:
                raise

    raise Exception("获取token失败")


def test_endpoint(method: str, path: str, token: str, description: str = "") -> Tuple[int, str]:
    """测试单个endpoint"""
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={}, timeout=10)
        else:
            return 0, f"不支持的方法: {method}"

        return response.status_code, ""

    except Exception as e:
        return 0, str(e)


def main():
    """主函数"""
    print("🚀 核心API验证开始...")
    print(f"Base URL: {BASE_URL}\n")

    # 获取token
    try:
        token = get_admin_token()
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        return

    print("\n" + "=" * 80)
    print("核心API验证")
    print("=" * 80 + "\n")

    # 定义核心endpoints
    core_endpoints = [
        # 认证模块
        ("GET", "/api/v1/auth/me", "获取当前用户信息"),
        ("GET", "/api/v1/auth/permissions", "获取当前用户权限"),
        # 用户管理
        ("GET", "/api/v1/users", "用户列表"),
        # 项目管理
        ("GET", "/api/v1/projects", "项目列表"),
        ("GET", "/api/v1/projects/dashboard", "项目仪表板"),
        # 生产管理
        ("GET", "/api/v1/production/dashboard", "生产仪表板"),
        ("GET", "/api/v1/production/workshops", "车间列表"),
        ("GET", "/api/v1/production/plans", "生产计划列表"),
        ("GET", "/api/v1/production/work-orders", "工单列表"),
        # 销售管理
        ("GET", "/api/v1/sales/leads", "销售线索列表"),
        ("GET", "/api/v1/sales/opportunities", "销售机会列表"),
        ("GET", "/api/v1/sales/quotations", "报价列表"),
    ]

    results = []
    success_count = 0
    fail_count = 0

    for method, path, description in core_endpoints:
        print(f"Testing {method} {path}")
        print(f"  描述: {description}")

        status_code, error = test_endpoint(method, path, token, description)

        if status_code == 0:
            print(f"  ❌ 错误: {error}\n")
            results.append((method, path, description, "ERROR", error))
            fail_count += 1
        elif 200 <= status_code < 300:
            print(f"  ✅ 成功: {status_code}\n")
            results.append((method, path, description, "SUCCESS", str(status_code)))
            success_count += 1
        elif status_code == 401 or status_code == 403:
            print(f"  🔒 需要权限: {status_code}\n")
            results.append((method, path, description, "PERMISSION", str(status_code)))
            fail_count += 1
        elif status_code == 404:
            print(f"  ❌ 未找到: {status_code}\n")
            results.append((method, path, description, "NOT_FOUND", str(status_code)))
            fail_count += 1
        elif status_code == 422:
            print(f"  ⚠️ 验证错误: {status_code}\n")
            results.append((method, path, description, "VALIDATION_ERROR", str(status_code)))
            fail_count += 1
        else:
            print(f"  ⚠️ 其他错误: {status_code}\n")
            results.append((method, path, description, "OTHER_ERROR", str(status_code)))
            fail_count += 1

        # 避免请求过快
        time.sleep(0.2)

    # 生成报告
    print("\n" + "=" * 80)
    print("验证结果摘要")
    print("=" * 80)
    print(f"总共: {len(core_endpoints)} 个")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"成功率: {success_count / len(core_endpoints) * 100:.1f}%")

    # 详细失败列表
    if fail_count > 0:
        print("\n" + "=" * 80)
        print("失败详情")
        print("=" * 80)

        for method, path, description, status, detail in results:
            if status != "SUCCESS":
                print(f"\n{method} {path}")
                print(f"  描述: {description}")
                print(f"  状态: {status}")
                print(f"  详情: {detail}")

    # 保存报告
    report_file = project_root / "data" / "core_api_verification.txt"
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("核心API验证报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"总共: {len(core_endpoints)} 个\n")
        f.write(f"成功: {success_count} 个\n")
        f.write(f"失败: {fail_count} 个\n")
        f.write(f"成功率: {success_count / len(core_endpoints) * 100:.1f}%\n\n")

        f.write("=" * 80 + "\n")
        f.write("详细结果\n")
        f.write("=" * 80 + "\n\n")

        for method, path, description, status, detail in results:
            f.write(f"{method} {path}\n")
            f.write(f"  描述: {description}\n")
            f.write(f"  状态: {status}\n")
            f.write(f"  详情: {detail}\n\n")

    print(f"\n📄 报告已保存到: {report_file}")

    # 返回状态码
    if fail_count > 0:
        sys.exit(1)
    else:
        print("\n✅ 所有核心API验证通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
