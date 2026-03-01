#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目API端点是否正常
"""

import os
import sys
from typing import Any, Dict

import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_login() -> str:
    """测试登录获取token"""
    print("\n" + "=" * 60)
    print("1. 测试登录...")
    print("=" * 60)

    login_url = f"{BASE_URL}/auth/login"
    login_data = {"username": "admin", "password": "admin123"}

    try:
        response = requests.post(login_url, data=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 登录成功")
            print(f"   Token长度: {len(token) if token else 0}")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {str(e)}")
        return None


def test_project_list(token: str, keyword: str = None) -> Dict[str, Any]:
    """测试项目列表API"""
    print("\n" + "=" * 60)
    print(f"2. 测试项目列表API" + (f" (关键词: {keyword})" if keyword else ""))
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/projects/"
    params = {"page": 1, "page_size": 20}
    if keyword:
        params["keyword"] = keyword

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            items = data.get("items", [])
            print(f"✅ 项目列表获取成功")
            print(f"   - 总数: {total}")
            print(f"   - 当前页项目数: {len(items)}")
            return data
        else:
            print(f"❌ 项目列表获取失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 项目列表异常: {str(e)}")
        return None


def test_project_detail(token: str, project_id: int) -> Dict[str, Any]:
    """测试项目详情API"""
    print("\n" + "=" * 60)
    print(f"3. 测试项目详情API (项目ID: {project_id})")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/projects/{project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 项目详情获取成功")
            print(f"   - 项目编码: {data.get('project_code')}")
            print(f"   - 项目名称: {data.get('project_name')}")
            print(f"   - 阶段: {data.get('stage')}")
            print(f"   - 健康度: {data.get('health')}")
            print(f"   - 进度: {data.get('progress_pct')}%")
            return data
        elif response.status_code == 404:
            print(f"❌ 项目不存在 (404)")
            return None
        elif response.status_code == 403:
            print(f"❌ 无权限访问 (403)")
            return None
        else:
            print(f"❌ 项目详情获取失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 项目详情异常: {str(e)}")
        return None


def test_project_by_code(token: str, project_code: str) -> Dict[str, Any]:
    """通过项目编码搜索项目"""
    print("\n" + "=" * 60)
    print(f"4. 通过项目编码搜索: {project_code}")
    print("=" * 60)

    list_data = test_project_list(token, keyword=project_code)
    if list_data and list_data.get("items"):
        items = list_data.get("items", [])
        for item in items:
            if item.get("project_code") == project_code:
                print(f"✅ 找到项目: {item.get('project_name')}")
                print(f"   - 项目ID: {item.get('id')}")
                print(f"   - 阶段: {item.get('stage')}")
                print(f"   - 健康度: {item.get('health')}")
                print(f"   - 进度: {item.get('progress_pct')}%")
                return item

        print(f"⚠️  搜索到 {len(items)} 个项目，但编码不完全匹配")
        return items[0] if items else None
    else:
        print(f"❌ 未找到项目编码: {project_code}")
        return None


def test_all_projects(token: str, project_codes: list):
    """测试所有指定项目"""
    print("\n" + "=" * 60)
    print("5. 逐个测试项目")
    print("=" * 60)

    results = {}

    for code in project_codes:
        print(f"\n--- 测试项目: {code} ---")

        # 通过编码搜索
        project = test_project_by_code(token, code)

        if project:
            project_id = project.get("id")
            # 测试详情API
            detail = test_project_detail(token, project_id)
            results[code] = {
                "found": True,
                "project_id": project_id,
                "list_api": project is not None,
                "detail_api": detail is not None,
            }
        else:
            results[code] = {
                "found": False,
                "project_id": None,
                "list_api": False,
                "detail_api": False,
            }

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for code, result in results.items():
        status = (
            "✅"
            if result["found"] and result["list_api"] and result["detail_api"]
            else "❌"
        )
        print(f"{status} {code}:")
        print(f"   - 列表API: {'✅' if result['list_api'] else '❌'}")
        print(f"   - 详情API: {'✅' if result['detail_api'] else '❌'}")
        if result["project_id"]:
            print(f"   - 项目ID: {result['project_id']}")
        print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("项目API测试")
    print("=" * 60)

    # 1. 登录
    token = test_login()
    if not token:
        print("\n❌ 无法获取token，测试终止")
        return

    # 2. 测试项目列表
    test_project_list(token)

    # 3. 测试指定项目
    project_codes = ["PJ250111", "PJ250110", "PJ250109"]
    test_all_projects(token, project_codes)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
