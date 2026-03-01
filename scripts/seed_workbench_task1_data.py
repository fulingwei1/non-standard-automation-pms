#!/usr/bin/env python3
"""
任务 1/6：生成工作台演示数据

生成并写入以下数据：
1) task_unified：50 条（含管理员我的待办 10 条）
2) alert_records：30 条（作为工作台预警消息）

说明：
- 本脚本使用 alert_records 作为“alerts”数据源（项目中无独立 alerts 表）
- 数据时间分布在最近 1-30 天
- 支持重复执行，会先清理本脚本历史插入数据再重建
"""

from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

TASK_COUNT = 50
ALERT_COUNT = 30
ADMIN_TODO_COUNT = 10

TASK_CODE_PREFIX = "WB26T1-"
ALERT_NO_PREFIX = "WB26A1-"

RNG = random.Random(20260301)

TASK_SCENARIOS = [
    {
        "category": "合同审批",
        "title_tpl": "合同审批：{customer}{line}项目商务合同（{amount}万元）",
        "desc_tpl": "需审核付款节点、质保条款及违约责任；客户：{customer}，项目：{project}。",
    },
    {
        "category": "报价审批",
        "title_tpl": "报价审批：{customer}{line}测试线方案报价（版本{ver}）",
        "desc_tpl": "请确认毛利率、备件配置及交期承诺；报价编号：{quote_no}。",
    },
    {
        "category": "项目立项",
        "title_tpl": "项目立项：{customer}{line}自动化测试产线导入",
        "desc_tpl": "请审批立项申请，核对项目预算、资源计划及里程碑。",
    },
    {
        "category": "采购审批",
        "title_tpl": "采购审批：{material}批量采购申请（{qty}套）",
        "desc_tpl": "涉及关键长交期物料，请确认供应商资质、交付周期与付款条件。",
    },
    {
        "category": "费用报销",
        "title_tpl": "费用报销：{person}差旅报销单（{amount}元）",
        "desc_tpl": "报销类型：客户现场调试差旅；请核对发票合规与成本归集项目。",
    },
]

ALERT_SCENARIOS = [
    {
        "alert_type": "PROJECT_DELAY",
        "alert_type_cn": "项目延期",
        "title_tpl": "项目延期预警：{project}关键里程碑延后{days}天",
        "content_tpl": "受设计变更与现场资源冲突影响，预计总工期延后{days}天，需调整交付计划。",
        "threshold": "里程碑偏差>3天",
        "trigger_value_tpl": "{days}天",
    },
    {
        "alert_type": "MATERIAL_SHORTAGE",
        "alert_type_cn": "物料短缺",
        "title_tpl": "物料短缺预警：{material}库存仅剩{qty}套",
        "content_tpl": "关键物料{material}在途延迟，影响{project}装配排产，建议紧急替代或加急采购。",
        "threshold": "安全库存<10套",
        "trigger_value_tpl": "{qty}套",
    },
    {
        "alert_type": "CONTRACT_EXPIRY",
        "alert_type_cn": "合同到期",
        "title_tpl": "合同到期预警：{contract_no}将在{days}天后到期",
        "content_tpl": "合同{contract_no}即将到期，尚有验收/收款节点未关闭，需启动续签或补充协议评估。",
        "threshold": "到期前<=30天",
        "trigger_value_tpl": "{days}天",
    },
    {
        "alert_type": "PAYMENT_OVERDUE",
        "alert_type_cn": "收款逾期",
        "title_tpl": "收款逾期预警：{customer}应收款逾期{days}天",
        "content_tpl": "客户{customer}阶段款未按计划回款，影响项目现金流，请跟进财务与商务催收。",
        "threshold": "账期超期>7天",
        "trigger_value_tpl": "{days}天",
    },
]

