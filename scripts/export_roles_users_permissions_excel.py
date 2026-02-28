#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export roles/users/permissions mapping from SQLite to Excel.

Generates an xlsx with multiple sheets:
- 角色清单
- 权限清单
- 角色-权限
- 用户清单
- 用户-角色
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Sequence, Tuple

import pandas as pd


@dataclass(frozen=True)
class ExportPaths:
    project_root: Path
    db_path: Path
    output_dir: Path
    output_path: Path


def _project_root() -> Path:
    # scripts/ -> project root
    return Path(__file__).resolve().parents[1]


def _default_paths() -> ExportPaths:
    root = _project_root()
    db_path = root / "data" / "app.db"
    output_dir = root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"角色_用户_权限清单_{ts}.xlsx"
    return ExportPaths(
        project_root=root,
        db_path=db_path,
        output_dir=output_dir,
        output_path=output_path,
    )

EXCLUDED_ROLE_CODES = {"ROLE_01FD11"}
EXCLUDED_ROLE_NAMES = {"测试角色-01fd11"}

EXCLUDED_USERNAMES = {
    # 用户提出要从清单中移除的测试/演示账号
    "test_user_4dc3ad",
}

EXCLUDED_REAL_NAMES = {
    "系统管理员",
    "工程师一号",
    "项目经理",
    "密码测试用户",
    "普通业务用户",
    "销售用户",
    "普通用户",
}


