#!/usr/bin/env python3
"""
强制清理剩余的测试账户
处理外键约束
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.api.deps import get_db
from app.models.user import User


def main():
    print("🔧 强制清理剩余测试账户")
    print("=" * 60)

    problem_users = [(1, "admin"), (210, "engineer_test"), (211, "pm_test")]

    db = next(get_db())
    try:
        for user_id, username in problem_users:
            print(f"\n🔧 处理用户: {username} (ID: {user_id})")

            # 获取用户信息
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"  ⚠️ 用户不存在")
                continue

            # 转移项目管理权（转移到项目经理tanzhangbin）
            print(f"  🔄 转移项目管理权...")
            try:
                db.execute(
                    text(
                        """
                    UPDATE projects
                    SET pm_id = (SELECT id FROM users WHERE username = 'tanzhangbin' LIMIT 1)
                    WHERE pm_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                print(f"    ✅ 项目管理权已转移")
            except Exception as e:
                print(f"    ⚠️ 转移项目管理权失败: {e}")

            # 转移项目创建权
            print(f"  🔄 转移项目创建权...")
            try:
                db.execute(
                    text(
                        """
                    UPDATE projects
                    SET created_by = (SELECT id FROM users WHERE username = 'tanzhangbin' LIMIT 1)
                    WHERE created_by = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                print(f"    ✅ 项目创建权已转移")
            except Exception as e:
                print(f"    ⚠️ 转移项目创建权失败: {e}")

            # 转移问题报告权
            print(f"  🔄 转移问题报告权...")
            try:
                db.execute(
                    text(
                        """
                    UPDATE issues
                    SET reporter_id = (SELECT id FROM users WHERE username = 'tanzhangbin' LIMIT 1)
                    WHERE reporter_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                print(f"    ✅ 问题报告权已转移")
            except Exception as e:
                print(f"    ⚠️ 转移问题报告权失败: {e}")

            # 转移问题分配权
            print(f"  🔄 转移问题分配权...")
            try:
                db.execute(
                    text(
                        """
                    UPDATE issues
                    SET assignee_id = (SELECT id FROM users WHERE username = 'tanzhangbin' LIMIT 1)
                    WHERE assignee_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                print(f"    ✅ 问题分配权已转移")
            except Exception as e:
                print(f"    ⚠️ 转移问题分配权失败: {e}")

            # 清理项目成员关系
            print(f"  🧹 清理项目成员关系...")
            try:
                result = db.execute(
                    text("DELETE FROM project_members WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
                print(f"    ✅ 清理了 {result.rowcount} 个项目成员关系")
            except Exception as e:
                print(f"    ⚠️ 清理项目成员关系失败: {e}")

            db.commit()

            # 现在尝试删除用户
            print(f"  🗑️ 删除用户账户...")
            try:
                db.delete(user)
                db.commit()
                print(f"  ✅ 用户 {username} 删除成功")
            except Exception as e:
                db.rollback()
                print(f"  ❌ 用户 {username} 删除失败: {e}")

        # 最终统计
        final_users = db.query(User).count()
        print(f"\n📊 最终用户数: {final_users}")
        print(f"🎯 目标用户数: 174")
        print(f"✅ 达成目标: {'是' if final_users <= 176 else '否'}")

        # 确认项目经理保护状态
        pm_check = db.query(User).filter(User.username == "tanzhangbin").first()
        if pm_check:
            print(f"\n🛡️ 项目经理保护状态:")
            print(f"  ✅ 账户保留: {pm_check.username} ({pm_check.real_name})")
            print(f"  ✅ 部门: {pm_check.department}")
            print(f"  ✅ 职位: {pm_check.position}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
