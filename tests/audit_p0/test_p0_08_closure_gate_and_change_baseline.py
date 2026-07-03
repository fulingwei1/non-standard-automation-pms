# -*- coding: utf-8 -*-
"""
P0-8: 项目治理两大闸门全虚。

8a 结项无门禁：create_closure 只查重，不校验验收/成本/任务，未达标也能落 DRAFT
   （pmo/closure.py:64-144）。真正的 readiness 服务只被 advisory 端点调用。
8b 变更审批不回基线：approve_change_request 只改变更单状态+写审批记录，对 Project
   基线（planned_end_date/budget）零写入，也不调 execute_linkage
   （project_change_requests/service.py:193-242）。
"""
import re

import pytest

pytestmark = pytest.mark.audit_p0


# ---------------------------------------------------------------- 8a
def test_closure_blocked_when_not_ready(api, sandbox_conn):
    row = sandbox_conn.execute(
        "SELECT p.id FROM projects p "
        "LEFT JOIN pmo_project_closure c ON c.project_id=p.id "
        "WHERE c.id IS NULL AND p.status NOT IN ('COMPLETED','archived') LIMIT 1"
    ).fetchone()
    if not row:
        pytest.skip("沙箱库无『未结项且未完成』的项目")
    pid = row[0]

    readiness = api.get(f"/pmo/projects/{pid}/closure-readiness")
    assert readiness.status_code == 200, readiness.text
    assert readiness.json().get("ready") is False, "前置：该项目应处于未达标状态"

    r = api.post(
        f"/pmo/projects/{pid}/closure",
        json={"project_summary": "audit-p0", "acceptance_result": "PASS"},
    )
    # 正确行为：未达 readiness 的项目不允许创建结项
    assert r.status_code >= 400, (
        f"未验收/未达 readiness 的项目 {pid} 仍能创建结项（HTTP {r.status_code}）："
        f"{r.text[:200]} -> 结项闸门形同虚设"
    )


# ---------------------------------------------------------------- 8b
def test_change_approval_writes_project_baseline(repo_root):
    src = (repo_root / "app/services/project_change_requests/service.py").read_text(
        encoding="utf-8"
    )
    m = re.search(r"def approve_change_request\(.*?\n(?=\n    def )", src, re.S)
    assert m, "未能定位 approve_change_request 函数"
    body = m.group(0)
    writes_baseline = any(
        sig in body for sig in ("planned_end_date", "budget_amount", "execute_linkage")
    )
    # 正确行为：变更审批通过后应回写项目基线（工期/预算）或调联动引擎
    assert writes_baseline, (
        "approve_change_request 审批通过后对 Project 基线零写入（无 planned_end_date/"
        "budget_amount/execute_linkage）-> 批了不改基线，工期影响不落地"
    )
