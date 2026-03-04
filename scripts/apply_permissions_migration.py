#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用权限表结构升级迁移脚本
安全地添加缺失字段，避免重复添加导致的错误
"""

import os
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns


def apply_sqlite_migration(db_path):
    """应用 SQLite 迁移"""
    print(f"正在应用 SQLite 迁移到: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")

        # 检查并添加字段
        changes_made = False

        # 1. 添加 resource 字段
        if not check_column_exists(cursor, "permissions", "resource"):
            print("  ➕ 添加 resource 字段...")
            cursor.execute("ALTER TABLE permissions ADD COLUMN resource VARCHAR(50)")
            changes_made = True
        else:
            print("  ✓ resource 字段已存在")

        # 2. 添加 description 字段
        if not check_column_exists(cursor, "permissions", "description"):
            print("  ➕ 添加 description 字段...")
            cursor.execute("ALTER TABLE permissions ADD COLUMN description TEXT")
            changes_made = True
        else:
            print("  ✓ description 字段已存在")

        # 3. 添加 is_active 字段
        if not check_column_exists(cursor, "permissions", "is_active"):
            print("  ➕ 添加 is_active 字段...")
            cursor.execute("ALTER TABLE permissions ADD COLUMN is_active BOOLEAN DEFAULT 1")
            changes_made = True
        else:
            print("  ✓ is_active 字段已存在")

        # 4. 添加 created_at 字段
        if not check_column_exists(cursor, "permissions", "created_at"):
            print("  ➕ 添加 created_at 字段...")
            # SQLite 不支持在 ADD COLUMN 时使用 CURRENT_TIMESTAMP，先添加字段，后更新
            cursor.execute("ALTER TABLE permissions ADD COLUMN created_at DATETIME")
            changes_made = True
        else:
            print("  ✓ created_at 字段已存在")

        # 5. 添加 updated_at 字段
        if not check_column_exists(cursor, "permissions", "updated_at"):
            print("  ➕ 添加 updated_at 字段...")
            # SQLite 不支持在 ADD COLUMN 时使用 CURRENT_TIMESTAMP，先添加字段，后更新
            cursor.execute("ALTER TABLE permissions ADD COLUMN updated_at DATETIME")
            changes_made = True
        else:
            print("  ✓ updated_at 字段已存在")

        if not changes_made:
            print("  ℹ️  所有字段已存在，无需更新")
            return True

        # 更新现有数据的默认值
        print("\n  更新现有数据...")

        # 设置 is_active 默认值
        cursor.execute("UPDATE permissions SET is_active = 1 WHERE is_active IS NULL")
        active_count = cursor.rowcount
        if active_count > 0:
            print(f"    ✓ 更新了 {active_count} 条记录的 is_active 字段")

        # 设置 created_at 默认值
        cursor.execute(
            "UPDATE permissions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )
        created_count = cursor.rowcount
        if created_count > 0:
            print(f"    ✓ 更新了 {created_count} 条记录的 created_at 字段")

        # 设置 updated_at 默认值
        cursor.execute(
            "UPDATE permissions SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
        )
        updated_count = cursor.rowcount
        if updated_count > 0:
            print(f"    ✓ 更新了 {updated_count} 条记录的 updated_at 字段")

        # 从 permission_code 推断 resource
        print("\n  推断 resource 字段值...")
        cursor.execute(
            """
            UPDATE permissions
            SET resource = CASE
                WHEN perm_code LIKE '%:%:%' THEN
                    SUBSTR(perm_code, INSTR(perm_code, ':') + 1,
                           INSTR(SUBSTR(perm_code, INSTR(perm_code, ':') + 1), ':') - 1)
                WHEN perm_code LIKE '%:%' THEN
                    SUBSTR(perm_code, 1, INSTR(perm_code, ':') - 1)
                ELSE module
            END
            WHERE resource IS NULL OR resource = ''
        """
        )
        resource_count = cursor.rowcount
        if resource_count > 0:
            print(f"    ✓ 更新了 {resource_count} 条记录的 resource 字段")

        # 如果 resource 仍为空，使用 module
        cursor.execute(
            "UPDATE permissions SET resource = module WHERE resource IS NULL OR resource = ''"
        )
        module_fallback_count = cursor.rowcount
        if module_fallback_count > 0:
            print(f"    ✓ 使用 module 作为 resource 回退值，更新了 {module_fallback_count} 条记录")

        # 提交事务
        conn.commit()
        print("\n✅ 迁移成功完成！")

        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM permissions")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM permissions WHERE is_active = 1")
        active = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM permissions WHERE resource IS NOT NULL AND resource != ''"
        )
        with_resource = cursor.fetchone()[0]

        print(f"\n📊 验证结果:")
        print(f"  总权限数: {total}")
        print(f"  启用权限数: {active}")
        print(f"  有 resource 的权限数: {with_resource}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("权限表结构升级迁移脚本")
    print("=" * 60)

    # 检测数据库类型
    db_path = project_root / "data" / "app.db"

    if db_path.exists():
        print(f"\n检测到 SQLite 数据库: {db_path}")
        success = apply_sqlite_migration(str(db_path))
        if success:
            print("\n✅ 所有迁移已完成！")
            sys.exit(0)
        else:
            print("\n❌ 迁移失败，请检查错误信息")
            sys.exit(1)
    else:
        print(f"\n⚠️  未找到数据库文件: {db_path}")
        print("   如果是 MySQL 数据库，请手动执行 MySQL 迁移脚本:")
        print("   migrations/20250120_permissions_table_upgrade_mysql.sql")
        sys.exit(1)


if __name__ == "__main__":
    main()
