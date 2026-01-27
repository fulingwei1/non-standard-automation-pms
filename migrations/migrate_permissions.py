#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统迁移脚本

将权限数据从旧表 (permissions, role_permissions) 迁移到新表 (api_permissions, role_api_permissions)

用法:
    python migrations/migrate_permissions.py [--dry-run]

选项:
    --dry-run   仅显示将执行的操作，不实际修改数据库
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, List, Set

from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError


def get_db_connection():
    """获取数据库连接"""
    from app.models.base import get_session, get_engine

    return get_session(), get_engine()


def ensure_tables_exist(engine):
    """确保新表存在"""
    from app.models.user import ApiPermission, RoleApiPermission
    from app.models.base import Base

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    tables_to_create = []
    if "api_permissions" not in existing_tables:
        tables_to_create.append("api_permissions")
    if "role_api_permissions" not in existing_tables:
        tables_to_create.append("role_api_permissions")

    if tables_to_create:
        print(f"创建新表: {', '.join(tables_to_create)}")
        # 只创建指定的表
        Base.metadata.create_all(
            engine, tables=[ApiPermission.__table__, RoleApiPermission.__table__]
        )
        print("✅ 新表创建成功")
    else:
        print("✅ 新表已存在")

    return tables_to_create


def get_old_permissions(db) -> List[Dict]:
    """获取旧权限表数据"""
    result = db.execute(
        text("""
        SELECT 
            id,
            perm_code,
            perm_name,
            module,
            page_code,
            action,
            description,
            permission_type,
            is_active,
            created_at,
            updated_at
        FROM permissions
    """)
    )

    permissions = []
    for row in result:
        permissions.append(
            {
                "old_id": row[0],
                "perm_code": row[1],
                "perm_name": row[2],
                "module": row[3],
                "page_code": row[4],
                "action": row[5],
                "description": row[6],
                "permission_type": row[7],
                "is_active": row[8] if row[8] is not None else True,
                "created_at": row[9],
                "updated_at": row[10],
            }
        )

    return permissions


def get_old_role_permissions(db) -> List[Dict]:
    """获取旧角色权限关联表数据"""
    result = db.execute(
        text("""
        SELECT 
            role_id,
            permission_id,
            created_at
        FROM role_permissions
    """)
    )

    role_permissions = []
    for row in result:
        role_permissions.append(
            {"role_id": row[0], "permission_id": row[1], "created_at": row[2]}
        )

    return role_permissions


def get_existing_api_permissions(db) -> Dict[str, int]:
    """获取已存在的 API 权限 (perm_code -> id)"""
    try:
        result = db.execute(text("SELECT id, perm_code FROM api_permissions"))
        return {row[1]: row[0] for row in result}
    except Exception:
        return {}


def get_existing_role_api_permissions(db) -> Set[tuple]:
    """获取已存在的角色API权限关联 (role_id, permission_id)"""
    try:
        result = db.execute(
            text("SELECT role_id, permission_id FROM role_api_permissions")
        )
        return {(row[0], row[1]) for row in result}
    except Exception:
        return set()


def migrate_permissions(
    db, old_permissions: List[Dict], dry_run: bool = False
) -> Dict[int, int]:
    """
    迁移权限数据

    Returns:
        旧权限ID到新权限ID的映射
    """
    existing = get_existing_api_permissions(db)
    old_to_new_id = {}
    inserted = 0
    skipped = 0

    for perm in old_permissions:
        perm_code = perm["perm_code"]

        if perm_code in existing:
            old_to_new_id[perm["old_id"]] = existing[perm_code]
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] 将插入权限: {perm_code} - {perm['perm_name']}")
            inserted += 1
            continue

        try:
            result = db.execute(
                text("""
                INSERT INTO api_permissions (
                    perm_code, perm_name, module, page_code, action,
                    description, permission_type, is_active, created_at, updated_at
                ) VALUES (
                    :perm_code, :perm_name, :module, :page_code, :action,
                    :description, :permission_type, :is_active, :created_at, :updated_at
                )
            """),
                {
                    "perm_code": perm_code,
                    "perm_name": perm["perm_name"],
                    "module": perm["module"],
                    "page_code": perm["page_code"],
                    "action": perm["action"],
                    "description": perm["description"],
                    "permission_type": perm["permission_type"],
                    "is_active": 1 if perm["is_active"] else 0,
                    "created_at": perm["created_at"] or datetime.now(),
                    "updated_at": perm["updated_at"] or datetime.now(),
                },
            )

            # 获取新插入的 ID
            new_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            old_to_new_id[perm["old_id"]] = new_id
            existing[perm_code] = new_id
            inserted += 1

        except IntegrityError as e:
            print(f"  ⚠️ 插入权限失败 ({perm_code}): {e}")
            skipped += 1

    print(f"  权限迁移: 插入 {inserted} 条, 跳过 {skipped} 条 (已存在)")
    return old_to_new_id


