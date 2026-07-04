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


def _insert_assignment(conn, *, engineer_id, project_id, start_date, end_date, assignment_no):
    conn.execute(
        """
        INSERT INTO engineer_task_assignments (
            assignment_no,
            engineer_id,
            project_id,
            task_type,
            task_description,
            estimated_hours,
            planned_start_date,
            planned_end_date,
            status,
            priority,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, '现场调试', 'P0 冲突复现任务', 8, ?, ?, 'PENDING', 50, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (assignment_no, engineer_id, project_id, start_date, end_date),
    )
    conn.commit()


def _insert_dispatch_order(conn, *, project_id, scheduled_date, order_no):
    row = conn.execute(
        """
        INSERT INTO installation_dispatch_orders (
            order_no,
            project_id,
            customer_id,
            task_type,
            task_title,
            scheduled_date,
            estimated_hours,
            status,
            priority,
            created_at,
            updated_at
        )
        VALUES (?, ?, 1, 'DEBUGGING', 'P0 冲突派工单', ?, 8, 'PENDING', 'NORMAL', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id
        """,
        (order_no, project_id, scheduled_date),
    ).fetchone()
    conn.commit()
    return int(row[0])


def test_conflict_detect_endpoint_reports_overlap(api, sandbox_conn):
    """重叠时间、不同项目、同一工程师必须返回冲突。"""
    _insert_assignment(
        sandbox_conn,
        engineer_id=1,
        project_id=1001,
        start_date="2026-07-01",
        end_date="2026-07-10",
        assignment_no="P0-CONFLICT-EXISTING",
    )

    r = api.post(
        "/engineer-scheduling/engineers/1/conflict-detect",
        json={
            "project_id": 1002,
            "planned_start_date": "2026-07-05",
            "planned_end_date": "2026-07-12",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("conflict_count", 0) > 0
    conflict = body["conflicts"][0]
    assert conflict["conflict_project_id"] == 1001
    assert conflict["overlap_start"] == "2026-07-05"
    assert conflict["overlap_end"] == "2026-07-10"


def test_installation_dispatch_assign_blocks_overlapping_engineer(api, sandbox_conn):
    _insert_assignment(
        sandbox_conn,
        engineer_id=1,
        project_id=2001,
        start_date="2026-07-01",
        end_date="2026-07-10",
        assignment_no="P0-DISPATCH-CONFLICT-EXISTING",
    )
    order_id = _insert_dispatch_order(
        sandbox_conn,
        project_id=2002,
        scheduled_date="2026-07-05",
        order_no="P0-DISPATCH-CONFLICT-ORDER",
    )

    r = api.put(
        f"/installation-dispatch/orders/{order_id}/assign",
        json={"assigned_to_id": 1},
    )

    assert r.status_code == 409, r.text
    body = r.json()
    assert body["detail"]["conflict_count"] > 0

    row = sandbox_conn.execute(
        "SELECT status, assigned_to_id FROM installation_dispatch_orders WHERE id=?",
        (order_id,),
    ).fetchone()
    assert row == ("PENDING", None)
