#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理数据库中重复的角色

功能：
1. 查找 role_code 重复的角色
2. 对于每个重复的角色编码，保留一个（优先保留系统角色或最早创建的）
3. 将其他重复角色的关联数据（用户角色、角色权限）迁移到保留的角色
4. 删除重复的角色记录

使用方法：
    python scripts/cleanup_duplicate_roles.py [--dry-run] [--verbose]
"""

import sys
import os
from collections import defaultdict
from typing import List, Dict, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, func
from app.models.base import get_db_session, get_engine
from app.models.user import Role, UserRole, RolePermission


def is_chinese_role_code(role_code: str) -> bool:
    """判断 role_code 是否包含中文字符"""
    import re
    return bool(re.search(r'[\u4e00-\u9fff]', role_code))


def find_duplicate_roles(session) -> Dict[str, List[Dict]]:
    """
    查找重复的角色（按 role_name 分组，因为 role_code 有 UNIQUE 约束不会重复）
    同时标记中文 role_code 的角色为需要清理
    
    Returns:
        Dict[str, List[Dict]]: {role_name: [角色信息列表]}
    """
    # 查询所有角色
    result = session.execute(text("""
        SELECT 
            id,
            role_code,
            role_name,
            description,
            data_scope,
            is_system,
            is_active,
            created_at,
            updated_at
        FROM roles
        ORDER BY role_name, created_at
    """))
    
    roles_by_name = defaultdict(list)
    chinese_role_codes = []
    
    for row in result:
        role = {
            'id': row.id,
            'role_code': row.role_code,
            'role_name': row.role_name,
            'description': row.description,
            'data_scope': row.data_scope,
            'is_system': row.is_system,
            'is_active': row.is_active,
            'created_at': row.created_at,
            'updated_at': row.updated_at,
        }
        roles_by_name[row.role_name].append(role)
        
        # 检查是否是中文 role_code
        if is_chinese_role_code(row.role_code):
            chinese_role_codes.append(role)
    
    # 只返回重复的角色名称
    duplicates = {name: roles for name, roles in roles_by_name.items() if len(roles) > 1}
    
    # 添加中文 role_code 的角色到清理列表
    for role in chinese_role_codes:
        if role['role_name'] not in duplicates:
            duplicates[role['role_name']] = [role]
        elif role not in duplicates[role['role_name']]:
            duplicates[role['role_name']].append(role)
    
    return duplicates


def choose_role_to_keep(roles: List[Dict]) -> Dict:
    """
    选择要保留的角色
    
    优先级：
    1. 系统角色 (is_system = 1)
    2. role_code 不是中文的（优先保留英文编码）
    3. 启用的角色 (is_active = 1)
    4. 最早创建的 (created_at 最小)
    
    Args:
        roles: 角色列表
        
    Returns:
        要保留的角色信息
    """
    # 优先保留系统角色
    system_roles = [r for r in roles if r.get('is_system')]
    if system_roles:
        roles = system_roles
    
    # 优先保留 role_code 不是中文的
    non_chinese_roles = [r for r in roles if not is_chinese_role_code(r.get('role_code', ''))]
    if non_chinese_roles:
        roles = non_chinese_roles
    
    # 优先保留启用的角色
    active_roles = [r for r in roles if r.get('is_active')]
    if active_roles:
        roles = active_roles
    
    # 保留最早创建的
    roles.sort(key=lambda x: x.get('created_at') or '9999-12-31')
    return roles[0]


def migrate_user_roles(session, from_role_id: int, to_role_id: int, dry_run: bool = False) -> int:
    """
    迁移用户角色关联
    
    Args:
        session: 数据库会话
        from_role_id: 源角色ID
        to_role_id: 目标角色ID
        dry_run: 是否只是预览，不实际执行
        
    Returns:
        迁移的记录数
    """
    # 先查询需要迁移的记录
    result = session.execute(text("""
        SELECT user_id, role_id
        FROM user_roles
        WHERE role_id = :from_role_id
    """), {"from_role_id": from_role_id})
    
    user_roles = result.fetchall()
    migrated_count = 0
    
    for user_id, role_id in user_roles:
        # 检查目标角色是否已经存在该用户的关联
        check_result = session.execute(text("""
            SELECT COUNT(*) FROM user_roles
            WHERE user_id = :user_id AND role_id = :to_role_id
        """), {"user_id": user_id, "to_role_id": to_role_id})
        
        exists = check_result.scalar() > 0
        
        if not exists:
            if not dry_run:
                # 迁移到新角色
                session.execute(text("""
                    UPDATE user_roles
                    SET role_id = :to_role_id
                    WHERE user_id = :user_id AND role_id = :from_role_id
                """), {
                    "user_id": user_id,
                    "from_role_id": from_role_id,
                    "to_role_id": to_role_id
                })
            migrated_count += 1
        else:
            # 如果已存在，直接删除旧的关联
            if not dry_run:
                session.execute(text("""
                    DELETE FROM user_roles
                    WHERE user_id = :user_id AND role_id = :from_role_id
                """), {
                    "user_id": user_id,
                    "from_role_id": from_role_id
                })
    
    return migrated_count


def migrate_role_permissions(session, from_role_id: int, to_role_id: int, dry_run: bool = False) -> int:
    """
    迁移角色权限关联
    
    Args:
        session: 数据库会话
        from_role_id: 源角色ID
        to_role_id: 目标角色ID
        dry_run: 是否只是预览，不实际执行
        
    Returns:
        迁移的记录数
    """
    # 先查询需要迁移的记录
    result = session.execute(text("""
        SELECT permission_id
        FROM role_permissions
        WHERE role_id = :from_role_id
    """), {"from_role_id": from_role_id})
    
    permissions = [row[0] for row in result]
    migrated_count = 0
    
    for permission_id in permissions:
        # 检查目标角色是否已经存在该权限
        check_result = session.execute(text("""
            SELECT COUNT(*) FROM role_permissions
            WHERE role_id = :to_role_id AND permission_id = :permission_id
        """), {"to_role_id": to_role_id, "permission_id": permission_id})
        
        exists = check_result.scalar() > 0
        
        if not exists:
            if not dry_run:
                # 迁移到新角色
                session.execute(text("""
                    UPDATE role_permissions
                    SET role_id = :to_role_id
                    WHERE role_id = :from_role_id AND permission_id = :permission_id
                """), {
                    "from_role_id": from_role_id,
                    "to_role_id": to_role_id,
                    "permission_id": permission_id
                })
            migrated_count += 1
        else:
            # 如果已存在，直接删除旧的关联
            if not dry_run:
                session.execute(text("""
                    DELETE FROM role_permissions
                    WHERE role_id = :from_role_id AND permission_id = :permission_id
                """), {
                    "from_role_id": from_role_id,
                    "permission_id": permission_id
                })
    
    return migrated_count


def migrate_user_role_assignments(session, from_role_id: int, to_role_id: int, dry_run: bool = False) -> int:
    """
    迁移用户角色分配记录（如果表存在）
    
    Args:
        session: 数据库会话
        from_role_id: 源角色ID
        to_role_id: 目标角色ID
        dry_run: 是否只是预览，不实际执行
        
    Returns:
        迁移的记录数
    """
    try:
        # 检查表是否存在
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_role_assignments'
        """))
        
        if not result.fetchone():
            return 0
        
        # 查询需要迁移的记录
        result = session.execute(text("""
            SELECT id, user_id
            FROM user_role_assignments
            WHERE role_id = :from_role_id
        """), {"from_role_id": from_role_id})
        
        assignments = result.fetchall()
        migrated_count = 0
        
        for assignment_id, user_id in assignments:
            # 检查目标角色是否已经存在该用户的分配
            check_result = session.execute(text("""
                SELECT COUNT(*) FROM user_role_assignments
                WHERE user_id = :user_id AND role_id = :to_role_id
            """), {"user_id": user_id, "to_role_id": to_role_id})
            
            exists = check_result.scalar() > 0
            
            if not exists:
                if not dry_run:
                    # 迁移到新角色
                    session.execute(text("""
                        UPDATE user_role_assignments
                        SET role_id = :to_role_id
                        WHERE id = :assignment_id
                    """), {
                        "assignment_id": assignment_id,
                        "to_role_id": to_role_id
                    })
                migrated_count += 1
            else:
                # 如果已存在，直接删除旧的分配
                if not dry_run:
                    session.execute(text("""
                        DELETE FROM user_role_assignments
                        WHERE id = :assignment_id
                    """), {"assignment_id": assignment_id})
        
        return migrated_count
    except Exception as e:
        # 表不存在或查询失败，忽略
        return 0


