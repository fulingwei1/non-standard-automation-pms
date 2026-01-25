#!/usr/bin/env python3
"""
数据库迁移：BOM自动创建采购订单
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
        # 验证bom_headers表
        cursor.execute("PRAGMA table_info(bom_headers)")
        bom_columns = [col[1] for col in cursor.fetchall()]
        print(f"BOM headers columns: {bom_columns}")

        # 1. 为bom_headers表添加source_type字段（如果不存在）
        if "source_type" not in bom_columns:
            print("Adding source_type column to bom_headers table...")
            cursor.execute("ALTER TABLE bom_headers ADD COLUMN source_type VARCHAR(20) DEFAULT 'MANUAL'")
            print("✓ source_type column added")

        # 2. 检查purchase_orders表是否存在，如果不存在则创建
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='purchase_orders'"
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Creating purchase_orders table if not exists...")
            cursor.execute("""
                CREATE TABLE purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    bom_id INTEGER,
                    source_type VARCHAR(20) DEFAULT 'MANUAL',
                    order_type VARCHAR(20) DEFAULT 'STANDARD',
                    status VARCHAR(20) DEFAULT 'DRAFT',
                    total_amount NUMERIC(14,2) DEFAULT 0,
                    tax_rate NUMERIC(5,2) DEFAULT 13,
                    tax_amount NUMERIC(14,2) DEFAULT 0,
                    amount_with_tax NUMERIC(14,2) DEFAULT 0,
                    due_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (supplier_id) REFERENCES vendors(id),
                    FOREIGN KEY (bom_id) REFERENCES bom_headers(id)
                )
            """)
            print("✓ purchase_orders table created")
        else:
            print("purchase_orders table already exists")
        
        # 为bom_headers表添加bom_id外键关联到purchase_orders（如果不存在）
        cursor.execute("PRAGMA table_info(bom_headers)")
        bom_columns = [col[1] for col in cursor.fetchall()]
        
        # 检查是否有bom_id外键字段
        bom_has_foreign_key = False
        for col in bom_columns:
            if "bom_id" in col[1].lower() and "purchase" in col[1].lower():
                bom_has_foreign_key = True
                break
        
        if not bom_has_foreign_key:
            # 需要添加外键约束比较复杂，使用Python添加
            print("Note: Foreign key constraint from bom_headers to purchase_orders needs to be added separately")

        # 3. 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_bom ON purchase_orders(bom_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_project ON purchase_orders(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_source_type ON purchase_orders(source_type)")

        conn.commit()
        print("\n=== Migration completed successfully ===")

        # 验证迁移结果
        print("\n=== Verifying migration ===")
        cursor.execute("PRAGMA table_info(bom_headers)")
        new_bom_columns = [col[1] for col in cursor.fetchall()]
        print(f"BOM headers columns after migration: {new_bom_columns}")

        cursor.execute("PRAGMA table_info(purchase_orders)")
        cursor.execute("SELECT COUNT(*) FROM purchase_orders")
        po_count = cursor.fetchone()[0]
        print(f"Purchase orders table exists with {po_count} records")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
