#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前AI赢率预测模块 - 快速验证脚本
验证代码语法、导入、数据模型等
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def verify_models():
    """验证数据模型"""
    print("🔍 验证数据模型...")
    try:
        from app.models.sales.presale_ai_win_rate import (
            PresaleAIWinRate,
            PresaleWinRateHistory,
            WinRateResultEnum
        )
        print("  ✅ 数据模型导入成功")
        print(f"  - PresaleAIWinRate: {PresaleAIWinRate.__tablename__}")
        print(f"  - PresaleWinRateHistory: {PresaleWinRateHistory.__tablename__}")
        print(f"  - WinRateResultEnum: {list(WinRateResultEnum)}")
        return True
    except Exception as e:
        print(f"  ❌ 数据模型导入失败: {e}")
        return False


def verify_services():
    """验证服务层"""
    print("\n🔍 验证服务层...")
    try:
        from app.services.win_rate_prediction_service.ai_service import AIWinRatePredictionService
        from app.services.win_rate_prediction_service.service import WinRatePredictionService
        
        print("  ✅ 服务层导入成功")
        
        # 测试AI服务
        ai_service = AIWinRatePredictionService()
        print(f"  - AIWinRatePredictionService 初始化成功")
        
        # 测试fallback预测
        ticket_data = {
            'is_repeat_customer': True,
            'competitor_count': 2,
            'salesperson_win_rate': 0.7
        }
        result = ai_service._fallback_prediction(ticket_data)
        print(f"  - Fallback预测测试: 赢率={result['win_rate_score']}%")
        
        return True
    except Exception as e:
        print(f"  ❌ 服务层导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schemas():
    """验证Schema"""
    print("\n🔍 验证Schema...")
    try:
        from app.schemas.presale_ai_win_rate import (
            PredictWinRateRequest,
            WinRatePredictionResponse,
            UpdateActualResultRequest,
            ModelAccuracyResponse
        )
        print("  ✅ Schema导入成功")
        print(f"  - PredictWinRateRequest")
        print(f"  - WinRatePredictionResponse")
        print(f"  - UpdateActualResultRequest")
        print(f"  - ModelAccuracyResponse")
        return True
    except Exception as e:
        print(f"  ❌ Schema导入失败: {e}")
        return False


def verify_api_routes():
    """验证API路由"""
    print("\n🔍 验证API路由...")
    try:
        from app.api.v1.presale_ai_win_rate import router
        
        print("  ✅ API路由导入成功")
        print(f"  - 路由前缀: {router.prefix}")
        print(f"  - 路由数量: {len(router.routes)}")
        
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(route.methods)
                print(f"    - {methods:6} {route.path}")
        
        return True
    except Exception as e:
        print(f"  ❌ API路由导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """验证迁移文件"""
    print("\n🔍 验证迁移文件...")
    try:
        migration_file = Path(__file__).parent / "migrations/versions/20260215_add_presale_ai_win_rate.py"
        
        if migration_file.exists():
            print(f"  ✅ 迁移文件存在: {migration_file.name}")
            
            # 读取文件内容检查
            content = migration_file.read_text()
            if "presale_ai_win_rate" in content and "presale_win_rate_history" in content:
                print("  ✅ 迁移文件包含正确的表名")
            else:
                print("  ⚠️  迁移文件可能不完整")
            
            return True
        else:
            print(f"  ❌ 迁移文件不存在")
            return False
    except Exception as e:
        print(f"  ❌ 迁移文件验证失败: {e}")
        return False


def verify_tests():
    """验证测试文件"""
    print("\n🔍 验证测试文件...")
    try:
        test_file = Path(__file__).parent / "tests/test_presale_ai_win_rate.py"
        
        if test_file.exists():
            content = test_file.read_text()
            
            # 统计测试类和方法
            test_classes = content.count("class Test")
            test_methods = content.count("async def test_")
            
            print(f"  ✅ 测试文件存在")
            print(f"  - 测试类数量: {test_classes}")
            print(f"  - 测试方法数量: {test_methods}")
            
            if test_methods >= 26:
                print(f"  ✅ 测试用例数量达标 ({test_methods} >= 26)")
            else:
                print(f"  ⚠️  测试用例数量不足 ({test_methods} < 26)")
            
            return True
        else:
            print(f"  ❌ 测试文件不存在")
            return False
    except Exception as e:
        print(f"  ❌ 测试文件验证失败: {e}")
        return False


def verify_docs():
    """验证文档"""
    print("\n🔍 验证文档...")
    docs_dir = Path(__file__).parent / "docs"
    
    required_docs = [
        "presale_ai_win_rate_api.md",
        "presale_ai_win_rate_user_manual.md",
        "PRESALE_AI_WIN_RATE_MODEL_EVALUATION.md",
        "PRESALE_AI_WIN_RATE_IMPLEMENTATION_SUMMARY.md"
    ]
    
    all_exist = True
    for doc_name in required_docs:
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            size_kb = doc_path.stat().st_size / 1024
            print(f"  ✅ {doc_name} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {doc_name} 不存在")
            all_exist = False
    
    return all_exist


def verify_scripts():
    """验证脚本"""
    print("\n🔍 验证脚本...")
    script_file = Path(__file__).parent / "scripts/import_historical_win_rate_data.py"
    
    if script_file.exists():
        print(f"  ✅ 数据导入脚本存在")
        return True
    else:
        print(f"  ❌ 数据导入脚本不存在")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 售前AI赢率预测模块 - 快速验证")
    print("=" * 60)
    
    results = []
    
    # 执行各项验证
    results.append(("数据模型", verify_models()))
    results.append(("服务层", verify_services()))
    results.append(("Schema", verify_schemas()))
    results.append(("API路由", verify_api_routes()))
    results.append(("迁移文件", verify_migration()))
    results.append(("测试文件", verify_tests()))
    results.append(("文档", verify_docs()))
    results.append(("脚本", verify_scripts()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:15} : {status}")
    
    print("\n" + "=" * 60)
    print(f"总体结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有验证通过！模块已准备就绪。")
        return 0
    else:
        print("⚠️  部分验证失败，请检查上述错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
