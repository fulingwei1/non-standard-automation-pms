#!/usr/bin/env python3
"""
最终的账户清理脚本 - 简化版本
专注于删除测试账户和保护项目经理
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
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

    db = next(get_db())
    try:
        users = db.query(User).all()
        test_accounts = []
        for user in users:
            username = user.username.lower()
            if any(pattern in username for pattern in test_patterns):
                test_accounts.append(user)
        return test_accounts
    finally:
        db.close()


def get_project_manager():
    """获取项目经理谭章斌"""
    db = next(get_db())
    try:
        return db.query(User).filter(User.username == "tanzhangbin").first()
    finally:
        db.close()


def cleanup_all_related_data(db: Session, user_id: int):
    """使用原生SQL清理用户相关的所有数据"""
    print(f"  🧹 清理用户ID {user_id} 的相关数据...")

    tables_to_clean = [
        ("project_members", "user_id"),
        ("task_assignments", "user_id"),
        ("timesheets", "user_id"),
        ("approval_records", "requester_id"),
        ("approval_records", "approver_id"),
        ("issues", "reporter_id"),
        ("issues", "assignee_id"),
        ("uploaded_files", "uploaded_by"),
        ("system_logs", "user_id"),
    ]

    for table, column in tables_to_clean:
        try:
            db.execute(text(f"DELETE FROM {table} WHERE {column} = :user_id"), {"user_id": user_id})
            print(f"    ✅ 清理 {table}.{column}")
        except Exception as e:
            print(f"    ⚠️ 跳过 {table}: {e}")

    db.commit()
    print(f"  ✅ 清理完成用户ID {user_id} 的相关数据")


def main():
    """主函数"""
    print("🧹 最终账户清理脚本")
    print("=" * 60)

    # 获取项目经理信息
    project_manager = get_project_manager()
    if project_manager:
        print(f"👑 找到项目经理: {project_manager.username} ({project_manager.real_name})")
    else:
        print("❌ 未找到项目经理谭章斌")
        return 1

    # 获取测试账户
    test_accounts = get_test_accounts()
    print(f"📊 找到 {len(test_accounts)} 个测试/演示账户:")
    for user in test_accounts:
        print(f"  - {user.username} ({user.real_name})")

    # 获取当前用户总数
    db = next(get_db())
    try:
        initial_users = db.query(User).count()
        print(f"\n📊 初始用户数: {initial_users}")

        # 确保项目经理不会被误删
        if project_manager in test_accounts:
            test_accounts.remove(project_manager)
            print(f"🛡️ 从删除列表中移除项目经理: {project_manager.username}")

        # 逐个删除测试账户
        deleted_count = 0
        failed_count = 0

        print(f"\n🗑️ 开始删除测试账户:")
        for user in test_accounts:
            print(f"\n  处理: {user.username} (ID: {user.id})")

            # 清理相关数据
            try:
                cleanup_all_related_data(db, user.id)
            except Exception as e:
                print(f"  ⚠️ 清理相关数据失败: {e}")

            # 尝试删除用户
            try:
                db.delete(user)
                db.commit()
                deleted_count += 1
                print(f"  ✅ 删除成功: {user.username}")
            except Exception as e:
                db.rollback()
                failed_count += 1
                print(f"  ❌ 删除失败: {user.username} - {e}")

        # 最终统计
        final_users = db.query(User).count()

        print(f"\n🎉 清理完成总结:")
        print(f"=" * 60)
        print(f"📊 初始用户数: {initial_users}")
        print(f"🗑️ 成功删除: {deleted_count}")
        print(f"❌ 删除失败: {failed_count}")
        print(f"📊 最终用户数: {final_users}")
        print(f"🎯 目标用户数: 174")
        print(f"✅ 达成目标: {'是' if final_users <= 176 else '否'}")

        # 再次确认项目经理保护状态
        pm_check = db.query(User).filter(User.username == "tanzhangbin").first()
        if pm_check:
            print(f"\n🛡️ 项目经理保护状态:")
            print(f"  ✅ 账户保留: {pm_check.username} ({pm_check.real_name})")
            print(f"  ✅ 部门: {pm_check.department}")
            print(f"  ✅ 职位: {pm_check.position}")
        else:
            print(f"\n❌ 项目经理账户异常!")

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
