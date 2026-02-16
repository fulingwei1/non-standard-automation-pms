#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产进度模块 - 数据库表测试

直接测试SQLite数据库中的表是否存在，不使用ORM
"""

import sqlite3
import sys

def test_tables():
    """测试15个生产模块表是否存在"""
    
    # 连接数据库
    db_path = "data/app.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 定义预期的表（8个Agent Teams的15个表）
    expected_tables = {
        "Team 2 - 排程优化": [
            "production_schedule",
            "resource_conflict",  # 实际表名
            "schedule_adjustment_log"
        ],
        "Team 3 - 质量管理": [
            "quality_inspection",
            "defect_analysis",  # 实际表名
            "rework_order",  # 实际表名
            "quality_alert_rule"
        ],
        "Team 4 - 产能分析": [
            "equipment_oee_record"
        ],
        "Team 5 - 物料跟踪": [
            "material_batch",
            "material_consumption",
            "material_alert",
            "material_alert_rule"
        ],
        "Team 6 - 异常处理": [
            "exception_handling_flow",
            "exception_knowledge",
            "exception_pdca"
        ]
    }
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = {row[0] for row in cursor.fetchall()}
    
    print("\n" + "🚀" * 30)
    print("生产进度模块 - 数据库表测试")
    print("="*60)
    
    results = {}
    total_expected = 0
    total_found = 0
    
    for team, tables in expected_tables.items():
        print(f"\n{team} ({len(tables)}个表):")
        found = []
        missing = []
        
        for table in tables:
            if table in all_tables:
                found.append(table)
                print(f"  ✓ {table}")
            else:
                missing.append(table)
                print(f"  ✗ {table} (不存在)")
        
        total_expected += len(tables)
        total_found += len(found)
        results[team] = {
            "found": len(found),
            "total": len(tables),
            "missing": missing
        }
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for team, result in results.items():
        found = result['found']
        total = result['total']
        percentage = found / total * 100 if total > 0 else 0
        status = "✅" if found == total else "⚠️ "
        print(f"{status} {team}: {found}/{total} ({percentage:.0f}%)")
        
        if result['missing']:
            for table in result['missing']:
                print(f"    缺失: {table}")
    
    print("\n" + "-"*60)
    print(f"总计: {total_found}/{total_expected} 个表创建成功")
    print(f"成功率: {total_found/total_expected*100:.1f}%")
    
    # 测试表结构（取一个表为例）
    if "production_schedule" in all_tables:
        print("\n" + "="*60)
        print("📋 表结构示例 (production_schedule)")
        print("="*60)
        cursor.execute("PRAGMA table_info(production_schedule)")
        columns = cursor.fetchall()
        print(f"共 {len(columns)} 个字段:")
        for col in columns[:10]:  # 显示前10个字段
            print(f"  - {col[1]} ({col[2]})")
        if len(columns) > 10:
            print(f"  ... (还有 {len(columns) - 10} 个字段)")
    
    conn.close()
    
    if total_found == total_expected:
        print("\n🎉 完美! 所有15个表都创建成功!")
        return 0
    else:
        print(f"\n⚠️  缺失 {total_expected - total_found} 个表")
        return 1


if __name__ == "__main__":
    sys.exit(test_tables())
