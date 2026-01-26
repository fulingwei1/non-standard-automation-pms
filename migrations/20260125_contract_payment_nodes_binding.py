#!/usr/bin/env python3
"""
数据库迁移：合同付款节点与里程碑自动绑定
执行日期：2026-01-25
"""

import sqlite3
import sys
from pathlib import Path


def migrate():
    """执行数据库迁移"""

    db_path = Path("data/app.db")
    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查现有表结构
        cursor.execute("PRAGMA table_info(contracts)")
        contract_columns = [col[1] for col in cursor.fetchall()]
        print(f"Contracts columns: {contract_columns}")

        # 检查payment_plans表是否存在，如果不存在则创建
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='payment_plans'"
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Creating payment_plans table...")
            cursor.execute("""
                CREATE TABLE payment_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    contract_id INTEGER,
                    node_name VARCHAR(100),
                    percentage NUMERIC(5,2),
                    amount NUMERIC(14,2),
                    due_date DATE,
                    milestone_id INTEGER,
                    status VARCHAR(20) DEFAULT 'PENDING',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (contract_id) REFERENCES contracts(id),
                    FOREIGN KEY (milestone_id) REFERENCES project_milestones(id)
                )
            """)
            print("✓ payment_plans table created")

        cursor.execute("PRAGMA table_info(payment_plans)")
        payment_plans_columns = [col[1] for col in cursor.fetchall()]
        print(f"Payment plans columns: {payment_plans_columns}")

        # 1. 添加payment_nodes, sow_text, acceptance_criteria字段到contracts表
        if "payment_nodes" not in contract_columns:
            print("Adding payment_nodes column to contracts table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN payment_nodes JSON")
            print("✓ payment_nodes column added")

        if "sow_text" not in contract_columns:
            print("Adding sow_text column to contracts table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN sow_text TEXT")
            print("✓ sow_text column added")

        if "acceptance_criteria" not in contract_columns:
            print("Adding acceptance_criteria column to contracts table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN acceptance_criteria JSON")
            print("✓ acceptance_criteria column added")

        # 创建索引（SQLite不支持USING GIN）
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='contracts' AND name='idx_contracts_payment_nodes'"
        )
        index_exists = cursor.fetchone()

        if not index_exists:
            print("Creating index on contracts.payment_nodes...")
            cursor.execute(
                "CREATE INDEX idx_contracts_payment_nodes ON contracts(payment_nodes)"
            )
            print("✓ Index created")

        # 2. 添加milestone_id字段到payment_plans表
        if "milestone_id" not in payment_plans_columns:
            print("Adding milestone_id column to payment_plans table...")
            cursor.execute("ALTER TABLE payment_plans ADD COLUMN milestone_id INTEGER")
            print("✓ milestone_id column added")

        # 创建索引（SQLite不支持USING GIN）
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='payment_plans' AND name='idx_payment_plans_milestone'"
        )
        index_exists = cursor.fetchone()

        if not index_exists:
            print("Creating index on payment_plans.milestone_id...")
            cursor.execute(
                "CREATE INDEX idx_payment_plans_milestone ON payment_plans(milestone_id)"
            )
            print("✓ Index created")

        # 2. 添加milestone_id字段到payment_plans表
        if "milestone_id" not in payment_plans_columns:
            print("Adding milestone_id column to payment_plans table...")
            cursor.execute("ALTER TABLE payment_plans ADD COLUMN milestone_id INTEGER")
            print("✓ milestone_id column added")

        # 创建索引
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='payment_plans' AND name='idx_payment_plans_milestone'"
        )
        index_exists = cursor.fetchone()

        if not index_exists:
            print("Creating index on payment_plans.milestone_id...")
            cursor.execute(
                "CREATE INDEX idx_payment_plans_milestone ON payment_plans(milestone_id)"
            )
            print("✓ Index created")

        conn.commit()
        print("\n=== Migration completed successfully ===")

        # 验证迁移结果
        print("\n=== Verifying migration ===")
        cursor.execute("PRAGMA table_info(contracts)")
        new_contract_columns = [col[1] for col in cursor.fetchall()]
        print(f"Contracts columns after migration: {new_contract_columns}")

        cursor.execute("PRAGMA table_info(payment_plans)")
        new_payment_plans_columns = [col[1] for col in cursor.fetchall()]
        print(f"Payment plans columns after migration: {new_payment_plans_columns}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
