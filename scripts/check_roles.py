#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的角色数据
"""

import os
import sys
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.models.base import get_db_session


def check_roles():
    """检查所有角色数据"""
    with get_db_session() as session:
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
                created_at
            FROM roles
            ORDER BY role_code, created_at
        """))

        roles = []
        roles_by_code = defaultdict(list)
        roles_by_name = defaultdict(list)

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
            }
            roles.append(role)
            roles_by_code[row.role_code].append(role)
            roles_by_name[row.role_name].append(role)

        print("=" * 80)
        print("角色数据检查报告")
        print("=" * 80)
        print(f"总角色数: {len(roles)}")
        print()

        # 检查 role_code 重复
        code_duplicates = {code: roles for code, roles in roles_by_code.items() if len(roles) > 1}
        if code_duplicates:
            print(f"⚠️  发现 {len(code_duplicates)} 个重复的 role_code:")
            for code, role_list in code_duplicates.items():
                print(f"\n  角色编码: {code}")
                for role in role_list:
                    print(f"    - ID {role['id']}: {role['role_name']} "
                          f"(系统: {role['is_system']}, 启用: {role['is_active']}, "
                          f"创建: {role['created_at']})")
        else:
            print("✓ role_code 无重复")

        print()

        # 检查 role_name 重复
        name_duplicates = {name: roles for name, roles in roles_by_name.items() if len(roles) > 1}
        if name_duplicates:
            print(f"⚠️  发现 {len(name_duplicates)} 个重复的 role_name:")
            for name, role_list in name_duplicates.items():
                print(f"\n  角色名称: {name}")
                for role in role_list:
                    print(f"    - ID {role['id']}: role_code={role['role_code']} "
                          f"(系统: {role['is_system']}, 启用: {role['is_active']}, "
                          f"创建: {role['created_at']})")
        else:
            print("✓ role_name 无重复")

        print()
        print("=" * 80)
        print("所有角色列表:")
        print("=" * 80)
        for role in roles:
            print(f"ID {role['id']:3d} | {role['role_code']:20s} | {role['role_name']:20s} | "
                  f"系统: {role['is_system']:1d} | 启用: {role['is_active']:1d} | "
                  f"创建: {role['created_at']}")


if __name__ == "__main__":
    check_roles()
