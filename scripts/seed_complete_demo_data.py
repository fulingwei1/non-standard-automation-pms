#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非标自动化测试设备行业完整演示数据脚本

业务链条:
销售信息 -> 销售线索 -> 线索评估 -> 商机转换 -> 报价 -> 合同 ->
工程项目 -> 采购 -> 生产 -> 售后

用法:
    python3 scripts/seed_complete_demo_data.py
"""

import json
import random
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"
PREFIX = "DEMO26"
PASSWORD_HASH = "$2b$12$9SwT6h8spI9T7YzBY2jJQe2F1Iu5LBskfMaMcHn0P3RYH2xX1YfBO"
RNG_SEED = 20260301
BASE_DATE = date(2026, 3, 1)
TARGET_SALES_AMOUNT = 250_000_000

COUNTS = {
    "customers": 40,
    "leads": 120,
    "opportunities": 52,
    "quotes": 40,
    "contracts": 24,
    "projects": 20,
    "purchase_orders": 72,
    "work_orders": 48,
    "service_tickets": 28,
}

PRODUCT_TYPES = ["ICT测试", "FCT测试", "EOL测试", "烧录设备", "老化设备", "视觉检测"]

GROUPS = [
    {"code": "G1", "name": "动力电池解决方案组", "dept": "动力电池销售组", "region": "华南/华东"},
    {"code": "G2", "name": "消费电子测试组", "dept": "消费电子销售组", "region": "华东/华中"},
    {"code": "G3", "name": "新能源整车测试组", "dept": "新能源整车销售组", "region": "华北/华中"},
    {"code": "G4", "name": "通信终端与泛工业组", "dept": "通信终端销售组", "region": "华南/西南"},
]

CUSTOMER_CATALOG = [
    ("比亚迪股份有限公司", "比亚迪", "新能源汽车", "深圳", "A", "large"),
    ("宁德时代新能源科技股份有限公司", "宁德时代", "动力电池", "宁德", "A", "large"),
    ("小米科技有限责任公司", "小米", "消费电子", "北京", "A", "large"),
    ("华为技术有限公司", "华为", "通信设备", "深圳", "A", "large"),
    ("吉利汽车集团有限公司", "吉利汽车", "新能源汽车", "杭州", "A", "large"),
    ("上汽通用五菱汽车股份有限公司", "上汽五菱", "新能源汽车", "柳州", "B", "large"),
    ("长城汽车股份有限公司", "长城汽车", "新能源汽车", "保定", "A", "large"),
    ("理想汽车科技有限公司", "理想汽车", "新能源汽车", "北京", "A", "large"),
    ("蔚来汽车科技有限公司", "蔚来汽车", "新能源汽车", "上海", "A", "large"),
    ("小鹏汽车科技有限公司", "小鹏汽车", "新能源汽车", "广州", "B", "large"),
    ("中创新航科技股份有限公司", "中创新航", "动力电池", "常州", "A", "large"),
    ("欣旺达电子股份有限公司", "欣旺达", "动力电池", "深圳", "B", "large"),
    ("惠州亿纬锂能股份有限公司", "亿纬锂能", "动力电池", "惠州", "A", "large"),
    ("国轩高科股份有限公司", "国轩高科", "动力电池", "合肥", "B", "large"),
    ("蜂巢能源科技股份有限公司", "蜂巢能源", "动力电池", "常州", "B", "large"),
    ("珠海冠宇电池股份有限公司", "珠海冠宇", "消费电子", "珠海", "B", "large"),
    ("立讯精密工业股份有限公司", "立讯精密", "消费电子", "东莞", "A", "large"),
    ("蓝思科技股份有限公司", "蓝思科技", "消费电子", "长沙", "B", "large"),
    ("歌尔股份有限公司", "歌尔股份", "消费电子", "潍坊", "B", "large"),
    ("闻泰科技股份有限公司", "闻泰科技", "消费电子", "上海", "B", "large"),
    ("OPPO广东移动通信有限公司", "OPPO", "消费电子", "东莞", "B", "large"),
    ("vivo移动通信有限公司", "vivo", "消费电子", "东莞", "B", "large"),
    ("荣耀终端有限公司", "荣耀", "消费电子", "深圳", "B", "large"),
    ("联想集团有限公司", "联想", "消费电子", "北京", "B", "large"),
    ("中兴通讯股份有限公司", "中兴通讯", "通信设备", "深圳", "A", "large"),
    ("海信集团有限公司", "海信", "消费电子", "青岛", "B", "large"),
    ("TCL实业控股股份有限公司", "TCL", "消费电子", "惠州", "B", "large"),
    ("美的集团股份有限公司", "美的", "智能家电", "佛山", "B", "large"),
    ("格力电器股份有限公司", "格力", "智能家电", "珠海", "B", "large"),
    ("海尔智家股份有限公司", "海尔", "智能家电", "青岛", "B", "large"),
    ("大疆创新科技有限公司", "大疆", "智能硬件", "深圳", "B", "large"),
    ("安克创新科技股份有限公司", "安克创新", "消费电子", "长沙", "B", "large"),
    ("广汽埃安新能源汽车有限公司", "广汽埃安", "新能源汽车", "广州", "B", "large"),
    ("赛力斯汽车有限公司", "赛力斯", "新能源汽车", "重庆", "B", "large"),
    ("极氪智能科技有限公司", "极氪", "新能源汽车", "杭州", "B", "large"),
    ("零跑汽车有限公司", "零跑汽车", "新能源汽车", "杭州", "C", "large"),
    ("先导智能装备股份有限公司", "先导智能", "锂电设备", "无锡", "B", "medium"),
    ("赢合科技股份有限公司", "赢合科技", "锂电设备", "深圳", "C", "medium"),
    ("德赛西威汽车电子股份有限公司", "德赛西威", "汽车电子", "惠州", "B", "medium"),
    ("联合汽车电子有限公司", "联合电子", "汽车电子", "上海", "B", "medium"),
]

VENDOR_NAMES = [
    "深圳华科自动化部件有限公司",
    "苏州精测工业技术有限公司",
    "东莞华信电控科技有限公司",
    "上海毅联智能系统有限公司",
    "常州宏远机械制造有限公司",
    "无锡腾创视觉科技有限公司",
    "宁波新力传感器股份有限公司",
    "广州迅达工业电气有限公司",
    "昆山瀚博工装设备有限公司",
    "佛山鸿力钣金科技有限公司",
    "合肥智达控制系统有限公司",
    "武汉远航工业软件有限公司",
]

MATERIAL_TEMPLATES = [
    ("ICT夹具总成", "套", 85000),
    ("FCT负载模块", "套", 62000),
    ("EOL高压测试模块", "套", 96000),
    ("工业相机组件", "套", 28000),
    ("伺服驱动总成", "套", 22000),
    ("安全光栅总成", "套", 12000),
    ("工控机I7平台", "台", 15000),
    ("PLC控制柜", "套", 18000),
    ("测试针床治具", "套", 42000),
    ("烧录工位模块", "套", 36000),
    ("老化负载柜", "台", 75000),
    ("MES通讯模块", "套", 16000),
]


def ts(dt: datetime | None = None) -> str:
    return (dt or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def dstr(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def connect_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库不存在: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    return conn


def ensure_tables(conn: sqlite3.Connection) -> None:
    required = [
        "departments",
        "employees",
        "users",
        "sales_teams",
        "sales_team_members",
        "sales_targets_v2",
        "team_performance_snapshots",
        "customers",
        "leads",
        "lead_requirement_details",
        "technical_assessments",
        "opportunities",
        "opportunity_requirements",
        "quotes",
        "quote_versions",
        "quote_items",
        "contracts",
        "projects",
        "project_milestones",
        "tasks",
        "vendors",
        "materials",
        "purchase_orders",
        "purchase_order_items",
        "production_plan",
        "work_order",
        "service_tickets",
        "customer_satisfactions",
    ]
    cur = conn.cursor()
    missing = []
    for table in required:
        exists = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if not exists:
            missing.append(table)
    if missing:
        raise RuntimeError(f"数据库缺少必要数据表: {', '.join(missing)}")


def cleanup_old_data(conn: sqlite3.Connection) -> None:
    like = f"{PREFIX}-%"
    user_like = f"{PREFIX.lower()}_%"
    desc_like = f"[{PREFIX}]%"
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM quote_items WHERE quote_version_id IN ("
        "SELECT id FROM quote_versions WHERE quote_id IN (SELECT id FROM quotes WHERE quote_code LIKE ?)"
        ")",
        (like,),
    )
    cur.execute("DELETE FROM quote_versions WHERE quote_id IN (SELECT id FROM quotes WHERE quote_code LIKE ?)", (like,))
    cur.execute(
        "DELETE FROM purchase_order_items WHERE order_id IN (SELECT id FROM purchase_orders WHERE order_no LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM project_milestones WHERE project_id IN (SELECT id FROM projects WHERE project_code LIKE ?) OR milestone_code LIKE ?",
        (like, like),
    )
    cur.execute(
        "DELETE FROM tasks WHERE project_id IN (SELECT id FROM projects WHERE project_code LIKE ?) OR task_code LIKE ?",
        (like, like),
    )
    cur.execute(
        "DELETE FROM opportunity_requirements WHERE opportunity_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM lead_requirement_details WHERE lead_id IN (SELECT id FROM leads WHERE lead_code LIKE ?)",
        (like,),
    )
    cur.execute(
        "DELETE FROM technical_assessments "
        "WHERE (source_type='LEAD' AND source_id IN (SELECT id FROM leads WHERE lead_code LIKE ?)) "
        "OR (source_type='OPPORTUNITY' AND source_id IN (SELECT id FROM opportunities WHERE opp_code LIKE ?))",
        (like, like),
    )

    cur.execute("DELETE FROM team_performance_snapshots WHERE period_value = ?", (f"{PREFIX}-2026Q1",))
    cur.execute("DELETE FROM sales_targets_v2 WHERE description LIKE ?", (desc_like,))
    cur.execute("DELETE FROM sales_team_members WHERE team_id IN (SELECT id FROM sales_teams WHERE team_code LIKE ?)", (like,))

    cur.execute("DELETE FROM service_tickets WHERE ticket_no LIKE ?", (like,))
    cur.execute("DELETE FROM work_order WHERE work_order_no LIKE ?", (like,))
    cur.execute("DELETE FROM production_plan WHERE plan_no LIKE ?", (like,))
    cur.execute("DELETE FROM purchase_orders WHERE order_no LIKE ?", (like,))
    cur.execute("DELETE FROM customer_satisfactions WHERE survey_no LIKE ?", (like,))
    cur.execute("DELETE FROM projects WHERE project_code LIKE ?", (like,))
    cur.execute("DELETE FROM contracts WHERE contract_code LIKE ?", (like,))
    cur.execute("DELETE FROM quotes WHERE quote_code LIKE ?", (like,))
    cur.execute("DELETE FROM opportunities WHERE opp_code LIKE ?", (like,))
    cur.execute("DELETE FROM leads WHERE lead_code LIKE ?", (like,))
    cur.execute("DELETE FROM customers WHERE customer_code LIKE ?", (like,))
    cur.execute("DELETE FROM materials WHERE material_code LIKE ?", (like,))
    cur.execute("DELETE FROM vendors WHERE supplier_code LIKE ?", (like,))
    cur.execute("DELETE FROM sales_teams WHERE team_code LIKE ?", (like,))
    cur.execute("DELETE FROM users WHERE username LIKE ?", (user_like,))
    cur.execute("DELETE FROM employees WHERE employee_code LIKE ?", (like,))
    cur.execute("DELETE FROM departments WHERE dept_code LIKE ?", (like,))
    conn.commit()


def seed_sales_team(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    created_at = ts()

    departments = {}
    cur.execute(
        """
        INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active, created_at, updated_at)
        VALUES (?, ?, NULL, 1, 900, 1, ?, ?)
        """,
        (f"{PREFIX}-DEPT-SALES", "销售中心（演示）", created_at, created_at),
    )
    sales_dept_id = cur.lastrowid
    departments["SALES"] = sales_dept_id

    for idx, group in enumerate(GROUPS, start=1):
        cur.execute(
            """
            INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 2, ?, 1, ?, ?)
            """,
            (
                f"{PREFIX}-DEPT-{group['code']}",
                f"{group['dept']}（演示）",
                sales_dept_id,
                900 + idx,
                created_at,
                created_at,
            ),
        )
        departments[group["code"]] = cur.lastrowid

    members = [
        {"name": "谢海峰", "title": "销售总经理", "group": None, "kind": "gm"},
        {"name": "唐峻峰", "title": "销售总监", "group": "G1", "kind": "director"},
        {"name": "宋文韬", "title": "销售总监", "group": "G2", "kind": "director"},
        {"name": "梁宇辰", "title": "销售总监", "group": "G3", "kind": "director"},
        {"name": "曹嘉宁", "title": "销售总监", "group": "G4", "kind": "director"},
        {"name": "邓思远", "title": "销售经理", "group": "G1", "kind": "manager"},
        {"name": "罗晨曦", "title": "销售经理", "group": "G2", "kind": "manager"},
        {"name": "纪铭哲", "title": "销售经理", "group": "G3", "kind": "manager"},
        {"name": "段彦廷", "title": "销售经理", "group": "G4", "kind": "manager"},
        {"name": "韩明轩", "title": "销售工程师", "group": "G1", "kind": "engineer"},
        {"name": "方祺瑞", "title": "销售工程师", "group": "G1", "kind": "engineer"},
        {"name": "蒋志豪", "title": "销售工程师", "group": "G1", "kind": "engineer"},
        {"name": "徐云川", "title": "销售工程师", "group": "G2", "kind": "engineer"},
        {"name": "贺一凡", "title": "销售工程师", "group": "G2", "kind": "engineer"},
        {"name": "苗旭东", "title": "销售工程师", "group": "G2", "kind": "engineer"},
        {"name": "白若尧", "title": "销售工程师", "group": "G3", "kind": "engineer"},
        {"name": "魏凯文", "title": "销售工程师", "group": "G3", "kind": "engineer"},
        {"name": "严启航", "title": "销售工程师", "group": "G4", "kind": "engineer"},
        {"name": "周伯谦", "title": "销售工程师", "group": "G4", "kind": "engineer"},
    ]

    users = []
    group_to_users = defaultdict(list)
    group_director = {}
    group_manager = {}
    gm_user_id = None
    frontline_user_ids = []
    user_to_group = {}

    for idx, member in enumerate(members, start=1):
        emp_code = f"{PREFIX}-EMP-{idx:03d}"
        username = f"{PREFIX.lower()}_sales_{idx:03d}"
        group = member["group"]
        dept_id = sales_dept_id if group is None else departments[group]
        dept_name = "销售中心" if group is None else GROUPS[[g["code"] for g in GROUPS].index(group)]["dept"]

        cur.execute(
            """
            INSERT INTO employees (employee_code, name, department, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (emp_code, member["name"], dept_name, member["title"], created_at, created_at),
        )
        employee_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO users (
                username, password_hash, employee_id, real_name, department_id, department, position,
                is_active, is_superuser, solution_credits, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 0, ?, ?)
            """,
            (
                username,
                PASSWORD_HASH,
                employee_id,
                member["name"],
                dept_id,
                dept_name,
                member["title"],
                1 if member["kind"] == "gm" else 0,
                created_at,
                created_at,
            ),
        )
        user_id = cur.lastrowid
        member_info = {
            "user_id": user_id,
            "employee_id": employee_id,
            "name": member["name"],
            "title": member["title"],
            "kind": member["kind"],
            "group": group,
        }
        users.append(member_info)
        if group:
            group_to_users[group].append(member_info)
            user_to_group[user_id] = group

        if member["kind"] == "gm":
            gm_user_id = user_id
        elif member["kind"] == "director":
            group_director[group] = user_id
        elif member["kind"] == "manager":
            group_manager[group] = user_id
            frontline_user_ids.append(user_id)
        else:
            frontline_user_ids.append(user_id)

    cur.execute(
        """
        INSERT INTO sales_teams (
            team_code, team_name, description, team_type, department_id, leader_id,
            parent_team_id, is_active, sort_order, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, 1, 900, ?, ?, ?)
        """,
        (
            f"{PREFIX}-TEAM-HQ",
            "销售中心战区（演示）",
            "金凯博自动化测试设备销售中心",
            "REGION",
            sales_dept_id,
            gm_user_id,
            gm_user_id,
            created_at,
            created_at,
        ),
    )
    root_team_id = cur.lastrowid

    teams = []
    for idx, group in enumerate(GROUPS, start=1):
        code = group["code"]
        cur.execute(
            """
            INSERT INTO sales_teams (
                team_code, team_name, description, team_type, department_id, leader_id,
                parent_team_id, is_active, sort_order, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (
                f"{PREFIX}-TEAM-{code}",
                f"{group['name']}（演示）",
                f"{group['region']}市场",
                "REGION",
                departments[code],
                group_director[code],
                root_team_id,
                900 + idx,
                gm_user_id,
                created_at,
                created_at,
            ),
        )
        team_id = cur.lastrowid
        teams.append({"team_id": team_id, "group": code, "name": group["name"]})

        for member in group_to_users[code]:
            role = "ENGINEER"
            if member["kind"] == "director":
                role = "DIRECTOR"
            elif member["kind"] == "manager":
                role = "MANAGER"
            cur.execute(
                """
                INSERT INTO sales_team_members (team_id, user_id, role, joined_at, is_primary, is_active, remark, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?)
                """,
                (
                    team_id,
                    member["user_id"],
                    role,
                    created_at,
                    f"{PREFIX}演示成员",
                    created_at,
                    created_at,
                ),
            )

    cur.execute(
        """
        INSERT INTO sales_team_members (team_id, user_id, role, joined_at, is_primary, is_active, remark, created_at, updated_at)
        VALUES (?, ?, 'GENERAL_MANAGER', ?, 1, 1, ?, ?, ?)
        """,
        (root_team_id, gm_user_id, created_at, f"{PREFIX}演示总经理", created_at, created_at),
    )
    for director_id in group_director.values():
        cur.execute(
            """
            INSERT INTO sales_team_members (team_id, user_id, role, joined_at, is_primary, is_active, remark, created_at, updated_at)
            VALUES (?, ?, 'DIRECTOR', ?, 0, 1, ?, ?, ?)
            """,
            (root_team_id, director_id, created_at, f"{PREFIX}演示总监", created_at, created_at),
        )

    conn.commit()
    return {
        "users": users,
        "gm_user_id": gm_user_id,
        "group_manager": group_manager,
        "group_director": group_director,
        "frontline_user_ids": frontline_user_ids,
        "teams": teams,
        "user_to_group": user_to_group,
        "departments": departments,
    }


