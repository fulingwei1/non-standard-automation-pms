#!/usr/bin/env python3
"""
检查剩余测试账户的依赖关系
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.api.deps import get_db
from app.models.user import User


def main():
    problem_users = [1, 210, 211]  # admin, engineer_test, pm_test

    db = next(get_db())
    try:
        for user_id in problem_users:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                print(f"\n检查用户: {user.username} (ID: {user.id})")

                # 检查项目创建者
                projects_created = db.execute(
                    text("SELECT COUNT(*) FROM projects WHERE created_by = :user_id"),
                    {"user_id": user_id},
                ).scalar()
                if projects_created > 0:
                    print(f"  - 创建了 {projects_created} 个项目")

                # 检查项目管理
                projects_managed = db.execute(
                    text("SELECT COUNT(*) FROM projects WHERE pm_id = :user_id"),
                    {"user_id": user_id},
                ).scalar()
                if projects_managed > 0:
                    print(f"  - 管理 {projects_managed} 个项目")

                # 检查员工记录
                employee = db.execute(
                    text("SELECT * FROM employees WHERE id = :emp_id"),
                    {"emp_id": user.employee_id},
                ).fetchone()
                if employee:
                    print(f"  - 关联员工ID: {user.employee_id}")

                # 检查其他可能的依赖
                try:
                    issues_created = db.execute(
                        text(
                            "SELECT COUNT(*) FROM issues WHERE reporter_id = :user_id"
                        ),
                        {"user_id": user_id},
                    ).scalar()
                    if issues_created > 0:
                        print(f"  - 创建了 {issues_created} 个问题")
                except Exception:
                    pass

                try:
                    issues_assigned = db.execute(
                        text(
                            "SELECT COUNT(*) FROM issues WHERE assignee_id = :user_id"
                        ),
                        {"user_id": user_id},
                    ).scalar()
                    if issues_assigned > 0:
                        print(f"  - 分配了 {issues_assigned} 个问题")
                except Exception:
                    pass

    finally:
        db.close()


if __name__ == "__main__":
    main()
