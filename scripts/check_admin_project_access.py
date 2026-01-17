#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本：检查管理员账号权限和项目访问问题
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.project import Project
from app.models.user import User
from app.services.data_scope_service import DataScopeService


def check_admin_access(db):
    """检查管理员账号权限配置"""
    # 查找管理员账号
    admin = db.query(User).filter(User.username == "admin").first()

    if not admin:
        print("❌ 未找到管理员账号 'admin'")
        return None

    print(f"✓ 找到管理员账号: {admin.username}")
    print(f"  - ID: {admin.id}")
    print(f"  - is_superuser: {admin.is_superuser}")
    print(f"  - is_active: {admin.is_active}")
    print(f"  - real_name: {admin.real_name}")

    if not admin.is_superuser:
        print("⚠️  警告：管理员账号的 is_superuser 为 False")
        print("   这可能导致权限检查失败")

    # 检查数据权限范围
    data_scope = DataScopeService.get_user_data_scope(db, admin)
    print(f"  - data_scope: {data_scope}")

    # 检查角色
    roles = admin.roles.all()
    print(f"  - 角色数量: {len(roles)}")
    for role in roles:
        print(f"    * {role.role.role_name if role.role else 'N/A'} (data_scope: {role.role.data_scope if role.role else 'N/A'})")

    return admin


def check_project(project_id: int, admin_id: int, db, admin: User):
    """检查项目是否存在和权限"""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        print(f"❌ 项目 ID {project_id} 不存在")
        return False

    print(f"\n✓ 找到项目: {project.project_name}")
    print(f"  - ID: {project.id}")
    print(f"  - 编码: {project.project_code}")
    print(f"  - 状态: {project.status}")
    print(f"  - 阶段: {project.stage}")
    print(f"  - is_active: {project.is_active}")

    # 检查权限
    has_access = DataScopeService.check_project_access(db, admin, project_id)
    print(f"  - 管理员访问权限: {'✓ 有权限' if has_access else '❌ 无权限'}")

    if not has_access:
        print("\n⚠️  权限检查失败原因分析：")
        if not admin.is_superuser:
            print("  - 管理员账号 is_superuser = False")
        data_scope = DataScopeService.get_user_data_scope(db, admin)
        print(f"  - 数据权限范围: {data_scope}")

        if data_scope == "OWN":
            print(f"  - 项目创建人ID: {project.created_by}")
            print(f"  - 项目经理ID: {project.pm_id}")
            print(f"  - 管理员ID: {admin.id}")

    return has_access


def list_projects(db):
    """列出所有项目"""
    projects = db.query(Project).order_by(Project.id).limit(10).all()

    print(f"\n前10个项目列表：")
    for p in projects:
        print(f"  - ID: {p.id}, 编码: {p.project_code}, 名称: {p.project_name}")


if __name__ == "__main__":
    print("=" * 60)
    print("管理员权限和项目访问诊断")
    print("=" * 60)

    with get_db_session() as db:
        # 检查管理员
        admin = check_admin_access(db)
        if not admin:
            sys.exit(1)

        # 列出项目
        list_projects(db)

        # 检查特定项目（从命令行参数获取，默认14）
        project_id = int(sys.argv[1]) if len(sys.argv) > 1 else 14
        print(f"\n检查项目 ID: {project_id}")
        has_access = check_project(project_id, admin.id, db, admin)

        print("\n" + "=" * 60)
        if has_access:
            print("✓ 诊断完成：管理员应该可以访问该项目")
        else:
            print("❌ 诊断完成：管理员无法访问该项目")
            print("\n建议修复：")
            print("1. 确保管理员账号的 is_superuser = True")
            print("2. 或者为管理员角色配置 data_scope = 'ALL'")
        print("=" * 60)
