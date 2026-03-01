#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知中心演示数据生成脚本

生成内容:
1) notifications: 50 条（SYSTEM/TASK/ALERT）
2) notification_settings: 5 条（用户通知偏好）
3) 已读记录: 35 条（通过 notifications.is_read/read_at 体现）

用法:
    python3 scripts/seed_notification_center_demo_data.py
    python3 scripts/seed_notification_center_demo_data.py --db-path data/app.db
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"
RNG_SEED = 20260301


SYSTEM_APPROVAL_CASES = [
    ("PR-202602-038", "采购申请", "华东产线治具备件", "182000"),
    ("PO-202602-117", "采购订单", "伺服驱动总成", "364500"),
    ("ECN-2026-019", "工程变更", "线束走向优化", "0"),
    ("CON-2026-008", "合同评审", "宁德二期EOL检测线", "5200000"),
    ("INV-202602-051", "发票审核", "预付款发票(50%)", "910000"),
    ("REQ-202602-212", "费用申请", "客户现场调试差旅", "16800"),
]

TASK_ASSIGNMENT_CASES = [
    ("PJ2025001", "比亚迪ICT在线测试设备", "BOM清单复核并冻结", "陈亮", "机械部"),
    ("PJ2025002", "宁德EOL检测系统", "PLC联调脚本更新", "谭章斌", "电气部"),
    ("PJ2025003", "华为5G老化系统", "温控回路稳定性测试", "王俊", "软件部"),
    ("PJ2025004", "立讯视觉检测项目", "相机标定参数回归", "于振华", "软件部"),
    ("PJ2026001", "小米FCT测试设备", "治具夹具装配验收", "高勇", "生产部"),
    ("PJ2026002", "赛力斯充放电测试台", "CAN报文解析联调", "赵敏", "研发部"),
    ("PJ2026003", "广汽埃安电池包检测线", "电气柜二次配线检查", "刘强", "电气部"),
]