CUSTOMERS = ["比亚迪", "宁德时代", "华为", "小米", "立讯精密", "富士康", "OPPO", "中创新航"]
LINES = ["电池包", "储能柜", "ICT", "FCT", "EOL", "视觉检测", "老化", "模组装配"]
MATERIALS = ["伺服电机", "PLC主控模块", "工业相机", "电磁阀", "工控机", "光电传感器", "丝杆模组"]
PEOPLE = ["李工", "张工", "王工", "陈工", "赵工", "周工", "刘工", "邓工"]


def now_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def date_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def fetch_users(cur: sqlite3.Cursor) -> dict[int, str]:
    rows = cur.execute(
        """
        SELECT id, COALESCE(real_name, username, '用户' || id)
        FROM users
        WHERE is_active = 1
        ORDER BY id
        """
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def fetch_projects(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    rows = cur.execute(
        """
        SELECT id, project_code, project_name
        FROM projects
        ORDER BY id
        LIMIT 120
        """
    ).fetchall()
    projects: list[dict[str, Any]] = []
    for row in rows:
        projects.append({"id": row[0], "project_code": row[1], "project_name": row[2]})
    return projects


def ensure_alert_rule(cur: sqlite3.Cursor) -> int:
    existing = cur.execute("SELECT id FROM alert_rules ORDER BY id LIMIT 1").fetchone()
    if existing:
        return int(existing[0])

    ts = now_str(datetime.now())
    cur.execute(
        """
        INSERT INTO alert_rules (
            rule_code, rule_name, rule_type, target_type, condition_type,
            condition_operator, threshold_value, alert_level, check_frequency,
            is_enabled, is_system, is_active, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "WB-RULE-001",
            "工作台演示预警规则",
            "WORKBENCH",
            "WORKBENCH",
            "THRESHOLD",
            ">=",
            "1",
            "MEDIUM",
            "DAILY",
            1,
            1,
            1,
            1,
            ts,
            ts,
        ),
    )
    return int(cur.lastrowid)


def cleanup_previous_data(cur: sqlite3.Cursor) -> None:
    cur.execute("DELETE FROM task_unified WHERE task_code LIKE ?", (f"{TASK_CODE_PREFIX}%",))
    cur.execute("DELETE FROM alert_records WHERE alert_no LIKE ?", (f"{ALERT_NO_PREFIX}%",))


def build_tasks(
    users: dict[int, str],
    projects: list[dict[str, Any]],
) -> list[tuple[Any, ...]]:
    now = datetime.now()
    assignee_pool = [uid for uid in users if uid != 1]
    if not assignee_pool:
        assignee_pool = [1]

    tasks: list[tuple[Any, ...]] = []
    for idx in range(TASK_COUNT):
        scenario = TASK_SCENARIOS[idx % len(TASK_SCENARIOS)]
        customer = CUSTOMERS[idx % len(CUSTOMERS)]
        line = LINES[idx % len(LINES)]
        project = projects[idx % len(projects)] if projects else {"id": None, "project_code": None, "project_name": f"{customer}{line}项目"}

        amount_wan = RNG.randint(80, 650)
        amount_yuan = RNG.randint(1200, 18000)
        qty = RNG.randint(8, 120)
        ver = f"V{RNG.randint(1, 3)}.{RNG.randint(0, 9)}"
        quote_no = f"QT{now.year}{idx + 101:04d}"
        person = PEOPLE[idx % len(PEOPLE)]

        title = scenario["title_tpl"].format(
            customer=customer,
            line=line,
            amount=amount_wan if scenario["category"] != "费用报销" else amount_yuan,
            qty=qty,
            ver=ver,
            quote_no=quote_no,
            person=person,
            material=MATERIALS[idx % len(MATERIALS)],
        )
        description = scenario["desc_tpl"].format(
            customer=customer,
            project=project["project_name"],
            amount=amount_wan,
            qty=qty,
            ver=ver,
            quote_no=quote_no,
            person=person,
            material=MATERIALS[idx % len(MATERIALS)],
        )

        status = RNG.choices(["PENDING", "IN_PROGRESS"], weights=[0.58, 0.42], k=1)[0]
        priority = RNG.choices(["HIGH", "MEDIUM", "LOW"], weights=[0.26, 0.52, 0.22], k=1)[0]

        days_ago = RNG.randint(1, 30)
        created_at_dt = now - timedelta(days=days_ago, hours=RNG.randint(0, 20), minutes=RNG.randint(0, 55))
        plan_start_dt = created_at_dt + timedelta(days=RNG.randint(0, 3))
        plan_end_dt = plan_start_dt + timedelta(days=RNG.randint(3, 15))
        deadline_dt = plan_end_dt + timedelta(hours=RNG.randint(9, 18))
        actual_start = date_str(plan_start_dt) if status == "IN_PROGRESS" else None
        progress = RNG.randint(28, 88) if status == "IN_PROGRESS" else RNG.randint(0, 22)
        estimated_hours = round(RNG.uniform(1.5, 16.0), 2)
        actual_hours = round(estimated_hours * RNG.uniform(0.2, 0.9), 2) if status == "IN_PROGRESS" else 0
        is_urgent = 1 if priority == "HIGH" and RNG.random() < 0.45 else 0

        if idx < ADMIN_TODO_COUNT:
            assignee_id = 1
        else:
            assignee_id = assignee_pool[(idx - ADMIN_TODO_COUNT) % len(assignee_pool)]
        assignee_name = users.get(assignee_id, f"用户{assignee_id}")

        task_code = f"{TASK_CODE_PREFIX}{idx + 1:04d}"
        tags = json.dumps(
            [
                "工作台演示",
                scenario["category"],
                f"优先级:{priority}",
                f"状态:{status}",
            ],
            ensure_ascii=False,
        )

        tasks.append(
            (
                task_code,
                title,
                description,
                "WORKFLOW",
                "WORKBENCH_DEMO",
                "TASK1",
                project["id"],
                project["project_code"],
                project["project_name"],
                assignee_id,
                assignee_name,
                1,
                users.get(1, "系统管理员"),
                date_str(plan_start_dt),
                date_str(plan_end_dt),
                actual_start,
                now_str(deadline_dt),
                estimated_hours,
                actual_hours,
                status,
                progress,
                1,
                priority,
                is_urgent,
                scenario["category"],
                tags,
                1,
                "PENDING_APPROVAL",
                1,
                1,
                now_str(created_at_dt),
                now_str(created_at_dt),
            )
        )
    return tasks


def build_alerts(
    rule_id: int,
    projects: list[dict[str, Any]],
) -> list[tuple[Any, ...]]:
    now = datetime.now()
    alerts: list[tuple[Any, ...]] = []

    for idx in range(ALERT_COUNT):
        scenario = ALERT_SCENARIOS[idx % len(ALERT_SCENARIOS)]
        customer = CUSTOMERS[idx % len(CUSTOMERS)]
        material = MATERIALS[idx % len(MATERIALS)]
        project = projects[idx % len(projects)] if projects else {"id": None, "project_code": None, "project_name": f"{customer}项目"}

        days = RNG.randint(2, 28)
        qty = RNG.randint(1, 9)
        contract_no = f"HT{now.year - 1}{idx + 31:04d}"

        alert_title = scenario["title_tpl"].format(
            project=project["project_name"],
            days=days,
            material=material,
            qty=qty,
            contract_no=contract_no,
            customer=customer,
        )
        alert_content = scenario["content_tpl"].format(
            project=project["project_name"],
            days=days,
            material=material,
            qty=qty,
            contract_no=contract_no,
            customer=customer,
        )
        trigger_value = scenario["trigger_value_tpl"].format(days=days, qty=qty)

        alert_level = RNG.choices(["HIGH", "MEDIUM", "LOW"], weights=[0.30, 0.46, 0.24], k=1)[0]
        days_ago = RNG.randint(1, 30)
        triggered_at_dt = now - timedelta(days=days_ago, hours=RNG.randint(0, 20), minutes=RNG.randint(0, 55))

        alert_data = json.dumps(
            {
                "source": "WORKBENCH_DEMO_TASK1",
                "alert_type_cn": scenario["alert_type_cn"],
                "customer": customer,
                "material": material,
                "impact": RNG.choice(["成本上升", "交付风险", "现金流压力", "客户满意度风险"]),
            },
            ensure_ascii=False,
        )

        alerts.append(
            (
                f"{ALERT_NO_PREFIX}{idx + 1:04d}",
                rule_id,
                scenario["alert_type"],
                project["id"] if project["id"] is not None else idx + 1,
                project["project_code"] if project["project_code"] else f"TGT{idx + 1:04d}",
                project["project_name"],
                project["id"],
                alert_level,
                alert_level,
                alert_title,
                alert_content,
                alert_data,
                now_str(triggered_at_dt),
                trigger_value,
                scenario["threshold"],
                "ACTIVE",
                1,
                now_str(triggered_at_dt),
                now_str(triggered_at_dt),
            )
        )
    return alerts


def insert_tasks(cur: sqlite3.Cursor, tasks: list[tuple[Any, ...]]) -> None:
    cur.executemany(
        """
        INSERT INTO task_unified (
            task_code, title, description, task_type, source_type, source_name,
            project_id, project_code, project_name, assignee_id, assignee_name,
            assigner_id, assigner_name, plan_start_date, plan_end_date, actual_start_date, deadline,
            estimated_hours, actual_hours, status, progress, is_active, priority, is_urgent,
            category, tags, approval_required, approval_status, created_by, updated_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tasks,
    )


def insert_alerts(cur: sqlite3.Cursor, alerts: list[tuple[Any, ...]]) -> None:
    cur.executemany(
        """
        INSERT INTO alert_records (
            alert_no, rule_id, target_type, target_id, target_no, target_name, project_id,
            alert_level, severity, alert_title, alert_content, alert_data, triggered_at,
            trigger_value, threshold_value, status, handler_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        alerts,
    )


def query_distribution(cur: sqlite3.Cursor, table: str, key: str, code_col: str, prefix: str) -> dict[str, int]:
    rows = cur.execute(
        f"""
        SELECT {key}, COUNT(*)
        FROM {table}
        WHERE {code_col} LIKE ?
        GROUP BY {key}
        """,
        (f"{prefix}%",),
    ).fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def print_report(cur: sqlite3.Cursor) -> None:
    inserted_task_count = int(
        cur.execute(
            "SELECT COUNT(*) FROM task_unified WHERE task_code LIKE ?",
            (f"{TASK_CODE_PREFIX}%",),
        ).fetchone()[0]
    )
    inserted_alert_count = int(
        cur.execute(
            "SELECT COUNT(*) FROM alert_records WHERE alert_no LIKE ?",
            (f"{ALERT_NO_PREFIX}%",),
        ).fetchone()[0]
    )
    admin_todos = int(
        cur.execute(
            """
            SELECT COUNT(*)
            FROM task_unified
            WHERE task_code LIKE ?
              AND assignee_id = 1
            """,
            (f"{TASK_CODE_PREFIX}%",),
        ).fetchone()[0]
    )

    task_status_dist = query_distribution(cur, "task_unified", "status", "task_code", TASK_CODE_PREFIX)
    task_priority_dist = query_distribution(cur, "task_unified", "priority", "task_code", TASK_CODE_PREFIX)
    task_category_dist = query_distribution(cur, "task_unified", "category", "task_code", TASK_CODE_PREFIX)
    alert_type_dist = query_distribution(cur, "alert_records", "target_type", "alert_no", ALERT_NO_PREFIX)
    alert_level_dist = query_distribution(cur, "alert_records", "alert_level", "alert_no", ALERT_NO_PREFIX)
    alert_status_dist = query_distribution(cur, "alert_records", "status", "alert_no", ALERT_NO_PREFIX)

    task_date_span = cur.execute(
        """
        SELECT MIN(date(created_at)), MAX(date(created_at))
        FROM task_unified
        WHERE task_code LIKE ?
        """,
        (f"{TASK_CODE_PREFIX}%",),
    ).fetchone()

    alert_date_span = cur.execute(
        """
        SELECT MIN(date(created_at)), MAX(date(created_at))
        FROM alert_records
        WHERE alert_no LIKE ?
        """,
        (f"{ALERT_NO_PREFIX}%",),
    ).fetchone()

    task_recent_range_ok = int(
        cur.execute(
            """
            SELECT COUNT(*)
            FROM task_unified
            WHERE task_code LIKE ?
              AND CAST(julianday(date('now')) - julianday(date(created_at)) AS INTEGER) BETWEEN 1 AND 30
            """,
            (f"{TASK_CODE_PREFIX}%",),
        ).fetchone()[0]
    )
    alert_recent_range_ok = int(
        cur.execute(
            """
            SELECT COUNT(*)
            FROM alert_records
            WHERE alert_no LIKE ?
              AND CAST(julianday(date('now')) - julianday(date(created_at)) AS INTEGER) BETWEEN 1 AND 30
            """,
            (f"{ALERT_NO_PREFIX}%",),
        ).fetchone()[0]
    )

    print("\n=== 插入记录数统计 ===")
    print(f"- 待办任务 (task_unified): {inserted_task_count}")
    print(f"- 预警消息 (alerts -> alert_records): {inserted_alert_count}")
    print(f"- 我的待办 (assignee_id=1): {admin_todos}")

    print("\n=== 数据验证报告 ===")
    checks = [
        ("待办任务数量=50", inserted_task_count == TASK_COUNT),
        ("预警消息数量=30", inserted_alert_count == ALERT_COUNT),
        ("我的待办数量=10", admin_todos == ADMIN_TODO_COUNT),
        ("任务状态仅包含 PENDING/IN_PROGRESS", set(task_status_dist) <= {"PENDING", "IN_PROGRESS"}),
        ("任务优先级仅包含 HIGH/MEDIUM/LOW", set(task_priority_dist) <= {"HIGH", "MEDIUM", "LOW"}),
        ("预警级别仅包含 HIGH/MEDIUM/LOW", set(alert_level_dist) <= {"HIGH", "MEDIUM", "LOW"}),
        ("预警状态仅包含 ACTIVE", set(alert_status_dist) == {"ACTIVE"}),
        ("任务时间分布在最近1-30天", task_recent_range_ok == inserted_task_count),
        ("预警时间分布在最近1-30天", alert_recent_range_ok == inserted_alert_count),
    ]
    for check_name, passed in checks:
        print(f"- [{'PASS' if passed else 'FAIL'}] {check_name}")

    print("\n任务分布：")
    print(f"- 分类分布: {dict(sorted(task_category_dist.items()))}")
    print(f"- 状态分布: {dict(sorted(task_status_dist.items()))}")
    print(f"- 优先级分布: {dict(sorted(task_priority_dist.items()))}")
    print(f"- 时间范围: {task_date_span[0]} ~ {task_date_span[1]}")

    print("\n预警分布：")
    print(f"- 类型分布: {dict(sorted(alert_type_dist.items()))}")
    print(f"- 级别分布: {dict(sorted(alert_level_dist.items()))}")
    print(f"- 状态分布: {dict(sorted(alert_status_dist.items()))}")
    print(f"- 时间范围: {alert_date_span[0]} ~ {alert_date_span[1]}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库不存在: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        users = fetch_users(cur)
        if 1 not in users:
            raise RuntimeError("未找到管理员用户 user_id=1，无法生成“我的待办”数据。")

        projects = fetch_projects(cur)
        rule_id = ensure_alert_rule(cur)

        cleanup_previous_data(cur)

        tasks = build_tasks(users, projects)
        alerts = build_alerts(rule_id, projects)

        insert_tasks(cur, tasks)
        insert_alerts(cur, alerts)

        conn.commit()
        print_report(cur)


if __name__ == "__main__":
    main()
