#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVM (Earned Value Management) 挣值管理模块 - 数据库迁移脚本（简化版）

创建两个表：
1. earned_value_data - 挣值数据表（记录项目EVM基础数据）
2. earned_value_snapshots - EVM快照表（记录定期分析快照）

符合PMBOK标准的项目绩效测量体系
"""

import sqlite3
from pathlib import Path


def create_earned_value_tables():
    """创建EVM相关表"""
    
    # SQLite建表语句
    create_earned_value_data_sqlite = """
    CREATE TABLE IF NOT EXISTS earned_value_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        project_code VARCHAR(50),
        period_type VARCHAR(20) NOT NULL DEFAULT 'MONTH',
        period_date DATE NOT NULL,
        period_label VARCHAR(50),
        planned_value DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
        earned_value DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
        actual_cost DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
        budget_at_completion DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
        schedule_variance DECIMAL(18, 4),
        cost_variance DECIMAL(18, 4),
        schedule_performance_index DECIMAL(10, 6),
        cost_performance_index DECIMAL(10, 6),
        estimate_at_completion DECIMAL(18, 4),
        estimate_to_complete DECIMAL(18, 4),
        variance_at_completion DECIMAL(18, 4),
        to_complete_performance_index DECIMAL(10, 6),
        planned_percent_complete DECIMAL(5, 2),
        actual_percent_complete DECIMAL(5, 2),
        data_source VARCHAR(50) DEFAULT 'MANUAL',
        is_baseline BOOLEAN DEFAULT 0,
        is_forecast BOOLEAN DEFAULT 0,
        is_verified BOOLEAN DEFAULT 0,
        verified_by INTEGER,
        verified_at DATE,
        notes TEXT,
        calculation_notes TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(project_id, period_type, period_date)
    );
    """
    
    create_indexes_evm_data = [
        "CREATE INDEX IF NOT EXISTS idx_evm_project ON earned_value_data(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_evm_period_type ON earned_value_data(period_type);",
        "CREATE INDEX IF NOT EXISTS idx_evm_period_date ON earned_value_data(period_date);",
        "CREATE INDEX IF NOT EXISTS idx_evm_project_date ON earned_value_data(project_id, period_date);",
        "CREATE INDEX IF NOT EXISTS idx_evm_verified ON earned_value_data(is_verified);",
        "CREATE INDEX IF NOT EXISTS idx_evm_baseline ON earned_value_data(is_baseline);"
    ]
    
    create_earned_value_snapshots_sqlite = """
    CREATE TABLE IF NOT EXISTS earned_value_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_code VARCHAR(100) UNIQUE NOT NULL,
        snapshot_name VARCHAR(200),
        snapshot_date DATE NOT NULL,
        snapshot_type VARCHAR(20) DEFAULT 'MONTHLY',
        project_id INTEGER NOT NULL,
        project_code VARCHAR(50),
        evm_data_id INTEGER,
        snapshot_data TEXT,
        performance_status VARCHAR(20),
        trend_direction VARCHAR(20),
        risk_level VARCHAR(20),
        key_findings TEXT,
        recommendations TEXT,
        created_by INTEGER,
        reviewed_by INTEGER,
        reviewed_at DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_indexes_snapshots = [
        "CREATE INDEX IF NOT EXISTS idx_evm_snapshot_project ON earned_value_snapshots(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_evm_snapshot_date ON earned_value_snapshots(snapshot_date);",
        "CREATE INDEX IF NOT EXISTS idx_evm_snapshot_type ON earned_value_snapshots(snapshot_type);",
        "CREATE INDEX IF NOT EXISTS idx_evm_snapshot_status ON earned_value_snapshots(performance_status);"
    ]
    
    # 连接到SQLite数据库
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"🗄️  数据库路径: {db_path}")
    print("📊 开始创建EVM表...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 创建earned_value_data表
        print("  ├─ 创建 earned_value_data 表...")
        cursor.execute(create_earned_value_data_sqlite)
        
        # 创建索引
        print("  ├─ 创建索引...")
        for index_sql in create_indexes_evm_data:
            cursor.execute(index_sql)
        
        # 创建earned_value_snapshots表
        print("  ├─ 创建 earned_value_snapshots 表...")
        cursor.execute(create_earned_value_snapshots_sqlite)
        
        # 创建索引
        print("  └─ 创建索引...")
        for index_sql in create_indexes_snapshots:
            cursor.execute(index_sql)
        
        conn.commit()
        
        print("\n✅ EVM表创建成功！")
        print("\n📋 已创建表：")
        print("   1. earned_value_data - 挣值数据表")
        print("   2. earned_value_snapshots - EVM快照表")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'earned_value%';")
        tables = cursor.fetchall()
        print("\n🔍 验证结果：")
        for table in tables:
            print(f"   ✓ {table[0]}")
        
    except Exception as e:
        print(f"\n❌ 创建表失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def rollback_earned_value_tables():
    """回滚：删除EVM相关表"""
    
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print("🔄 开始回滚EVM表...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS earned_value_snapshots;")
        cursor.execute("DROP TABLE IF EXISTS earned_value_data;")
        conn.commit()
        print("✅ EVM表回滚成功！")
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EVM数据库迁移脚本")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移（删除表）"
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_earned_value_tables()
    else:
        create_earned_value_tables()