ALERT_CASES = [
    ("PJ2025001", "关键里程碑延期", "总装联调节点预计延期2天"),
    ("PJ2025002", "采购交付风险", "伺服驱动供应商承诺交期延后48小时"),
    ("PJ2025003", "质量异常", "老化柜风扇震动值超过阈值8%"),
    ("PJ2025004", "成本预警", "本周实际成本较预算超出6.3%"),
    ("PJ2026001", "任务阻塞", "上位机驱动签名未通过导致联调暂停"),
    ("PJ2026002", "库存告急", "安全库存低于下限: 工控机I7平台仅剩2台"),
    ("PJ2026003", "进度偏差", "累计计划偏差达到-11.5%"),
    ("PJ2026004", "合规提醒", "现场施工安全培训到期需补签"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成通知中心演示数据")
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="SQLite 数据库路径，默认 data/app.db",
    )
    return parser.parse_args()


def _dt_str(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def ensure_tables(conn: sqlite3.Connection) -> None:
    required = {"notifications", "notification_settings", "users"}
    existing = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(f"数据库缺少必要表: {', '.join(missing)}")


def seed_notification_settings(conn: sqlite3.Connection, now: datetime) -> int:
    rows = [
        # 管理员：全渠道开启，接收全部类型
        (1, 1, 0, 1, 1, 1, 1, 1, 1, 1, "23:00", "07:00"),
        # 项目经理：短信关闭，保留站内+企业微信
        (2, 1, 0, 1, 1, 1, 1, 1, 0, 1, "22:30", "07:30"),
        # 销售代表：更关注审批/项目动态
        (3, 1, 0, 1, 1, 0, 1, 1, 0, 1, "23:30", "08:00"),
        # 工程师：任务/预警优先，邮件关闭
        (4, 0, 0, 1, 1, 1, 0, 1, 1, 0, "00:00", "07:00"),
        # 董事长：仅接收关键类通知
        (5, 1, 0, 1, 1, 0, 1, 1, 0, 1, "22:00", "06:30"),
    ]

    now_str = _dt_str(now)
    conn.executemany(
        """
        INSERT INTO notification_settings (
            user_id, email_enabled, sms_enabled, wechat_enabled, system_enabled,
            task_notifications, approval_notifications, alert_notifications,
            issue_notifications, project_notifications,
            quiet_hours_start, quiet_hours_end,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(*row, now_str, now_str) for row in rows],
    )
    return len(rows)


def _system_message(idx: int) -> tuple[str, str, str, int, str, str]:
    code, module_name, subject, amount = SYSTEM_APPROVAL_CASES[idx % len(SYSTEM_APPROVAL_CASES)]
    phase = idx % 3
    if phase == 0:
        title = f"审批通知：{module_name} {code} 已提交待处理"
        content = (
            f"{module_name}{code} 已由流程发起人提交，事项: {subject}，金额 {amount} 元。"
            "请在 4 小时内完成审批，避免影响本周排产。"
        )
        priority = "MEDIUM"
    elif phase == 1:
        title = f"审批通知：{module_name} {code} 已通过一级审批"
        content = (
            f"{module_name}{code} 一级审批已通过，事项: {subject}。"
            "当前已流转至财务复核节点，请关注付款计划与预算占用。"
        )
        priority = "LOW"
    else:
        title = f"审批通知：{module_name} {code} 退回补充材料"
        content = (
            f"{module_name}{code} 审批被退回，原因: 附件缺少供应商报价对比。"
            "请补充材料后重新提交，以免影响交付节奏。"
        )
        priority = "HIGH"

    return title, content, "approval", 7000 + idx, "/approvals/detail"


def _task_message(idx: int, due_date: datetime) -> tuple[str, str, str, int, str, str]:
    project_code, project_name, task_name, assignee, dept = TASK_ASSIGNMENT_CASES[idx % len(TASK_ASSIGNMENT_CASES)]
    title = f"任务分配：{project_code} - {task_name}"
    content = (
        f"{project_name} 已分配新任务「{task_name}」给 {dept} {assignee}，"
        f"计划截止时间 {due_date.strftime('%Y-%m-%d %H:%M')}。"
        "请确认资源冲突并在今日内反馈风险。"
    )
    source_id = 9000 + idx
    return title, content, "task", source_id, "/tasks/detail"


def _alert_message(idx: int) -> tuple[str, str, str, int, str, str]:
    project_code, risk_name, detail = ALERT_CASES[idx % len(ALERT_CASES)]
    title = f"预警提醒：{project_code} {risk_name}"
    content = (
        f"{project_code} 触发预警规则，{detail}。"
        "系统建议 24 小时内完成风险处置并更新纠偏计划。"
    )
    source_id = 11000 + idx
    return title, content, "alert", source_id, "/alerts/detail"


def seed_notifications(conn: sqlite3.Connection, now: datetime) -> int:
    rng = random.Random(RNG_SEED)

    type_list = ["SYSTEM"] * 18 + ["TASK"] * 20 + ["ALERT"] * 12
    rng.shuffle(type_list)

    priority_pool = {
        "SYSTEM": ["HIGH"] * 3 + ["MEDIUM"] * 7 + ["LOW"] * 8,
        "TASK": ["HIGH"] * 4 + ["MEDIUM"] * 12 + ["LOW"] * 4,
        "ALERT": ["HIGH"] * 8 + ["MEDIUM"] * 3 + ["LOW"] * 1,
    }
    for key in priority_pool:
        rng.shuffle(priority_pool[key])

    read_flags = [1] * 35 + [0] * 15
    rng.shuffle(read_flags)

    day_offsets = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6]
    records: list[tuple] = []

    system_idx = 0
    task_idx = 0
    alert_idx = 0

    for i, ntype in enumerate(type_list):
        created_at = now - timedelta(
            days=rng.choice(day_offsets),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        updated_at = created_at + timedelta(minutes=rng.randint(5, 40))
        if updated_at > now:
            updated_at = now

        if ntype == "SYSTEM":
            title, content, source_type, source_id, link_url = _system_message(system_idx)
            system_idx += 1
        elif ntype == "TASK":
            due_date = created_at + timedelta(days=rng.randint(1, 4), hours=rng.randint(1, 8))
            title, content, source_type, source_id, link_url = _task_message(task_idx, due_date)
            task_idx += 1
        else:
            title, content, source_type, source_id, link_url = _alert_message(alert_idx)
            alert_idx += 1

        priority = priority_pool[ntype].pop()
        is_read = read_flags[i]
        read_at = None
        if is_read:
            minutes_since_create = int((now - created_at).total_seconds() // 60)
            delay_max = max(5, min(960, minutes_since_create))
            delay_min = 3 if delay_max <= 5 else 5
            delay_minutes = rng.randint(delay_min, delay_max)
            read_at = created_at + timedelta(minutes=delay_minutes)
            if read_at > now:
                read_at = now - timedelta(minutes=1)

        link_params = json.dumps(
            {"source_type": source_type, "source_id": source_id, "from": "notification_center"},
            ensure_ascii=False,
        )
        extra_data = json.dumps(
            {
                "demo": True,
                "type": ntype,
                "priority": priority,
                "index": i + 1,
            },
            ensure_ascii=False,
        )

        records.append(
            (
                1,  # 所有通知投递给管理员，确保 user_id=1 可见全部演示通知
                ntype,
                source_type,
                source_id,
                title,
                content,
                link_url,
                link_params,
                is_read,
                _dt_str(read_at) if read_at else None,
                priority,
                extra_data,
                _dt_str(created_at),
                _dt_str(updated_at),
            )
        )

    conn.executemany(
        """
        INSERT INTO notifications (
            user_id, notification_type, source_type, source_id,
            title, content, link_url, link_params,
            is_read, read_at, priority, extra_data,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )
    return len(records)


def print_summary(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    read_count = conn.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 1").fetchone()[0]
    unread_count = conn.execute("SELECT COUNT(*) FROM notifications WHERE COALESCE(is_read, 0) = 0").fetchone()[0]
    type_rows = conn.execute(
        "SELECT notification_type, COUNT(*) FROM notifications GROUP BY notification_type ORDER BY notification_type"
    ).fetchall()
    settings_count = conn.execute("SELECT COUNT(*) FROM notification_settings").fetchone()[0]
    read_records = conn.execute("SELECT COUNT(*) FROM notifications WHERE read_at IS NOT NULL").fetchone()[0]

    print("通知中心演示数据生成完成")
    print(f"- 通知总数: {total}")
    print(f"- 已读/未读: {read_count}/{unread_count}")
    print("- 类型分布:")
    for notification_type, count in type_rows:
        print(f"  - {notification_type}: {count}")
    print(f"- 通知设置条数: {settings_count}")
    print(f"- 已读记录(read_at非空): {read_records}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path).expanduser().resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"数据库不存在: {db_path}")

    now = datetime.now().replace(microsecond=0)
    conn = sqlite3.connect(db_path)

    try:
        ensure_tables(conn)
        conn.execute("PRAGMA foreign_keys = ON")

        # 清理旧演示数据，保证结果可重复且满足目标比例
        conn.execute("DELETE FROM notifications")
        conn.execute("DELETE FROM notification_settings")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('notifications', 'notification_settings')"
        )

        seed_notification_settings(conn, now)
        seed_notifications(conn, now)
        conn.commit()
        print_summary(conn)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
