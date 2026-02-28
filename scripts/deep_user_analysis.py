#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度用户数据分析 - 解决数据差异问题
"""

import sys

sys.path.append('/Users/flw/non-standard-automation-pm')


from app.models.base import SessionLocal
from app.models.user import User, UserRole


def analyze_user_discrepancy():
    """分析用户数据差异"""
    with SessionLocal() as db:
        print("🔍 用户数据差异深度分析")
        print("=" * 60)

        # 1. 检查总用户数
        total_users = db.query(User).count()
        print(f"📊 数据库中总用户数: {total_users}")

        # 2. 检查用户详细信息
        users = db.query(User).all()

        print(f"\n👥 详细用户分析:")
        print("-" * 60)

        # 统计不同状态的用户
        active_users = 0
        inactive_users = 0
        superuser_users = 0
        demo_users = 0
        real_users = 0

        employee_ids = []
        usernames = []

        for user in users:
            if user.is_active:
                active_users += 1
            else:
                inactive_users += 1

            if user.is_superuser:
                superuser_users += 1

            # 检查是否是演示/测试用户
            if (user.username and (
                'admin' in user.username.lower() or
                'test' in user.username.lower() or
                'demo' in user.username.lower() or
                'guest' in user.username.lower()
            )):
                demo_users += 1
            else:
                real_users += 1

            # 收集员工ID和用户名
            if user.employee_id:
                employee_ids.append(user.employee_id)
            if user.username:
                usernames.append(user.username)

        print(f"  ✅ 活跃用户: {active_users}")
        print(f"  ❌ 非活跃用户: {inactive_users}")
        print(f"  👑 超级管理员: {superuser_users}")
        print(f"  🧪 演示/测试用户: {demo_users}")
        print(f"  👤 真实用户: {real_users}")

        # 3. 检查重复的员工ID
        unique_employee_ids = len(set(employee_ids))
        duplicate_employee_ids = len(employee_ids) - unique_employee_ids

        print(f"\n🆔 员工ID分析:")
        print("-" * 60)
        print(f"  总员工ID数: {len(employee_ids)}")
        print(f"  唯一员工ID数: {unique_employee_ids}")
        print(f"  重复员工ID数: {duplicate_employee_ids}")

        if duplicate_employee_ids > 0:
            # 找出重复的员工ID
            from collections import Counter
            id_counts = Counter(employee_ids)
            duplicates = [id for id, count in id_counts.items() if count > 1]
            print(f"  重复的员工ID: {duplicates}")

        # 4. 检查用户名模式
        print(f"\n👤 用户名模式分析:")
        print("-" * 60)

        # 检查用户名生成模式
        pattern_users = 0
        auto_generated = 0

        for username in usernames:
            if username:
                # 检查是否是自动生成的用户名
                if any(pattern in username.lower() for pattern in ['user', 'user_', 'test', 'demo', 'guest']):
                    pattern_users += 1
                if any(username.startswith(prefix) for prefix in ['user_', 'test_', 'demo_']):
                    auto_generated += 1

        print(f"  模式化用户名: {pattern_users}")
        print(f"  自动生成用户名: {auto_generated}")

        # 5. 检查部门分布
        print(f"\n🏢 部门分布详细:")
        print("-" * 60)

        dept_counts = {}
        for user in users:
            dept = user.department or "未知部门"
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dept:<30}: {count:>3} 人")

        # 6. 检查角色关联情况
        print(f"\n🏷️ 角色关联分析:")
        print("-" * 60)

        # 用户-角色关联统计
        user_role_count = db.query(UserRole).count()
        users_with_roles = db.query(UserRole.user_id).distinct().count()

        print(f"  用户-角色关联记录数: {user_role_count}")
        print(f"  有角色的用户数: {users_with_roles}")
        print(f"  没有角色的用户数: {total_users - users_with_roles}")

        # 7. 检查是否有测试数据
        print(f"\n🧪 测试数据检查:")
        print("-" * 60)

        # 查找可能的测试账户
        test_accounts = []
        for user in users:
            if user.username and (
                'admin' in user.username.lower() or
                'test' in user.username.lower() or
                'demo' in user.username.lower()
            ):
                test_accounts.append({
                    'username': user.username,
                    'real_name': user.real_name,
                    'department': user.department,
                    'is_active': user.is_active,
                    'is_superuser': user.is_superuser,
                    'created_at': user.created_at
                })

        print(f"  可能的测试账户数: {len(test_accounts)}")

        if test_accounts:
            print("  测试账户列表:")
            for i, account in enumerate(test_accounts, 1):
                print(f"    {i}. {account['username']} - {account['real_name']} ({account['department']})")

        # 8. 检查账户创建时间
        print(f"\n📅 账户创建时间分析:")
        print("-" * 60)

        # 统计不同时期创建的账户
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_month = now - timedelta(days=30)
        recent_year = now - timedelta(days=365)

        recent_month_users = len([u for u in users if u.created_at and u.created_at >= recent_month])
        recent_year_users = len([u for u in users if u.created_at and u.created_at >= recent_year])
        old_users = len([u for u in users if u.created_at and u.created_at < recent_year])

        print(f"  最近30天创建: {recent_month_users}")
        print(f"  最近1年创建: {recent_year_users}")
        print(f"  1年前创建: {old_users}")

        # 9. 提供账号密码信息
        print(f"\n🔐 系统默认账号信息:")
        print("-" * 60)
        print("  根据分析，可能的默认账号:")
        print("  🔸 默认管理员账号: admin / admin (如果存在)")
        print("  🔸 测试账号: test / test123456 (如果存在)")
        print("  🔸 演示账号: demo / demo123456 (如果存在)")
        print("  🔸 注意：请使用真实员工账号登录")

        # 10. 总结和建议
        print(f"\n📋 差异分析总结:")
        print("=" * 60)

        if total_users > 174:  # 实际用户数比公司员工数多
            excess = total_users - 174
            print(f"❌ 数据差异: 数据库用户数({total_users}) > 实际员工数(174)")
            print(f"❌ 超出用户数: {excess}")
            print("\n可能原因:")
            print("  1. 包含测试/演示账户")
            print("  2. 包含已离职员工账户")
            print("  3. 包含重复账户")
            print("  4. 包含系统自动生成账户")
        else:
            print("✅ 用户数在合理范围内")

        print(f"\n🎯 解决方案:")
        print("1. 清理测试和演示账户")
        print("2. 停用离职员工账户")
        print("3. 去重并合并重复用户")
        print("4. 建立定期账户清理机制")

        return {
            'total_users': total_users,
            'active_users': active_users,
            'demo_users': demo_users,
            'real_users': real_users,
            'departments': dept_counts,
            'test_accounts': test_accounts
        }

if __name__ == "__main__":
    result = analyze_user_discrepancy()

    # 保存分析结果
    import json
    with open('user_discrepancy_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
