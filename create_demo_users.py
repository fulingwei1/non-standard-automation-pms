#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建演示用户脚本
用于快速创建用于演示的测试账户
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.base import get_db_session, Base, get_engine
from app.models.user import User, Role, UserRole
from app.models.organization import Employee
from app.core.security import get_password_hash
from sqlalchemy import select, exc

# 演示用户配置
DEMO_USERS = [
    {
        "username": "chairman",
        "password": "123456",
        "real_name": "董事长",
        "employee_code": "E0001",
        "department": "董事会",
        "position": "董事长",
        "role_code": "ADMIN",
    },
    {
        "username": "gm",
        "password": "123456",
        "real_name": "总经理",
        "employee_code": "E0002",
        "department": "总经理办公室",
        "position": "总经理",
        "role_code": "GM",
    },
    {
        "username": "pm",
        "password": "123456",
        "real_name": "项目经理",
        "employee_code": "E0003",
        "department": "技术中心",
        "position": "项目经理",
        "role_code": "PM",
    },
    {
        "username": "sales_director",
        "password": "123456",
        "real_name": "销售总监",
        "employee_code": "E0005",
        "department": "销售部",
        "position": "销售总监",
        "role_code": "SALES_DIR",
    },
    {
        "username": "sales_manager",
        "password": "123456",
        "real_name": "销售经理",
        "employee_code": "E0006",
        "department": "销售部",
        "position": "销售经理",
        "role_code": "SA",
    },
    {
        "username": "pmc",
        "password": "123456",
        "real_name": "P&C",
        "employee_code": "E0004",
        "department": "计划部",
        "position": "计划管理",
        "role_code": "PMC",
    },
    {
        "username": "mech_manager",
        "password": "123456",
        "real_name": "机械部经理",
        "employee_code": "E0007",
        "department": "机械部",
        "position": "机械部经理",
        "role_code": "DEPT_MGR",
    },
]


def create_demo_users():
    """创建演示用户"""
    with get_db_session() as session:
        for user_config in DEMO_USERS:
            try:
                # 检查用户是否已存在
                existing_user = session.query(User).filter(
                    User.username == user_config["username"]
                ).first()

                if existing_user:
                    print(f"✓ 用户 '{user_config['username']}' 已存在，跳过创建")
                    continue

                # 创建或获取员工
                employee = session.query(Employee).filter(
                    Employee.employee_code == user_config["employee_code"]
                ).first()

                if not employee:
                    employee = Employee(
                        employee_code=user_config["employee_code"],
                        name=user_config["real_name"],
                        department=user_config["department"],
                        role=user_config["position"],
                        is_active=True,
                    )
                    session.add(employee)
                    session.flush()
                    print(f"  创建员工: {user_config['real_name']}")

                # 创建用户
                user = User(
                    employee_id=employee.id,
                    username=user_config["username"],
                    password_hash=get_password_hash(user_config["password"]),
                    email=f"{user_config['username']}@demo.local",
                    real_name=user_config["real_name"],
                    employee_no=user_config["employee_code"],
                    department=user_config["department"],
                    position=user_config["position"],
                    is_active=True,
                    is_superuser=(user_config["role_code"] == "ADMIN"),
                )
                session.add(user)
                session.flush()

                # 获取角色并分配
                role = session.query(Role).filter(
                    Role.role_code == user_config["role_code"]
                ).first()

                if role:
                    user_role = UserRole(user_id=user.id, role_id=role.id)
                    session.add(user_role)
                    print(f"✓ 创建用户: {user_config['username']} ({user_config['real_name']}) - 角色: {role.role_name}")
                else:
                    print(f"✗ 角色 '{user_config['role_code']}' 不存在，创建用户失败")
                    session.rollback()
                    continue

            except Exception as e:
                print(f"✗ 创建用户 '{user_config['username']}' 失败: {str(e)}")
                session.rollback()
                continue

        session.commit()
        print("\n✓ 演示用户创建完成！")
        print("\n=== 演示账户登录信息 ===")
        for user in DEMO_USERS:
            print(f"用户名: {user['username']}, 密码: {user['password']}, 角色: {user['real_name']}")


if __name__ == "__main__":
    print("开始创建演示用户...\n")
    create_demo_users()
