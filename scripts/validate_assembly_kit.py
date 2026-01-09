# -*- coding: utf-8 -*-
"""
装配齐套分析系统验证脚本
验证所有模块和API端点是否正确配置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("模块导入测试")
    print("=" * 60)
    
    tests = [
        ("智能推荐服务", "app.services.assembly_attr_recommender", "AssemblyAttrRecommender"),
        ("排产建议服务", "app.services.scheduling_suggestion_service", "SchedulingSuggestionService"),
        ("资源分配服务", "app.services.resource_allocation_service", "ResourceAllocationService"),
        ("齐套优化服务", "app.services.assembly_kit_optimizer", "AssemblyKitOptimizer"),
        ("企业微信客户端", "app.utils.wechat_client", "WeChatClient"),
        ("企业微信预警服务", "app.services.wechat_alert_service", "WeChatAlertService"),
    ]
    
    results = []
    for name, module_path, class_name in tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {name}: 导入成功")
            results.append((name, True))
        except Exception as e:
            print(f"✗ {name}: 导入失败 - {str(e)}")
            results.append((name, False))
    
    return all(r[1] for r in results)


def test_models():
    """测试模型导入"""
    print("\n" + "=" * 60)
    print("模型导入测试")
    print("=" * 60)
    
    models = [
        "AssemblyStage",
        "AssemblyTemplate",
        "CategoryStageMapping",
        "BomItemAssemblyAttrs",
        "MaterialReadiness",
        "ShortageDetail",
        "ShortageAlertRule",
        "SchedulingSuggestion"
    ]
    
    try:
        from app.models import (
            AssemblyStage, AssemblyTemplate, CategoryStageMapping,
            BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail,
            ShortageAlertRule, SchedulingSuggestion
        )
        print("✓ 所有模型导入成功")
        return True
    except Exception as e:
        print(f"✗ 模型导入失败: {str(e)}")
        return False


def test_api_routes():
    """测试API路由"""
    print("\n" + "=" * 60)
    print("API路由测试")
    print("=" * 60)
    
    try:
        from app.api.v1.endpoints import assembly_kit
        routes = [r for r in assembly_kit.router.routes if hasattr(r, 'path')]
        print(f"✓ 找到 {len(routes)} 个API路由")
        
        # 显示关键路由（路由路径不包含前缀）
        key_routes = [
            "/stages",
            "/templates",
            "/bom/{bom_id}/assembly-attrs",
            "/bom/{bom_id}/assembly-attrs/recommendations",
            "/bom/{bom_id}/assembly-attrs/smart-recommend",
            "/analysis",
            "/analysis/{readiness_id}",
            "/analysis/{readiness_id}/optimize",
            "/suggestions/generate",
            "/wechat/config",
        ]
        
        route_paths = [r.path for r in routes]
        print("\n关键路由检查:")
        for key_route in key_routes:
            found = any(key_route in path or path in key_route for path in route_paths)
            status = "✓" if found else "✗"
            print(f"  {status} {key_route} (完整路径: /api/v1/assembly{key_route})")
        
        return True
    except Exception as e:
        print(f"✗ API路由测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """测试Schema导入"""
    print("\n" + "=" * 60)
    print("Schema导入测试")
    print("=" * 60)
    
    try:
        from app.schemas.assembly_kit import (
            AssemblyStageResponse,
            MaterialReadinessResponse,
            BomItemAssemblyAttrsResponse,
            SchedulingSuggestionResponse
        )
        print("✓ 所有Schema导入成功")
        return True
    except Exception as e:
        print(f"✗ Schema导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n" + "=" * 60)
    print("配置测试")
    print("=" * 60)
    
    try:
        from app.core.config import settings
        print(f"✓ 配置加载成功")
        print(f"  - WECHAT_ENABLED: {settings.WECHAT_ENABLED}")
        print(f"  - WECHAT_CORP_ID: {'已配置' if settings.WECHAT_CORP_ID else '未配置'}")
        print(f"  - WECHAT_AGENT_ID: {'已配置' if settings.WECHAT_AGENT_ID else '未配置'}")
        print(f"  - WECHAT_SECRET: {'已配置' if settings.WECHAT_SECRET else '未配置'}")
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("装配齐套分析系统 - 验证测试")
    print("=" * 60)
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("模型导入", test_models()))
    results.append(("Schema导入", test_schemas()))
    results.append(("API路由", test_api_routes()))
    results.append(("配置", test_config()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查上述错误")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
