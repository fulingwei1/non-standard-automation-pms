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


EXPECTED_TEMPLATE_CODES = {
    "SALES_QUOTE_APPROVAL",
    "SALES_CONTRACT_APPROVAL",
    "SALES_INVOICE",
    "ECN_STANDARD",
    "TIMESHEET_APPROVAL",
    "TPL_PURCHASE",
    "TPL_OUTSOURCING",
    "TPL_ACCEPTANCE",
    "TPL_PROJECT",
    "PROJECT_STAGE_OVERRIDE",
}


def _approval_seed_summary(db_file):
    con = sqlite3.connect(db_file)
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'approval_%'"
            )
        }
        required_tables = {
            "approval_templates",
            "approval_flow_definitions",
            "approval_node_definitions",
            "approval_routing_rules",
        }
        if not required_tables <= tables:
            return {"missing_tables": sorted(required_tables - tables)}

        templates = {
            row[0]: {"entity_type": row[1], "is_active": row[2], "is_published": row[3]}
            for row in con.execute(
                """
                SELECT template_code, entity_type, is_active, is_published
                FROM approval_templates
                """
            )
        }
        flow_count = con.execute("SELECT count(*) FROM approval_flow_definitions").fetchone()[0]
        node_count = con.execute("SELECT count(*) FROM approval_node_definitions").fetchone()[0]
        route_count = con.execute("SELECT count(*) FROM approval_routing_rules").fetchone()[0]

        seeded_codes = tuple(EXPECTED_TEMPLATE_CODES)
        seeded_flow_count = con.execute(
            """
            SELECT count(*)
            FROM approval_flow_definitions f
            JOIN approval_templates t ON t.id = f.template_id
            WHERE t.template_code IN ({})
            """.format(",".join("?" for _ in seeded_codes)),
            seeded_codes,
        ).fetchone()[0]
        seeded_node_count = con.execute(
            """
            SELECT count(*)
            FROM approval_node_definitions n
            JOIN approval_flow_definitions f ON f.id = n.flow_id
            JOIN approval_templates t ON t.id = f.template_id
            WHERE t.template_code IN ({})
            """.format(",".join("?" for _ in seeded_codes)),
            seeded_codes,
        ).fetchone()[0]

        templates_without_default_flow = [
            row[0]
            for row in con.execute(
                """
                SELECT t.template_code
                FROM approval_templates t
                WHERE t.template_code IN ({})
                  AND NOT EXISTS (
                    SELECT 1
                    FROM approval_flow_definitions f
                    WHERE f.template_id = t.id
                      AND f.is_default = 1
                      AND f.is_active = 1
                  )
                ORDER BY t.template_code
                """.format(",".join("?" for _ in seeded_codes)),
                seeded_codes,
            )
        ]
        default_flows_without_nodes = [
            row[0]
            for row in con.execute(
                """
                SELECT t.template_code
                FROM approval_templates t
                JOIN approval_flow_definitions f ON f.template_id = t.id
                WHERE t.template_code IN ({})
                  AND f.is_default = 1
                  AND f.is_active = 1
                  AND NOT EXISTS (
                    SELECT 1
                    FROM approval_node_definitions n
                    WHERE n.flow_id = f.id
                      AND n.node_type = 'APPROVAL'
                      AND n.is_active = 1
                  )
                ORDER BY t.template_code
                """.format(",".join("?" for _ in seeded_codes)),
                seeded_codes,
            )
        ]

        return {
            "missing_tables": [],
            "templates": templates,
            "flow_count": flow_count,
            "node_count": node_count,
            "route_count": route_count,
            "seeded_flow_count": seeded_flow_count,
            "seeded_node_count": seeded_node_count,
            "templates_without_default_flow": templates_without_default_flow,
            "default_flows_without_nodes": default_flows_without_nodes,
        }
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

    summary = _approval_seed_summary(str(fresh_db))
    assert not summary["missing_tables"], f"审批核心表缺失: {summary['missing_tables']}"

    templates = summary["templates"]
    missing_codes = EXPECTED_TEMPLATE_CODES - set(templates)
    assert not missing_codes, (
        f"init_db 后审批模板缺失 {sorted(missing_codes)}；实有 {sorted(templates)}。"
        f"新环境审批模板不完整 -> 对应审批提交会抛『审批模板不存在』。"
        f"\ninit_db stdout tail: {proc.stdout[-400:]}"
    )

    inactive_or_unpublished = {
        code: templates[code]
        for code in EXPECTED_TEMPLATE_CODES
        if not templates[code]["is_active"] or not templates[code]["is_published"]
    }
    assert not inactive_or_unpublished, f"审批模板未启用/未发布: {inactive_or_unpublished}"

    assert summary["seeded_flow_count"] >= 13, (
        f"审批种子 flow 不足：{summary['seeded_flow_count']}，期望至少 13；"
        f"总 flow={summary['flow_count']}"
    )
    assert summary["seeded_node_count"] >= 30, (
        f"审批种子 node 不足：{summary['seeded_node_count']}，期望至少 30；"
        f"总 node={summary['node_count']}"
    )
    assert summary["route_count"] >= 3, (
        f"审批 routing rule 不足：{summary['route_count']}，期望至少 3"
    )
    assert not summary["templates_without_default_flow"], (
        f"以下模板缺少 active 默认流程: {summary['templates_without_default_flow']}"
    )
    assert not summary["default_flows_without_nodes"], (
        f"以下模板默认流程缺少 active APPROVAL 节点: {summary['default_flows_without_nodes']}"
    )
