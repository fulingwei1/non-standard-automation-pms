#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVM (Earned Value Management) 挣值管理模块 - 数据库迁移脚本

创建两个表：
1. earned_value_data - 挣值数据表（记录项目EVM基础数据）
2. earned_value_snapshots - EVM快照表（记录定期分析快照）

符合PMBOK标准的项目绩效测量体系
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings


def get_db_url():
    """获取数据库连接URL"""
    return settings.DATABASE_URL


def create_earned_value_tables():
    """创建EVM相关表"""
    
    # MySQL建表语句
    create_earned_value_data_mysql = """
    CREATE TABLE IF NOT EXISTS `earned_value_data` (
        `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
        `project_id` INT NOT NULL COMMENT '项目ID',
        `project_code` VARCHAR(50) COMMENT '项目编号（冗余，便于查询）',
        
        -- 数据周期
        `period_type` VARCHAR(20) NOT NULL DEFAULT 'MONTH' COMMENT '周期类型：WEEK（周）/MONTH（月）/QUARTER（季度）',
        `period_date` DATE NOT NULL COMMENT '周期截止日期（周末日期/月末日期/季末日期）',
        `period_label` VARCHAR(50) COMMENT '周期标签（如：2026-W07, 2026-02, 2026-Q1）',
        
        -- EVM核心三要素
        `planned_value` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000 COMMENT 'PV - 计划价值（Planned Value）',
        `earned_value` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000 COMMENT 'EV - 挣得价值（Earned Value）',
        `actual_cost` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000 COMMENT 'AC - 实际成本（Actual Cost）',
        
        -- 项目基准
        `budget_at_completion` DECIMAL(18, 4) NOT NULL COMMENT 'BAC - 完工预算（Budget at Completion）',
        
        -- 货币
        `currency` VARCHAR(10) NOT NULL DEFAULT 'CNY' COMMENT '币种（CNY/USD/EUR等）',
        
        -- 计算结果缓存
        `schedule_variance` DECIMAL(18, 4) COMMENT 'SV - 进度偏差（Schedule Variance = EV - PV）',
        `cost_variance` DECIMAL(18, 4) COMMENT 'CV - 成本偏差（Cost Variance = EV - AC）',
        `schedule_performance_index` DECIMAL(10, 6) COMMENT 'SPI - 进度绩效指数（Schedule Performance Index = EV / PV）',
        `cost_performance_index` DECIMAL(10, 6) COMMENT 'CPI - 成本绩效指数（Cost Performance Index = EV / AC）',
        `estimate_at_completion` DECIMAL(18, 4) COMMENT 'EAC - 完工估算（Estimate at Completion）',
        `estimate_to_complete` DECIMAL(18, 4) COMMENT 'ETC - 完工尚需估算（Estimate to Complete = EAC - AC）',
        `variance_at_completion` DECIMAL(18, 4) COMMENT 'VAC - 完工偏差（Variance at Completion = BAC - EAC）',
        `to_complete_performance_index` DECIMAL(10, 6) COMMENT 'TCPI - 完工尚需绩效指数（To-Complete Performance Index）',
        
        -- 完成百分比
        `planned_percent_complete` DECIMAL(5, 2) COMMENT '计划完成百分比（PV / BAC * 100）',
        `actual_percent_complete` DECIMAL(5, 2) COMMENT '实际完成百分比（EV / BAC * 100）',
        
        -- 数据来源与状态
        `data_source` VARCHAR(50) DEFAULT 'MANUAL' COMMENT '数据来源：MANUAL（手工录入）/SYSTEM（系统计算）/IMPORT（导入）',
        `is_baseline` BOOLEAN DEFAULT FALSE COMMENT '是否基准数据（项目启动时的基准）',
        `is_forecast` BOOLEAN DEFAULT FALSE COMMENT '是否预测数据（未来的预测值）',
        `is_verified` BOOLEAN DEFAULT FALSE COMMENT '是否已核实（PMO或财务核实）',
        
        -- 审核信息
        `verified_by` INT COMMENT '核实人ID',
        `verified_at` DATE COMMENT '核实时间',
        
        -- 备注
        `notes` TEXT COMMENT '备注说明',
        `calculation_notes` TEXT COMMENT '计算说明（记录特殊计算逻辑）',
        
        -- 创建人和时间戳
        `created_by` INT COMMENT '创建人ID',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        
        -- 外键约束
        FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
        FOREIGN KEY (`verified_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
        
        -- 唯一约束
        UNIQUE KEY `uq_evm_project_period` (`project_id`, `period_type`, `period_date`),
        
        -- 索引
        INDEX `idx_evm_project` (`project_id`),
        INDEX `idx_evm_period_type` (`period_type`),
        INDEX `idx_evm_period_date` (`period_date`),
        INDEX `idx_evm_project_date` (`project_id`, `period_date`),
        INDEX `idx_evm_verified` (`is_verified`),
        INDEX `idx_evm_baseline` (`is_baseline`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='挣值管理数据表（符合PMBOK标准）';
    """
    
    create_earned_value_snapshots_mysql = """
    CREATE TABLE IF NOT EXISTS `earned_value_snapshots` (
        `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
        
        -- 快照信息
        `snapshot_code` VARCHAR(100) UNIQUE NOT NULL COMMENT '快照编码（如：PRJ001-2026-02-EVM）',
        `snapshot_name` VARCHAR(200) COMMENT '快照名称',
        `snapshot_date` DATE NOT NULL COMMENT '快照日期',
        `snapshot_type` VARCHAR(20) DEFAULT 'MONTHLY' COMMENT '快照类型：WEEKLY/MONTHLY/QUARTERLY/MILESTONE',
        
        -- 项目关联
        `project_id` INT NOT NULL COMMENT '项目ID',
        `project_code` VARCHAR(50) COMMENT '项目编号（冗余）',
        
        -- 关联EVM数据
        `evm_data_id` INT COMMENT '关联的EVM数据ID',
        
        -- 快照数据
        `snapshot_data` TEXT COMMENT '快照数据（JSON格式，包含所有EVM指标和分析结果）',
        
        -- 分析结论
        `performance_status` VARCHAR(20) COMMENT '绩效状态：EXCELLENT/GOOD/WARNING/CRITICAL',
        `trend_direction` VARCHAR(20) COMMENT '趋势方向：IMPROVING/STABLE/DECLINING',
        `risk_level` VARCHAR(20) COMMENT '风险等级：LOW/MEDIUM/HIGH/CRITICAL',
        
        -- 关键发现和建议
        `key_findings` TEXT COMMENT '关键发现',
        `recommendations` TEXT COMMENT '改进建议',
        
        -- 创建和审核
        `created_by` INT COMMENT '创建人ID',
        `reviewed_by` INT COMMENT '审核人ID',
        `reviewed_at` DATE COMMENT '审核时间',
        
        -- 时间戳
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        
        -- 外键约束
        FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`evm_data_id`) REFERENCES `earned_value_data`(`id`) ON DELETE SET NULL,
        FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
        FOREIGN KEY (`reviewed_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
        
        -- 索引
        INDEX `idx_evm_snapshot_project` (`project_id`),
        INDEX `idx_evm_snapshot_date` (`snapshot_date`),
        INDEX `idx_evm_snapshot_type` (`snapshot_type`),
        INDEX `idx_evm_snapshot_status` (`performance_status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='EVM分析快照表';
    """
    
    # SQLite建表语句（去掉外键约束和ENGINE）
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
    
    CREATE INDEX IF NOT EXISTS idx_evm_project ON earned_value_data(project_id);
    CREATE INDEX IF NOT EXISTS idx_evm_period_type ON earned_value_data(period_type);
    CREATE INDEX IF NOT EXISTS idx_evm_period_date ON earned_value_data(period_date);
    CREATE INDEX IF NOT EXISTS idx_evm_project_date ON earned_value_data(project_id, period_date);
    CREATE INDEX IF NOT EXISTS idx_evm_verified ON earned_value_data(is_verified);
    CREATE INDEX IF NOT EXISTS idx_evm_baseline ON earned_value_data(is_baseline);
    """
    
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
    
    CREATE INDEX IF NOT EXISTS idx_evm_snapshot_project ON earned_value_snapshots(project_id);
    CREATE INDEX IF NOT EXISTS idx_evm_snapshot_date ON earned_value_snapshots(snapshot_date);
    CREATE INDEX IF NOT EXISTS idx_evm_snapshot_type ON earned_value_snapshots(snapshot_type);
    CREATE INDEX IF NOT EXISTS idx_evm_snapshot_status ON earned_value_snapshots(performance_status);
    """
    
    engine = create_engine(get_db_url())
    
    with engine.connect() as conn:
        # 检测数据库类型
        db_type = "sqlite" if "sqlite" in get_db_url().lower() else "mysql"
        
        print(f"🗄️  数据库类型: {db_type.upper()}")
        print("📊 开始创建EVM表...")
        
        try:
            if db_type == "sqlite":
                # SQLite
                print("  ├─ 创建 earned_value_data 表...")
                conn.execute(text(create_earned_value_data_sqlite))
                conn.commit()
                
                print("  └─ 创建 earned_value_snapshots 表...")
                conn.execute(text(create_earned_value_snapshots_sqlite))
                conn.commit()
            else:
                # MySQL
                print("  ├─ 创建 earned_value_data 表...")
                conn.execute(text(create_earned_value_data_mysql))
                conn.commit()
                
                print("  └─ 创建 earned_value_snapshots 表...")
                conn.execute(text(create_earned_value_snapshots_mysql))
                conn.commit()
            
            print("\n✅ EVM表创建成功！")
            print("\n📋 已创建表：")
            print("   1. earned_value_data - 挣值数据表")
            print("   2. earned_value_snapshots - EVM快照表")
            
        except Exception as e:
            print(f"\n❌ 创建表失败: {e}")
            raise


def rollback_earned_value_tables():
    """回滚：删除EVM相关表"""
    
    drop_tables = """
    DROP TABLE IF EXISTS earned_value_snapshots;
    DROP TABLE IF EXISTS earned_value_data;
    """
    
    engine = create_engine(get_db_url())
    
    with engine.connect() as conn:
        print("🔄 开始回滚EVM表...")
        try:
            conn.execute(text(drop_tables))
            conn.commit()
            print("✅ EVM表回滚成功！")
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            raise


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
