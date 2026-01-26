#!/usr/bin/env python3
"""
数据库迁移：验收自动触发开票
执行日期：2026-01-25
"""

import sqlite3
import os
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
        # 验证contracts表
        cursor.execute("PRAGMA table_info(contracts)")
        contract_columns = [col[1] for col in cursor.fetchall()]
        print(f"Contracts columns: {contract_columns}")

        # 验证acceptance_orders表
        cursor.execute("PRAGMA table_info(acceptance_orders)")
        acceptance_columns = [col[1] for col in cursor.fetchall()]
        print(f"Acceptance orders columns: {acceptance_columns}")

        # 1. 为contracts表添加acceptance_order_id字段（如果不存在）
        if "acceptance_order_id" not in contract_columns:
            print("Adding acceptance_order_id column to contracts table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN acceptance_order_id INTEGER")
            print("✓ acceptance_order_id column added")

        # 为invoices表添加acceptance_order_id字段（如果不存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND tbl_name='invoices' AND name='idx_invoices_acceptance_order_id'")
        invoices_table_exists = cursor.fetchone()

        if not invoices_table_exists:
            print("Creating invoices table if not exists...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_code VARCHAR(50) UNIQUE NOT NULL,
                    project_id INTEGER,
                    project_id INTEGER,
                    contract_id INTEGER,
                    acceptance_order_id INTEGER,
                    invoice_type VARCHAR(20) DEFAULT 'MANUAL',
                    total_amount NUMERIC(14, 2),
                    tax_amount NUMERIC(14, 2) DEFAULT 0,
                    amount_with_tax NUMERIC(14, 2) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'DRAFT',
                    due_date DATE,
                    issued_date DATE,
                    paid_amount NUMERIC(14, 2) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ invoices table created")

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_acceptance_order_id ON invoices(acceptance_order_id)")

        # 2. 检查invoices表是否有acceptance_order_id字段
        cursor.execute("PRAGMA table_info(invoices)")
        invoice_columns = [col[1] for col in cursor.fetchall()]
        print(f"Invoices columns: {invoice_columns}")

        conn.commit()
        print("\n=== Migration completed successfully ===")

        # 验证结果
        print("\n=== Verifying migration ===")
        cursor.execute("PRAGMA table_info(contracts)")
        new_contract_columns = [col[1] for col in cursor.fetchall()]
        print(f"Contracts columns after migration: {new_contract_columns}")

        cursor.execute("PRAGMA table_info(invoices)")
        new_invoice_columns = [col[1] for col in cursor.fetchall()]
        print(f"Invoices columns after migration: {new_invoice_columns}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
