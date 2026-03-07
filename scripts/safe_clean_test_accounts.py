#!/usr/bin/env python3
"""
安全的测试账户清理脚本 - 处理外键约束
先清理相关数据，再删除用户账户
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.role import Role
from app.models.user import User


def get_test_accounts():
    """获取测试账户列表"""
    test_patterns = [
        "admin",  # 系统管理员
        "pwd_test_user",  # 密码测试用户
        "engineer_test",  # 工程师一号
        "pm_test",  # 项目经理
        "pwd_test_",  # 批量密码测试用户前缀
    ]

    test_accounts = []

    db = next(get_db())
    try:
        users = db.query(User).all()
        for user in users:
            username = user.username.lower()
            if any(pattern in username for pattern in test_patterns):
                test_accounts.append(user)
    finally:
        db.close()

    return test_accounts


def get_project_manager():
    """获取项目经理谭章斌"""
    db = next(get_db())
    try:
        return db.query(User).filter(User.username == "tanzhangbin").first()
    finally:
        db.close()


def cleanup_user_related_data(db: Session, user_id: int):
    """清理用户相关的数据"""
    print(f"  🧹 清理用户ID {user_id} 的相关数据...")

    # 清理项目相关数据
    try:
        # 项目成员
        db.execute(f"DELETE FROM project_members WHERE user_id = {user_id}")

        # 任务分配
        db.execute(f"DELETE FROM task_assignments WHERE user_id = {user_id}")

        # 工时记录
        db.execute(f"DELETE FROM timesheets WHERE user_id = {user_id}")

        # 审批记录
        db.execute(f"DELETE FROM approval_records WHERE approver_id = {user_id}")
        db.execute(f"DELETE FROM approval_records WHERE requester_id = {user_id}")

        # 问题跟踪
        db.execute(f"DELETE FROM issues WHERE reporter_id = {user_id}")
        db.execute(f"DELETE FROM issues WHERE assignee_id = {user_id}")

        # 文件上传
        db.execute(f"DELETE FROM uploaded_files WHERE uploaded_by = {user_id}")

        # 系统日志
        db.execute(f"DELETE FROM system_logs WHERE user_id = {user_id}")

        db.commit()
        print(f"  ✅ 清理完成用户ID {user_id} 的相关数据")

    except Exception as e:
        print(f"  ⚠️ 清理用户ID {user_id} 数据时出错: {e}")
        db.rollback()


def safe_delete_test_accounts():
    """安全删除测试账户"""
    print("🧹 安全清理测试账户（处理外键约束）")
    print("=" * 60)

    # 获取测试账户
    test_accounts = get_test_accounts()
    print(f"📊 找到 {len(test_accounts)} 个测试/演示账户")

    # 获取项目经理
    project_manager = get_project_manager()
    pm_count = 1 if project_manager else 0
    print(f"👥 查找项目经理用户（谭章斌）: {pm_count} 个")

    if project_manager:
        print(
            f"  - {project_manager.username} ({project_manager.real_name}) - {project_manager.department}"
        )

    # 获取当前用户总数
    db = next(get_db())
    try:
        initial_users = db.query(User).count()
        print(f"📊 初始用户数: {initial_users}")

        # 逐个删除测试账户
        deleted_count = 0
        for user in test_accounts:
            print(f"  🗑️ 准备删除: {user.username} ({user.real_name})")

            # 清理相关数据
            cleanup_user_related_data(db, user.id)

            try:
                # 删除用户
                db.delete(user)
                db.commit()
                deleted_count += 1
                print(f"  ✅ 删除成功: {user.username}")
            except Exception as e:
                print(f"  ❌ 删除失败: {user.username} - {e}")
                db.rollback()

        # 最终用户数
        final_users = db.query(User).count()

        print(f"\n🎉 清理完成总结:")
        print(f"=" * 60)
        print(f"📊 初始用户数: {initial_users}")
        print(f"🗑️ 删除测试账户: {deleted_count}")
        print(f"📊 最终用户数: {final_users}")
        print(f"🎯 预期用户数: 174")
        print(f"✅ 差额: {abs(final_users - 174)}")

        # 确认项目经理保护
        if project_manager:
            pm_check = db.query(User).filter(User.username == "tanzhangbin").first()
            if pm_check:
                print(f"\n👑 项目经理保护状态:")
                print(f"  ✅ 账户保留: {pm_check.username} ({pm_check.real_name})")
                print(f"  ✅ 角色确认: {pm_check.role}")
            else:
                print(f"\n❌ 项目经理账户异常!")

    finally:
        db.close()


def ensure_project_manager_role():
    """确保谭章斌有项目经理角色"""
    print("\n🛡️ 确保项目经理角色")
    print("=" * 60)

    db = next(get_db())
    try:
        # 获取项目经理角色
        pm_role = db.query(Role).filter(Role.name == "项目经理").first()

        # 获取谭章斌用户
        tanzhangbin = db.query(User).filter(User.username == "tanzhangbin").first()

        if tanzhangbin and pm_role:
            if tanzhangbin.role_id != pm_role.id:
                tanzhangbin.role_id = pm_role.id
                db.commit()
                print(f"  ✅ 已为谭章斌设置项目经理角色")
            else:
                print(f"  ✅ 谭章斌已有项目经理角色")
        else:
            if not tanzhangbin:
                print(f"  ❌ 未找到谭章斌用户")
            if not pm_role:
                print(f"  ❌ 未找到项目经理角色")

    finally:
        db.close()


def main():
    """主函数"""
    try:
        # 确保项目经理角色
        ensure_project_manager_role()

        # 安全删除测试账户
        safe_delete_test_accounts()

        print(f"\n🎉 账户清理完成!")

    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