def seed_customers(conn: sqlite3.Connection, sales_ctx: dict, rng: random.Random) -> list[dict]:
    cur = conn.cursor()
    owners = sales_ctx["frontline_user_ids"]
    created = []

    for idx in range(COUNTS["customers"]):
        full_name, short_name, industry, city, level, scale = CUSTOMER_CATALOG[idx]
        customer_code = f"{PREFIX}-CUST-{idx + 1:03d}"
        owner_id = owners[idx % len(owners)]
        created_at = ts(datetime.combine(BASE_DATE - timedelta(days=560 - idx * 3), datetime.min.time()))
        annual_revenue = round(rng.uniform(2.0, 120.0) * 100_000_000, 2)

        cur.execute(
            """
            INSERT INTO customers (
                customer_code, customer_name, short_name, customer_type, industry, scale, address,
                contact_person, contact_phone, contact_email, credit_level, payment_terms, status,
                customer_level, customer_source, sales_owner_id, annual_revenue, created_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, 'enterprise', ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_code,
                full_name,
                short_name,
                industry,
                scale,
                f"{city}市高新区智能制造园{idx + 1}号",
                f"客户联系人{idx + 1:02d}",
                f"139{idx + 10000000:08d}",
                f"contact{idx + 1:02d}@demo26.local",
                "A" if level == "A" else ("B" if level == "B" else "C"),
                "30%预付款+60%到货款+10%验收款",
                level,
                "行业展会/老客户转介绍",
                owner_id,
                annual_revenue,
                sales_ctx["gm_user_id"],
                created_at,
                created_at,
            ),
        )
        created.append(
            {
                "id": cur.lastrowid,
                "code": customer_code,
                "name": full_name,
                "short_name": short_name,
                "industry": industry,
                "owner_id": owner_id,
            }
        )

    conn.commit()
    return created


def generate_won_amounts(rng: random.Random, count: int, total_amount: int) -> list[int]:
    raw = [rng.uniform(6.5, 15.5) for _ in range(count)]
    scale = total_amount / (sum(raw) * 1_000_000)
    amounts = [int(v * scale * 1_000_000) for v in raw]
    delta = total_amount - sum(amounts)
    amounts[0] += delta
    return amounts


def seed_leads_and_assessments(
    conn: sqlite3.Connection,
    sales_ctx: dict,
    customers: list[dict],
    won_amounts: list[int],
    rng: random.Random,
) -> dict:
    cur = conn.cursor()
    converted_indexes = set(rng.sample(range(COUNTS["leads"]), COUNTS["opportunities"]))

    leads = []
    converted_leads = []
    assessment_rows = 0
    lead_sources = ["展会", "官网咨询", "老客户转介绍", "行业协会", "渠道伙伴", "招投标平台"]
    source_weights = [0.22, 0.18, 0.24, 0.12, 0.14, 0.10]
    frontline = sales_ctx["frontline_user_ids"]
    directors = list(sales_ctx["group_director"].values())

    for idx in range(COUNTS["leads"]):
        customer = customers[idx % len(customers)]
        product = PRODUCT_TYPES[idx % len(PRODUCT_TYPES)]
        owner_id = frontline[idx % len(frontline)]
        lead_code = f"{PREFIX}-LD-{idx + 1:04d}"

        if idx in converted_indexes:
            status = "CONVERTED"
        else:
            status = rng.choices(
                ["NEW", "CONTACTED", "QUALIFIED", "LOST"],
                weights=[0.32, 0.29, 0.27, 0.12],
                k=1,
            )[0]

        created_day = BASE_DATE - timedelta(days=320 - idx * 2)
        priority = rng.randint(48, 95)
        cur.execute(
            """
            INSERT INTO leads (
                lead_code, source, customer_name, industry, contact_name, contact_phone, demand_summary,
                owner_id, status, next_action_at, product_match_type, is_advantage_product,
                assessment_status, priority_score, completeness, health_status, health_score,
                last_follow_up_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ADVANTAGE', 1, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_code,
                rng.choices(lead_sources, source_weights, k=1)[0],
                customer["name"],
                customer["industry"],
                f"{customer['short_name']}对接人{(idx % 6) + 1}",
                f"138{idx + 20000000:08d}",
                f"{product}产线扩建，计划新增{rng.randint(2, 8)}个测试工位，目标CT {rng.randint(18, 55)}秒",
                owner_id,
                status,
                ts(datetime.combine(created_day + timedelta(days=rng.randint(5, 25)), datetime.min.time())),
                "ASSESSMENT_COMPLETED" if status in {"CONVERTED", "QUALIFIED"} else "PENDING",
                priority,
                rng.randint(70, 95) if status in {"CONVERTED", "QUALIFIED"} else rng.randint(30, 70),
                "H1" if priority >= 80 else ("H2" if priority >= 60 else "H3"),
                priority,
                ts(datetime.combine(created_day + timedelta(days=rng.randint(1, 12)), datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
            ),
        )
        lead_id = cur.lastrowid

        leads.append(
            {
                "id": lead_id,
                "code": lead_code,
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "customer_short": customer["short_name"],
                "industry": customer["industry"],
                "status": status,
                "owner_id": owner_id,
                "product": product,
                "created_date": created_day,
            }
        )
        if status == "CONVERTED":
            converted_leads.append(leads[-1])

    for idx, lead in enumerate(leads):
        if lead["status"] in {"NEW", "LOST"}:
            continue
        created_time = ts(datetime.combine(lead["created_date"] + timedelta(days=8), datetime.min.time()))
        maturity = rng.randint(2, 5) if lead["status"] == "CONVERTED" else rng.randint(1, 4)
        cur.execute(
            """
            INSERT INTO lead_requirement_details (
                lead_id, customer_factory_location, application_scenario, delivery_mode, requirement_maturity,
                has_sow, has_interface_doc, sample_availability, key_risk_factors, target_capacity_uph,
                cycle_time_seconds, safety_requirements, acceptance_basis, traceability_type,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["id"],
                f"{lead['customer_short']}工厂-{rng.choice(['一厂', '二厂', '三厂'])}",
                f"{lead['product']}量产导入",
                rng.choice(["整线交钥匙", "分段交付", "驻场实施"]),
                maturity,
                rng.choice(["客户提供样机", "提供Golden Sample", "提供关键治具"]),
                rng.choice(["新产品迭代快", "节拍压力大", "多型号混线", "接口变更频繁"]),
                round(rng.uniform(35, 160), 2),
                round(rng.uniform(18, 60), 2),
                "满足CE与国标安规要求",
                "FAT+SAT双阶段验收，CPK>=1.33",
                rng.choice(["SN+条码", "SN+MES", "全流程追溯"]),
                created_time,
                created_time,
            ),
        )
        requirement_id = cur.lastrowid

        score = rng.randint(68, 94) if lead["status"] == "CONVERTED" else rng.randint(55, 85)
        decision = "GO" if score >= 75 else "GO_WITH_CONDITIONS"
        dimensions = {
            "business_fit": rng.randint(65, 95),
            "technical_feasibility": rng.randint(60, 96),
            "delivery_risk": rng.randint(55, 90),
            "profitability": rng.randint(58, 92),
        }
        cur.execute(
            """
            INSERT INTO technical_assessments (
                source_type, source_id, evaluator_id, status, total_score, dimension_scores,
                veto_triggered, decision, risks, conditions, evaluated_at, created_at, updated_at
            ) VALUES ('LEAD', ?, ?, 'COMPLETED', ?, ?, 0, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["id"],
                directors[idx % len(directors)],
                score,
                json.dumps(dimensions, ensure_ascii=False),
                decision,
                json.dumps(
                    [rng.choice(["交期风险", "关键件风险", "现场接口不稳定", "需求边界不清晰"])],
                    ensure_ascii=False,
                ),
                json.dumps(["需锁定验收边界", "需提前确认样件批次"], ensure_ascii=False),
                created_time,
                created_time,
                created_time,
            ),
        )
        assessment_id = cur.lastrowid

        cur.execute(
            """
            UPDATE leads
            SET requirement_detail_id=?, assessment_id=?, assessment_status='ASSESSMENT_COMPLETED',
                completeness=?, updated_at=?
            WHERE id=?
            """,
            (
                requirement_id,
                assessment_id,
                rng.randint(78, 98),
                created_time,
                lead["id"],
            ),
        )
        assessment_rows += 1

    converted_leads = sorted(converted_leads, key=lambda item: item["id"])
    for idx, lead in enumerate(converted_leads):
        lead["planned_amount"] = won_amounts[idx] if idx < len(won_amounts) else rng.randint(2_000_000, 8_000_000)

    conn.commit()
    return {
        "leads": leads,
        "converted_leads": converted_leads,
        "assessments": assessment_rows,
    }


def seed_opportunities(conn: sqlite3.Connection, leads_ctx: dict, sales_ctx: dict, rng: random.Random) -> list[dict]:
    cur = conn.cursor()
    converted_leads = leads_ctx["converted_leads"]
    opportunities = []

    stage_plan = (
        ["WON"] * COUNTS["contracts"]
        + ["NEGOTIATION"] * 8
        + ["PROPOSAL"] * 8
        + ["QUALIFICATION"] * 6
        + ["LOST"] * 6
    )

    for idx in range(COUNTS["opportunities"]):
        lead = converted_leads[idx]
        stage = stage_plan[idx]
        product = PRODUCT_TYPES[idx % len(PRODUCT_TYPES)]
        created_day = lead["created_date"] + timedelta(days=rng.randint(10, 28))
        close_day = created_day + timedelta(days=rng.randint(30, 180))
        if stage == "WON":
            amount = lead["planned_amount"]
            probability = rng.randint(82, 95)
        elif stage == "NEGOTIATION":
            amount = int(rng.uniform(6_000_000, 14_000_000))
            probability = rng.randint(60, 80)
        elif stage == "PROPOSAL":
            amount = int(rng.uniform(4_500_000, 12_000_000))
            probability = rng.randint(45, 65)
        elif stage == "QUALIFICATION":
            amount = int(rng.uniform(3_000_000, 9_000_000))
            probability = rng.randint(30, 50)
        else:
            amount = int(rng.uniform(2_000_000, 8_000_000))
            probability = rng.randint(8, 25)

        margin = round(rng.uniform(35, 55), 2)
        opp_code = f"{PREFIX}-OPP-{idx + 1:04d}"

        cur.execute(
            """
            INSERT INTO opportunities (
                opp_code, lead_id, customer_id, opp_name, project_type, equipment_type, stage,
                probability, est_amount, est_margin, expected_close_date, decision_chain,
                acceptance_basis, risk_level, owner_id, updated_by, gate_status, priority_score,
                assessment_status, health_status, health_score, last_progress_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'NPI', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opp_code,
                lead["id"],
                lead["customer_id"],
                f"{lead['customer_short']}{product}非标自动化测试项目",
                product,
                stage,
                probability,
                amount,
                margin,
                dstr(close_day),
                json.dumps(
                    {
                        "EB": "工厂总监",
                        "TB": "测试经理",
                        "PB": "采购总监",
                        "Coach": "设备工程师",
                    },
                    ensure_ascii=False,
                ),
                "FAT+SAT，连续稳定运行72小时",
                rng.choice(["LOW", "MEDIUM", "HIGH"]),
                lead["owner_id"],
                lead["owner_id"],
                "PASSED" if stage in {"WON", "NEGOTIATION"} else "PENDING",
                probability,
                "ASSESSMENT_COMPLETED",
                "H1" if probability >= 75 else ("H2" if probability >= 50 else "H3"),
                probability,
                ts(datetime.combine(created_day + timedelta(days=5), datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
            ),
        )
        opp_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO opportunity_requirements (
                opportunity_id, product_object, ct_seconds, interface_desc, site_constraints,
                acceptance_criteria, safety_requirement, extra_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opp_id,
                product,
                rng.randint(20, 60),
                "MES/PLC/条码枪/相机多协议通讯",
                "场地净高3.2m，温湿度可控，单班换型<30min",
                "GRR<10%，CPK>=1.33，误判率<0.3%",
                "急停/光栅/门禁/ESD全闭环",
                json.dumps({"line_speed": rng.randint(40, 120), "uph": rng.randint(80, 420)}, ensure_ascii=False),
                ts(datetime.combine(created_day, datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
            ),
        )

        score = int(probability * 0.6 + margin * 0.4)
        cur.execute(
            """
            INSERT INTO technical_assessments (
                source_type, source_id, evaluator_id, status, total_score, dimension_scores,
                veto_triggered, decision, risks, conditions, evaluated_at, created_at, updated_at
            ) VALUES ('OPPORTUNITY', ?, ?, 'COMPLETED', ?, ?, 0, ?, ?, ?, ?, ?, ?)
            """,
            (
                opp_id,
                sales_ctx["group_director"][sales_ctx["user_to_group"][lead["owner_id"]]],
                score,
                json.dumps(
                    {
                        "technical": rng.randint(60, 96),
                        "cost": rng.randint(58, 90),
                        "delivery": rng.randint(55, 92),
                        "customer_relationship": rng.randint(62, 95),
                    },
                    ensure_ascii=False,
                ),
                "GO" if stage != "LOST" else "NO_GO",
                json.dumps([rng.choice(["交付窗口紧", "需锁定关键料号", "需求变更频繁"])], ensure_ascii=False),
                json.dumps(["项目里程碑需纳入合同条款"], ensure_ascii=False),
                ts(datetime.combine(created_day + timedelta(days=7), datetime.min.time())),
                ts(datetime.combine(created_day + timedelta(days=7), datetime.min.time())),
                ts(datetime.combine(created_day + timedelta(days=7), datetime.min.time())),
            ),
        )
        assess_id = cur.lastrowid
        cur.execute("UPDATE opportunities SET assessment_id=?, updated_at=? WHERE id=?", (assess_id, ts(), opp_id))

        opportunities.append(
            {
                "id": opp_id,
                "code": opp_code,
                "lead_id": lead["id"],
                "customer_id": lead["customer_id"],
                "customer_short": lead["customer_short"],
                "owner_id": lead["owner_id"],
                "product": product,
                "stage": stage,
                "probability": probability,
                "amount": amount,
            }
        )

    conn.commit()
    return opportunities


def seed_quotes(conn: sqlite3.Connection, opportunities: list[dict], rng: random.Random) -> dict:
    cur = conn.cursor()
    candidates = [o for o in opportunities if o["stage"] != "LOST"]
    selected = candidates[: COUNTS["quotes"]]
    quotes = []
    opp_to_quote = {}

    component_lines = [
        ("BOM", "机械机构与夹治具"),
        ("BOM", "电控系统与配线"),
        ("SOFTWARE", "测试软件与MES接口"),
        ("SERVICE", "调试联机与验收支持"),
        ("BOM", "视觉系统与传感组件"),
    ]

    for idx, opp in enumerate(selected):
        created_day = BASE_DATE - timedelta(days=120 - idx)
        if opp["stage"] == "WON":
            status = "ACCEPTED" if idx % 2 == 0 else "APPROVED"
        else:
            status = rng.choices(
                ["DRAFT", "SUBMITTED", "APPROVED"],
                weights=[0.30, 0.45, 0.25],
                k=1,
            )[0]

        quote_code = f"{PREFIX}-QT-{idx + 1:04d}"
        quote_total = int(opp["amount"] * rng.uniform(0.96, 1.05))
        gross_margin = round(rng.uniform(35, 55), 2)
        cost_total = round(quote_total * (1 - gross_margin / 100), 2)

        cur.execute(
            """
            INSERT INTO quotes (
                quote_code, opportunity_id, customer_id, status, valid_until, delivery_date,
                owner_id, health_status, health_score, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote_code,
                opp["id"],
                opp["customer_id"],
                status,
                dstr(created_day + timedelta(days=45)),
                dstr(created_day + timedelta(days=rng.randint(95, 260))),
                opp["owner_id"],
                "H1" if status in {"APPROVED", "ACCEPTED"} else "H2",
                rng.randint(68, 95),
                ts(datetime.combine(created_day, datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
            ),
        )
        quote_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO quote_versions (
                quote_id, version_no, total_price, cost_total, gross_margin, lead_time_days,
                risk_terms, delivery_date, created_by, approved_by, approved_at,
                cost_breakdown_complete, margin_warning, created_at, updated_at
            ) VALUES (?, 'V1.0', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                quote_id,
                quote_total,
                cost_total,
                gross_margin,
                rng.randint(90, 220),
                "关键元器件交期浮动±10天；客户现场接口变更不超过两轮",
                dstr(created_day + timedelta(days=rng.randint(100, 280))),
                opp["owner_id"],
                opp["owner_id"] if status in {"APPROVED", "ACCEPTED"} else None,
                ts(datetime.combine(created_day + timedelta(days=2), datetime.min.time()))
                if status in {"APPROVED", "ACCEPTED"}
                else None,
                1 if gross_margin < 38 else 0,
                ts(datetime.combine(created_day, datetime.min.time())),
                ts(datetime.combine(created_day, datetime.min.time())),
            ),
        )
        version_id = cur.lastrowid

        weights = [0.30, 0.23, 0.18, 0.14, 0.15]
        for line_no, (item_type, item_name) in enumerate(component_lines, start=1):
            line_amount = round(quote_total * weights[line_no - 1], 2)
            line_cost = round(line_amount * rng.uniform(0.72, 0.86), 2)
            qty = round(rng.uniform(1.0, 6.0), 2)
            unit_price = round(line_amount / qty, 2)
            cur.execute(
                """
                INSERT INTO quote_items (
                    quote_version_id, item_type, item_name, qty, unit_price, cost,
                    lead_time_days, remark, cost_category, cost_source, specification, unit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'BOM', ?, '项')
                """,
                (
                    version_id,
                    item_type,
                    item_name,
                    qty,
                    unit_price,
                    line_cost,
                    rng.randint(20, 90),
                    "演示数据BOM行",
                    "设备/软件/服务",
                    f"{opp['product']}方案分解",
                ),
            )

        cur.execute("UPDATE quotes SET current_version_id=?, updated_at=? WHERE id=?", (version_id, ts(), quote_id))

        record = {
            "id": quote_id,
            "version_id": version_id,
            "code": quote_code,
            "opp_id": opp["id"],
            "customer_id": opp["customer_id"],
            "status": status,
            "owner_id": opp["owner_id"],
            "total_price": quote_total,
            "cost_total": cost_total,
            "margin": gross_margin,
        }
        quotes.append(record)
        opp_to_quote[opp["id"]] = record

    conn.commit()
    return {"quotes": quotes, "opp_to_quote": opp_to_quote}


def seed_contracts(
    conn: sqlite3.Connection,
    opportunities: list[dict],
    quote_ctx: dict,
    sales_ctx: dict,
    rng: random.Random,
) -> list[dict]:
    cur = conn.cursor()
    won_opps = [o for o in opportunities if o["stage"] == "WON"]
    contracts = []

    for idx, opp in enumerate(won_opps):
        quote = quote_ctx["opp_to_quote"].get(opp["id"])
        total_amount = quote["total_price"] if quote else opp["amount"]
        total_amount = max(500_000, min(20_000_000, int(total_amount)))

        sign_day = BASE_DATE - timedelta(days=180 - idx * 4)
        cycle_months = rng.randint(3, 12)
        received_rate = rng.uniform(0.35, 0.88)
        received_amount = round(total_amount * received_rate, 2)
        contract_code = f"{PREFIX}-CT-{idx + 1:04d}"
        group_code = sales_ctx["user_to_group"][opp["owner_id"]]

        cur.execute(
            """
            INSERT INTO contracts (
                contract_code, contract_name, contract_type, opportunity_id, quote_id, customer_id,
                total_amount, received_amount, unreceived_amount, signing_date, effective_date, expiry_date,
                contract_period, contract_subject, payment_terms, delivery_terms, status,
                sales_owner_id, contract_manager_id, health_status, health_score, created_at, updated_at
            ) VALUES (?, ?, 'SALES', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_code,
                f"{opp['customer_short']}{opp['product']}自动化测试设备采购合同",
                opp["id"],
                quote["id"] if quote else None,
                opp["customer_id"],
                total_amount,
                received_amount,
                round(total_amount - received_amount, 2),
                dstr(sign_day),
                dstr(sign_day),
                dstr(sign_day + timedelta(days=365)),
                12,
                f"{opp['product']}设备开发、交付、安装调试及验收",
                "30%预付款，60%发货款，10%终验款（质保后30天内）",
                f"{cycle_months}个月内完成设计制造与交付",
                "ACTIVE" if idx >= 6 else "COMPLETED",
                opp["owner_id"],
                sales_ctx["group_director"][group_code],
                "H1",
                rng.randint(75, 96),
                ts(datetime.combine(sign_day, datetime.min.time())),
                ts(datetime.combine(sign_day, datetime.min.time())),
            ),
        )
        contracts.append(
            {
                "id": cur.lastrowid,
                "code": contract_code,
                "opp_id": opp["id"],
                "lead_id": opp["lead_id"],
                "customer_id": opp["customer_id"],
                "owner_id": opp["owner_id"],
                "product": opp["product"],
                "amount": total_amount,
                "sign_day": sign_day,
                "cycle_months": cycle_months,
            }
        )

    conn.commit()
    return contracts


def seed_projects(conn: sqlite3.Connection, contracts: list[dict], sales_ctx: dict, rng: random.Random) -> dict:
    cur = conn.cursor()
    manager_ids = list(sales_ctx["group_manager"].values())
    projects = []
    milestone_count = 0
    task_count = 0

    for idx, contract in enumerate(contracts[: COUNTS["projects"]]):
        pm_id = manager_ids[idx % len(manager_ids)]
        cycle_months = contract["cycle_months"]
        start_day = contract["sign_day"] + timedelta(days=rng.randint(7, 20))
        end_day = start_day + timedelta(days=cycle_months * 30)
        margin = round(rng.uniform(35, 55), 2)
        actual_cost = round(contract["amount"] * (1 - margin / 100), 2)
        budget_amount = round(actual_cost * rng.uniform(1.03, 1.12), 2)
        progress = rng.randint(18, 95)
        if progress < 30:
            stage = "planning"
        elif progress < 55:
            stage = "design"
        elif progress < 80:
            stage = "execution"
        else:
            stage = "testing"

        project_code = f"{PREFIX}-PRJ-{idx + 1:04d}"
        created_time = ts(datetime.combine(start_day, datetime.min.time()))
        cur.execute(
            """
            INSERT INTO projects (
                project_code, project_name, short_name, customer_id, customer_name, contract_no,
                project_type, product_category, industry, stage, status, health, progress_pct,
                contract_date, planned_start_date, planned_end_date, contract_amount, budget_amount,
                actual_cost, pm_id, pm_name, priority, tags, description, requirements,
                is_active, lead_id, opportunity_id, contract_id, salesperson_id, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, (SELECT customer_name FROM customers WHERE id=?), ?, ?, ?, (SELECT industry FROM customers WHERE id=?),
                      ?, 'ACTIVE', 'GOOD', ?, ?, ?, ?, ?, ?, ?, ?, (SELECT real_name FROM users WHERE id=?), ?,
                      ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_code,
                f"{contract['product']}自动化测试系统交付项目{idx + 1}",
                f"{contract['product']}交付{idx + 1}",
                contract["customer_id"],
                contract["customer_id"],
                contract["code"],
                contract["product"],
                contract["product"],
                contract["customer_id"],
                stage,
                progress,
                dstr(contract["sign_day"]),
                dstr(start_day),
                dstr(end_day),
                contract["amount"],
                budget_amount,
                actual_cost,
                pm_id,
                pm_id,
                "HIGH" if contract["amount"] >= 10_000_000 else "MEDIUM",
                json.dumps([contract["product"], "非标自动化", "交钥匙工程"], ensure_ascii=False),
                f"面向{contract['product']}产线的测试自动化项目，覆盖方案、制造、联机、验收。",
                "节拍满足目标，稳定性>=99.5%，支持MES追溯",
                contract["lead_id"],
                contract["opp_id"],
                contract["id"],
                contract["owner_id"],
                sales_ctx["gm_user_id"],
                created_time,
                created_time,
            ),
        )
        project_id = cur.lastrowid
        projects.append(
            {
                "id": project_id,
                "code": project_code,
                "customer_id": contract["customer_id"],
                "owner_id": contract["owner_id"],
                "pm_id": pm_id,
                "product": contract["product"],
                "start": start_day,
                "end": end_day,
                "progress": progress,
                "margin": margin,
            }
        )

        milestone_templates = [
            ("KICKOFF", "项目启动会", 0.05),
            ("DESIGN_FREEZE", "方案冻结", 0.25),
            ("FAT", "工厂预验收", 0.55),
            ("SAT", "现场验收", 0.82),
            ("FINAL", "终验与移交", 1.00),
        ]
        milestone_ids = []
        for m_idx, (m_type, m_name, ratio) in enumerate(milestone_templates, start=1):
            planned = start_day + timedelta(days=int((end_day - start_day).days * ratio))
            status = "DONE" if progress >= int(ratio * 100) else "PENDING"
            cur.execute(
                """
                INSERT INTO project_milestones (
                    project_id, milestone_code, milestone_name, milestone_type, planned_date, actual_date,
                    status, is_key, stage_code, deliverables, owner_id, remark, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    f"{PREFIX}-MS-{idx + 1:03d}-{m_idx}",
                    m_name,
                    m_type,
                    dstr(planned),
                    dstr(planned + timedelta(days=rng.randint(0, 3))) if status == "DONE" else None,
                    status,
                    stage,
                    "里程碑评审记录+签字单",
                    pm_id,
                    "演示里程碑",
                    created_time,
                    created_time,
                ),
            )
            milestone_ids.append(cur.lastrowid)
            milestone_count += 1

        task_templates = [
            ("1.0", "需求澄清与方案边界冻结"),
            ("2.0", "电气及机械详细设计"),
            ("3.0", "装配与配线实施"),
            ("4.0", "软件联机与联调"),
            ("5.0", "FAT验证与问题闭环"),
            ("6.0", "SAT导入与终验"),
        ]
        for t_idx, (wbs, task_name) in enumerate(task_templates, start=1):
            part_start = start_day + timedelta(days=int((t_idx - 1) * (end_day - start_day).days / 6))
            part_end = part_start + timedelta(days=max(12, int((end_day - start_day).days / 8)))
            threshold = int((t_idx / len(task_templates)) * 100)
            if progress >= threshold + 15:
                status = "DONE"
                prog = 100
            elif progress >= threshold - 10:
                status = "IN_PROGRESS"
                prog = min(95, max(25, progress))
            else:
                status = "TODO"
                prog = rng.randint(0, 20)

            cur.execute(
                """
                INSERT INTO tasks (
                    project_id, milestone_id, task_code, task_name, stage, status, owner_id,
                    plan_start, plan_end, progress_percent, weight, block_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    milestone_ids[min(t_idx - 1, len(milestone_ids) - 1)],
                    f"{PREFIX}-WBS-{idx + 1:03d}-{wbs}",
                    task_name,
                    stage,
                    status,
                    pm_id if t_idx <= 2 else contract["owner_id"],
                    dstr(part_start),
                    dstr(part_end),
                    int(prog),
                    round(100 / len(task_templates), 2),
                    None if status != "TODO" else "等待客户确认接口文档",
                    created_time,
                    created_time,
                ),
            )
            task_count += 1

    conn.commit()
    return {"projects": projects, "milestones": milestone_count, "tasks": task_count}


def seed_procurement(
    conn: sqlite3.Connection,
    projects: list[dict],
    sales_ctx: dict,
    rng: random.Random,
) -> dict:
    cur = conn.cursor()
    created_at = ts()

    vendors = []
    for idx, name in enumerate(VENDOR_NAMES, start=1):
        code = f"{PREFIX}-SUP-{idx:03d}"
        cur.execute(
            """
            INSERT INTO vendors (
                supplier_code, supplier_name, vendor_type, supplier_level, payment_terms,
                contact_person, contact_phone, address, status, created_by, created_at, updated_at
            ) VALUES (?, ?, 'MATERIAL', ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
            """,
            (
                code,
                name,
                rng.choice(["A", "B", "C"]),
                "月结60天",
                f"供应商联系人{idx:02d}",
                f"137{idx + 30000000:08d}",
                f"华南供应链基地{idx}号",
                sales_ctx["gm_user_id"],
                created_at,
                created_at,
            ),
        )
        vendors.append({"id": cur.lastrowid, "name": name})

    materials = []
    for idx in range(36):
        tpl = MATERIAL_TEMPLATES[idx % len(MATERIAL_TEMPLATES)]
        mat_code = f"{PREFIX}-MAT-{idx + 1:03d}"
        price = round(tpl[2] * rng.uniform(0.86, 1.18), 2)
        cur.execute(
            """
            INSERT INTO materials (
                material_code, material_name, specification, unit, source_type,
                standard_price, last_price, safety_stock, current_stock,
                lead_time_days, default_supplier_id, is_active, is_key_material,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'PURCHASE', ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (
                mat_code,
                f"{tpl[0]}-{idx + 1:02d}",
                f"版本{(idx % 4) + 1}，适配{PRODUCT_TYPES[idx % len(PRODUCT_TYPES)]}",
                tpl[1],
                price,
                price,
                round(rng.uniform(2, 12), 2),
                round(rng.uniform(8, 40), 2),
                rng.randint(10, 45),
                vendors[idx % len(vendors)]["id"],
                1 if idx % 6 == 0 else 0,
                sales_ctx["gm_user_id"],
                created_at,
                created_at,
            ),
        )
        materials.append({"id": cur.lastrowid, "name": tpl[0], "unit": tpl[1], "price": price})

    purchase_orders = []
    item_count = 0
    managers = list(sales_ctx["group_manager"].values())
    for idx in range(COUNTS["purchase_orders"]):
        project = projects[idx % len(projects)]
        supplier = vendors[idx % len(vendors)]
        order_no = f"{PREFIX}-PO-{idx + 1:04d}"
        order_day = project["start"] - timedelta(days=rng.randint(5, 45))
        required_day = order_day + timedelta(days=rng.randint(15, 75))
        promised_day = required_day + timedelta(days=rng.randint(-2, 12))
        status = rng.choices(
            ["DRAFT", "PENDING", "APPROVED", "SHIPPED", "RECEIVED"],
            weights=[0.12, 0.18, 0.24, 0.22, 0.24],
            k=1,
        )[0]
        order_total = round(rng.uniform(80_000, 1_200_000), 2)
        tax_rate = 13
        tax_amount = round(order_total * tax_rate / 100, 2)

        cur.execute(
            """
            INSERT INTO purchase_orders (
                order_no, supplier_id, project_id, order_type, order_title, total_amount, tax_rate, tax_amount,
                amount_with_tax, currency, order_date, required_date, promised_date, status, payment_terms,
                payment_status, paid_amount, delivery_address, received_amount, contract_no, remark,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, 'MATERIAL', ?, ?, ?, ?, ?, 'CNY', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_no,
                supplier["id"],
                project["id"],
                f"{project['code']}配套采购订单",
                order_total,
                tax_rate,
                tax_amount,
                round(order_total + tax_amount, 2),
                dstr(order_day),
                dstr(required_day),
                dstr(promised_day),
                status,
                "30天月结",
                "PAID" if status == "RECEIVED" else "PARTIAL",
                round(order_total * rng.uniform(0.2, 0.9), 2),
                "深圳宝安智能制造基地收货",
                round(order_total * rng.uniform(0.1, 0.8), 2),
                project["code"],
                "演示采购订单",
                managers[idx % len(managers)],
                ts(datetime.combine(order_day, datetime.min.time())),
                ts(datetime.combine(order_day, datetime.min.time())),
            ),
        )
        order_id = cur.lastrowid
        purchase_orders.append({"id": order_id, "order_no": order_no, "project_id": project["id"]})

        for item_no in range(1, 4):
            material = materials[(idx * 3 + item_no) % len(materials)]
            qty = round(rng.uniform(1.0, 12.0), 2)
            unit_price = round(material["price"] * rng.uniform(0.9, 1.15), 2)
            amount = round(qty * unit_price, 2)
            item_tax = round(amount * tax_rate / 100, 2)
            cur.execute(
                """
                INSERT INTO purchase_order_items (
                    order_id, item_no, material_id, material_code, material_name, specification, unit,
                    quantity, unit_price, amount, tax_rate, tax_amount, amount_with_tax,
                    required_date, promised_date, received_qty, qualified_qty, rejected_qty, status,
                    remark, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item_no,
                    material["id"],
                    f"{PREFIX}-MAT-{material['id']:03d}",
                    material["name"],
                    "标准件/定制件组合",
                    material["unit"],
                    qty,
                    unit_price,
                    amount,
                    tax_rate,
                    item_tax,
                    round(amount + item_tax, 2),
                    dstr(required_day),
                    dstr(promised_day),
                    round(qty * rng.uniform(0.2, 0.95), 2),
                    round(qty * rng.uniform(0.15, 0.90), 2),
                    round(qty * rng.uniform(0.0, 0.05), 2),
                    "RECEIVED" if status == "RECEIVED" else "PENDING",
                    "演示采购明细",
                    ts(datetime.combine(order_day, datetime.min.time())),
                    ts(datetime.combine(order_day, datetime.min.time())),
                ),
            )
            item_count += 1

    conn.commit()
    return {
        "vendors": vendors,
        "materials": materials,
        "purchase_orders": purchase_orders,
        "purchase_items": item_count,
    }


def seed_production(
    conn: sqlite3.Connection,
    projects: list[dict],
    sales_ctx: dict,
    rng: random.Random,
) -> dict:
    cur = conn.cursor()
    workshop_rows = cur.execute("SELECT id FROM workshop ORDER BY id").fetchall()
    workshop_ids = [row["id"] for row in workshop_rows] if workshop_rows else [None]
    production_plans = []

    for idx, project in enumerate(projects):
        plan_no = f"{PREFIX}-PP-{idx + 1:04d}"
        if project["progress"] <= 25:
            status = "PLANNED"
        elif project["progress"] <= 85:
            status = "IN_PROGRESS"
        else:
            status = "COMPLETED"
        plan_start = project["start"] - timedelta(days=5)
        plan_end = project["end"] - timedelta(days=15)
        cur.execute(
            """
            INSERT INTO production_plan (
                plan_no, plan_name, plan_type, project_id, workshop_id, plan_start_date, plan_end_date,
                status, progress, description, created_by, remark, created_at, updated_at
            ) VALUES (?, ?, 'STANDARD', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_no,
                f"{project['code']}生产计划",
                project["id"],
                workshop_ids[idx % len(workshop_ids)],
                dstr(plan_start),
                dstr(plan_end),
                status,
                min(100, max(0, int(project["progress"]))),
                f"{project['product']}整机装配与联调",
                project["pm_id"],
                "演示生产计划",
                ts(datetime.combine(plan_start, datetime.min.time())),
                ts(datetime.combine(plan_start, datetime.min.time())),
            ),
        )
        production_plans.append(
            {
                "id": cur.lastrowid,
                "project_id": project["id"],
                "workshop_id": workshop_ids[idx % len(workshop_ids)],
                "start": plan_start,
                "end": plan_end,
                "owner_id": project["pm_id"],
            }
        )

    work_orders = []
    task_pool = ["机械装配", "电气布线", "软件烧录", "ICT标定", "FCT联调", "EOL验证", "老化测试", "视觉检测调优"]
    for idx in range(COUNTS["work_orders"]):
        plan = production_plans[idx % len(production_plans)]
        wo_no = f"{PREFIX}-WO-{idx + 1:04d}"
        progress = rng.randint(8, 100)
        if progress >= 95:
            status = "COMPLETED"
        elif progress >= 40:
            status = "IN_PROGRESS"
        else:
            status = "PLANNED"
        plan_start = plan["start"] + timedelta(days=rng.randint(0, 35))
        plan_end = plan_start + timedelta(days=rng.randint(8, 26))
        std_hours = round(rng.uniform(16, 120), 2)
        actual_hours = round(std_hours * rng.uniform(0.9, 1.25), 2) if status != "PLANNED" else 0

        cur.execute(
            """
            INSERT INTO work_order (
                work_order_no, task_name, task_type, project_id, production_plan_id, workshop_id,
                plan_qty, completed_qty, qualified_qty, defect_qty, standard_hours, actual_hours,
                plan_start_date, plan_end_date, assigned_to, assigned_by, status, priority, progress,
                work_content, remark, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wo_no,
                task_pool[idx % len(task_pool)],
                rng.choice(["ASSEMBLY", "TEST", "DEBUG", "PACKING"]),
                plan["project_id"],
                plan["id"],
                plan["workshop_id"],
                rng.randint(1, 6),
                rng.randint(0, 5),
                rng.randint(0, 5),
                rng.randint(0, 1),
                std_hours,
                actual_hours,
                dstr(plan_start),
                dstr(plan_end),
                plan["owner_id"],
                plan["owner_id"],
                status,
                "HIGH" if idx % 5 == 0 else "NORMAL",
                progress,
                "按WBS执行装配/调试/验证",
                "演示生产工单",
                plan["owner_id"],
                ts(datetime.combine(plan_start, datetime.min.time())),
                ts(datetime.combine(plan_start, datetime.min.time())),
            ),
        )
        work_orders.append(cur.lastrowid)

    conn.commit()
    return {"production_plans": production_plans, "work_orders": work_orders}


def seed_after_sales(
    conn: sqlite3.Connection,
    projects: list[dict],
    sales_ctx: dict,
    rng: random.Random,
) -> dict:
    cur = conn.cursor()
    issues = [
        "测试治具定位重复精度偏差",
        "EOL高压测试偶发报警",
        "条码追溯上传延迟",
        "视觉检测误判率偏高",
        "老化柜温控波动超限",
        "烧录失败率异常升高",
        "FCT通讯中断告警",
        "ICT测试点接触不稳定",
    ]

    tickets = []
    for idx in range(COUNTS["service_tickets"]):
        project = projects[idx % len(projects)]
        ticket_no = f"{PREFIX}-ST-{idx + 1:04d}"
        reported = project["start"] + timedelta(days=rng.randint(35, 220))
        status = rng.choices(
            ["CLOSED", "IN_PROGRESS", "PENDING"],
            weights=[0.42, 0.36, 0.22],
            k=1,
        )[0]
        assigned_to = sales_ctx["frontline_user_ids"][idx % len(sales_ctx["frontline_user_ids"])]
        resolved = reported + timedelta(days=rng.randint(1, 10)) if status == "CLOSED" else None

        cur.execute(
            """
            INSERT INTO service_tickets (
                ticket_no, project_id, customer_id, problem_type, problem_desc, urgency, priority,
                ticket_type, reported_by, reported_time, assigned_to_id, assigned_to_name, assigned_time,
                status, response_time, resolved_time, solution, root_cause, preventive_action, satisfaction,
                feedback, timeline, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'AFTER_SALES', ?, ?, ?, (SELECT real_name FROM users WHERE id=?), ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_no,
                project["id"],
                project["customer_id"],
                rng.choice(["HARDWARE", "SOFTWARE", "PROCESS", "NETWORK"]),
                issues[idx % len(issues)],
                rng.choice(["LOW", "MEDIUM", "HIGH", "URGENT"]),
                rng.choice(["P3", "P2", "P1"]),
                f"客户运维{(idx % 5) + 1}",
                ts(datetime.combine(reported, datetime.min.time())),
                assigned_to,
                assigned_to,
                ts(datetime.combine(reported + timedelta(hours=2), datetime.min.time())),
                status,
                ts(datetime.combine(reported + timedelta(hours=4), datetime.min.time())),
                ts(datetime.combine(resolved, datetime.min.time())) if resolved else None,
                "调整工艺参数并升级控制程序",
                "现场工况波动+参数阈值偏保守",
                "新增启动前自检与预警阈值联动",
                rng.randint(3, 5) if status == "CLOSED" else None,
                "响应及时，问题定位清晰" if status == "CLOSED" else "待问题彻底解决",
                json.dumps(
                    [
                        {"time": ts(datetime.combine(reported, datetime.min.time())), "event": "客户报修"},
                        {"time": ts(datetime.combine(reported + timedelta(hours=2), datetime.min.time())), "event": "工程师受理"},
                    ],
                    ensure_ascii=False,
                ),
                ts(datetime.combine(reported, datetime.min.time())),
                ts(datetime.combine(reported, datetime.min.time())),
            ),
        )
        tickets.append(cur.lastrowid)

    satisfaction_rows = 0
    for idx, project in enumerate(projects[:20]):
        survey_day = min(project["end"], BASE_DATE)
        score = round(rng.uniform(4.0, 4.9), 1)
        cur.execute(
            """
            INSERT INTO customer_satisfactions (
                survey_no, survey_type, customer_name, customer_contact, customer_phone,
                project_code, project_name, survey_date, send_date, send_method, deadline, status,
                response_date, overall_score, scores, feedback, suggestions, created_by,
                created_by_name, created_at, updated_at
            ) VALUES (?, 'PROJECT', (SELECT customer_name FROM customers WHERE id=?), ?, ?,
                      ?, (SELECT project_name FROM projects WHERE id=?), ?, ?, 'EMAIL', ?, 'COMPLETED',
                      ?, ?, ?, ?, ?, ?, (SELECT real_name FROM users WHERE id=?), ?, ?)
            """,
            (
                f"{PREFIX}-CS-{idx + 1:04d}",
                project["customer_id"],
                f"运维负责人{idx + 1:02d}",
                f"136{idx + 40000000:08d}",
                project["code"],
                project["id"],
                dstr(survey_day),
                dstr(survey_day),
                dstr(survey_day + timedelta(days=10)),
                dstr(survey_day + timedelta(days=2)),
                score,
                json.dumps(
                    {"响应速度": score, "方案有效性": round(score - 0.1, 1), "交付质量": round(score - 0.2, 1)},
                    ensure_ascii=False,
                ),
                "设备稳定，售后响应快，问题闭环及时。",
                "建议增加线上诊断看板并开放更多日志权限。",
                sales_ctx["gm_user_id"],
                sales_ctx["gm_user_id"],
                ts(datetime.combine(survey_day, datetime.min.time())),
                ts(datetime.combine(survey_day, datetime.min.time())),
            ),
        )
        satisfaction_rows += 1

    conn.commit()
    return {"service_tickets": tickets, "satisfaction": satisfaction_rows}


def seed_targets_and_snapshots(
    conn: sqlite3.Connection,
    sales_ctx: dict,
    leads: list[dict],
    opportunities: list[dict],
    contracts: list[dict],
) -> None:
    cur = conn.cursor()
    created_at = ts()

    team_ids = {item["group"]: item["team_id"] for item in sales_ctx["teams"]}
    user_to_group = sales_ctx["user_to_group"]
    team_amount = defaultdict(float)
    team_leads = defaultdict(int)
    team_opps = defaultdict(int)
    team_contracts = defaultdict(int)
    user_amount = defaultdict(float)
    user_leads = defaultdict(int)
    user_opps = defaultdict(int)
    user_contracts = defaultdict(int)

    for lead in leads:
        group = user_to_group.get(lead["owner_id"])
        if group:
            team_leads[group] += 1
            user_leads[lead["owner_id"]] += 1

    for opp in opportunities:
        group = user_to_group.get(opp["owner_id"])
        if group:
            team_opps[group] += 1
            user_opps[opp["owner_id"]] += 1

    for contract in contracts:
        group = user_to_group.get(contract["owner_id"])
        if group:
            team_contracts[group] += 1
            team_amount[group] += contract["amount"]
            user_contracts[contract["owner_id"]] += 1
            user_amount[contract["owner_id"]] += contract["amount"]

    company_actual = float(sum(contract["amount"] for contract in contracts))
    company_target = float(TARGET_SALES_AMOUNT)
    company_completion = round(company_actual * 100 / company_target, 2)
    description = f"[{PREFIX}] 非标自动化测试设备销售目标（2026Q1）"

    cur.execute(
        """
        INSERT INTO sales_targets_v2 (
            target_period, target_year, target_quarter, target_type, team_id, user_id,
            sales_target, payment_target, new_customer_target, lead_target, opportunity_target, deal_target,
            actual_sales, actual_payment, actual_new_customers, actual_leads, actual_opportunities, actual_deals,
            completion_rate, description, created_by, created_at, updated_at
        ) VALUES ('2026Q1', 2026, 1, 'company', NULL, NULL, ?, ?, 12, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_target,
            round(company_target * 0.82, 2),
            COUNTS["leads"],
            COUNTS["opportunities"],
            COUNTS["contracts"],
            company_actual,
            round(company_actual * 0.78, 2),
            10,
            COUNTS["leads"],
            COUNTS["opportunities"],
            COUNTS["contracts"],
            company_completion,
            description,
            sales_ctx["gm_user_id"],
            created_at,
            created_at,
        ),
    )

    for group in GROUPS:
        code = group["code"]
        team_id = team_ids[code]
        actual_sales = round(team_amount[code], 2)
        target_sales = round(max(actual_sales * 1.08, 38_000_000), 2)
        completion = round(actual_sales * 100 / target_sales, 2) if target_sales else 0
        cur.execute(
            """
            INSERT INTO sales_targets_v2 (
                target_period, target_year, target_quarter, target_type, team_id, user_id,
                sales_target, payment_target, new_customer_target, lead_target, opportunity_target, deal_target,
                actual_sales, actual_payment, actual_new_customers, actual_leads, actual_opportunities, actual_deals,
                completion_rate, description, created_by, created_at, updated_at
            ) VALUES ('2026Q1', 2026, 1, 'team', ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team_id,
                target_sales,
                round(target_sales * 0.8, 2),
                3,
                max(20, team_leads[code]),
                max(10, team_opps[code]),
                max(5, team_contracts[code]),
                actual_sales,
                round(actual_sales * 0.75, 2),
                2,
                team_leads[code],
                team_opps[code],
                team_contracts[code],
                completion,
                f"[{PREFIX}] {group['name']}销售目标",
                sales_ctx["gm_user_id"],
                created_at,
                created_at,
            ),
        )

        member_count = sum(1 for u in sales_ctx["users"] if u["group"] == code)
        cur.execute(
            """
            INSERT INTO team_performance_snapshots (
                team_id, period_type, period_value, snapshot_date, lead_count, opportunity_count,
                opportunity_amount, contract_count, contract_amount, collection_amount, target_amount,
                completion_rate, rank_in_department, rank_overall, member_count, created_at, updated_at
            ) VALUES (?, 'QUARTER', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team_id,
                f"{PREFIX}-2026Q1",
                created_at,
                team_leads[code],
                team_opps[code],
                round(team_amount[code] * 1.15, 2),
                team_contracts[code],
                round(team_amount[code], 2),
                round(team_amount[code] * 0.72, 2),
                target_sales,
                completion,
                1,
                1,
                member_count,
                created_at,
                created_at,
            ),
        )

    for user in sales_ctx["users"]:
        if user["kind"] not in {"manager", "engineer"}:
            continue
        actual_sales = round(user_amount[user["user_id"]], 2)
        target_sales = round(max(actual_sales * 1.1, 8_000_000), 2)
        completion = round(actual_sales * 100 / target_sales, 2) if target_sales else 0
        cur.execute(
            """
            INSERT INTO sales_targets_v2 (
                target_period, target_year, target_quarter, target_type, team_id, user_id,
                sales_target, payment_target, new_customer_target, lead_target, opportunity_target, deal_target,
                actual_sales, actual_payment, actual_new_customers, actual_leads, actual_opportunities, actual_deals,
                completion_rate, description, created_by, created_at, updated_at
            ) VALUES ('2026Q1', 2026, 1, 'personal', ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team_ids[user["group"]],
                user["user_id"],
                target_sales,
                round(target_sales * 0.75, 2),
                max(6, user_leads[user["user_id"]]),
                max(3, user_opps[user["user_id"]]),
                max(1, user_contracts[user["user_id"]]),
                actual_sales,
                round(actual_sales * 0.72, 2),
                min(2, user_contracts[user["user_id"]]),
                user_leads[user["user_id"]],
                user_opps[user["user_id"]],
                user_contracts[user["user_id"]],
                completion,
                f"[{PREFIX}] {user['name']}个人销售目标",
                sales_ctx["gm_user_id"],
                created_at,
                created_at,
            ),
        )

    conn.commit()


def fetch_count(cur: sqlite3.Cursor, table: str, code_field: str) -> int:
    return int(cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {code_field} LIKE ?", (f"{PREFIX}-%",)).fetchone()[0])


def validate_and_report(conn: sqlite3.Connection) -> tuple[bool, dict]:
    cur = conn.cursor()
    stats = {
        "sales_team_total": int(cur.execute("SELECT COUNT(*) FROM users WHERE username LIKE ?", (f"{PREFIX.lower()}_%",)).fetchone()[0]),
        "customers": fetch_count(cur, "customers", "customer_code"),
        "leads": fetch_count(cur, "leads", "lead_code"),
        "opportunities": fetch_count(cur, "opportunities", "opp_code"),
        "quotes": fetch_count(cur, "quotes", "quote_code"),
        "contracts": fetch_count(cur, "contracts", "contract_code"),
        "projects": fetch_count(cur, "projects", "project_code"),
        "purchase_orders": fetch_count(cur, "purchase_orders", "order_no"),
        "work_orders": fetch_count(cur, "work_order", "work_order_no"),
        "service_tickets": fetch_count(cur, "service_tickets", "ticket_no"),
        "project_milestones": int(
            cur.execute("SELECT COUNT(*) FROM project_milestones WHERE milestone_code LIKE ?", (f"{PREFIX}-%",)).fetchone()[0]
        ),
        "project_tasks": int(cur.execute("SELECT COUNT(*) FROM tasks WHERE task_code LIKE ?", (f"{PREFIX}-%",)).fetchone()[0]),
        "sales_target_actual": float(
            cur.execute(
                "SELECT COALESCE(actual_sales, 0) FROM sales_targets_v2 WHERE target_type='company' AND description LIKE ?",
                (f"[{PREFIX}]%",),
            ).fetchone()[0]
            or 0
        ),
        "sales_target_goal": float(
            cur.execute(
                "SELECT COALESCE(sales_target, 0) FROM sales_targets_v2 WHERE target_type='company' AND description LIKE ?",
                (f"[{PREFIX}]%",),
            ).fetchone()[0]
            or 0
        ),
    }

    lead_conversion = stats["contracts"] * 100 / stats["leads"] if stats["leads"] else 0
    win_rate = stats["contracts"] * 100 / stats["opportunities"] if stats["opportunities"] else 0
    project_margin_rows = cur.execute(
        "SELECT contract_amount, actual_cost FROM projects WHERE project_code LIKE ?",
        (f"{PREFIX}-%",),
    ).fetchall()
    margins = []
    for row in project_margin_rows:
        amount = float(row["contract_amount"] or 0)
        cost = float(row["actual_cost"] or 0)
        if amount > 0:
            margins.append((amount - cost) * 100 / amount)
    avg_margin = sum(margins) / len(margins) if margins else 0

    cycle_rows = cur.execute(
        "SELECT planned_start_date, planned_end_date FROM projects WHERE project_code LIKE ?",
        (f"{PREFIX}-%",),
    ).fetchall()
    cycles = []
    for row in cycle_rows:
        if not row["planned_start_date"] or not row["planned_end_date"]:
            continue
        start = datetime.strptime(row["planned_start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(row["planned_end_date"], "%Y-%m-%d").date()
        cycles.append((end - start).days / 30.0)
    min_cycle = min(cycles) if cycles else 0
    max_cycle = max(cycles) if cycles else 0

    validations = {
        "销售团队人数>=15": stats["sales_team_total"] >= 15,
        "销售总经理=1": int(
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE username LIKE ? AND position='销售总经理'",
                (f"{PREFIX.lower()}_%",),
            ).fetchone()[0]
        )
        == 1,
        "销售总监=4": int(
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE username LIKE ? AND position='销售总监'",
                (f"{PREFIX.lower()}_%",),
            ).fetchone()[0]
        )
        == 4,
        "销售经理=4": int(
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE username LIKE ? AND position='销售经理'",
                (f"{PREFIX.lower()}_%",),
            ).fetchone()[0]
        )
        == 4,
        "销售工程师=10": int(
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE username LIKE ? AND position='销售工程师'",
                (f"{PREFIX.lower()}_%",),
            ).fetchone()[0]
        )
        == 10,
        "客户数量30-50": 30 <= stats["customers"] <= 50,
        "线索数量100-150": 100 <= stats["leads"] <= 150,
        "商机数量50-80": 50 <= stats["opportunities"] <= 80,
        "报价数量30-50": 30 <= stats["quotes"] <= 50,
        "合同数量20-30": 20 <= stats["contracts"] <= 30,
        "项目数量15-25": 15 <= stats["projects"] <= 25,
        "采购订单50-100": 50 <= stats["purchase_orders"] <= 100,
        "生产工单30-60": 30 <= stats["work_orders"] <= 60,
        "售后工单20-40": 20 <= stats["service_tickets"] <= 40,
        "线索转化率20-30%": 20 <= lead_conversion <= 30,
        "赢单率40-50%": 40 <= win_rate <= 50,
        "项目毛利率35-55%": margins and min(margins) >= 35 and max(margins) <= 55,
        "项目周期3-12个月": cycles and min_cycle >= 3 and max_cycle <= 12,
    }

    metrics = {
        "lead_conversion": lead_conversion,
        "win_rate": win_rate,
        "avg_margin": avg_margin,
        "margin_min": min(margins) if margins else 0,
        "margin_max": max(margins) if margins else 0,
        "cycle_min": min_cycle,
        "cycle_max": max_cycle,
        "sales_target_completion": stats["sales_target_actual"] * 100 / stats["sales_target_goal"] if stats["sales_target_goal"] else 0,
    }
    return all(validations.values()), {"stats": stats, "validations": validations, "metrics": metrics}


def print_report(report: dict, success: bool) -> None:
    stats = report["stats"]
    metrics = report["metrics"]
    validations = report["validations"]

    print("\n" + "=" * 72)
    print("金凯博自动化测试 - 非标行业完整演示数据报告")
    print("=" * 72)
    print(f"数据库: {DB_PATH}")
    print(f"数据前缀: {PREFIX}")
    print("")
    print("一、数据规模")
    print(f"  销售团队: {stats['sales_team_total']} 人（1总经理 / 4总监 / 4经理 / 10工程师）")
    print(f"  客户: {stats['customers']} | 线索: {stats['leads']} | 商机: {stats['opportunities']}")
    print(f"  报价: {stats['quotes']} | 合同: {stats['contracts']} | 项目: {stats['projects']}")
    print(f"  采购订单: {stats['purchase_orders']} | 生产工单: {stats['work_orders']} | 售后工单: {stats['service_tickets']}")
    print(f"  里程碑: {stats['project_milestones']} | WBS任务: {stats['project_tasks']}")
    print("")
    print("二、关键业务指标")
    print(f"  年销售目标: ¥{stats['sales_target_goal']:,.0f}")
    print(f"  年销售实际: ¥{stats['sales_target_actual']:,.0f}")
    print(f"  目标达成率: {metrics['sales_target_completion']:.2f}%")
    print(f"  线索转化率(线索->合同): {metrics['lead_conversion']:.2f}%")
    print(f"  赢单率(商机->合同): {metrics['win_rate']:.2f}%")
    print(f"  项目毛利率区间: {metrics['margin_min']:.2f}% ~ {metrics['margin_max']:.2f}% (均值 {metrics['avg_margin']:.2f}%)")
    print(f"  项目周期区间: {metrics['cycle_min']:.2f} ~ {metrics['cycle_max']:.2f} 月")
    print("")
    print("三、校验结果")
    for item, ok in validations.items():
        print(f"  {'PASS' if ok else 'FAIL'} - {item}")

    print("")
    print("四、结论")
    print("  ✅ 数据生成成功，可用于前端联调与业务演示。" if success else "  ❌ 存在未通过校验项，请检查数据逻辑。")
    print("=" * 72)


def main() -> int:
    rng = random.Random(RNG_SEED)
    conn = connect_db()

    try:
        ensure_tables(conn)
        cleanup_old_data(conn)

        sales_ctx = seed_sales_team(conn)
        won_amounts = generate_won_amounts(rng, COUNTS["contracts"], TARGET_SALES_AMOUNT)

        customers = seed_customers(conn, sales_ctx, rng)
        leads_ctx = seed_leads_and_assessments(conn, sales_ctx, customers, won_amounts, rng)
        opportunities = seed_opportunities(conn, leads_ctx, sales_ctx, rng)
        quote_ctx = seed_quotes(conn, opportunities, rng)
        contracts = seed_contracts(conn, opportunities, quote_ctx, sales_ctx, rng)
        project_ctx = seed_projects(conn, contracts, sales_ctx, rng)
        seed_procurement(conn, project_ctx["projects"], sales_ctx, rng)
        seed_production(conn, project_ctx["projects"], sales_ctx, rng)
        seed_after_sales(conn, project_ctx["projects"], sales_ctx, rng)
        seed_targets_and_snapshots(conn, sales_ctx, leads_ctx["leads"], opportunities, contracts)

        success, report = validate_and_report(conn)
        print_report(report, success)
        return 0 if success else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
