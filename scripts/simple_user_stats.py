#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的用户和角色统计
"""

import sys

sys.path.append("/Users/flw/non-standard-automation-pm")

from sqlalchemy import func

from app.models.base import SessionLocal
from app.models.user import Role, User, UserRole


def main():
    with SessionLocal() as db:
        total_users = db.query(User).count()
        total_roles = db.query(Role).count()
        active_users = db.query(User).filter(User.last_login_at.isnot(None)).count()

        print("📊 系统用户和角色统计")
        print("=" * 50)
        print(f"👥 总用户数: {total_users}")
        print(f"🏷️ 总角色数: {total_roles}")
        print(f"✅ 活跃用户数: {active_users}")
        print(f"💤 活跃率: {(active_users/total_users*100):.1f}%")
        print()

        # 各角色用户分布
        try:
            role_stats = (
                db.query(Role.role_name, func.count(UserRole.id).label("user_count"))
                .outerjoin(UserRole, Role.id == UserRole.role_id)
                .group_by(Role.id, Role.role_name)
                .all()
            )

            print("👥 各角色用户分布:")
            print("-" * 50)
            for role_name, count in sorted(role_stats, key=lambda x: x[1], reverse=True)[:15]:
                print(f"  {role_name:<25}: {count:>3} 人")
        except Exception as e:
            print(f"角色统计出错: {e}")

        # 用户状态
        try:
            active_count = db.query(User).filter(User.is_active == True).count()
            superuser_count = db.query(User).filter(User.is_superuser == True).count()

            print()
            print("📊 用户状态分布:")
            print("-" * 50)
            print(f"  ✅ 活跃状态: {active_count} 人")
            print(f"  👑 超级管理员: {superuser_count} 人")
        except Exception as e:
            print(f"状态统计出错: {e}")

        # 部门统计
        try:
            dept_stats = (
                db.query(User.department, func.count(User.id).label("count"))
                .filter(User.department.isnot(None))
                .group_by(User.department)
                .order_by(func.count(User.id).desc())
                .limit(10)
                .all()
            )

            print()
            print("🏢 部门用户分布 (前10):")
            print("-" * 50)
            for dept, count in dept_stats:
                print(f"  {dept:<30}: {count:>3} 人")
        except Exception as e:
            print(f"部门统计出错: {e}")


if __name__ == "__main__":
    main()
