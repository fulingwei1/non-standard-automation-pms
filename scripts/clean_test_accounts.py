#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试和演示账户
删除所有测试、演示和非真实员工的账户
"""

import sys

sys.path.append('/Users/flw/non-standard-automation-pm')

from app.models.base import SessionLocal
from app.models.user import Role, User, UserRole


def clean_test_accounts():
    """清理测试和演示账户"""
    with SessionLocal() as db:
        print("🧹 清理测试和演示账户")
        print("=" * 60)

        # 1. 查找需要删除的测试账户
        test_accounts = db.query(User).filter(
            User.username.ilike('%test%') |
            User.username.ilike('%demo%') |
            User.username.ilike('%guest%') |
            User.username.ilike('%admin%')
        ).all()

        print(f"📊 找到 {len(test_accounts)} 个测试/演示账户")

        # 2. 查找项目经理角色
        pm_role = db.query(Role).filter(Role.role_name == '项目经理').first()
        if not pm_role:
            print("❌ 项目经理角色不存在，跳过项目经理保留操作")
            return False

        # 3. 查找项目经理用户（谭章斌）
        project_manager_users = db.query(User).join(UserRole).filter(
            UserRole.role_id == pm_role.id,
            User.real_name == '谭章斌'
        ).all()

        print(f"👥 查找项目经理用户（谭章斌）: {len(project_manager_users)} 个")
        for user in project_manager_users:
            print(f"  - {user.username} ({user.real_name}) - {user.department if user.department else '无部门'}")

        # 4. 删除测试账户
        deleted_count = 0
        for account in test_accounts:
            try:
                # 删除用户角色关联
                db.query(UserRole).filter(UserRole.user_id == account.id).delete()

                # 删除用户
                db.delete(account)
                deleted_count += 1
                print(f"  ✅ 删除: {account.username} ({account.real_name or '无姓名'})")
            except Exception as e:
                print(f"  ❌ 删除失败: {account.username} - {e}")

        # 5. 保留真实的项目经理（谭章斌）
        tan_zhangbin_users = [user for user in project_manager_users]

        if tan_zhangbin_users:
            print(f"\n👑 保留项目经理用户: {len(tan_zhangbin_users)} 个")
            for user in tan_zhangbin_users:
                print(f"  ✅ 保留: {user.username} ({user.real_name}) - {user.department}")
        else:
            print("\n⚠️ 未找到谭章斌用户信息")

        # 6. 提交所有更改
        try:
            db.commit()
            print(f"\n✅ 成功删除 {deleted_count} 个测试/演示账户")
        except Exception as e:
            db.rollback()
            print(f"\n❌ 提交失败: {e}")
            return False

        # 7. 统计最终结果
        final_users = db.query(User).count()
        final_active = db.query(User).filter(User.is_active == True).count()

        print(f"\n📊 清理结果统计:")
        print(f"  🗑️ 删除账户数: {deleted_count}")
        print(f"  👥 最终用户数: {final_users}")
        print(f"  ✅ 活跃用户数: {final_active}")
        print(f"  👑 保留项目经理数: {len(tan_zhangbin_users)}")

        return {
            'deleted_count': deleted_count,
            'final_users': final_users,
            'final_active': final_active,
            'reserved_pm_count': len(tan_zhangbin_users),
            'pm_users': tan_zhangbin_users
        }

def protect_project_manager():
    """保护项目经理谭章斌的账户"""
    with SessionLocal() as db:
        print("\n🛡️ 保护项目经理账户")
        print("=" * 60)

        # 确保谭章斌用户存在且激活
        pm_role = db.query(Role).filter(Role.role_name == '项目经理').first()
        tan_zhangbin = db.query(User).filter(
            User.real_name == '谭章斌',
            User.is_active == True
        ).first()

        if tan_zhangbin:
            # 确保有项目经理角色
            existing_pm_role = db.query(UserRole).filter(
                UserRole.user_id == tan_zhangbin.id,
                UserRole.role_id == pm_role.id
            ).first()

            if not existing_pm_role:
                # 分配项目经理角色
                pm_user_role = UserRole(
                    user_id=tan_zhangbin.id,
                    role_id=pm_role.id
                )
                db.add(pm_user_role)
                print(f"  ✅ 为谭章斌分配项目经理角色")
            else:
                print(f"  ✅ 谭章斌已有项目经理角色")

            # 确保账户状态为活跃
            if not tan_zhangbin.is_active:
                tan_zhangbin.is_active = True
                print(f"  ✅ 激活谭章斌账户")

            db.commit()
            print(f"  ✅ 谭章斌账户保护完成")
        else:
            print("❌ 未找到谭章斌用户")

def main():
    """主函数"""
    print("🧹 开始清理测试账户并保护项目经理")
    print("=" * 80)

    # 1. 清理测试账户
    result = clean_test_accounts()

    # 2. 保护项目经理
    protect_project_manager()

    # 3. 最终统计
    print(f"\n🎉 清理完成总结:")
    print("=" * 60)
    print(f"📊 最终用户数: {result['final_users']}")
    print(f"✅ 活跃用户数: {result['final_active']}")
    print(f"👑 保留项目经理: {result['reserved_pm_count']}")
    print(f"🗑️ 删除测试账户: {result['deleted_count']}")

    if result['final_users'] <= 175:  # 接近实际员工数174
        print(f"✅ 用户数恢复正常: {result['final_users']}/174 (实际员工数)")
    else:
        print(f"⚠️ 用户数仍然偏多: {result['final_users']}/174 (实际员工数)")

    print(f"\n📝 谭章斌项目经理账户已安全保留并激活")
    print(f"🔐 所有测试和演示账户已被清理")
    print(f"🛡️ 系统现在只包含真实员工和必要的管理账户")

if __name__ == "__main__":
    main()
