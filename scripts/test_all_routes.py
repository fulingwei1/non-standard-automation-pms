#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由全面测试脚本

基于提取的routes列表进行测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
from typing import Dict, List, Any
import time

BASE_URL = "http://127.0.0.1:8000"


def get_admin_token() -> str:
    """获取admin账户的token"""
    print("🔐 正在获取admin token...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"响应: {response.text}")
        raise Exception("无法获取admin token")
    
    data = response.json()
    token = data.get("access_token")
    
    if not token:
        raise Exception("响应中没有access_token")
    
    print(f"✅ 成功获取token: {token[:20]}...")
    return token


def load_routes() -> List[Dict[str, Any]]:
    """加载提取的routes"""
    routes_file = project_root / "data" / "extracted_routes.json"
    
    if not routes_file.exists():
        print(f"❌ 路由文件不存在: {routes_file}")
        print("请先运行 scripts/extract_routes.py 提取路由")
        return []
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        routes = json.load(f)
    
    print(f"✅ 加载了 {len(routes)} 个路由")
    return routes


def has_path_parameters(path: str) -> bool:
    """检查路径是否包含路径参数"""
    return "{" in path and "}" in path


def test_route(route: Dict[str, Any], token: str) -> Dict[str, Any]:
    """测试单个路由"""
    path = route["path"]
    method = route["method"]
    
    # 构建完整URL
    url = f"{BASE_URL}{path}"
    
    # 准备headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            # 跳过POST请求（大多数需要body）
            return {
                "status": "skipped",
                "reason": "POST需要request body"
            }
        elif method == "PUT":
            return {
                "status": "skipped",
                "reason": "PUT需要request body"
            }
        elif method == "DELETE":
            return {
                "status": "skipped",
                "reason": "DELETE是破坏性操作"
            }
        elif method == "PATCH":
            return {
                "status": "skipped",
                "reason": "PATCH需要request body"
            }
        else:
            return {
                "status": "skipped",
                "reason": f"不支持的方法: {method}"
            }
        
        result = {
            "status_code": response.status_code,
            "status": "success" if response.status_code < 400 else "error",
        }
        
        # 尝试解析JSON响应
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:200]
        
        return result
    
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "reason": "请求超时 (5s)"
        }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }


def categorize_results(test_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """分类测试结果"""
    categories = {
        "✅ 正常 (2xx)": [],
        "🔒 需要权限 (401/403)": [],
        "⚠️ 路径参数缺失": [],
        "❌ 404 Not Found": [],
        "❌ 422 Validation Error": [],
        "❌ 500 Server Error": [],
        "⏭️ 跳过测试": [],
        "❓ 其他错误": []
    }
    
    for result in test_results:
        route = result["route"]
        test_info = result["test_result"]
        
        # 跳过需要路径参数的路由
        if has_path_parameters(route["path"]):
            categories["⚠️ 路径参数缺失"].append(result)
            continue
        
        # 跳过测试的路由
        if test_info.get("status") == "skipped":
            categories["⏭️ 跳过测试"].append(result)
            continue
        
        # 根据状态码分类
        status_code = test_info.get("status_code")
        
        if status_code is None:
            categories["❓ 其他错误"].append(result)
        elif 200 <= status_code < 300:
            categories["✅ 正常 (2xx)"].append(result)
        elif status_code in [401, 403]:
            categories["🔒 需要权限 (401/403)"].append(result)
        elif status_code == 404:
            categories["❌ 404 Not Found"].append(result)
        elif status_code == 422:
            categories["❌ 422 Validation Error"].append(result)
        elif 500 <= status_code < 600:
            categories["❌ 500 Server Error"].append(result)
        else:
            categories["❓ 其他错误"].append(result)
    
    return categories


def generate_report(categories: Dict[str, List[Dict[str, Any]]], total_routes: int) -> str:
    """生成测试报告"""
    report = []
    report.append("=" * 80)
    report.append("API路由全面检查报告")
    report.append("=" * 80)
    report.append("")
    
    # 统计摘要
    total_tested = sum(len(results) for results in categories.values())
    report.append(f"总路由数: {total_routes}")
    report.append(f"测试路由数: {total_tested}")
    report.append("")
    
    for category, results in categories.items():
        count = len(results)
        percentage = (count / total_routes * 100) if total_routes > 0 else 0
        report.append(f"{category}: {count} ({percentage:.1f}%)")
    
    report.append("")
    report.append("=" * 80)
    
    # 详细结果 - 重点关注问题路由
    priority_categories = [
        "❌ 404 Not Found",
        "❌ 422 Validation Error",
        "❌ 500 Server Error",
        "❓ 其他错误"
    ]
    
    for category in priority_categories:
        results = categories.get(category, [])
        if not results:
            continue
        
        report.append(f"\n{category} ({len(results)} 个)")
        report.append("-" * 80)
        
        for result in results[:50]:  # 最多显示50个
            route = result["route"]
            test_info = result["test_result"]
            
            report.append(f"\n  {route['method']} {route['path']}")
            if route.get('tags'):
                report.append(f"  Tags: {', '.join(route['tags'])}")
            
            if test_info.get("status_code"):
                report.append(f"  Status: {test_info['status_code']}")
            
            if test_info.get("reason"):
                report.append(f"  Reason: {test_info['reason']}")
            
            if test_info.get("response") and isinstance(test_info["response"], dict):
                detail = test_info["response"].get("detail", "")
                if detail:
                    report.append(f"  Detail: {detail}")
        
        if len(results) > 50:
            report.append(f"\n  ... 还有 {len(results) - 50} 个类似结果")
    
    # 其他分类的简要信息
    report.append(f"\n\n其他分类统计:")
    report.append("-" * 80)
    
    for category in ["✅ 正常 (2xx)", "🔒 需要权限 (401/403)", "⚠️ 路径参数缺失", "⏭️ 跳过测试"]:
        results = categories.get(category, [])
        if results:
            report.append(f"\n{category}: {len(results)} 个")
            # 显示前5个作为示例
            for result in results[:5]:
                route = result["route"]
                report.append(f"  {route['method']} {route['path']}")
            if len(results) > 5:
                report.append(f"  ... 还有 {len(results) - 5} 个")
    
    return "\n".join(report)


def main():
    """主函数"""
    print("🚀 开始API路由全面测试...")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # 加载routes
    routes = load_routes()
    
    if not routes:
        return
    
    # 获取token
    try:
        token = get_admin_token()
    except Exception as e:
        print(f"❌ 获取token失败: {e}")
        return
    
    print(f"\n🧪 开始测试路由...")
    print(f"注意：只测试GET方法且不需要路径参数的endpoints")
    print()
    
    # 测试所有routes
    test_results = []
    tested_count = 0
    
    for idx, route in enumerate(routes, 1):
        method = route["method"]
        path = route["path"]
        
        # 只测试GET方法
        if method != "GET":
            test_results.append({
                "route": route,
                "test_result": {
                    "status": "skipped",
                    "reason": f"非GET方法: {method}"
                }
            })
            continue
        
        # 跳过需要路径参数的路由
        if has_path_parameters(path):
            test_results.append({
                "route": route,
                "test_result": {
                    "status": "skipped",
                    "reason": "需要路径参数"
                }
            })
            continue
        
        # 跳过某些特殊路径
        if path in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]:
            test_results.append({
                "route": route,
                "test_result": {
                    "status": "skipped",
                    "reason": "文档路径"
                }
            })
            continue
        
        print(f"[{idx}/{len(routes)}] Testing {method} {path}...", end=" ")
        
        test_result = test_route(route, token)
        test_results.append({
            "route": route,
            "test_result": test_result
        })
        
        tested_count += 1
        
        # 显示结果
        status_code = test_result.get("status_code")
        if status_code:
            if status_code < 300:
                print(f"✅ {status_code}")
            elif status_code < 400:
                print(f"⚠️ {status_code}")
            else:
                print(f"❌ {status_code}")
        else:
            print(f"⏭️ {test_result.get('reason', 'skipped')[:30]}")
        
        # 小延迟避免请求过快
        time.sleep(0.05)
    
    print(f"\n✅ 测试完成！实际测试: {tested_count} 个")
    
    # 分类结果
    categories = categorize_results(test_results)
    
    # 生成报告
    report = generate_report(categories, len(routes))
    
    # 保存报告
    report_file = project_root / "data" / "route_test_report.txt"
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(report, encoding="utf-8")
    
    print(f"\n📄 报告已保存到: {report_file}")
    
    # 同时保存JSON格式
    json_file = project_root / "data" / "route_test_results.json"
    json_data = {
        "total_routes": len(routes),
        "tested_routes": tested_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "categories": {
            category: [
                {
                    "method": r["route"]["method"],
                    "path": r["route"]["path"],
                    "tags": r["route"]["tags"],
                    "status_code": r["test_result"].get("status_code"),
                    "reason": r["test_result"].get("reason"),
                }
                for r in results
            ]
            for category, results in categories.items()
        }
    }
    
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📄 JSON结果已保存到: {json_file}")
    
    # 输出摘要到控制台
    print("\n" + "=" * 80)
    print("测试摘要")
    print("=" * 80)
    for category, results in categories.items():
        count = len(results)
        percentage = (count / len(routes) * 100) if len(routes) > 0 else 0
        print(f"{category}: {count} ({percentage:.1f}%)")
    
    # 重点提示问题路由
    problem_count = len(categories.get("❌ 404 Not Found", [])) + \
                    len(categories.get("❌ 422 Validation Error", [])) + \
                    len(categories.get("❌ 500 Server Error", []))
    
    if problem_count > 0:
        print(f"\n⚠️ 发现 {problem_count} 个问题路由需要修复！")
    else:
        print(f"\n✅ 所有测试的路由都正常！")


if __name__ == "__main__":
    main()
