#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充售前工作台关联演示数据。

特点：
- 只写入 PWB26 前缀的数据，不清理历史业务数据。
- 根对象按固定编码 upsert，子对象按固定父级重建，重复运行不会无限增殖。
- 覆盖客户、线索、商机、需求包、技术评估、工单、方案、投标、报价和协作上下文。

运行：
    python scripts/seed_presale_workbench_demo_data.py
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"
PREFIX = "PWB26"


TECHNICAL_TEMPLATES = [
    {
        "code": f"{PREFIX}-TPL-NE-EOL",
        "name": "动力电池 PACK EOL 测试模板",
        "industry": "NEW_ENERGY",
        "test_type": "COMPREHENSIVE_TEST",
        "description": "面向动力电池 PACK 总成的高压、电气、通讯、安规与追溯一体化测试模板。",
        "parameters": {
            "test_station_count": {"label": "测试工位数", "type": "number", "default": 4, "unit": "个"},
            "cycle_time": {"label": "目标节拍", "type": "number", "default": 45, "unit": "秒"},
            "hv_range": {"label": "高压测试范围", "type": "text", "default": "0-1000V DC"},
            "traceability": {"label": "追溯方式", "type": "select", "default": "SN+MES"},
        },
        "cost_factors": {
            "base_cost": 980000,
            "factors": {
                "test_station_count": {"type": "linear", "coefficient": 180000},
                "cycle_time": {"type": "inverse", "base": 45, "coefficient": 65000},
            },
            "category_ratios": {
                "MECHANICAL": 0.28,
                "ELECTRICAL": 0.36,
                "SOFTWARE": 0.18,
                "OUTSOURCE": 0.10,
                "LABOR": 0.08,
            },
        },
        "typical_labor_hours": {
            "design_hours": 180,
            "assembly_hours": 260,
            "debug_hours": 220,
            "installation_hours": 96,
            "training_hours": 24,
        },
    },
    {
        "code": f"{PREFIX}-TPL-AUTO-EOL",
        "name": "新能源电驱 EOL 测试站模板",
        "industry": "AUTOMOTIVE_ELECTRONICS",
        "test_type": "PERFORMANCE_TEST",
        "description": "用于电驱总成加载、通讯、NVH 初筛与安全互锁的 EOL 测试站模板。",
        "parameters": {
            "torque_range": {"label": "扭矩范围", "type": "text", "default": "0-450Nm"},
            "max_speed": {"label": "最高转速", "type": "number", "default": 16000, "unit": "rpm"},
            "station_count": {"label": "并行工位", "type": "number", "default": 2, "unit": "个"},
            "communication": {"label": "通讯协议", "type": "multiselect", "default": ["CAN", "EtherCAT"]},
        },
        "cost_factors": {
            "base_cost": 1250000,
            "category_ratios": {
                "MECHANICAL": 0.24,
                "ELECTRICAL": 0.38,
                "SOFTWARE": 0.20,
                "OUTSOURCE": 0.10,
                "LABOR": 0.08,
            },
        },
        "typical_labor_hours": {
            "design_hours": 210,
            "assembly_hours": 310,
            "debug_hours": 260,
            "installation_hours": 120,
            "training_hours": 24,
        },
    },
    {
        "code": f"{PREFIX}-TPL-CE-FCT",
        "name": "消费电子 FCT+视觉检测模板",
        "industry": "CONSUMER_ELECTRONICS",
        "test_type": "FUNCTIONAL_TEST",
        "description": "覆盖消费电子主板功能测试、自动上下料、视觉复检与条码追溯的组合模板。",
        "parameters": {
            "uph": {"label": "目标产能", "type": "number", "default": 900, "unit": "UPH"},
            "fixture_count": {"label": "治具数量", "type": "number", "default": 8, "unit": "套"},
            "camera_count": {"label": "视觉相机", "type": "number", "default": 6, "unit": "台"},
            "changeover": {"label": "换型方式", "type": "select", "default": "快换治具"},
        },
        "cost_factors": {
            "base_cost": 760000,
            "category_ratios": {
                "MECHANICAL": 0.32,
                "ELECTRICAL": 0.28,
                "SOFTWARE": 0.22,
                "OUTSOURCE": 0.10,
                "LABOR": 0.08,
            },
        },
        "typical_labor_hours": {
            "design_hours": 140,
            "assembly_hours": 210,
            "debug_hours": 180,
            "installation_hours": 72,
            "training_hours": 16,
        },
    },
    {
        "code": f"{PREFIX}-TPL-HA-ICT",
        "name": "智能家电整机 ICT/FCT 模板",
        "industry": "HOME_APPLIANCE",
        "test_type": "ELECTRICAL_TEST",
        "description": "适配家电控制板 ICT、整机 FCT、安规耐压和产线防呆追溯的标准模板。",
        "parameters": {
            "product_models": {"label": "兼容机型数", "type": "number", "default": 12, "unit": "款"},
            "safety_test": {"label": "安规测试", "type": "select", "default": "耐压+接地"},
            "cycle_time": {"label": "目标节拍", "type": "number", "default": 38, "unit": "秒"},
            "mes_required": {"label": "MES 对接", "type": "boolean", "default": True},
        },
        "cost_factors": {
            "base_cost": 680000,
            "category_ratios": {
                "MECHANICAL": 0.30,
                "ELECTRICAL": 0.34,
                "SOFTWARE": 0.18,
                "OUTSOURCE": 0.10,
                "LABOR": 0.08,
            },
        },
        "typical_labor_hours": {
            "design_hours": 120,
            "assembly_hours": 190,
            "debug_hours": 150,
            "installation_hours": 64,
            "training_hours": 16,
        },
    },
]


