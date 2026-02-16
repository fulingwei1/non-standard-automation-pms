#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购库存系统 - 数据库表测试

测试7个Agent Teams交付的13个表：
- Team 1: 智能采购管理 (4表)
- Team 2: 物料全流程跟踪 (6表)
- Team 3: 智能缺料预警 (3表)
"""

import sqlite3
import sys

def test_tables():
    """测试13个采购库存系统表是否存在"""
    
    # 连接数据库
    db_path = "data/app.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 定义预期的表（7个Agent Teams的13个表）
    expected_tables = {
        "Team 1 - 智能采购管理": [
            "purchase_suggestions",
            "supplier_quotations",
            "supplier_performances",
            "purchase_order_trackings"
        ],
        "Team 2 - 物料库存跟踪": [
            "material_transaction",
            "material_stock",
            "material_reservation",
            "stock_count_task",
            "stock_count_detail",
            "stock_adjustment"
        ],
        "Team 3 - 智能缺料预警": [
            "shortage_alerts_enhanced",
            "shortage_handling_plans",
            "material_demand_forecasts"
        ]
    }
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = {row[0] for row in cursor.fetchall()}
    
    print("\n" + "🚀" * 30)
    print("采购库存系统 - 数据库表测试")
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
        status = "✅" if found == total else "⚠️ " if found > 0 else "❌"
        print(f"{status} {team}: {found}/{total} ({percentage:.0f}%)")
        
        if result['missing']:
            for table in result['missing']:
                print(f"    缺失: {table}")
    
    print("\n" + "-"*60)
    print(f"总计: {total_found}/{total_expected} 个表创建成功")
    print(f"成功率: {total_found/total_expected*100:.1f}%")
    
    # 测试表结构（取一个表为例）
    if "purchase_suggestions" in all_tables:
        print("\n" + "="*60)
        print("📋 表结构示例 (purchase_suggestions)")
        print("="*60)
        cursor.execute("PRAGMA table_info(purchase_suggestions)")
        columns = cursor.fetchall()
        print(f"共 {len(columns)} 个字段:")
        for col in columns[:10]:  # 显示前10个字段
            print(f"  - {col[1]} ({col[2]})")
        if len(columns) > 10:
            print(f"  ... (还有 {len(columns) - 10} 个字段)")
    
    # 分析缺失表的原因
    if total_found < total_expected:
        print("\n" + "="*60)
        print("❌ 缺失表分析")
        print("="*60)
        
        missing_tables = []
        for team, result in results.items():
            if result['missing']:
                missing_tables.extend(result['missing'])
        
        print(f"\n需要创建的表 ({len(missing_tables)}个):")
        for table in missing_tables:
            print(f"  - {table}")
        
        print("\n可能原因:")
        print("  1. 外键约束问题 (tenant_id, work_order_id等)")
        print("  2. 表名不匹配 (模型定义 vs 迁移文件)")
        print("  3. 迁移文件未执行")
    
    conn.close()
    
    if total_found == total_expected:
        print("\n🎉 完美! 所有13个表都创建成功!")
        return 0
    else:
        print(f"\n⚠️  缺失 {total_expected - total_found} 个表，需要创建")
        return 1


if __name__ == "__main__":
    sys.exit(test_tables())
