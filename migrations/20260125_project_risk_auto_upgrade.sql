#!/usr/bin/env python3
"""
数据库迁移：项目风险自动升级
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
        # 验证projects表
        cursor.execute("PRAGMA table_info(projects)")
        project_columns = [col[1] for col in cursor.fetchall()]
        print(f"Projects columns: {project_columns}")

        # 1. 为projects表添加risk_level和risk_factors字段（如果不存在）
        if "risk_level" not in project_columns:
            print("Adding risk_level column to projects table...")
            cursor.execute("ALTER TABLE projects ADD COLUMN risk_level VARCHAR(20) DEFAULT 'LOW'")
            print("✓ risk_level column added")

        if "risk_factors" not in project_columns:
            print("Adding risk_factors column to projects table...")
            cursor.execute("ALTER TABLE projects ADD COLUMN risk_factors JSON")
            print("✓ risk_factors column added")

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_risk_level ON projects(risk_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_health_status ON projects(health_status)")

        conn.commit()
        print("\n=== Migration completed successfully ===")

        # 验证迁移结果
        print("\n=== Verifying migration ===")
        cursor.execute("PRAGMA table_info(projects)")
        new_project_columns = [col[1] for col in cursor.fetchall()]
        print(f"Projects columns after migration: {new_project_columns}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
