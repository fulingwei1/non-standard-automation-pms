#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员账户脚本
用法: python3 create_admin.py [username] [password]
"""

import getpass
import sys

from sqlalchemy import text

from app.core import security
from app.models.base import get_session


def get_or_create_admin_role_id(db):
    """获取或创建 ADMIN 角色，返回角色ID"""
    # 查询 ADMIN 角色
    result = db.execute(text("SELECT id FROM roles WHERE role_code = 'ADMIN'")).first()

    if result:
        admin_role_id = result[0]
        print(f"✓ 找到 ADMIN 角色 (ID: {admin_role_id})")
        return admin_role_id
    else:
        # 创建 ADMIN 角色
        db.execute(
            text("""
            INSERT INTO roles (role_code, role_name, description, data_scope, is_system, status, role_type, scope_type, level, created_at)
            VALUES ('ADMIN', '系统管理员', '系统最高权限，可管理所有功能和数据', 'ALL', 1, 'ACTIVE', 'SYSTEM', 'GLOBAL', 0, CURRENT_TIMESTAMP)
        """)
        )
        db.commit()
        # 重新查询获取 ID
        result = db.execute(
            text("SELECT id FROM roles WHERE role_code = 'ADMIN'")
        ).first()
        admin_role_id = result[0]
        print(f"✓ 已创建 ADMIN 角色 (ID: {admin_role_id})")
        return admin_role_id


def create_or_update_admin_user(db, username, password):
    """创建或更新管理员用户"""
    # 获取或创建 ADMIN 角色ID
    admin_role_id = get_or_create_admin_role_id(db)

    # 检查用户是否已存在
    user_result = db.execute(
        text("SELECT id, employee_id FROM users WHERE username = :username"),
        {"username": username},
    ).first()

    if user_result:
        # 更新现有用户
        user_id = user_result[0]
        print(f"✓ 用户 '{username}' 已存在，正在更新...")

        # 更新密码和权限
        password_hash = security.get_password_hash(password)
        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash,
                    is_superuser = 1,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
            """),
            {"password_hash": password_hash, "user_id": user_id},
        )

        # 检查是否已关联 ADMIN 角色
        role_result = db.execute(
            text(
                "SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"
            ),
            {"user_id": user_id, "role_id": admin_role_id},
        ).first()

        if not role_result:
            db.execute(
                text(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                ),
                {"user_id": user_id, "role_id": admin_role_id},
            )
            print(f"✓ 已为用户 '{username}' 分配 ADMIN 角色")
        else:
            print(f"✓ 用户 '{username}' 已拥有 ADMIN 角色")
    else:
        # 创建新用户
        print(f"✓ 正在创建新用户 '{username}'...")

        # 创建或获取员工记录
        emp_result = db.execute(
            text("SELECT id FROM employees WHERE employee_code = 'E0001'")
        ).first()

        if emp_result:
            employee_id = emp_result[0]
            print(f"✓ 找到员工记录 (ID: {employee_id})")
        else:
            # 创建员工记录
            db.execute(
                text("""
                INSERT INTO employees (employee_code, name, department, role, is_active, created_at)
                VALUES ('E0001', '系统管理员', 'IT', '系统管理员', 1, CURRENT_TIMESTAMP)
            """)
            )
            db.commit()
            emp_result = db.execute(
                text("SELECT id FROM employees WHERE employee_code = 'E0001'")
            ).first()
            employee_id = emp_result[0]
            print(f"✓ 已创建员工记录 (ID: {employee_id})")

        # 创建用户
        password_hash = security.get_password_hash(password)
        db.execute(
            text("""
            INSERT INTO users (
                username, employee_id, password_hash, real_name, employee_no,
                department, position, is_active, is_superuser, auth_type, created_at
            ) VALUES (
                :username, :employee_id, :password_hash, '系统管理员', 'E0001',
                'IT', '系统管理员', 1, 1, 'password', CURRENT_TIMESTAMP
            )
        """),
            {
                "username": username,
                "employee_id": employee_id,
                "password_hash": password_hash,
            },
        )
        db.commit()

        # 获取新创建的用户ID
        user_result = db.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": username},
        ).first()
        user_id = user_result[0]

        # 分配 ADMIN 角色
        db.execute(
            text(
                "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
            ),
            {"user_id": user_id, "role_id": admin_role_id},
        )
        print(f"✓ 已为用户 '{username}' 分配 ADMIN 角色")

    db.commit()

    print(f"\n{'=' * 50}")
    print(f"✓ 管理员账户设置成功！")
    print(f"{'=' * 50}")
    print(f"用户名: {username}")
    print(f"密码: ********")
    print(f"超级管理员: 是")
    print(f"角色: ADMIN (系统管理员)")
    print(f"{'=' * 50}\n")


def main():
    """主函数"""
    print("=" * 50)
    print("管理员账户设置工具")
    print("=" * 50)
    print()

    # 获取用户名
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("请输入管理员用户名 [默认: admin]: ").strip() or "admin"

    # 获取密码
    if len(sys.argv) > 2:
        password = sys.argv[2]
    else:
        password = getpass.getpass("请输入管理员密码: ")
        if not password:
            print("错误: 密码不能为空")
            sys.exit(1)
        password_confirm = getpass.getpass("请再次输入密码确认: ")
        if password != password_confirm:
            print("错误: 两次输入的密码不一致")
            sys.exit(1)

    try:
        with get_session() as db:
            create_or_update_admin_user(db, username, password)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
