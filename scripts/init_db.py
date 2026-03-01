#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化本地 SQLite 数据库（全量表结构 + 迁移补丁 + 默认账号）

用途：
1) 重建 data/app.db
2) 创建当前模型对应的完整表结构
3) 尝试执行 migrations/*_sqlite.sql（兼容性错误会跳过）
4) 写入默认测试账号
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple


IGNORABLE_ERROR_SNIPPETS = (
    "already exists",
    "duplicate column name",
    "no such table",
    "no such column",
    "has no column named",
    "UNIQUE constraint failed",
    "NOT NULL constraint failed",
    "FOREIGN KEY constraint failed",
    "cannot add a NOT NULL column with default value NULL",
)


def split_sql_statements(sql_script: str) -> Iterable[str]:
    """轻量 SQL 分句器（足够覆盖当前迁移脚本场景）。"""
    for stmt in sql_script.split(";"):
        stripped = stmt.strip()
        if stripped:
            yield stripped


def apply_sqlite_migrations(db_path: Path, migration_files: Iterable[Path]) -> Tuple[int, int]:
    """
    尝试执行 sqlite 迁移。

    返回:
        (成功执行语句数, 忽略语句数)
    """
    applied = 0
    skipped = 0

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        for migration_file in migration_files:
            sql_script = migration_file.read_text(encoding="utf-8")
            print(f"  - 执行迁移: {migration_file.name}")
            try:
                cursor.executescript(sql_script)
                applied += 1
                continue
            except sqlite3.Error:
                pass

            for statement in split_sql_statements(sql_script):
                normalized = statement.strip().upper()
                if normalized in {"BEGIN", "COMMIT", "END", "ROLLBACK"}:
                    skipped += 1
                    continue
                if normalized.startswith("BEGIN "):
                    skipped += 1
                    continue

                try:
                    cursor.execute(statement)
                    applied += 1
                except sqlite3.Error as exc:
                    skipped += 1
                    continue

        conn.commit()

    return applied, skipped


def seed_default_accounts() -> None:
    """初始化默认账号（admin/pm/sales/eng）。"""
    from app.core import security
    from app.models.base import get_db_session
    from app.models.organization import Employee
    from app.models.user import Role, User, UserRole

    accounts = [
        {
            "username": "admin",
            "password": "admin123",
            "employee_code": "E0001",
            "name": "系统管理员",
            "department": "IT",
            "position": "系统管理员",
            "role_code": "ADMIN",
            "role_name": "系统管理员",
            "is_superuser": True,
        },
        {
            "username": "pm001",
            "password": "pm123",
            "employee_code": "E0002",
            "name": "项目经理",
            "department": "项目管理部",
            "position": "项目经理",
            "role_code": "PM",
            "role_name": "项目经理",
            "is_superuser": False,
        },
        {
            "username": "sales001",
            "password": "sales123",
            "employee_code": "E0003",
            "name": "销售代表",
            "department": "销售部",
            "position": "销售工程师",
            "role_code": "SALES",
            "role_name": "销售人员",
            "is_superuser": False,
        },
        {
            "username": "eng001",
            "password": "eng123",
            "employee_code": "E0004",
            "name": "工程师",
            "department": "工程技术部",
            "position": "机械工程师",
            "role_code": "ENGINEER",
            "role_name": "工程师",
            "is_superuser": False,
        },
    ]

    with get_db_session() as db:
        for item in accounts:
            employee = db.query(Employee).filter(
                Employee.employee_code == item["employee_code"]
            ).first()
            if not employee:
                employee = Employee(
                    employee_code=item["employee_code"],
                    name=item["name"],
                    department=item["department"],
                    role=item["position"],
                    is_active=True,
                    employment_status="active",
                )
                db.add(employee)
                db.flush()

            role = db.query(Role).filter(Role.role_code == item["role_code"]).first()
            if not role:
                role = Role(
                    role_code=item["role_code"],
                    role_name=item["role_name"],
                    description=f"系统初始化角色: {item['role_name']}",
                    data_scope="ALL" if item["is_superuser"] else "OWN",
                    is_system=item["is_superuser"],
                    is_active=True,
                    role_type="SYSTEM" if item["is_superuser"] else "BUSINESS",
                    scope_type="GLOBAL",
                    level=0 if item["is_superuser"] else 2,
                    status="ACTIVE",
                )
                db.add(role)
                db.flush()

            user = db.query(User).filter(User.username == item["username"]).first()
            password_hash = security.get_password_hash(item["password"])
            if not user:
                user = User(
                    username=item["username"],
                    employee_id=employee.id,
                    password_hash=password_hash,
                    real_name=item["name"],
                    employee_no=item["employee_code"],
                    department=item["department"],
                    position=item["position"],
                    is_active=True,
                    is_superuser=item["is_superuser"],
                    auth_type="password",
                )
                db.add(user)
                db.flush()
            else:
                user.employee_id = employee.id
                user.password_hash = password_hash
                user.real_name = item["name"]
                user.department = item["department"]
                user.position = item["position"]
                user.is_active = True
                user.is_superuser = item["is_superuser"]

            user_role = db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            ).first()
            if not user_role:
                db.add(UserRole(user_id=user.id, role_id=role.id))


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化本地 SQLite 数据库")
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="仅创建模型表结构，不执行 migrations/*_sqlite.sql",
    )
    args = parser.parse_args()

    from app.core.config import settings
    from app.models.base import Base, get_engine, reset_engine
    import app.models  # noqa: F401  注册全部模型

    project_root = Path(__file__).resolve().parents[1]
    db_path = Path(settings.SQLITE_DB_PATH)
    if not db_path.is_absolute():
        db_path = project_root / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        backup_path = db_path.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
        )
        shutil.copy2(db_path, backup_path)
        db_path.unlink()
        print(f"已备份并删除旧数据库: {backup_path}")

    db_url = f"sqlite:///{db_path}"
    reset_engine()
    engine = get_engine(database_url=db_url)
    Base.metadata.create_all(bind=engine)
    print(f"已创建模型表结构，数据库: {db_path}")

    if not args.skip_migrations:
        migration_dir = project_root / "migrations"
        migration_files = sorted(migration_dir.glob("*_sqlite.sql"))
        print(f"开始执行 SQLite 迁移脚本，共 {len(migration_files)} 个文件...")
        applied, skipped = apply_sqlite_migrations(db_path, migration_files)
        print(f"迁移执行完成：成功语句 {applied}，忽略语句 {skipped}")
    else:
        print("已跳过迁移脚本执行。")

    seed_default_accounts()
    print("默认账号初始化完成：admin / pm001 / sales001 / eng001")
    print("数据库初始化完成。")


if __name__ == "__main__":
    main()