def _read_sql(db_path: Path, sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")
    with sqlite3.connect(str(db_path)) as conn:
        return pd.read_sql_query(sql, conn, params=params or ())


def _safe_sheet_name(name: str) -> str:
    # Excel sheet name limit 31 chars
    if len(name) <= 31:
        return name
    return name[:31]


def _autosize_columns(writer: pd.ExcelWriter, df: pd.DataFrame, sheet_name: str) -> None:
    # Works for openpyxl engine
    ws = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns, start=1):
        series = df[col].astype(str).fillna("")
        max_len = max([len(str(col))] + [len(v) for v in series.values.tolist()]) if len(series) else len(str(col))
        # cap width to avoid insane columns
        width = min(max(10, max_len + 2), 60)
        ws.column_dimensions[chr(64 + idx)].width = width if idx <= 26 else width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def main() -> None:
    paths = _default_paths()

    # Roles
    roles_df = _read_sql(
        paths.db_path,
        """
        SELECT
            id AS role_id,
            role_code,
            role_name,
            data_scope,
            is_active,
            is_system,
            role_type,
            scope_type,
            level,
            status,
            sort_order,
            description
        FROM roles
        ORDER BY role_code
        """,
    )
    if not roles_df.empty:
        roles_df = roles_df[
            ~roles_df["role_code"].isin(EXCLUDED_ROLE_CODES)
            & ~roles_df["role_name"].isin(EXCLUDED_ROLE_NAMES)
        ].copy()

    # Permissions
    perms_df = _read_sql(
        paths.db_path,
        """
        SELECT
            id AS permission_id,
            perm_code,
            perm_name,
            module,
            action,
            resource,
            is_active,
            permission_type,
            description
        FROM permissions
        ORDER BY perm_code
        """,
    )

    # Role-Permission mapping (one row per mapping)
    role_perm_df = _read_sql(
        paths.db_path,
        """
        SELECT
            r.id AS role_id,
            r.role_code,
            r.role_name,
            r.data_scope,
            p.id AS permission_id,
            p.perm_code,
            p.perm_name,
            p.module,
            p.action,
            p.resource,
            p.is_active AS permission_is_active
        FROM role_permissions rp
        JOIN roles r ON r.id = rp.role_id
        JOIN permissions p ON p.id = rp.permission_id
        ORDER BY r.role_code, p.perm_code
        """,
    )
    if not role_perm_df.empty:
        role_perm_df = role_perm_df[
            ~role_perm_df["role_code"].isin(EXCLUDED_ROLE_CODES)
            & ~role_perm_df["role_name"].isin(EXCLUDED_ROLE_NAMES)
        ].copy()

    # Add permission_count and permission_list summary to roles
    if not role_perm_df.empty:
        role_perm_agg = (
            role_perm_df.groupby(["role_id", "role_code"])["perm_code"]
            .agg(permission_count="count", permission_codes=lambda s: ", ".join(sorted(set(s.astype(str).tolist()))))
            .reset_index()
        )
        roles_df = roles_df.merge(role_perm_agg[["role_id", "permission_count", "permission_codes"]], on="role_id", how="left")
    else:
        roles_df["permission_count"] = 0
        roles_df["permission_codes"] = ""

    roles_df["permission_count"] = roles_df["permission_count"].fillna(0).astype(int)
    roles_df["permission_codes"] = roles_df["permission_codes"].fillna("")

    # Users
    users_df = _read_sql(
        paths.db_path,
        """
        SELECT
            id AS user_id,
            employee_id,
            username,
            real_name,
            employee_no,
            department,
            position,
            email,
            phone,
            is_active,
            is_superuser,
            last_login_at,
            created_at,
            updated_at
        FROM users
        ORDER BY username
        """,
    )

    # User-Role mapping (one row per mapping)
    user_role_df = _read_sql(
        paths.db_path,
        """
        SELECT
            u.id AS user_id,
            u.username,
            u.real_name,
            u.department,
            r.id AS role_id,
            r.role_code,
            r.role_name,
            r.data_scope,
            r.is_active AS role_is_active
        FROM user_roles ur
        JOIN users u ON u.id = ur.user_id
        JOIN roles r ON r.id = ur.role_id
        ORDER BY u.username, r.role_code
        """,
    )

    if not users_df.empty:
        users_df = users_df[
            ~users_df["username"].isin(EXCLUDED_USERNAMES)
            & ~users_df["real_name"].isin(EXCLUDED_REAL_NAMES)
        ].copy()

    if not user_role_df.empty:
        user_role_df = user_role_df[
            ~user_role_df["role_code"].isin(EXCLUDED_ROLE_CODES)
            & ~user_role_df["role_name"].isin(EXCLUDED_ROLE_NAMES)
        ].copy()

    # Apply user exclusions to user-role mapping
    if not user_role_df.empty and not users_df.empty:
        allowed_user_ids = set(users_df["user_id"].tolist())
        user_role_df = user_role_df[user_role_df["user_id"].isin(allowed_user_ids)].copy()

    # Add aggregated roles info to users
    if not user_role_df.empty:
        user_roles_agg = (
            user_role_df.groupby(["user_id", "username"])["role_code"]
            .agg(role_count="count", role_codes=lambda s: ", ".join(sorted(set(s.astype(str).tolist()))))
            .reset_index()
        )
        users_df = users_df.merge(user_roles_agg[["user_id", "role_count", "role_codes"]], on="user_id", how="left")
    else:
        users_df["role_count"] = 0
        users_df["role_codes"] = ""

    users_df["role_count"] = users_df["role_count"].fillna(0).astype(int)
    users_df["role_codes"] = users_df["role_codes"].fillna("")

    # Write Excel
    with pd.ExcelWriter(paths.output_path, engine="openpyxl") as writer:
        sheets: List[Tuple[str, pd.DataFrame]] = [
            ("角色清单", roles_df),
            ("权限清单", perms_df),
            ("角色-权限", role_perm_df),
            ("用户清单", users_df),
            ("用户-角色", user_role_df),
        ]
        for sheet_name, df in sheets:
            safe_name = _safe_sheet_name(sheet_name)
            df.to_excel(writer, sheet_name=safe_name, index=False)
            _autosize_columns(writer, df, safe_name)

    print(f"OK: {paths.output_path}")


if __name__ == "__main__":
    main()
