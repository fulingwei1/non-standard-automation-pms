#!/usr/bin/env python3
"""
项目管理模块演示数据种子脚本
覆盖：任务依赖、延期原因、齐套率、工时记录

用法: python scripts/seed_project_management_demo.py
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta
from decimal import Decimal

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db"
)

NOW = datetime.now()
NOW_STR = NOW.strftime("%Y-%m-%d %H:%M:%S")

# 项目61-65的负责人映射（来自employees表）
ASSIGNEES = [
    (36, "邓思远", "动力电池销售组"),
    (37, "罗晨曦", "消费电子销售组"),
    (38, "纪铭哲", "新能源整车销售组"),
    (39, "段彦廷", "通信终端销售组"),
    (40, "韩明轩", "动力电池销售组"),
    (41, "方祺瑞", "动力电池销售组"),
    (42, "蒋志豪", "动力电池销售组"),
    (43, "徐云川", "消费电子销售组"),
    (44, "贺一凡", "消费电子销售组"),
    (45, "苗旭东", "消费电子销售组"),
]

# 延期原因分类
DELAY_REASONS = [
    "客户需求变更",
    "物料延迟到货",
    "设计问题返工",
    "外协加工延期",
    "技术方案调整",
    "人员资源不足",
    "测试问题整改",
    "客户现场配合",
]


def create_task_dependencies(cur):
    """为项目61和62创建任务依赖关系，形成阻塞链"""
    print("\n📎 创建任务依赖关系...")

    # 清除旧的依赖数据
    cur.execute("DELETE FROM task_dependencies WHERE project_id IN (61, 62)")

    dependencies = []

    # 项目61的任务依赖链: 4 -> 5 -> 6 -> 7 -> 8 -> 9
    # WBS顺序: 需求澄清 -> 详细设计 -> 装配配线 -> 软件联调 -> FAT验证 -> SAT终验
    for i in range(4, 9):
        dependencies.append({
            "task_id": i + 1,
            "depends_on_task_id": i,
            "dependency_type": "FS",  # Finish-to-Start
            "lag_days": 0,
            "project_id": 61,
        })

    # 项目62的任务依赖链: 10 -> 11 -> 12 -> 13 -> 14 -> 15
    for i in range(10, 15):
        dependencies.append({
            "task_id": i + 1,
            "depends_on_task_id": i,
            "dependency_type": "FS",
            "lag_days": 0,
            "project_id": 62,
        })

    # 添加一些跨项目依赖（共享资源导致的阻塞）
    # 项目61的软件联调依赖项目62的设计完成（共享工程师资源）
    dependencies.append({
        "task_id": 7,
        "depends_on_task_id": 11,
        "dependency_type": "SS",  # Start-to-Start
        "lag_days": 5,
        "project_id": 61,
    })

    for dep in dependencies:
        cur.execute("""
            INSERT INTO task_dependencies
            (task_id, depends_on_task_id, dependency_type, lag_days, project_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dep["task_id"],
            dep["depends_on_task_id"],
            dep["dependency_type"],
            dep["lag_days"],
            dep["project_id"],
            NOW_STR,
            NOW_STR,
        ))

    print(f"  ✅ 创建 {len(dependencies)} 条任务依赖")
    return len(dependencies)