def cleanup_duplicate_roles(dry_run: bool = True, verbose: bool = False):
    """
    清理重复的角色
    
    Args:
        dry_run: 是否只是预览，不实际执行
        verbose: 是否显示详细信息
    """
    with get_db_session() as session:
        print("=" * 60)
        print("清理重复角色工具")
        print("=" * 60)
        print(f"模式: {'预览模式（不会实际删除）' if dry_run else '执行模式（将删除重复角色）'}")
        print()
        
        # 查找重复的角色
        duplicates = find_duplicate_roles(session)
        
        if not duplicates:
            print("✓ 未发现重复的角色，数据库是干净的！")
            return
        
        print(f"发现 {len(duplicates)} 个重复的角色编码：")
        print()
        
        total_to_delete = 0
        total_user_roles_migrated = 0
        total_permissions_migrated = 0
        total_assignments_migrated = 0
        
        for role_name, roles in duplicates.items():
            print(f"角色名称: {role_name}")
            print(f"  重复数量: {len(roles)}")
            
            # 选择要保留的角色
            role_to_keep = choose_role_to_keep(roles)
            roles_to_delete = [r for r in roles if r['id'] != role_to_keep['id']]
            
            print(f"  保留角色 ID: {role_to_keep['id']} (role_code: {role_to_keep['role_code']})")
            if role_to_keep.get('is_system'):
                print(f"    - 系统角色")
            if role_to_keep.get('is_active'):
                print(f"    - 启用状态")
            if is_chinese_role_code(role_to_keep.get('role_code', '')):
                print(f"    ⚠️  role_code 是中文（建议手动处理）")
            print(f"    - 创建时间: {role_to_keep.get('created_at')}")
            
            print(f"  待删除角色: {len(roles_to_delete)} 个")
            
            for role in roles_to_delete:
                chinese_mark = " ⚠️ 中文role_code" if is_chinese_role_code(role.get('role_code', '')) else ""
                print(f"    - ID {role['id']}: role_code={role['role_code']} (创建于 {role.get('created_at')}){chinese_mark}")
                
                # 统计需要迁移的数据
                if not dry_run:
                    # 迁移用户角色
                    user_roles_count = migrate_user_roles(
                        session, role['id'], role_to_keep['id'], dry_run=False
                    )
                    total_user_roles_migrated += user_roles_count
                    
                    # 迁移角色权限
                    permissions_count = migrate_role_permissions(
                        session, role['id'], role_to_keep['id'], dry_run=False
                    )
                    total_permissions_migrated += permissions_count
                    
                    # 迁移用户角色分配
                    assignments_count = migrate_user_role_assignments(
                        session, role['id'], role_to_keep['id'], dry_run=False
                    )
                    total_assignments_migrated += assignments_count
                    
                    if verbose:
                        print(f"      迁移: {user_roles_count} 个用户角色, "
                              f"{permissions_count} 个权限, {assignments_count} 个分配记录")
                    
                    # 先删除所有关联数据（使用原始连接禁用外键检查）
                    conn = session.connection()
                    conn.execute(text("PRAGMA foreign_keys = OFF"))
                    
                    try:
                        # 删除所有关联表的数据
                        tables_to_clean = [
                            'department_default_roles',
                            'role_exclusions',
                            'role_permissions',
                            'user_roles',
                            'user_role_assignments',
                            'hourly_rate_configs',
                        ]
                        
                        for table in tables_to_clean:
                            try:
                                # 检查表是否存在
                                check = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                                if check.fetchone():
                                    # 删除该角色相关的数据
                                    if table == 'role_exclusions':
                                        conn.execute(text(f"DELETE FROM {table} WHERE role_id_a = :role_id OR role_id_b = :role_id"), {
                                            "role_id": role['id']
                                        })
                                    else:
                                        conn.execute(text(f"DELETE FROM {table} WHERE role_id = :role_id"), {
                                            "role_id": role['id']
                                        })
                            except Exception as e:
                                if verbose:
                                    print(f"      清理 {table} 时出错: {e}")
                                pass
                        
                        # 更新角色的父级关系
                        try:
                            conn.execute(text("""
                                UPDATE roles
                                SET parent_role_id = :to_role_id
                                WHERE parent_role_id = :from_role_id
                            """), {
                                "from_role_id": role['id'],
                                "to_role_id": role_to_keep['id']
                            })
                        except:
                            pass
                        
                        # 最后删除角色本身
                        conn.execute(text("DELETE FROM roles WHERE id = :role_id"), {
                            "role_id": role['id']
                        })
                    finally:
                        conn.execute(text("PRAGMA foreign_keys = ON"))
            
            total_to_delete += len(roles_to_delete)
            print()
        
        print("=" * 60)
        print("统计信息:")
        print(f"  重复的角色名称数: {len(duplicates)}")
        print(f"  待删除的角色数: {total_to_delete}")
        if not dry_run:
            print(f"  迁移的用户角色关联: {total_user_roles_migrated}")
            print(f"  迁移的角色权限关联: {total_permissions_migrated}")
            print(f"  迁移的用户角色分配: {total_assignments_migrated}")
        print("=" * 60)
        
        if dry_run:
            print()
            print("这是预览模式，未实际删除任何数据。")
            print("要执行清理，请运行: python scripts/cleanup_duplicate_roles.py --execute")
        else:
            session.commit()
            print()
            print("✓ 清理完成！重复的角色已删除，关联数据已迁移。")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理数据库中重复的角色")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行清理（默认是预览模式）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    
    args = parser.parse_args()
    
    cleanup_duplicate_roles(dry_run=not args.execute, verbose=args.verbose)
