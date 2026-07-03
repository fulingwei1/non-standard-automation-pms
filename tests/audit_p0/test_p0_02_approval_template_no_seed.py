# -*- coding: utf-8 -*-
"""
P0-2: 审批模板无种子。scripts/init_db.py / init_data / migrations 均不写 approval_templates。

正确行为：一个全新初始化的数据库应带有审批模板种子（>0 行），否则任何新部署审批全瘫。
复现方式：对一个全新空 sqlite 跑 scripts/init_db.py，然后统计 approval_templates 行数。
当前必然为 0（或表都不建）-> 失败即证明无种子。
"""
import os
import sqlite3
import subprocess
import sys

import pytest

pytestmark = pytest.mark.audit_p0


def _count_templates(db_file):
    con = sqlite3.connect(db_file)
    try:
        cur = con.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='approval_templates'"
        )
        if cur.fetchone()[0] == 0:
            return None  # 表都不存在
        return con.execute("SELECT count(*) FROM approval_templates").fetchone()[0]
    finally:
        con.close()


def test_fresh_init_db_seeds_approval_templates(repo_root, tmp_path):
    fresh_db = tmp_path / "fresh_init.db"
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)  # 强制走 SQLITE_DB_PATH
    env.pop("POSTGRES_URL", None)
    env.update({"SQLITE_DB_PATH": str(fresh_db), "DEBUG": "true"})

    proc = subprocess.run(
        [sys.executable, "scripts/init_db.py"],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert fresh_db.exists(), f"init_db 未生成数据库\nstdout={proc.stdout}\nstderr={proc.stderr[-800:]}"

    count = _count_templates(str(fresh_db))
    assert count is not None and count > 0, (
        f"init_db 后 approval_templates 种子行数={count!r}（None=表不存在）。"
        f"新环境审批模板为空 -> 所有审批提交必抛『审批模板不存在』。"
        f"\ninit_db stdout tail: {proc.stdout[-400:]}"
    )
