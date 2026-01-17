#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户和角色统计脚本
"""

import sys

sys.path.append('/Users/flw/non-standard-automation-pm')

from sqlalchemy import func

from app.models.base import SessionLocal
from app.models.user import Role, User, UserRole


def main():
    """主统计函数"""
    with SessionLocal() as db:
        # 基础统计
        total_users = db.query(User).count()
        total_roles = db.query(Role).count()
        active_users = db.query(User).filter(User.last_login_at.isnot(None)).count()

        print('📊 系统用户和角色统计')
        print('=' * 60)
        print(f'👥 总用户数: {total_users}')
        print(f'🏷️ 总角色数: {total_roles}')
        print(f'✅ 活跃用户数: {active_users}')
        print(f'💤 活跃率: {(active_users/total_users*100):.1f}%')
        print()

        # 各角色用户分布
        role_stats = (
            db.query(
                Role.role_name,
                func.count(UserRole.id).label("user_count"),
            )
            .outerjoin(UserRole, Role.id == UserRole.role_id)
            .group_by(Role.id, Role.role_name)
            .all()
        )

        print('👥 各角色用户分布:')
        print('-' * 60)

        # 按用户数排序，显示前20个
        sorted_roles = sorted(role_stats, key=lambda x: x[1], reverse=True)

        for i, (role_name, count) in enumerate(sorted_roles[:20], 1):
            print(f'  {i:2d}. {role_name:<25}: {count:>3} 人')

        if len(sorted_roles) > 20:
            print(f'  ... 还有 {len(sorted_roles)-20} 个角色未显示')

        print()

        # 部门统计
        dept_stats = (
            db.query(
                User.department,
                func.count(User.id).label("count"),
            )
            .filter(User.department.isnot(None))
            .group_by(User.department)
            .order_by(func.count(User.id).desc())
            .limit(10)
            .all()
        )

        print('🏢 部门用户分布:')
        print('-' * 60)
        for i, (dept, count) in enumerate(dept_stats, 1):
            print(f'  {i:2d}. {dept:<30}: {count:>3} 人')

        print()

        # 职位统计
        pos_stats = (
            db.query(
                User.position,
                func.count(User.id).label("count"),
            )
            .filter(User.position.isnot(None))
            .group_by(User.position)
            .order_by(func.count(User.id).desc())
            .limit(10)
            .all()
        )

        print('💼 职位用户分布:')
        print('-' * 60)
        for i, (pos, count) in enumerate(pos_stats, 1):
            print(f'  {i:2d}. {pos:<30}: {count:>3} 人')

        print()

        # 认证方式统计
        auth_stats = db.query(
            User.auth_type,
            func.count(User.id).label('count')
        ).group_by(User.auth_type).all()

        print('🔐 认证方式分布:')
        print('-' * 60)
        for auth_type, count in auth_stats:
            print(f'  {auth_type:<15}: {count:>3} 人')

        print()

        # 用户状态统计
        active_count = db.query(User).filter(User.is_active == True).count()
        inactive_count = total_users - active_count
        superuser_count = db.query(User).filter(User.is_superuser == True).count()

        print('📊 用户状态分布:')
        print('-' * 60)
        print(f'  ✅ 活跃用户: {active_count} 人')
        print(f'  ❌ 非活跃用户: {inactive_count} 人')
        print(f'  👑 超级管理员: {superuser_count} 人')
        print()

        # 平均统计
        avg_users_per_role = total_users / total_roles if total_roles > 0 else 0
        roles_with_users = len([r for r in role_stats if r[1] > 0])

        print('📈 平均统计信息:')
        print('-' * 60)
        print(f'  📊 平均每角色用户数: {avg_users_per_role:.1f}')
        print(f'  🏷️ 有用户的角色数: {roles_with_users}/{total_roles}')
        print(f'  📊 空角色比例: {((total_roles-roles_with_users)/total_roles*100):.1f}%')

if __name__ == "__main__":
    main()