def update_tasks_with_delays(cur):
    """更新任务的延期信息和负责人，用于测试延期原因报告"""
    print("\n⏰ 更新任务延期信息...")

    # 给项目61-65的部分任务添加延期信息
    delay_updates = [
        # (task_id, delay_days, reason, assignee_id)
        (8, 5, "客户需求变更", 38),
        (9, 3, "客户需求变更", 38),
        (12, 7, "物料延迟到货", 40),
        (13, 4, "物料延迟到货", 40),
        (14, 2, "设计问题返工", 40),

        # 项目63的任务
        (16, 6, "技术方案调整", 41),
        (17, 8, "外协加工延期", 41),
        (18, 3, "人员资源不足", 42),

        # 项目64的任务
        (22, 4, "客户需求变更", 43),
        (23, 5, "测试问题整改", 43),
        (24, 2, "客户现场配合", 44),

        # 项目65的任务
        (28, 10, "物料延迟到货", 45),
        (29, 6, "设计问题返工", 45),
        (30, 3, "技术方案调整", 36),
    ]

    updated = 0
    for task_id, delay_days, reason, assignee_id in delay_updates:
        # 检查任务是否存在
        cur.execute("SELECT id, plan_end FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row:
            original_end = row[1]
            if original_end:
                # 计算新的实际结束日期（比计划延期）
                new_end = (datetime.strptime(original_end, "%Y-%m-%d") + timedelta(days=delay_days)).strftime("%Y-%m-%d")
                cur.execute("""
                    UPDATE tasks
                    SET block_reason = ?,
                        owner_id = ?,
                        actual_end = ?
                    WHERE id = ?
                """, (reason, assignee_id, new_end, task_id))
                updated += 1

    print(f"  ✅ 更新 {updated} 条任务延期信息")
    return updated


def create_timesheet_records(cur):
    """创建工时记录，用于测试SyncStatus和工时成本联动"""
    print("\n📝 创建工时记录...")

    # 清除旧的工时数据（只清除演示数据）
    cur.execute("DELETE FROM timesheet WHERE timesheet_no LIKE 'TS-DEMO-%'")

    # 获取现有的最大ID
    cur.execute("SELECT MAX(id) FROM timesheet")
    max_id = cur.fetchone()[0] or 0

    timesheets = []
    timesheet_id = max_id + 1

    # 为每个项目创建工时记录
    projects = [
        (61, "DEMO26-PRJ-0001", "ICT测试自动化测试系统交付项目1"),
        (62, "DEMO26-PRJ-0002", "FCT测试自动化测试系统交付项目2"),
        (63, "DEMO26-PRJ-0003", "EOL测试自动化测试系统交付项目3"),
        (64, "DEMO26-PRJ-0004", "烧录设备自动化测试系统交付项目4"),
        (65, "DEMO26-PRJ-0005", "老化设备自动化测试系统交付项目5"),
    ]

    # 工时类型
    work_types = ["设计", "装配", "调试", "测试", "现场支持", "会议", "文档"]

    for proj_id, proj_code, proj_name in projects:
        # 每个项目随机3-5个工程师
        engineers = random.sample(ASSIGNEES, random.randint(3, 5))

        for emp_id, emp_name, dept_name in engineers:
            # 每人每周2-4条工时记录，覆盖最近30天
            for day_offset in range(30):
                if random.random() < 0.7:  # 70%的天数有工时
                    work_date = (NOW - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    hours = round(random.uniform(4, 10), 1)
                    work_type = random.choice(work_types)

                    # 状态分布：60%已审批，25%待审批，15%草稿
                    status_rand = random.random()
                    if status_rand < 0.60:
                        status = "APPROVED"
                    elif status_rand < 0.85:
                        status = "PENDING"
                    else:
                        status = "DRAFT"

                    timesheets.append({
                        "id": timesheet_id,
                        "timesheet_no": f"TS-DEMO-{timesheet_id:06d}",
                        "user_id": emp_id,
                        "user_name": emp_name,
                        "department_name": dept_name,
                        "project_id": proj_id,
                        "project_code": proj_code,
                        "project_name": proj_name,
                        "work_date": work_date,
                        "hours": hours,
                        "work_content": f"{work_type}工作",
                        "status": status,
                    })
                    timesheet_id += 1

    for ts in timesheets:
        cur.execute("""
            INSERT INTO timesheet
            (id, timesheet_no, user_id, user_name, department_name,
             project_id, project_code, project_name, work_date, hours,
             work_content, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts["id"],
            ts["timesheet_no"],
            ts["user_id"],
            ts["user_name"],
            ts["department_name"],
            ts["project_id"],
            ts["project_code"],
            ts["project_name"],
            ts["work_date"],
            ts["hours"],
            ts["work_content"],
            ts["status"],
            NOW_STR,
            NOW_STR,
        ))

    print(f"  ✅ 创建 {len(timesheets)} 条工时记录")

    # 统计同步状态
    pending_sync = len([t for t in timesheets if t["status"] in ("DRAFT", "PENDING")])
    print(f"  📊 待同步: {pending_sync} 条 | 已同步: {len(timesheets) - pending_sync} 条")

    return len(timesheets)


def create_bom_data(cur):
    """创建BOM数据，用于测试齐套率"""
    print("\n📦 创建BOM物料数据...")

    # 检查bom_headers表是否已有数据
    cur.execute("SELECT COUNT(*) FROM bom_headers WHERE bom_no LIKE 'BOM-DEMO-%'")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"  ℹ️ 已存在 {existing} 条BOM数据，跳过创建")
        return 0

    # 获取最大ID
    cur.execute("SELECT MAX(id) FROM bom_headers")
    max_bom_id = cur.fetchone()[0] or 0
    cur.execute("SELECT MAX(id) FROM bom_items")
    max_item_id = cur.fetchone()[0] or 0

    # 物料清单（非标设备行业典型物料）
    materials = [
        ("PLC控制器", "三菱FX5U-32MT", 8500, True),
        ("伺服电机", "松下A6 750W", 3200, True),
        ("触摸屏", "威纶MT8102iE", 2800, True),
        ("传感器", "基恩士LR-TB5000", 1200, False),
        ("气缸", "SMC CDU20-50D", 450, False),
        ("开关电源", "明纬LRS-350-24", 350, False),
        ("继电器", "欧姆龙MY2N-GS", 85, False),
        ("铝型材", "4040国标", 65, False),
        ("线缆", "RVVP 4x1.5", 12, False),
        ("端子排", "菲尼克斯UK5N", 28, False),
        ("工业相机", "海康MV-CA050-10GM", 4500, True),
        ("光源控制器", "OPT-DPA1024E", 1800, False),
        ("步进驱动器", "雷赛DM542", 680, False),
        ("测试治具", "定制针床", 15000, True),
        ("工控机", "研华IPC-610H", 7500, True),
    ]

    # 为每个项目创建BOM
    projects = [
        (61, "ICT测试系统"),
        (62, "FCT测试系统"),
        (63, "EOL测试系统"),
        (64, "烧录设备"),
        (65, "老化设备"),
    ]

    bom_id = max_bom_id + 1
    item_id = max_item_id + 1
    total_boms = 0
    total_items = 0

    for proj_id, proj_desc in projects:
        # 随机选择8-12种物料
        selected_materials = random.sample(materials, random.randint(8, 12))

        bom_no = f"BOM-DEMO-{proj_id:03d}"
        bom_name = f"{proj_desc}物料清单"

        # 计算齐套率（随机40%-95%）
        kit_rate_target = random.uniform(0.40, 0.95)

        cur.execute("""
            INSERT INTO bom_headers
            (id, bom_no, bom_name, project_id, version, is_latest, status,
             total_items, total_amount, created_at, updated_at)
            VALUES (?, ?, ?, ?, '1.0', 1, 'APPROVED', ?, 0, ?, ?)
        """, (
            bom_id,
            bom_no,
            bom_name,
            proj_id,
            len(selected_materials),
            NOW_STR,
            NOW_STR,
        ))

        total_amount = 0
        for idx, (name, spec, price, is_key) in enumerate(selected_materials, 1):
            quantity = random.randint(1, 10)
            amount = quantity * price
            total_amount += amount

            # 根据齐套率目标决定到货量
            if random.random() < kit_rate_target:
                received = quantity  # 已齐套
            else:
                received = random.randint(0, quantity - 1)  # 部分到货或未到货

            # 需求日期（项目开始后30-60天）
            required_days = random.randint(30, 60)
            required_date = (NOW + timedelta(days=required_days)).strftime("%Y-%m-%d")

            cur.execute("""
                INSERT INTO bom_items
                (id, bom_id, item_no, material_code, material_name, specification,
                 unit, quantity, unit_price, amount, received_qty, required_date,
                 is_key_item, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, '个', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                bom_id,
                idx,
                f"MAT-{proj_id:03d}-{idx:02d}",
                name,
                spec,
                quantity,
                price,
                amount,
                received,
                required_date,
                1 if is_key else 0,
                NOW_STR,
                NOW_STR,
            ))

            item_id += 1
            total_items += 1

        # 更新BOM总金额
        cur.execute("UPDATE bom_headers SET total_amount = ? WHERE id = ?", (total_amount, bom_id))

        bom_id += 1
        total_boms += 1

    print(f"  ✅ 创建 {total_boms} 个BOM，共 {total_items} 条物料明细")
    return total_boms


def create_milestone_data(cur):
    """创建里程碑数据，用于测试项目中心的里程碑Tab"""
    print("\n🎯 创建里程碑数据...")

    # 清除旧的演示里程碑数据
    cur.execute("DELETE FROM project_milestones WHERE milestone_name LIKE '%演示%' OR milestone_name LIKE '%Demo%'")

    # 获取最大ID
    cur.execute("SELECT MAX(id) FROM project_milestones")
    max_id = cur.fetchone()[0] or 0

    milestones = []
    milestone_id = max_id + 1

    # 里程碑类型和模板 (name, type, target_day_offset, is_key)
    milestone_templates = [
        ("需求确认", "PROJECT", 15, True),
        ("设计评审", "PROJECT", 30, True),
        ("采购完成", "PROCUREMENT", 45, False),
        ("装配完成", "PRODUCTION", 60, True),
        ("联调测试", "TEST", 75, False),
        ("FAT验收", "ACCEPTANCE", 85, True),
        ("发货", "DELIVERY", 90, False),
        ("SAT验收", "ACCEPTANCE", 100, True),
    ]

    # 阶段代码映射
    stage_mapping = {
        "需求确认": "S1",
        "设计评审": "S2",
        "采购完成": "S3",
        "装配完成": "S4",
        "联调测试": "S5",
        "FAT验收": "S6",
        "发货": "S7",
        "SAT验收": "S8",
    }

    projects = [
        (61, "DEMO26-PRJ-0001"),
        (62, "DEMO26-PRJ-0002"),
        (63, "DEMO26-PRJ-0003"),
        (64, "DEMO26-PRJ-0004"),
        (65, "DEMO26-PRJ-0005"),
    ]

    for proj_id, proj_code in projects:
        # 项目开始日期（假设30天前开始）
        project_start = NOW - timedelta(days=30)

        for idx, (name, m_type, target_day, is_key) in enumerate(milestone_templates, 1):
            planned_date = (project_start + timedelta(days=target_day)).strftime("%Y-%m-%d")
            milestone_code = f"MS-{proj_id}-{idx:02d}"
            stage_code = stage_mapping.get(name, "S1")

            # 根据计划日期和当前时间决定状态
            planned_dt = project_start + timedelta(days=target_day)

            if planned_dt < NOW - timedelta(days=5):
                # 已过期5天以上 - 80%已完成，20%逾期
                if random.random() < 0.8:
                    status = "COMPLETED"
                    actual_date = (planned_dt + timedelta(days=random.randint(-3, 2))).strftime("%Y-%m-%d")
                else:
                    status = "OVERDUE"
                    actual_date = None
            elif planned_dt < NOW:
                # 刚过期 - 50%已完成，30%进行中，20%逾期
                rand = random.random()
                if rand < 0.5:
                    status = "COMPLETED"
                    actual_date = planned_dt.strftime("%Y-%m-%d")
                elif rand < 0.8:
                    status = "IN_PROGRESS"
                    actual_date = None
                else:
                    status = "OVERDUE"
                    actual_date = None
            elif planned_dt < NOW + timedelta(days=15):
                # 即将到期 - 30%进行中，70%待开始
                status = "IN_PROGRESS" if random.random() < 0.3 else "PENDING"
                actual_date = None
            else:
                # 远期 - 待开始
                status = "PENDING"
                actual_date = None

            milestones.append({
                "id": milestone_id,
                "project_id": proj_id,
                "milestone_code": milestone_code,
                "milestone_name": f"{name}(演示)",
                "milestone_type": m_type,
                "planned_date": planned_date,
                "actual_date": actual_date,
                "reminder_days": 3,
                "status": status,
                "is_key": is_key,
                "stage_code": stage_code,
                "deliverables": f"{name}交付物",
                "remark": f"{proj_code} - {name}里程碑",
            })
            milestone_id += 1

    for m in milestones:
        cur.execute("""
            INSERT INTO project_milestones
            (id, project_id, milestone_code, milestone_name, milestone_type, planned_date,
             actual_date, reminder_days, status, is_key, stage_code, deliverables, remark,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m["id"],
            m["project_id"],
            m["milestone_code"],
            m["milestone_name"],
            m["milestone_type"],
            m["planned_date"],
            m["actual_date"],
            m["reminder_days"],
            m["status"],
            1 if m["is_key"] else 0,
            m["stage_code"],
            m["deliverables"],
            m["remark"],
            NOW_STR,
            NOW_STR,
        ))

    print(f"  ✅ 创建 {len(milestones)} 条里程碑数据")

    # 统计各状态数量
    status_counts = {}
    for m in milestones:
        status_counts[m["status"]] = status_counts.get(m["status"], 0) + 1
    print(f"  📊 状态分布: {status_counts}")

    return len(milestones)


def create_delay_summary(cur):
    """汇总延期数据，用于延期原因报告"""
    print("\n📊 生成延期原因统计...")

    # 统计各原因的延期任务数
    cur.execute("""
        SELECT block_reason, COUNT(*) as cnt,
               AVG(JULIANDAY(actual_end) - JULIANDAY(plan_end)) as avg_delay
        FROM tasks
        WHERE block_reason IS NOT NULL AND block_reason != ''
        GROUP BY block_reason
        ORDER BY cnt DESC
    """)

    print("  延期原因分布:")
    for row in cur.fetchall():
        reason, count, avg_delay = row
        avg_delay = avg_delay or 0
        print(f"    {reason}: {count}个任务, 平均延期{avg_delay:.1f}天")

    # 统计各负责人的延期任务数
    cur.execute("""
        SELECT e.name, COUNT(*) as cnt,
               AVG(JULIANDAY(t.actual_end) - JULIANDAY(t.plan_end)) as avg_delay
        FROM tasks t
        JOIN employees e ON t.owner_id = e.id
        WHERE t.block_reason IS NOT NULL AND t.block_reason != ''
        GROUP BY t.owner_id
        ORDER BY cnt DESC
    """)

    print("\n  负责人延期统计:")
    for row in cur.fetchall():
        name, count, avg_delay = row
        avg_delay = avg_delay or 0
        print(f"    {name}: {count}个延期任务, 平均延期{avg_delay:.1f}天")


def main():
    print("=" * 60)
    print("🚀 项目管理模块演示数据生成")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    try:
        # 1. 创建任务依赖关系
        dep_count = create_task_dependencies(cur)

        # 2. 更新任务延期信息
        delay_count = update_tasks_with_delays(cur)

        # 3. 创建工时记录
        ts_count = create_timesheet_records(cur)

        # 4. 创建BOM数据
        bom_count = create_bom_data(cur)

        # 5. 创建里程碑数据
        milestone_count = create_milestone_data(cur)

        # 6. 生成统计报告
        create_delay_summary(cur)

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ 演示数据生成完成！")
        print("=" * 60)
        print(f"  📎 任务依赖: {dep_count} 条")
        print(f"  ⏰ 延期任务: {delay_count} 条")
        print(f"  📝 工时记录: {ts_count} 条")
        print(f"  📦 BOM清单: {bom_count} 个")
        print(f"  🎯 里程碑: {milestone_count} 条")
        print()
        print("可测试功能:")
        print("  1. /board - 项目中心（卡片/看板/矩阵/列表/流水线/时间轴/分解树视图）")
        print("  2. /board + 选择项目 + 里程碑Tab - 项目里程碑管理")
        print("  3. /project-health-monitor - 项目健康监控（齐套率+健康度+毛利率）")
        print("  4. /time-cost-margin-flow - 工时成本毛利联动视图")
        print("  5. /gantt-resource - 甘特图阻塞高亮模式")

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