def migrate_role_permissions(
    db,
    old_role_permissions: List[Dict],
    old_to_new_perm_id: Dict[int, int],
    dry_run: bool = False,
):
    """迁移角色权限关联数据"""
    existing = get_existing_role_api_permissions(db)
    inserted = 0
    skipped = 0
    missing = 0

    for rp in old_role_permissions:
        old_perm_id = rp["permission_id"]
        role_id = rp["role_id"]

        # 查找新的权限 ID
        if old_perm_id not in old_to_new_perm_id:
            # 尝试从数据库直接查询
            perm_code = db.execute(
                text("SELECT perm_code FROM permissions WHERE id = :id"),
                {"id": old_perm_id},
            ).scalar()

            if perm_code:
                new_perm_id = db.execute(
                    text("SELECT id FROM api_permissions WHERE perm_code = :code"),
                    {"code": perm_code},
                ).scalar()

                if new_perm_id:
                    old_to_new_perm_id[old_perm_id] = new_perm_id
                else:
                    missing += 1
                    continue
            else:
                missing += 1
                continue

        new_perm_id = old_to_new_perm_id[old_perm_id]

        # 检查是否已存在
        if (role_id, new_perm_id) in existing:
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] 将关联: 角色ID={role_id} -> 权限ID={new_perm_id}")
            inserted += 1
            continue

        try:
            db.execute(
                text("""
                INSERT INTO role_api_permissions (role_id, permission_id, created_at)
                VALUES (:role_id, :permission_id, :created_at)
            """),
                {
                    "role_id": role_id,
                    "permission_id": new_perm_id,
                    "created_at": rp["created_at"] or datetime.now(),
                },
            )
            existing.add((role_id, new_perm_id))
            inserted += 1

        except IntegrityError as e:
            print(f"  ⚠️ 插入关联失败 (role={role_id}, perm={new_perm_id}): {e}")
            skipped += 1

    print(
        f"  角色权限关联迁移: 插入 {inserted} 条, 跳过 {skipped} 条, 缺失 {missing} 条"
    )


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("权限系统数据迁移")
    print(f"模式: {'DRY-RUN (仅预览)' if dry_run else '实际执行'}")
    print("=" * 60)
    print()

    db, engine = get_db_connection()

    try:
        # 步骤 1: 确保新表存在
        print("步骤 1: 检查/创建新表")
        ensure_tables_exist(engine)
        print()

        # 步骤 2: 读取旧数据
        print("步骤 2: 读取旧权限数据")
        old_permissions = get_old_permissions(db)
        old_role_permissions = get_old_role_permissions(db)
        print(f"  旧权限记录: {len(old_permissions)} 条")
        print(f"  旧角色权限关联: {len(old_role_permissions)} 条")
        print()

        # 步骤 3: 迁移权限数据
        print("步骤 3: 迁移权限数据")
        old_to_new_id = migrate_permissions(db, old_permissions, dry_run)
        print()

        # 步骤 4: 迁移角色权限关联
        print("步骤 4: 迁移角色权限关联")
        migrate_role_permissions(db, old_role_permissions, old_to_new_id, dry_run)
        print()

        # 提交事务
        if not dry_run:
            db.commit()
            print("✅ 迁移完成并已提交")
        else:
            print("ℹ️ DRY-RUN 完成，未做实际修改")

        # 验证
        print()
        print("步骤 5: 验证迁移结果")
        new_perms = db.execute(text("SELECT COUNT(*) FROM api_permissions")).scalar()
        new_role_perms = db.execute(
            text("SELECT COUNT(*) FROM role_api_permissions")
        ).scalar()
        print(f"  api_permissions 记录数: {new_perms}")
        print(f"  role_api_permissions 记录数: {new_role_perms}")

    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

    print()
    print("=" * 60)
    print("迁移完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
