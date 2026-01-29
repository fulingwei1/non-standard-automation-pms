#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建前端首页13个快捷登录账号
这些账号用于前端登录页面的快捷登录功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_db_session
from app.models.user import User, Role, UserRole
from app.models.organization import Employee
from app.core.auth import get_password_hash

# 前端13个快捷登录账号配置
FRONTEND_ACCOUNTS = [
    {
        "username": "zhengrucai",
        "password": "123456",
        "real_name": "郑汝才",
        "employee_code": "E1001",
        "department": "高层管理",
        "position": "常务副总",
        "role_code": "GM",  # 使用总经理角色
    },
    {
        "username": "luoyixing",
        "password": "123456",
        "real_name": "骆奕兴",
        "employee_code": "E1002",
        "department": "高层管理",
        "position": "副总经理",
        "role_code": "GM",
    },
    {
        "username": "fulingwei",
        "password": "123456",
        "real_name": "符凌维",
        "employee_code": "E1003",
        "department": "高层管理",
        "position": "副总经理（董秘）",
        "role_code": "GM",
    },
    {
        "username": "songkui",
        "password": "123456",
        "real_name": "宋魁",
        "employee_code": "E1004",
        "department": "营销中心",
        "position": "营销中心总监",
        "role_code": "SALES_DIR",
    },
    {
        "username": "zhengqin",
        "password": "123456",
        "real_name": "郑琴",
        "employee_code": "E1005",
        "department": "营销中心",
        "position": "销售经理",
        "role_code": "SA",  # 销售专员角色
    },
    {
        "username": "yaohong",
        "password": "123456",
        "real_name": "姚洪",
        "employee_code": "E1006",
        "department": "营销中心",
        "position": "销售工程师",
        "role_code": "SA",
    },
    {
        "username": "changxiong",
        "password": "123456",
        "real_name": "常雄",
        "employee_code": "E1007",
        "department": "生产管理中心",
        "position": "PMC主管",
        "role_code": "PMC",
    },
    {
        "username": "gaoyong",
        "password": "123456",
        "real_name": "高勇",
        "employee_code": "E1008",
        "department": "生产部",
        "position": "生产部经理",
        "role_code": "DEPT_MGR",
    },
    {
        "username": "chenliang",
        "password": "123456",
        "real_name": "陈亮",
        "employee_code": "E1009",
        "department": "项目管理部",
        "position": "项目管理部总监",
        "role_code": "PM",
    },
    {
        "username": "tanzhangbin",
        "password": "123456",
        "real_name": "谭章斌",
        "employee_code": "E1010",
        "department": "项目管理部",
        "position": "项目经理",
        "role_code": "PM",
    },
    {
        "username": "yuzhenhua",
        "password": "123456",
        "real_name": "于振华",
        "employee_code": "E1011",
        "department": "技术部",
        "position": "经理",
        "role_code": "DEPT_MGR",
    },
    {
        "username": "wangjun",
        "password": "123456",
        "real_name": "王俊",
        "employee_code": "E1012",
        "department": "质量部",
        "position": "经理",
        "role_code": "QA_MGR",
    },
    {
        "username": "wangzhihong",
        "password": "123456",
        "real_name": "王志红",
        "employee_code": "E1013",
        "department": "客服部",
        "position": "客服主管",
        "role_code": "DEPT_MGR",
    },
]


def create_frontend_accounts():
    """创建前端快捷登录账号"""
    with get_db_session() as session:
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for account in FRONTEND_ACCOUNTS:
            try:
                # 获取角色
                role = session.query(Role).filter(
                    Role.role_code == account["role_code"]
                ).first()

                if not role:
                    print(f"⚠️  角色 '{account['role_code']}' 不存在，跳过用户: {account['username']}")
                    skipped_count += 1
                    continue

                # 创建或获取员工
                employee = session.query(Employee).filter(
                    Employee.employee_code == account["employee_code"]
                ).first()

                if not employee:
                    employee = Employee(
                        employee_code=account["employee_code"],
                        name=account["real_name"],
                        department=account["department"],
                        role=account["position"],
                        is_active=True,
                        employment_status="active",
                    )
                    session.add(employee)
                    session.flush()

                # 检查用户是否已存在
                existing_user = session.query(User).filter(
                    User.username == account["username"]
                ).first()

                if existing_user:
                    # 更新现有用户
                    existing_user.employee_id = employee.id
                    existing_user.password_hash = get_password_hash(account["password"])
                    existing_user.real_name = account["real_name"]
                    existing_user.employee_no = account["employee_code"]
                    existing_user.department = account["department"]
                    existing_user.position = account["position"]
                    existing_user.is_active = True
                    existing_user.auth_type = "password"
                    session.add(existing_user)
                    session.flush()
                    user = existing_user
                    action = "更新"
                    updated_count += 1
                else:
                    # 创建新用户
                    user = User(
                        employee_id=employee.id,
                        username=account["username"],
                        password_hash=get_password_hash(account["password"]),
                        email=f"{account['username']}@demo.local",
                        real_name=account["real_name"],
                        employee_no=account["employee_code"],
                        department=account["department"],
                        position=account["position"],
                        is_active=True,
                        is_superuser=False,
                        auth_type="password",
                    )
                    session.add(user)
                    session.flush()
                    action = "创建"
                    created_count += 1

                # 确保角色关联存在
                existing_role = session.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id
                ).first()

                if not existing_role:
                    session.add(UserRole(user_id=user.id, role_id=role.id))
                    role_action = "绑定角色"
                else:
                    role_action = "角色已存在"

                session.commit()
                print(f"✓ {action}用户: {account['username']} ({account['real_name']}) - {account['position']} [{role.role_name}]（{role_action}）")

            except Exception as e:
                print(f"✗ 创建用户 '{account['username']}' 失败: {str(e)}")
                session.rollback()
                skipped_count += 1
                continue

        print()
        print("=" * 60)
        print(f"✓ 前端快捷登录账号处理完成！")
        print(f"  - 新建: {created_count} 个")
        print(f"  - 更新: {updated_count} 个")
        print(f"  - 跳过: {skipped_count} 个")
        print()
        print("=== 账号列表 ===")
        for account in FRONTEND_ACCOUNTS:
            print(f"  {account['real_name']}: {account['username']} / {account['password']}")


if __name__ == "__main__":
    print("开始创建前端快捷登录账号...\n")
    create_frontend_accounts()