SCENARIOS = [
    {
        "seq": "001",
        "customer_code": f"{PREFIX}-CUST-CATL",
        "customer_name": "宁德时代新能源科技股份有限公司（演示）",
        "short_name": "宁德时代演示",
        "industry": "动力电池",
        "city": "宁德",
        "lead_source": "老客户转介绍",
        "lead_status": "CONVERTED",
        "opp_stage": "PROPOSAL",
        "probability": 78,
        "amount": 8_600_000,
        "margin": 31.5,
        "project_type": "BATTERY_EOL",
        "equipment_type": "PACK EOL 综合测试线",
        "title": "宁德时代 PACK EOL 综合测试线售前支持",
        "ticket_type": "TENDER",
        "ticket_status": "REVIEW",
        "urgency": "URGENT",
        "solution_status": "APPROVED",
        "tender_result": "PENDING",
        "template_code": f"{PREFIX}-TPL-NE-EOL",
        "test_type": "COMPREHENSIVE_TEST",
        "application": "动力电池 PACK 下线测试与数据追溯",
        "target_object": "动力电池 PACK 总成",
        "capacity": 120,
        "cycle_time": 45,
        "workstations": 4,
        "risk_level": "MEDIUM",
        "open_item": "客户 MES 字段清单仍需冻结，报价前需确认追溯字段与接口节拍。",
        "blocks_quote": 1,
    },
    {
        "seq": "002",
        "customer_code": f"{PREFIX}-CUST-BYD",
        "customer_name": "比亚迪汽车工业有限公司（演示）",
        "short_name": "比亚迪演示",
        "industry": "新能源汽车",
        "city": "深圳",
        "lead_source": "招投标平台",
        "lead_status": "CONVERTED",
        "opp_stage": "NEGOTIATION",
        "probability": 86,
        "amount": 12_800_000,
        "margin": 29.8,
        "project_type": "EV_DRIVE_EOL",
        "equipment_type": "电驱总成 EOL 测试站",
        "title": "比亚迪电驱总成 EOL 测试站投标支持",
        "ticket_type": "TENDER",
        "ticket_status": "COMPLETED",
        "urgency": "VERY_URGENT",
        "solution_status": "WON",
        "tender_result": "WON",
        "template_code": f"{PREFIX}-TPL-AUTO-EOL",
        "test_type": "PERFORMANCE_TEST",
        "application": "电驱总成加载、通讯、NVH 初筛与安全互锁",
        "target_object": "三合一电驱总成",
        "capacity": 80,
        "cycle_time": 60,
        "workstations": 2,
        "risk_level": "LOW",
        "open_item": "客户试验台接口协议已冻结，需在合同附件中确认验收曲线。",
        "blocks_quote": 0,
        "contract": True,
    },
    {
        "seq": "003",
        "customer_code": f"{PREFIX}-CUST-LUX",
        "customer_name": "立讯精密工业股份有限公司（演示）",
        "short_name": "立讯精密演示",
        "industry": "消费电子",
        "city": "东莞",
        "lead_source": "行业展会",
        "lead_status": "QUALIFIED",
        "opp_stage": "QUALIFICATION",
        "probability": 62,
        "amount": 4_200_000,
        "margin": 34.2,
        "project_type": "CE_FCT",
        "equipment_type": "FCT+视觉检测工作站",
        "title": "立讯精密 FCT 与视觉检测组合方案",
        "ticket_type": "SOLUTION",
        "ticket_status": "PROCESSING",
        "urgency": "NORMAL",
        "solution_status": "REVIEW",
        "tender_result": "PENDING",
        "template_code": f"{PREFIX}-TPL-CE-FCT",
        "test_type": "FUNCTIONAL_TEST",
        "application": "消费电子主板多工位 FCT 与外观缺陷复检",
        "target_object": "Type-C 控制板与无线充模块",
        "capacity": 900,
        "cycle_time": 28,
        "workstations": 8,
        "risk_level": "MEDIUM",
        "open_item": "缺陷样本库数量不足，视觉算法训练前需补 300 张 NG 样本。",
        "blocks_quote": 1,
    },
    {
        "seq": "004",
        "customer_code": f"{PREFIX}-CUST-MIDEA",
        "customer_name": "美的集团股份有限公司（演示）",
        "short_name": "美的演示",
        "industry": "智能家电",
        "city": "佛山",
        "lead_source": "官网咨询",
        "lead_status": "QUALIFIED",
        "opp_stage": "DISCOVERY",
        "probability": 48,
        "amount": 3_600_000,
        "margin": 32.0,
        "project_type": "HA_ICT_FCT",
        "equipment_type": "整机 ICT/FCT 测试单元",
        "title": "美的智能家电整机测试单元需求调研",
        "ticket_type": "SURVEY",
        "ticket_status": "ACCEPTED",
        "urgency": "NORMAL",
        "solution_status": "DRAFT",
        "tender_result": "PENDING",
        "template_code": f"{PREFIX}-TPL-HA-ICT",
        "test_type": "ELECTRICAL_TEST",
        "application": "家电控制板 ICT、整机 FCT、耐压与 MES 追溯",
        "target_object": "变频控制板与整机测试位",
        "capacity": 500,
        "cycle_time": 38,
        "workstations": 6,
        "risk_level": "LOW",
        "open_item": "客户现场可用空间和物流方向待二次测绘确认。",
        "blocks_quote": 0,
    },
]


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def ts(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def ds(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"数据库不存在: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def require_tables(conn: sqlite3.Connection) -> None:
    required = {
        "customers",
        "leads",
        "lead_requirement_details",
        "technical_assessments",
        "opportunities",
        "opportunity_requirements",
        "presale_support_ticket",
        "presale_ticket_deliverable",
        "presale_ticket_progress",
        "presale_solution",
        "presale_solution_cost",
        "presale_tender_record",
        "technical_parameter_templates",
        "quotes",
        "quote_versions",
        "quote_items",
        "contracts",
        "open_items",
        "requirement_freezes",
        "ai_clarifications",
        "presale_expenses",
        "users",
    }
    existing = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(f"数据库缺少必要表: {', '.join(missing)}")


def filter_values(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> dict[str, Any]:
    columns = table_columns(conn, table)
    return {key: value for key, value in values.items() if key in columns}


def upsert_by_key(
    conn: sqlite3.Connection,
    table: str,
    key_column: str,
    values: dict[str, Any],
) -> tuple[int, bool]:
    values = filter_values(conn, table, values)
    if key_column not in values:
        raise ValueError(f"{table} 缺少唯一键字段: {key_column}")

    existing = conn.execute(
        f"SELECT id FROM {table} WHERE {key_column} = ?",
        (values[key_column],),
    ).fetchone()
    if existing:
        update_values = {key: value for key, value in values.items() if key != key_column}
        if update_values:
            assignments = ", ".join(f"{key}=?" for key in update_values)
            conn.execute(
                f"UPDATE {table} SET {assignments} WHERE id=?",
                (*update_values.values(), existing["id"]),
            )
        return int(existing["id"]), False

    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cursor = conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(values.values()),
    )
    return int(cursor.lastrowid), True


def get_user(conn: sqlite3.Connection, username: str, fallback_username: str = "admin") -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND COALESCE(is_active, 1) = 1",
        (username,),
    ).fetchone()
    if row:
        return row
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND COALESCE(is_active, 1) = 1",
        (fallback_username,),
    ).fetchone()
    if row:
        return row
    row = conn.execute(
        "SELECT * FROM users WHERE COALESCE(is_active, 1) = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if not row:
        raise RuntimeError("未找到可用用户，无法写入演示数据")
    return row


def cleanup_demo_children(conn: sqlite3.Connection) -> None:
    like = f"{PREFIX}-%"
    tagged = f"[{PREFIX}]%"
    cur = conn.cursor()

    cur.execute("UPDATE quotes SET current_version_id=NULL WHERE quote_code LIKE ?", (like,))
    cur.execute(
        """
        DELETE FROM quote_items
        WHERE quote_version_id IN (
            SELECT id FROM quote_versions
            WHERE quote_id IN (SELECT id FROM quotes WHERE quote_code LIKE ?)
        )
        """,
        (like,),
    )
    cur.execute(
        "DELETE FROM quote_versions WHERE quote_id IN (SELECT id FROM quotes WHERE quote_code LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM presale_solution_cost WHERE solution_id IN (SELECT id FROM presale_solution WHERE solution_no LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM presale_ticket_progress WHERE ticket_id IN (SELECT id FROM presale_support_ticket WHERE ticket_no LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM presale_ticket_deliverable WHERE ticket_id IN (SELECT id FROM presale_support_ticket WHERE ticket_no LIKE ?)",
        (like,),
    )
    cur.execute(
        """
        DELETE FROM technical_assessments
        WHERE presale_ticket_id IN (SELECT id FROM presale_support_ticket WHERE ticket_no LIKE ?)
           OR (source_type='LEAD' AND source_id IN (SELECT id FROM leads WHERE lead_code LIKE ?))
           OR (source_type='OPPORTUNITY' AND source_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?))
        """,
        (like, like, like),
    )
    cur.execute(
        "DELETE FROM lead_requirement_details WHERE lead_id IN (SELECT id FROM leads WHERE lead_code LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM opportunity_requirements WHERE opportunity_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?)",
        (like,),
    )
    cur.execute("DELETE FROM open_items WHERE item_code LIKE ?", (like,))
    cur.execute(
        "DELETE FROM requirement_freezes WHERE source_type='OPPORTUNITY' AND source_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM ai_clarifications WHERE source_type='OPPORTUNITY' AND source_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?)",
        (like,),
    )
    cur.execute("DELETE FROM presale_expenses WHERE description LIKE ?", (tagged,))

    if "stage_dwell_time_alerts" in {
        row["name"] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }:
        cur.execute("DELETE FROM stage_dwell_time_alerts WHERE alert_code LIKE ?", (like,))
    if "funnel_transition_logs" in {
        row["name"] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }:
        cur.execute("DELETE FROM funnel_transition_logs WHERE entity_code LIKE ?", (like,))


def seed_templates(
    conn: sqlite3.Connection,
    created_at: datetime,
    admin_user: sqlite3.Row,
) -> tuple[dict[str, int], dict[str, int]]:
    stats = {"created": 0, "updated": 0}
    template_ids: dict[str, int] = {}
    for item in TECHNICAL_TEMPLATES:
        template_id, created = upsert_by_key(
            conn,
            "technical_parameter_templates",
            "code",
            {
                "code": item["code"],
                "name": item["name"],
                "industry": item["industry"],
                "test_type": item["test_type"],
                "description": item["description"],
                "parameters": json_dump(item["parameters"]),
                "cost_factors": json_dump(item["cost_factors"]),
                "typical_labor_hours": json_dump(item["typical_labor_hours"]),
                "reference_docs": json_dump(
                    [
                        {"name": "客户需求澄清清单", "type": "checklist"},
                        {"name": "FAT/SAT 验收模板", "type": "acceptance"},
                    ]
                ),
                "sample_images": json_dump([]),
                "use_count": 12,
                "is_active": 1,
                "created_by": admin_user["id"],
                "created_at": ts(created_at),
                "updated_at": ts(created_at),
            },
        )
        template_ids[item["code"]] = template_id
        stats["created" if created else "updated"] += 1
    return template_ids, stats


def insert_row(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    values = filter_values(conn, table, values)
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cursor = conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(values.values()),
    )
    return int(cursor.lastrowid)


def seed_scenario(
    conn: sqlite3.Connection,
    scenario: dict[str, Any],
    template_ids: dict[str, int],
    users: dict[str, sqlite3.Row],
    base_time: datetime,
) -> dict[str, int]:
    seq = scenario["seq"]
    created_at = base_time - timedelta(minutes=(int(seq) - 1) * 5)
    today = created_at.date()
    sales_user = users["sales"]
    tech_user = users["tech"]
    pm_user = users["pm"]
    admin_user = users["admin"]

    customer_id, customer_created = upsert_by_key(
        conn,
        "customers",
        "customer_code",
        {
            "customer_code": scenario["customer_code"],
            "customer_name": scenario["customer_name"],
            "short_name": scenario["short_name"],
            "customer_type": "enterprise",
            "industry": scenario["industry"],
            "scale": "large",
            "address": f"{scenario['city']}市智能制造示范园区",
            "contact_person": "项目采购经理",
            "contact_phone": f"1382026{seq}",
            "contact_email": f"presale-{seq}@demo.local",
            "credit_level": "A",
            "credit_limit": scenario["amount"] * 2,
            "payment_terms": "30%预付款+60%发货前+10%验收款",
            "status": "ACTIVE",
            "customer_level": "A",
            "customer_source": scenario["lead_source"],
            "sales_owner_id": sales_user["id"],
            "last_follow_up_at": ts(created_at),
            "annual_revenue": scenario["amount"] * 5,
            "cooperation_years": 2,
            "remark": f"[{PREFIX}] 售前工作台关联演示客户",
            "created_by": admin_user["id"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
            "is_active": 1,
        },
    )

    lead_code = f"{PREFIX}-LD-{seq}"
    lead_id, lead_created = upsert_by_key(
        conn,
        "leads",
        "lead_code",
        {
            "lead_code": lead_code,
            "source": scenario["lead_source"],
            "customer_name": scenario["customer_name"],
            "industry": scenario["industry"],
            "contact_name": "客户技术经理",
            "contact_phone": f"1392026{seq}",
            "demand_summary": (
                f"{scenario['application']}，目标 CT {scenario['cycle_time']} 秒，"
                f"{scenario['workstations']} 个工位，目标产能 {scenario['capacity']}。"
            ),
            "owner_id": sales_user["id"],
            "status": scenario["lead_status"],
            "next_action_at": ts(created_at + timedelta(days=2)),
            "selected_advantage_products": json_dump(["EOL", "FCT", "MES"]),
            "product_match_type": "ADVANTAGE",
            "is_advantage_product": 1,
            "assessment_status": "COMPLETED",
            "priority_score": min(96, scenario["probability"] + 8),
            "completeness": 92 if scenario["lead_status"] == "CONVERTED" else 82,
            "assignee_id": tech_user["id"],
            "health_status": "H1",
            "health_score": min(98, scenario["probability"] + 10),
            "last_follow_up_at": ts(created_at),
            "break_risk_level": scenario["risk_level"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    requirement_id = insert_row(
        conn,
        "lead_requirement_details",
        {
            "lead_id": lead_id,
            "customer_factory_location": f"{scenario['city']}工厂",
            "target_object_type": scenario["target_object"],
            "application_scenario": scenario["application"],
            "delivery_mode": "整线交钥匙" if int(seq) <= 2 else "工作站交付",
            "expected_delivery_date": ts(created_at + timedelta(days=90 + int(seq) * 10)),
            "requirement_source": scenario["lead_source"],
            "participant_ids": json_dump([sales_user["id"], tech_user["id"], pm_user["id"]]),
            "requirement_maturity": 5 if scenario["probability"] >= 80 else 4,
            "has_sow": 1,
            "has_interface_doc": 1 if int(seq) <= 3 else 0,
            "has_drawing_doc": 1,
            "sample_availability": json_dump({"status": "AVAILABLE", "note": "客户可提供样件与 NG 样本"}),
            "customer_support_resources": json_dump(["工艺工程师", "MES 工程师", "设备维护"]),
            "key_risk_factors": json_dump([scenario["open_item"]]),
            "veto_triggered": 0,
            "target_capacity_uph": scenario["capacity"],
            "cycle_time_seconds": scenario["cycle_time"],
            "workstation_count": scenario["workstations"],
            "changeover_method": "快换治具+参数配方",
            "yield_target": 99.2,
            "traceability_type": "SN+MES",
            "data_retention_period": 3650,
            "test_scope": json_dump([scenario["equipment_type"], "数据追溯", "安全互锁"]),
            "acceptance_method": "FAT+SAT",
            "acceptance_basis": "CPK>=1.33，连续 3 批次稳定运行，关键数据可追溯",
            "delivery_checklist": json_dump(["技术方案", "成本测算", "测试程序", "验收报告"]),
            "communication_protocols": json_dump(["MES API", "Modbus TCP", "OPC UA"]),
            "power_supply": json_dump({"main": "AC380V", "control": "AC220V"}),
            "air_supply": json_dump({"pressure": "0.6MPa", "flow": "按最终方案核定"}),
            "safety_requirements": json_dump(["安全门互锁", "急停回路", "权限分级"]),
            "requirement_version": f"{PREFIX}-REQ-{seq}-V1",
            "is_frozen": 1 if int(seq) <= 2 else 0,
            "frozen_at": ts(created_at + timedelta(hours=6)) if int(seq) <= 2 else None,
            "frozen_by": pm_user["id"] if int(seq) <= 2 else None,
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    conn.execute(
        "UPDATE leads SET requirement_detail_id=?, updated_at=? WHERE id=?",
        (requirement_id, ts(created_at), lead_id),
    )

    opp_code = f"{PREFIX}-OP-{seq}"
    opp_id, opp_created = upsert_by_key(
        conn,
        "opportunities",
        "opp_code",
        {
            "opp_code": opp_code,
            "lead_id": lead_id,
            "customer_id": customer_id,
            "opp_name": f"{scenario['short_name']}{scenario['equipment_type']}项目",
            "project_type": scenario["project_type"],
            "equipment_type": scenario["equipment_type"],
            "stage": scenario["opp_stage"],
            "probability": scenario["probability"],
            "est_amount": scenario["amount"],
            "est_margin": scenario["margin"],
            "expected_close_date": ds(today + timedelta(days=25 + int(seq) * 12)),
            "budget_range": f"{scenario['amount'] / 10000:.0f}万元级",
            "decision_chain": "设备部->工艺部->采购部->总经理办公会",
            "delivery_window": "合同后 90-150 天分阶段交付",
            "acceptance_basis": "FAT/SAT 双阶段验收，关键测试数据全量追溯",
            "score": min(95, scenario["probability"] + 6),
            "risk_level": scenario["risk_level"],
            "owner_id": sales_user["id"],
            "updated_by": sales_user["id"],
            "gate_status": "PASSED" if int(seq) <= 3 else "PENDING",
            "gate_passed_at": ts(created_at + timedelta(hours=8)) if int(seq) <= 3 else None,
            "requirement_maturity": 5 if int(seq) <= 2 else 4,
            "assessment_status": "COMPLETED",
            "priority_score": min(98, scenario["probability"] + 9),
            "health_status": "H1" if scenario["probability"] >= 60 else "H2",
            "health_score": min(98, scenario["probability"] + 11),
            "last_progress_at": ts(created_at),
            "break_risk_level": scenario["risk_level"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    insert_row(
        conn,
        "opportunity_requirements",
        {
            "opportunity_id": opp_id,
            "product_object": scenario["target_object"],
            "ct_seconds": scenario["cycle_time"],
            "interface_desc": "MES API + 设备 PLC + 条码/视觉追溯",
            "site_constraints": "需确认现场线体方向、上下料节拍和安全围栏边界",
            "acceptance_criteria": "连续生产稳定，关键指标达成，异常数据可复盘",
            "safety_requirement": "安全门、光栅、急停和权限控制必须纳入验收",
            "attachments": json_dump(["客户URS", "节拍测算表", "接口清单"]),
            "extra_json": json_dump({"workstations": scenario["workstations"], "capacity": scenario["capacity"]}),
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    ticket_no = f"{PREFIX}-TK-{seq}"
    ticket_id, ticket_created = upsert_by_key(
        conn,
        "presale_support_ticket",
        "ticket_no",
        {
            "ticket_no": ticket_no,
            "title": scenario["title"],
            "ticket_type": scenario["ticket_type"],
            "urgency": scenario["urgency"],
            "description": f"{scenario['application']}，需输出方案、成本、风险和投标口径。",
            "customer_id": customer_id,
            "customer_name": scenario["customer_name"],
            "lead_id": lead_id,
            "opportunity_id": opp_id,
            "project_id": None,
            "applicant_id": sales_user["id"],
            "applicant_name": sales_user["real_name"] or sales_user["username"],
            "applicant_dept": sales_user["department"],
            "apply_time": ts(created_at),
            "assignee_id": tech_user["id"],
            "assignee_name": tech_user["real_name"] or tech_user["username"],
            "accept_time": ts(created_at + timedelta(hours=2)),
            "expected_date": ds(today + timedelta(days=7 + int(seq))),
            "deadline": ts(created_at + timedelta(days=7 + int(seq))),
            "status": scenario["ticket_status"],
            "complete_time": ts(created_at + timedelta(days=6)) if scenario["ticket_status"] == "COMPLETED" else None,
            "actual_hours": 42 + int(seq) * 8 if scenario["ticket_status"] == "COMPLETED" else None,
            "satisfaction_score": 5 if scenario["ticket_status"] == "COMPLETED" else None,
            "feedback": "方案响应及时，成本口径清晰。" if scenario["ticket_status"] == "COMPLETED" else None,
            "pm_involvement_required": 1 if scenario["amount"] >= 8_000_000 else 0,
            "pm_involvement_risk_level": "高" if scenario["amount"] >= 8_000_000 else "低",
            "pm_involvement_risk_factors": json_dump(["金额大", "接口复杂"]) if scenario["amount"] >= 8_000_000 else json_dump([]),
            "pm_involvement_checked_at": ts(created_at + timedelta(hours=1)),
            "pm_assigned": 1 if scenario["amount"] >= 8_000_000 else 0,
            "pm_user_id": pm_user["id"] if scenario["amount"] >= 8_000_000 else None,
            "pm_assigned_at": ts(created_at + timedelta(hours=3)) if scenario["amount"] >= 8_000_000 else None,
            "assessment_required": 1,
            "assessment_status": "COMPLETED" if int(seq) <= 2 else "IN_PROGRESS",
            "assessment_priority": "HIGH" if scenario["urgency"] != "NORMAL" else "NORMAL",
            "assessment_due_date": ts(created_at + timedelta(days=5)),
            "created_by": sales_user["id"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    assessment_id = insert_row(
        conn,
        "technical_assessments",
        {
            "source_type": "OPPORTUNITY",
            "source_id": opp_id,
            "evaluator_id": tech_user["id"],
            "status": "COMPLETED" if int(seq) <= 3 else "IN_PROGRESS",
            "total_score": min(94, scenario["probability"] + 7),
            "dimension_scores": json_dump(
                {
                    "technical_feasibility": min(96, scenario["probability"] + 8),
                    "delivery_risk": 88 if scenario["risk_level"] == "LOW" else 76,
                    "profitability": round(scenario["margin"], 1),
                    "requirement_clarity": 91 if int(seq) <= 2 else 78,
                }
            ),
            "veto_triggered": 0,
            "decision": "GO" if scenario["probability"] >= 70 else "GO_WITH_CONDITIONS",
            "risks": json_dump([scenario["open_item"]]),
            "similar_cases": json_dump(["动力电池 EOL 线成功案例", "消费电子 FCT 快换治具案例"]),
            "ai_analysis": f"[{PREFIX}] 演示评估：项目匹配公司优势设备能力，需锁定接口、节拍和验收边界。",
            "conditions": json_dump(["需求冻结后进入报价", "关键外购件交期需采购确认"]),
            "evaluated_at": ts(created_at + timedelta(hours=10)),
            "presale_ticket_id": ticket_id,
            "version_no": "V1.0",
            "is_latest": 1,
            "item_scores": json_dump({"接口成熟度": 85, "交付可控性": 82, "毛利空间": 88}),
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    conn.execute(
        "UPDATE opportunities SET assessment_id=?, assessment_status='COMPLETED', updated_at=? WHERE id=?",
        (assessment_id, ts(created_at), opp_id),
    )
    conn.execute(
        "UPDATE presale_support_ticket SET current_assessment_id=?, updated_at=? WHERE id=?",
        (assessment_id, ts(created_at), ticket_id),
    )

    insert_row(
        conn,
        "technical_assessments",
        {
            "source_type": "LEAD",
            "source_id": lead_id,
            "evaluator_id": tech_user["id"],
            "status": "COMPLETED",
            "total_score": min(92, scenario["probability"] + 5),
            "dimension_scores": json_dump({"需求完整度": 90, "客户价值": 88, "技术匹配": 86}),
            "veto_triggered": 0,
            "decision": "GO",
            "risks": json_dump([scenario["open_item"]]),
            "conditions": json_dump(["进入商机后补齐报价边界"]),
            "evaluated_at": ts(created_at + timedelta(hours=5)),
            "presale_ticket_id": ticket_id,
            "version_no": "V1.0",
            "is_latest": 1,
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    deliverables = [
        ("需求澄清纪要", "DOC", "APPROVED" if int(seq) <= 2 else "SUBMITTED", 1),
        ("技术方案书", "DOC", "APPROVED" if int(seq) <= 2 else "DRAFT", 1),
        ("成本测算表", "XLSX", "APPROVED" if int(seq) <= 2 else "DRAFT", 1),
        ("FAT/SAT 验收清单", "DOC", "SUBMITTED", 0),
    ]
    for order, (name, file_type, status, is_required) in enumerate(deliverables, start=1):
        insert_row(
            conn,
            "presale_ticket_deliverable",
            {
                "ticket_id": ticket_id,
                "name": f"{scenario['short_name']}-{name}",
                "file_type": file_type,
                "file_path": f"/demo/{PREFIX}/{ticket_no}/{order:02d}-{name}.{file_type.lower()}",
                "file_size": 204800 + order * 65536,
                "version": "V1.0",
                "is_required": is_required,
                "status": status,
                "reviewer_id": pm_user["id"] if status == "APPROVED" else None,
                "review_time": ts(created_at + timedelta(days=2, hours=order)) if status == "APPROVED" else None,
                "review_comment": "演示数据：已确认口径" if status == "APPROVED" else None,
                "created_by": tech_user["id"],
                "created_at": ts(created_at + timedelta(hours=order)),
                "updated_at": ts(created_at + timedelta(hours=order)),
            },
        )

    progress_points = [(20, "已接单并完成需求初筛"), (55, "完成技术路线与成本粗算"), (85, "方案进入评审")]
    if scenario["ticket_status"] == "COMPLETED":
        progress_points.append((100, "投标/方案支持已完成"))
    for percent, content in progress_points:
        insert_row(
            conn,
            "presale_ticket_progress",
            {
                "ticket_id": ticket_id,
                "progress_type": "UPDATE",
                "content": f"[{PREFIX}] {content}",
                "progress_percent": percent,
                "operator_id": tech_user["id"],
                "operator_name": tech_user["real_name"] or tech_user["username"],
                "created_at": ts(created_at + timedelta(hours=percent // 10)),
                "updated_at": ts(created_at + timedelta(hours=percent // 10)),
            },
        )

    template_id = template_ids[scenario["template_code"]]
    estimated_cost = round(scenario["amount"] * (1 - scenario["margin"] / 100), 2)
    suggested_price = scenario["amount"]
    cost_breakdown = {
        "MECHANICAL": {"amount": round(estimated_cost * 0.30, 2), "ratio": 0.30},
        "ELECTRICAL": {"amount": round(estimated_cost * 0.34, 2), "ratio": 0.34},
        "SOFTWARE": {"amount": round(estimated_cost * 0.18, 2), "ratio": 0.18},
        "OUTSOURCE": {"amount": round(estimated_cost * 0.10, 2), "ratio": 0.10},
        "LABOR": {"amount": round(estimated_cost * 0.08, 2), "ratio": 0.08},
        "notes": "售前演示成本拆解，已关联模板参数。",
    }
    solution_no = f"{PREFIX}-SOL-{seq}"
    solution_id, solution_created = upsert_by_key(
        conn,
        "presale_solution",
        "solution_no",
        {
            "solution_no": solution_no,
            "name": f"{scenario['short_name']}{scenario['equipment_type']}技术方案",
            "solution_type": "CUSTOM",
            "industry": scenario["industry"],
            "test_type": scenario["test_type"],
            "ticket_id": ticket_id,
            "project_id": None,
            "customer_id": customer_id,
            "opportunity_id": opp_id,
            "template_id": template_id,
            "template_parameters": json_dump(
                {
                    "workstations": scenario["workstations"],
                    "cycle_time": scenario["cycle_time"],
                    "capacity": scenario["capacity"],
                    "traceability": "SN+MES",
                }
            ),
            "requirement_summary": f"{scenario['application']}，预算 {scenario['amount'] / 10000:.0f} 万元。",
            "solution_overview": "采用标准测试平台+定制治具+MES追溯的组合方案，缩短方案周期并降低交付风险。",
            "technical_spec": "PLC 控制、上位机测试程序、自动扫码、数据追溯、安全互锁和远程诊断。",
            "estimated_cost": estimated_cost,
            "suggested_price": suggested_price,
            "cost_breakdown": json_dump(cost_breakdown),
            "estimated_hours": 420 + int(seq) * 30,
            "estimated_duration": 75 + int(seq) * 8,
            "status": scenario["solution_status"],
            "version": "V1.0",
            "reviewer_id": pm_user["id"] if scenario["solution_status"] in {"APPROVED", "WON"} else None,
            "review_time": ts(created_at + timedelta(days=3)) if scenario["solution_status"] in {"APPROVED", "WON"} else None,
            "review_status": "APPROVED" if scenario["solution_status"] in {"APPROVED", "WON"} else "PENDING",
            "review_comment": "成本口径与验收边界清晰，可进入报价。" if scenario["solution_status"] in {"APPROVED", "WON"} else None,
            "author_id": tech_user["id"],
            "author_name": tech_user["real_name"] or tech_user["username"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    for order, (category, label) in enumerate(
        [
            ("MECHANICAL", "机架与工装夹具"),
            ("ELECTRICAL", "PLC/电控/传感器"),
            ("SOFTWARE", "上位机与数据追溯"),
            ("OUTSOURCE", "机加工与钣金外协"),
            ("LABOR", "设计装配调试工时"),
        ],
        start=1,
    ):
        amount = cost_breakdown[category]["amount"]
        insert_row(
            conn,
            "presale_solution_cost",
            {
                "solution_id": solution_id,
                "category": category,
                "item_name": label,
                "specification": "演示口径",
                "unit": "项",
                "quantity": 1,
                "unit_price": amount,
                "amount": amount,
                "remark": f"{scenario['short_name']}方案成本拆解",
                "sort_order": order,
                "created_at": ts(created_at),
                "updated_at": ts(created_at),
            },
        )

    tender_id, tender_created = upsert_by_key(
        conn,
        "presale_tender_record",
        "tender_no",
        {
            "ticket_id": ticket_id,
            "opportunity_id": opp_id,
            "project_id": None,
            "tender_no": f"{PREFIX}-BID-{seq}",
            "tender_name": f"{scenario['short_name']}{scenario['equipment_type']}招投标项目",
            "customer_name": scenario["customer_name"],
            "publish_date": ds(today - timedelta(days=3)),
            "deadline": ts(created_at + timedelta(days=10)),
            "bid_opening_date": ds(today + timedelta(days=12)),
            "budget_amount": scenario["amount"] * 1.03,
            "qualification_requirements": "具备非标自动化测试设备交付案例与质量体系能力。",
            "technical_requirements": scenario["application"],
            "our_bid_amount": suggested_price,
            "technical_score": 88 + int(seq),
            "commercial_score": 84 + int(seq),
            "total_score": 86 + int(seq),
            "competitors": json_dump(
                [
                    {"name": "竞品A", "strength": "交期短"},
                    {"name": "竞品B", "strength": "本地服务"},
                ]
            ),
            "result": scenario["tender_result"],
            "result_reason": "演示数据：方案匹配度高，成本口径清晰。" if scenario["tender_result"] == "WON" else "演示数据：等待客户开标/技术澄清。",
            "leader_id": sales_user["id"],
            "team_members": json_dump([sales_user["id"], tech_user["id"], pm_user["id"]]),
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    quote_id, quote_created = upsert_by_key(
        conn,
        "quotes",
        "quote_code",
        {
            "quote_code": f"{PREFIX}-QT-{seq}",
            "opportunity_id": opp_id,
            "customer_id": customer_id,
            "status": "APPROVED" if int(seq) <= 2 else "SUBMITTED",
            "valid_until": ds(today + timedelta(days=30)),
            "delivery_date": ds(today + timedelta(days=100 + int(seq) * 7)),
            "owner_id": sales_user["id"],
            "health_status": "H1",
            "health_score": min(98, scenario["probability"] + 12),
            "break_risk_level": scenario["risk_level"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    quote_version_id = insert_row(
        conn,
        "quote_versions",
        {
            "quote_id": quote_id,
            "version_no": "V1.0",
            "total_price": suggested_price,
            "cost_total": estimated_cost,
            "gross_margin": scenario["margin"],
            "lead_time_days": 90 + int(seq) * 8,
            "risk_terms": "需求冻结后报价有效；客户现场接口变更需走变更评审。",
            "delivery_date": ds(today + timedelta(days=100 + int(seq) * 7)),
            "created_by": sales_user["id"],
            "approved_by": pm_user["id"] if int(seq) <= 2 else None,
            "approved_at": ts(created_at + timedelta(days=4)) if int(seq) <= 2 else None,
            "cost_breakdown_complete": 1,
            "margin_warning": 0,
            "solution_version_id": None,
            "cost_estimation_id": None,
            "presale_solution_id": solution_id,
            "presale_ticket_id": ticket_id,
            "binding_status": "valid",
            "binding_validated_at": ts(created_at + timedelta(days=4)),
            "binding_warning": None,
            "quote_code": f"{PREFIX}-QT-{seq}-V1",
            "status": "APPROVED" if int(seq) <= 2 else "SUBMITTED",
            "approval_status": "APPROVED" if int(seq) <= 2 else "PENDING",
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    conn.execute(
        "UPDATE quotes SET current_version_id=?, updated_at=? WHERE id=?",
        (quote_version_id, ts(created_at), quote_id),
    )

    quote_items = [
        ("EQUIPMENT", scenario["equipment_type"], suggested_price * 0.55, estimated_cost * 0.56, "套"),
        ("SOFTWARE", "测试程序与 MES 追溯软件", suggested_price * 0.18, estimated_cost * 0.17, "套"),
        ("SERVICE", "现场安装调试与培训", suggested_price * 0.12, estimated_cost * 0.11, "项"),
        ("RISK", "项目管理与风险预备费", suggested_price * 0.15, estimated_cost * 0.16, "项"),
    ]
    for order, (item_type, item_name, price, cost, unit) in enumerate(quote_items, start=1):
        insert_row(
            conn,
            "quote_items",
            {
                "quote_version_id": quote_version_id,
                "item_type": item_type,
                "item_name": item_name,
                "qty": 1,
                "unit_price": round(price, 2),
                "cost": round(cost, 2),
                "lead_time_days": 35 + order * 10,
                "remark": f"[{PREFIX}] 与售前方案 {solution_no} 绑定",
                "cost_category": item_type,
                "cost_source": "PRESALE_SOLUTION",
                "specification": "演示规格",
                "unit": unit,
            },
        )

    insert_row(
        conn,
        "open_items",
        {
            "source_type": "OPPORTUNITY",
            "source_id": opp_id,
            "item_code": f"{PREFIX}-OI-{seq}",
            "item_type": "REQUIREMENT_CLARIFICATION",
            "description": scenario["open_item"],
            "responsible_party": "CUSTOMER" if scenario["blocks_quote"] else "INTERNAL",
            "responsible_person_id": sales_user["id"] if scenario["blocks_quote"] else tech_user["id"],
            "due_date": ts(created_at + timedelta(days=3 + int(seq))),
            "status": "PENDING",
            "blocks_quotation": scenario["blocks_quote"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    insert_row(
        conn,
        "requirement_freezes",
        {
            "source_type": "OPPORTUNITY",
            "source_id": opp_id,
            "freeze_type": "QUOTE_BASELINE",
            "freeze_time": ts(created_at + timedelta(days=2)),
            "frozen_by": pm_user["id"],
            "version_number": f"{PREFIX}-FRZ-{seq}-V1",
            "requires_ecr": 1,
            "description": "演示数据：报价口径冻结，后续变更需走 ECR/ECN。",
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )
    insert_row(
        conn,
        "ai_clarifications",
        {
            "source_type": "OPPORTUNITY",
            "source_id": opp_id,
            "round": 1,
            "questions": json_dump(
                [
                    "客户现场 CT 与 UPH 是否以单工位还是整线统计？",
                    "MES 返回超时时间和重试策略是否已定义？",
                ]
            ),
            "answers": json_dump(
                [
                    "以整线统计，单工位需保留 15% 节拍余量。",
                    "接口文档暂按 3 秒超时、2 次重试设计。",
                ]
            ),
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    insert_row(
        conn,
        "presale_expenses",
        {
            "project_id": 0,
            "project_code": f"{PREFIX}-PRE-{seq}",
            "project_name": scenario["title"],
            "ticket_id": ticket_id,
            "lead_id": lead_id,
            "opportunity_id": opp_id,
            "expense_type": "SOLUTION",
            "expense_category": "方案支持",
            "amount": 2800 + int(seq) * 650,
            "labor_hours": 12 + int(seq) * 3,
            "hourly_rate": 220,
            "user_id": tech_user["id"],
            "user_name": tech_user["real_name"] or tech_user["username"],
            "department_name": tech_user["department"],
            "salesperson_id": sales_user["id"],
            "salesperson_name": sales_user["real_name"] or sales_user["username"],
            "expense_date": ds(today),
            "description": f"[{PREFIX}] {scenario['short_name']}售前方案/投标支持费用",
            "approval_status": "APPROVED" if int(seq) <= 2 else "PENDING",
            "approved_by": pm_user["id"] if int(seq) <= 2 else None,
            "approved_at": ts(created_at + timedelta(days=1)) if int(seq) <= 2 else None,
            "approval_note": "演示数据：费用归集合理" if int(seq) <= 2 else None,
            "created_by": tech_user["id"],
            "created_at": ts(created_at),
            "updated_at": ts(created_at),
        },
    )

    contract_created = False
    if scenario.get("contract"):
        _contract_id, contract_created = upsert_by_key(
            conn,
            "contracts",
            "contract_code",
            {
                "contract_code": f"{PREFIX}-CT-{seq}",
                "contract_name": f"{scenario['short_name']}{scenario['equipment_type']}销售合同",
                "contract_type": "SALES",
                "customer_contract_no": f"DEMO-CUST-{seq}",
                "opportunity_id": opp_id,
                "quote_id": quote_id,
                "customer_id": customer_id,
                "total_amount": suggested_price,
                "received_amount": suggested_price * 0.3,
                "unreceived_amount": suggested_price * 0.7,
                "signing_date": ds(today - timedelta(days=1)),
                "effective_date": ds(today),
                "expiry_date": ds(today + timedelta(days=365)),
                "contract_period": 365,
                "contract_subject": scenario["equipment_type"],
                "payment_terms": "30%预付款+60%发货前+10%终验收",
                "delivery_terms": "合同生效后分阶段交付，现场 SAT 合格后终验。",
                "status": "SIGNED",
                "sales_owner_id": sales_user["id"],
                "contract_manager_id": pm_user["id"],
                "health_status": "H1",
                "health_score": 90,
                "approval_status": "APPROVED",
                "created_at": ts(created_at),
                "updated_at": ts(created_at),
            },
        )

    return {
        "customer_created": int(customer_created),
        "lead_created": int(lead_created),
        "opportunity_created": int(opp_created),
        "ticket_created": int(ticket_created),
        "solution_created": int(solution_created),
        "tender_created": int(tender_created),
        "quote_created": int(quote_created),
        "contract_created": int(contract_created),
    }


def seed_demo_data(db_path: Path, base_time: datetime | None = None) -> dict[str, Any]:
    conn = connect_db(db_path)
    try:
        require_tables(conn)
        cleanup_demo_children(conn)

        now = base_time or datetime.now()
        users = {
            "admin": get_user(conn, "admin", "fulingwei"),
            "sales": get_user(conn, "zhangzq", "admin"),
            "tech": get_user(conn, "limh", "admin"),
            "pm": get_user(conn, "wangjg", "admin"),
        }

        template_ids, template_stats = seed_templates(conn, now, users["admin"])
        totals = {
            "templates_created": template_stats["created"],
            "templates_updated": template_stats["updated"],
            "customers_created": 0,
            "leads_created": 0,
            "opportunities_created": 0,
            "tickets_created": 0,
            "solutions_created": 0,
            "tenders_created": 0,
            "quotes_created": 0,
            "contracts_created": 0,
        }
        for scenario in SCENARIOS:
            stats = seed_scenario(conn, scenario, template_ids, users, now)
            totals["customers_created"] += stats["customer_created"]
            totals["leads_created"] += stats["lead_created"]
            totals["opportunities_created"] += stats["opportunity_created"]
            totals["tickets_created"] += stats["ticket_created"]
            totals["solutions_created"] += stats["solution_created"]
            totals["tenders_created"] += stats["tender_created"]
            totals["quotes_created"] += stats["quote_created"]
            totals["contracts_created"] += stats["contract_created"]

        conn.commit()
        return {
            "db_path": str(db_path),
            "prefix": PREFIX,
            "scenario_count": len(SCENARIOS),
            "template_count": len(TECHNICAL_TEMPLATES),
            **totals,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="补充售前工作台关联演示数据")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite 数据库路径，默认 {DEFAULT_DB_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = seed_demo_data(args.db_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
