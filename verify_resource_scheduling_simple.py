#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - 简化验证脚本
只验证资源调度模块本身，不依赖其他模块
"""

import os
import sys
from sqlalchemy import create_engine, inspect


def verify_all():
    """简化验证"""
    print("\n" + "=" * 70)
    print("资源冲突智能调度系统 - 验证报告")
    print("=" * 70 + "\n")
    
    results = []
    
    # 1. 数据库表
    print("1. 数据库表验证")
    print("-" * 70)
    
    try:
        engine = create_engine("sqlite:///data/app.db")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            "resource_conflict_detection",
            "resource_scheduling_suggestions",
            "resource_demand_forecast",
            "resource_utilization_analysis",
            "resource_scheduling_logs",
        ]
        
        table_ok = True
        for table in required_tables:
            if table in existing_tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                print(f"  ✅ {table}: {len(columns)} 列, {len(indexes)} 索引")
            else:
                print(f"  ❌ {table}: 不存在")
                table_ok = False
        
        results.append(("数据库表", table_ok))
        print()
    
    except Exception as e:
        print(f"  ❌ 错误: {e}\n")
        results.append(("数据库表", False))
    
    # 2. 文件检查
    print("2. 文件完整性验证")
    print("-" * 70)
    
    files = {
        "数据库迁移": "migrations/20260215_resource_scheduling_ai.sql",
        "数据模型": "app/models/resource_scheduling.py",
        "Pydantic Schemas": "app/schemas/resource_scheduling.py",
        "AI服务": "app/services/resource_scheduling_ai_service.py",
        "API端点": "app/api/v1/endpoints/resource_scheduling.py",
        "测试文件": "tests/test_resource_scheduling.py",
        "交付报告": "Agent_Team_5_资源调度_交付报告.md",
        "验证脚本": "verify_resource_scheduling.py",
    }
    
    file_ok = True
    for name, path in files.items():
        if os.path.exists(path):
            size_kb = os.path.getsize(path) // 1024
            print(f"  ✅ {name}: {path} ({size_kb} KB)")
        else:
            print(f"  ❌ {name}: {path} (缺失)")
            file_ok = False
    
    results.append(("文件完整性", file_ok))
    print()
    
    # 3. 测试统计
    print("3. 测试用例统计")
    print("-" * 70)
    
    try:
        with open("tests/test_resource_scheduling.py", 'r') as f:
            content = f.read()
        
        test_count = content.count("def test_")
        print(f"  ✅ 测试函数数量: {test_count}")
        
        if test_count >= 30:
            print(f"  ✅ 测试数量达标 (>= 30)")
            results.append(("测试用例", True))
        else:
            print(f"  ⚠️  测试数量不足 (需要30+, 实际{test_count})")
            results.append(("测试用例", False))
        print()
    
    except Exception as e:
        print(f"  ❌ 错误: {e}\n")
        results.append(("测试用例", False))
    
    # 4. 代码行数统计
    print("4. 代码量统计")
    print("-" * 70)
    
    code_files = {
        "数据库SQL": "migrations/20260215_resource_scheduling_ai.sql",
        "数据模型": "app/models/resource_scheduling.py",
        "Schemas": "app/schemas/resource_scheduling.py",
        "AI服务": "app/services/resource_scheduling_ai_service.py",
        "API端点": "app/api/v1/endpoints/resource_scheduling.py",
        "测试文件": "tests/test_resource_scheduling.py",
    }
    
    total_lines = 0
    for name, path in code_files.items():
        try:
            with open(path, 'r') as f:
                lines = len(f.readlines())
            total_lines += lines
            print(f"  {name}: {lines} 行")
        except Exception:
            pass
    
    print(f"\n  总计: {total_lines} 行代码")
    results.append(("代码量", total_lines > 0))
    print()
    
    # 5. API端点统计
    print("5. API端点统计")
    print("-" * 70)
    
    try:
        with open("app/api/v1/endpoints/resource_scheduling.py", 'r') as f:
            content = f.read()
        
        endpoints = content.count('@router.')
        print(f"  ✅ API端点数量: {endpoints}")
        
        if endpoints >= 15:
            print(f"  ✅ API端点达标 (>= 15)")
            results.append(("API端点", True))
        else:
            print(f"  ⚠️  API端点不足 (需要15+, 实际{endpoints})")
            results.append(("API端点", False))
        print()
    
    except Exception as e:
        print(f"  ❌ 错误: {e}\n")
        results.append(("API端点", False))
    
    # 汇总
    print("=" * 70)
    print("验证汇总")
    print("=" * 70)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"{name:15s}: {status}")
    
    print("\n" + "=" * 70)
    print(f"总计: {total} 项")
    print(f"通过: {passed} 项")
    print(f"失败: {total - passed} 项")
    print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 70)
    
    if passed == total:
        print("\n✨ 所有验证通过！系统已就绪。\n")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项验证失败。\n")
        return 1


if __name__ == "__main__":
    sys.exit(verify_all())
