# -*- coding: utf-8 -*-
"""
装配齐套分析系统API测试脚本
测试所有API端点的基本功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_assembly_stages():
    """测试装配阶段API"""
    print("\n=== 测试装配阶段API ===")
    response = client.get("/api/v1/assembly/stages")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✓ 获取装配阶段列表成功")
    else:
        print(f"✗ 失败: {response.text}")

def test_assembly_templates():
    """测试装配模板API"""
    print("\n=== 测试装配模板API ===")
    response = client.get("/api/v1/assembly/templates")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✓ 获取装配模板列表成功")
    else:
        print(f"✗ 失败: {response.text}")

def test_category_mappings():
    """测试物料分类映射API"""
    print("\n=== 测试物料分类映射API ===")
    response = client.get("/api/v1/assembly/category-mappings")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✓ 获取物料分类映射列表成功")
    else:
        print(f"✗ 失败: {response.text}")

def test_alert_rules():
    """测试预警规则API"""
    print("\n=== 测试预警规则API ===")
    response = client.get("/api/v1/assembly/alert-rules")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✓ 获取预警规则列表成功")
    else:
        print(f"✗ 失败: {response.text}")

def test_wechat_config():
    """测试企业微信配置API"""
    print("\n=== 测试企业微信配置API ===")
    response = client.get("/api/v1/assembly/wechat/config")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 获取企业微信配置成功: {data.get('data', {})}")
    else:
        print(f"✗ 失败: {response.text}")

def test_api_routes():
    """测试API路由是否注册"""
    print("\n=== 测试API路由注册 ===")
    routes = [route.path for route in app.routes]
    assembly_routes = [r for r in routes if '/assembly' in r]
    print(f"找到 {len(assembly_routes)} 个装配相关路由:")
    for route in assembly_routes[:10]:  # 只显示前10个
        print(f"  - {route}")
    if len(assembly_routes) > 10:
        print(f"  ... 还有 {len(assembly_routes) - 10} 个路由")
    print("✓ API路由检查完成")

if __name__ == "__main__":
    print("=" * 60)
    print("装配齐套分析系统API测试")
    print("=" * 60)
    
    try:
        test_api_routes()
        test_assembly_stages()
        test_assembly_templates()
        test_category_mappings()
        test_alert_rules()
        test_wechat_config()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
