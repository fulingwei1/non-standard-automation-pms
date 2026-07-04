# -*- coding: utf-8 -*-
"""
P0-9: 现场调试签到/完工全链假实现。

POST /field/tasks/{id}/checkin 只回『签到已记录』成功消息，不写 field_checkins。
（field_commissioning.py:70-111 假实现）。

正确行为：签到成功后 field_checkins 应新增一行。当前不写库 -> 数据全丢。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def _count(conn):
    return conn.execute("SELECT count(*) FROM field_checkins").fetchone()[0]


def _create_task(conn, task_no):
    row = conn.execute(
        """
        INSERT INTO field_tasks (
            task_no,
            customer_name,
            project_name,
            address,
            status,
            progress
        )
        VALUES (?, '审计客户', '现场调试审计项目', '审计现场', 'pending', 0)
        RETURNING id
        """,
        (task_no,),
    ).fetchone()
    conn.commit()
    return int(row[0])


def _task_row(conn, task_id):
    conn.row_factory = None
    return conn.execute(
        """
        SELECT status, progress, progress_note, completion_signature, completion_time
        FROM field_tasks
        WHERE id=?
        """,
        (task_id,),
    ).fetchone()


def _issue_count(conn, task_id):
    return conn.execute("SELECT count(*) FROM field_issues WHERE task_id=?", (task_id,)).fetchone()[0]


def test_field_checkin_persists_a_row(api, sandbox_conn):
    before = _count(sandbox_conn)

    r = api.post(
        "/field/tasks/1/checkin",
        json={"location": "audit-site", "note": "p0-repro", "latitude": 0, "longitude": 0},
    )
    # 端点自称成功
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("success") is True or body.get("code") == 200, body

    # sqlite 需要新连接才能看到服务进程已提交的写入
    import sqlite3

    con2 = sqlite3.connect(sandbox_conn.execute("PRAGMA database_list").fetchone()[2])
    try:
        after = con2.execute("SELECT count(*) FROM field_checkins").fetchone()[0]
    finally:
        con2.close()

    # 正确行为：成功签到必须落库
    assert after > before, (
        f"checkin 返回成功但 field_checkins 无新增（{before} -> {after}）：数据全部丢失"
    )


def test_field_progress_persists_to_task(api, sandbox_conn):
    task_id = _create_task(sandbox_conn, "P0-FIELD-PROGRESS")

    r = api.post(
        f"/field/tasks/{task_id}/progress",
        json={"progress": 45, "note": "完成设备上电"},
    )
    assert r.status_code == 200, r.text

    import sqlite3

    con2 = sqlite3.connect(sandbox_conn.execute("PRAGMA database_list").fetchone()[2])
    try:
        status, progress, note, _, _ = _task_row(con2, task_id)
    finally:
        con2.close()

    assert status == "in_progress"
    assert progress == 45
    assert note == "完成设备上电"


def test_field_issue_and_completion_persist_to_task(api, sandbox_conn):
    task_id = _create_task(sandbox_conn, "P0-FIELD-COMPLETE")
    before_issues = _issue_count(sandbox_conn, task_id)

    issue = api.post(
        f"/field/tasks/{task_id}/issue",
        json={"title": "气源压力不足", "description": "现场气压低于调试要求"},
    )
    assert issue.status_code == 200, issue.text

    import sqlite3

    db_path = sandbox_conn.execute("PRAGMA database_list").fetchone()[2]
    con2 = sqlite3.connect(db_path)
    try:
        after_issues = _issue_count(con2, task_id)
        _, _, note, _, _ = _task_row(con2, task_id)
    finally:
        con2.close()
    assert after_issues > before_issues
    assert "气源压力不足" in note
    assert "现场气压低于调试要求" in note

    complete = api.post(
        f"/field/tasks/{task_id}/complete",
        json={"signature": "客户代表张三", "note": "SAT 调试完成"},
    )
    assert complete.status_code == 200, complete.text

    con3 = sqlite3.connect(db_path)
    try:
        status, progress, note, signature, completed_at = _task_row(con3, task_id)
    finally:
        con3.close()

    assert status == "completed"
    assert progress == 100
    assert note == "SAT 调试完成"
    assert signature == "客户代表张三"
    assert completed_at is not None
