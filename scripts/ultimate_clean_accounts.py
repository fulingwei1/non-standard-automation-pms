#!/usr/bin/env python3
"""
终极清理脚本 - 解决所有外键约束
包括employees表的外键关系
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.api.deps import get_db
from app.models.user import User


def main():
    print("🧹 终极清理测试账户")
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

            # 转移所有权到项目经理tanzhangbin
            tanzhangbin_id = db.execute(
                text("SELECT id FROM users WHERE username = 'tanzhangbin' LIMIT 1")
            ).scalar()

            if tanzhangbin_id:
                # 转移项目
                try:
                    db.execute(
                        text("UPDATE projects SET pm_id = :pm_id WHERE pm_id = :user_id"),
                        {"pm_id": tanzhangbin_id, "user_id": user_id},
                    )
                    db.execute(
                        text("UPDATE projects SET created_by = :pm_id WHERE created_by = :user_id"),
                        {"pm_id": tanzhangbin_id, "user_id": user_id},
                    )
                    print(f"    ✅ 项目已转移")
                except Exception as e:
                    print(f"    ⚠️ 转移项目失败: {e}")

                # 转移问题
                try:
                    db.execute(
                        text("UPDATE issues SET reporter_id = :pm_id WHERE reporter_id = :user_id"),
                        {"pm_id": tanzhangbin_id, "user_id": user_id},
                    )
                    db.execute(
                        text("UPDATE issues SET assignee_id = :pm_id WHERE assignee_id = :user_id"),
                        {"pm_id": tanzhangbin_id, "user_id": user_id},
                    )
                    print(f"    ✅ 问题已转移")
                except Exception as e:
                    print(f"    ⚠️ 转移问题失败: {e}")

            # 清理所有用户相关表
            cleanup_tables = [
                ("user_roles", "user_id"),
                ("project_members", "user_id"),
                ("issue_comments", "user_id"),
                ("issue_attachments", "user_id"),
                ("risk_records", "user_id"),
                ("milestone_records", "user_id"),
                ("deliverable_records", "user_id"),
                ("change_request_records", "user_id"),
                ("quality_inspection_records", "user_id"),
                ("bonus_records", "user_id"),
                ("performance_records", "user_id"),
                ("ecr_records", "user_id"),
                ("ecn_records", "user_id"),
                ("project_phases", "user_id"),
                ("deliverables", "user_id"),
            ]

            for table, column in cleanup_tables:
                try:
                    result = db.execute(
                        text(f"DELETE FROM {table} WHERE {column} = :user_id"), {"user_id": user_id}
                    )
                    if result.rowcount > 0:
                        print(f"    ✅ 清理 {table}: {result.rowcount} 条记录")
                except Exception:
                    pass  # 忽略表不存在的错误

            # 关键步骤：先删除employees记录（因为users表有外键指向employees）
            try:
                result = db.execute(
                    text("DELETE FROM employees WHERE id = :user_id"), {"user_id": user_id}
                )
                if result.rowcount > 0:
                    print(f"    ✅ 删除员工记录: {result.rowcount} 条")
            except Exception as e:
                print(f"    ⚠️ 删除员工记录失败: {e}")

            db.commit()

            # 现在可以安全删除用户
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
        print(f"\n🎉 清理完成总结:")
        print(f"=" * 60)
        print(f"📊 最终用户数: {final_users}")
        print(f"🎯 目标用户数: 174")
        print(f"✅ 达成目标: {'是' if 174 <= final_users <= 176 else '否'}")

        # 确认项目经理保护状态
        pm_check = db.query(User).filter(User.username == "tanzhangbin").first()
        if pm_check:
            print(f"\n🛡️ 项目经理保护状态:")
            print(f"  ✅ 账户保留: {pm_check.username} ({pm_check.real_name})")
            print(f"  ✅ 部门: {pm_check.department}")
            print(f"  ✅ 职位: {pm_check.position}")

        # 显示最终用户状态
        print(f"\n📋 最终用户状态:")
        users = db.query(User).all()
        test_patterns = ["admin", "pwd_test", "engineer_test", "pm_test"]
        real_users = []
        remaining_test = []

        for u in users:
            if any(pattern in u.username.lower() for pattern in test_patterns):
                remaining_test.append(u)
            else:
                real_users.append(u)

        print(f"  真实用户: {len(real_users)}")
        print(f"  剩余测试用户: {len(remaining_test)}")

        if remaining_test == []:
            print(f"  🎉 所有测试账户已清理完成!")
        else:
            print(f"  ⚠️ 仍有 {len(remaining_test)} 个测试账户未清理:")
            for u in remaining_test:
                print(f"    - {u.username} ({u.real_name})")

    finally:
        db.close()


if __name__ == "__main__":
    main()
