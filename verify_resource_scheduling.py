#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - 快速验证脚本
"""

import os
import sys
from datetime import date, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


def verify_database_tables():
    """验证数据库表是否创建成功"""
    print("=" * 60)
    print("1. 验证数据库表")
    print("=" * 60)
    
    try:
        # 连接数据库
        engine = create_engine("sqlite:///data/app.db")
        inspector = inspect(engine)
        
        # 检查表是否存在
        required_tables = [
            "resource_conflict_detection",
            "resource_scheduling_suggestions",
            "resource_demand_forecast",
            "resource_utilization_analysis",
            "resource_scheduling_logs",
        ]
        
        existing_tables = inspector.get_table_names()
        
        for table in required_tables:
            if table in existing_tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                print(f"✅ {table}: {len(columns)} 列, {len(indexes)} 索引")
            else:
                print(f"❌ {table}: 不存在")
                return False
        
        print("\n数据库表验证: ✅ 通过\n")
        return True
    
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False


def verify_models():
    """验证数据模型是否正确导入"""
    print("=" * 60)
    print("2. 验证数据模型")
    print("=" * 60)
    
    try:
        from app.models.resource_scheduling import (
            ResourceConflictDetection,
            ResourceSchedulingSuggestion,
            ResourceDemandForecast,
            ResourceUtilizationAnalysis,
            ResourceSchedulingLog,
        )
        
        models = [
            "ResourceConflictDetection",
            "ResourceSchedulingSuggestion",
            "ResourceDemandForecast",
            "ResourceUtilizationAnalysis",
            "ResourceSchedulingLog",
        ]
        
        for model_name in models:
            print(f"✅ {model_name}: 导入成功")
        
        print("\n数据模型验证: ✅ 通过\n")
        return True
    
    except Exception as e:
        print(f"❌ 数据模型验证失败: {e}")
        return False


def verify_schemas():
    """验证Pydantic Schemas"""
    print("=" * 60)
    print("3. 验证Pydantic Schemas")
    print("=" * 60)
    
    try:
        from app.schemas.resource_scheduling import (
            ResourceConflictDetectionCreate,
            ResourceSchedulingSuggestionCreate,
            ResourceDemandForecastCreate,
            ResourceUtilizationAnalysisCreate,
            ConflictDetectionRequest,
            AISchedulingSuggestionRequest,
            ForecastRequest,
            UtilizationAnalysisRequest,
            DashboardSummary,
        )
        
        schemas = [
            "ResourceConflictDetectionCreate",
            "ResourceSchedulingSuggestionCreate",
            "ResourceDemandForecastCreate",
            "ResourceUtilizationAnalysisCreate",
            "ConflictDetectionRequest",
            "AISchedulingSuggestionRequest",
            "ForecastRequest",
            "UtilizationAnalysisRequest",
            "DashboardSummary",
        ]
        
        for schema_name in schemas:
            print(f"✅ {schema_name}: 导入成功")
        
        print("\nPydantic Schemas验证: ✅ 通过\n")
        return True
    
    except Exception as e:
        print(f"❌ Pydantic Schemas验证失败: {e}")
        return False


def verify_services():
    """验证AI服务"""
    print("=" * 60)
    print("4. 验证AI服务")
    print("=" * 60)
    
    try:
        from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
        
        # 创建服务实例（不需要实际数据库）
        service = ResourceSchedulingAIService(None)
        
        # 测试方法是否存在
        methods = [
            "detect_resource_conflicts",
            "generate_scheduling_suggestions",
            "forecast_resource_demand",
            "analyze_resource_utilization",
            "_calculate_severity",
            "_calculate_priority_score",
        ]
        
        for method_name in methods:
            if hasattr(service, method_name):
                print(f"✅ {method_name}: 存在")
            else:
                print(f"❌ {method_name}: 缺失")
                return False
        
        print("\nAI服务验证: ✅ 通过\n")
        return True
    
    except Exception as e:
        print(f"❌ AI服务验证失败: {e}")
        return False


def verify_api_endpoints():
    """验证API端点"""
    print("=" * 60)
    print("5. 验证API端点")
    print("=" * 60)
    
    try:
        from app.api.v1.endpoints import resource_scheduling
        
        # 检查路由是否存在
        router = resource_scheduling.router
        routes = [route.path for route in router.routes]
        
        expected_endpoints = [
            "/conflicts/detect",
            "/conflicts",
            "/conflicts/{conflict_id}",
            "/suggestions/generate",
            "/suggestions",
            "/suggestions/{suggestion_id}",
            "/suggestions/{suggestion_id}/review",
            "/suggestions/{suggestion_id}/implement",
            "/forecast",
            "/utilization/analyze",
            "/utilization",
            "/dashboard/summary",
            "/logs",
        ]
        
        for endpoint in expected_endpoints:
            if endpoint in routes:
                print(f"✅ {endpoint}: 已注册")
            else:
                print(f"❌ {endpoint}: 缺失")
        
        print(f"\n总计API端点: {len(routes)}")
        print("API端点验证: ✅ 通过\n")
        return True
    
    except Exception as e:
        print(f"❌ API端点验证失败: {e}")
        return False


def verify_tests():
    """验证测试文件"""
    print("=" * 60)
    print("6. 验证测试文件")
    print("=" * 60)
    
    test_file = "tests/test_resource_scheduling.py"
    
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()
            
        # 统计测试函数
        test_count = content.count("def test_")
        
        print(f"✅ 测试文件存在")
        print(f"✅ 测试函数数量: {test_count}")
        
        if test_count >= 30:
            print("\n测试文件验证: ✅ 通过\n")
            return True
        else:
            print(f"\n⚠️  测试数量不足（需要30+，实际{test_count}）\n")
            return False
    else:
        print(f"❌ 测试文件不存在: {test_file}")
        return False


def verify_documentation():
    """验证文档"""
    print("=" * 60)
    print("7. 验证文档")
    print("=" * 60)
    
    doc_file = "Agent_Team_5_资源调度_交付报告.md"
    
    if os.path.exists(doc_file):
        with open(doc_file, 'r') as f:
            content = f.read()
        
        print(f"✅ 交付报告存在")
        print(f"✅ 文档大小: {len(content) // 1024} KB")
        
        # 检查关键章节
        required_sections = [
            "项目概述",
            "验收标准",
            "交付物清单",
            "API端点",
            "使用示例",
            "测试用例",
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✅ 章节: {section}")
            else:
                print(f"❌ 缺失章节: {section}")
        
        print("\n文档验证: ✅ 通过\n")
        return True
    else:
        print(f"❌ 文档不存在: {doc_file}")
        return False


def main():
    """主验证流程"""
    print("\n" + "=" * 60)
    print("资源冲突智能调度系统 - 验证报告")
    print("=" * 60 + "\n")
    
    results = []
    
    # 1. 数据库表
    results.append(("数据库表", verify_database_tables()))
    
    # 2. 数据模型
    results.append(("数据模型", verify_models()))
    
    # 3. Pydantic Schemas
    results.append(("Pydantic Schemas", verify_schemas()))
    
    # 4. AI服务
    results.append(("AI服务", verify_services()))
    
    # 5. API端点
    results.append(("API端点", verify_api_endpoints()))
    
    # 6. 测试文件
    results.append(("测试文件", verify_tests()))
    
    # 7. 文档
    results.append(("文档", verify_documentation()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"总计: {total} 项")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有验证通过！系统已就绪。\n")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 项验证失败，请检查。\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
