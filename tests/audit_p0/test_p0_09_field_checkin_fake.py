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
