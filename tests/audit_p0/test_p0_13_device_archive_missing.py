# -*- coding: utf-8 -*-
"""
P0-13: 售后无设备档案，机台级溯源断链。

service_tickets 无 machine 外键列；machines 无 serial_no/customer_id/warranty 列。
设计级缺失，无法写行为用例 —— 用 PRAGMA 断言应有的列存在。

正确行为：具备设备全生命周期溯源所需的列。当前缺失 -> 失败。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def test_service_tickets_have_machine_foreign_key(sandbox_conn):
    cols = _cols(sandbox_conn, "service_tickets")
    assert cols & {"machine_id", "machine"}, (
        f"service_tickets 无机台外键列（现有: {sorted(cols)}）—— 售后工单无法定位设备"
    )


@pytest.mark.parametrize("col", ["serial_no", "customer_id", "warranty"])
def test_machines_have_device_lifecycle_columns(col, sandbox_conn):
    cols = _cols(sandbox_conn, "machines")
    assert col in cols, (
        f"machines 缺列 {col}（现有: {sorted(cols)}）—— 无客户侧设备档案，质保只能按项目算"
    )
