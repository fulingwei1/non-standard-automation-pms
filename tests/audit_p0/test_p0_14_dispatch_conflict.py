# -*- coding: utf-8 -*-
"""
P0-14: 派工冲突检测空转（依赖表不存在，静默返回 0 冲突）。

engineer_scheduling_service.py:41-47 依赖的 engineer_task_assignments 表在库中不存在，
service 捕获异常静默返回 []，conflict-detect 恒返回 0 冲突。

正确行为：
  1) 冲突检测依赖表应存在（否则算法永远空转）。
  2) 冲突检测端点应能对重叠派工返回冲突（此处以“表存在”为可测前置）。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def test_conflict_dependency_table_exists(sandbox_conn):
    row = sandbox_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='engineer_task_assignments'"
    ).fetchone()
    assert row is not None, (
        "engineer_task_assignments 依赖表不存在 -> 冲突检测 service 静默返回 []，"
        "撞期派工/替人完工无拦截"
    )


def test_conflict_detect_endpoint_reports_structure(api):
    """记录端点当前行为：因依赖表缺失，conflict_count 恒 0。"""
    r = api.post(
        "/engineer-scheduling/engineers/1/conflict-detect",
        json={"start_date": "2026-07-01", "end_date": "2026-07-10"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # 依赖表补齐后，这里应能对真正重叠的派工返回 >0；当前恒 0（空转）
    assert body.get("conflict_count", 0) == 0
