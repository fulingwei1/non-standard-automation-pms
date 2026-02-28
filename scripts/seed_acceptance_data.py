#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户验收管理 (FAT/SAT) 种子数据脚本
创建 4-5 个验收记录，包含检查清单和问题
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_acceptance_data():
    """创建验收记录种子数据"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("开始创建验收管理种子数据...")

    # 种子数据：4-5 个验收记录
    acceptance_records = [
        {
            "project_id": 1,
            "acceptance_type": "FAT",
            "title": "ICT 测试系统 FAT 验收",
            "status": "signed",
            "scheduled_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "actual_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
            "location": "公司装配车间",
            "customer_representative": "张工",
            "our_representative": "李经理",
            "overall_result": "pass",
            "sign_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
            "sign_by": "张工",
            "notes": "所有测试项通过，客户满意",
        },
        {
            "project_id": 2,
            "acceptance_type": "SAT",
            "title": "FCT 产线 SAT 现场验收",
            "status": "in_progress",
            "scheduled_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "actual_date": None,
            "location": "客户工厂 - 苏州",
            "customer_representative": "王总",
            "our_representative": "陈工",
            "overall_result": None,
            "sign_date": None,
            "sign_by": None,
            "notes": "正在进行现场调试",
        },
        {
            "project_id": 3,
            "acceptance_type": "FAT",
            "title": "EOL 测试设备 FAT 验收",
            "status": "passed",
            "scheduled_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
            "actual_date": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
            "location": "公司测试中心",
            "customer_representative": "刘工",
            "our_representative": "赵经理",
            "overall_result": "pass",
            "sign_date": None,
            "sign_by": None,
            "notes": "等待正式签收",
        },
        {
            "project_id": 4,
            "acceptance_type": "SAT",
            "title": "自动化装配线 SAT 验收",
            "status": "failed",
            "scheduled_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "actual_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "location": "客户工厂 - 深圳",
            "customer_representative": "周总",
            "our_representative": "吴工",
            "overall_result": "fail",
            "sign_date": None,
            "sign_by": None,
            "notes": "发现 3 个关键问题，需整改后重新验收",
        },
        {
            "project_id": 5,
            "acceptance_type": "FAT",
            "title": "功能测试台 FAT 验收",
            "status": "draft",
            "scheduled_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "actual_date": None,
            "location": "公司装配车间",
            "customer_representative": "郑工",
            "our_representative": "孙经理",
            "overall_result": None,
            "sign_date": None,
            "sign_by": None,
            "notes": "准备中",
        },
    ]

    # 插入验收记录
    inserted_ids = []
    for idx, record in enumerate(acceptance_records):
        # 生成验收编号
        project_code = f"PRJ{record['project_id']:03d}"
        count_sql = """
            SELECT COUNT(*) as cnt FROM acceptance_records 
            WHERE project_id = ? AND acceptance_type = ?
        """
        cursor.execute(count_sql, (record["project_id"], record["acceptance_type"]))
        count = cursor.fetchone()["cnt"]
        acceptance_code = f"{project_code}-{record['acceptance_type']}-{str(count + 1).zfill(3)}"

        cursor.execute("""
            INSERT INTO acceptance_records (
                project_id, acceptance_type, acceptance_code, title, status,
                scheduled_date, actual_date, location, customer_representative,
                our_representative, overall_result, notes, sign_date, sign_by,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            record["project_id"],
            record["acceptance_type"],
            acceptance_code,
            record["title"],
            record["status"],
            record["scheduled_date"],
            record["actual_date"],
            record["location"],
            record["customer_representative"],
            record["our_representative"],
            record["overall_result"],
            record["notes"],
            record["sign_date"],
            record["sign_by"],
        ))
        inserted_ids.append(cursor.lastrowid)
        print(f"  ✓ 创建验收记录：{acceptance_code} - {record['title']}")

    conn.commit()

    # 检查清单模板
    checklist_templates = {
        "FAT": [
            (1, "functional", "设备开机自检", "正常启动，无报错", "pending"),
            (2, "functional", "通信接口测试", "所有通信接口正常", "pending"),
            (3, "performance", "连续运行测试", "连续运行 24 小时无故障", "pending"),
            (4, "performance", "精度测试", "测试精度达到规格要求", "pending"),
            (5, "safety", "急停功能", "急停按钮响应正常", "pending"),
            (6, "safety", "防护装置", "所有防护装置完好", "pending"),
            (7, "documentation", "操作手册", "提供完整操作手册", "pending"),
            (8, "documentation", "维护手册", "提供完整维护手册", "pending"),
        ],
        "SAT": [
            (1, "functional", "现场安装检查", "安装位置正确，固定牢靠", "pending"),
            (2, "functional", "接线检查", "所有接线正确，标识清晰", "pending"),
            (3, "performance", "空载运行", "空载运行正常", "pending"),
            (4, "performance", "负载测试", "带载运行达到规格", "pending"),
            (5, "performance", "节拍测试", "生产节拍满足要求", "pending"),
            (6, "safety", "接地检查", "接地电阻符合要求", "pending"),
            (7, "safety", "安全标识", "安全标识完整清晰", "pending"),
            (8, "documentation", "验收文档", "验收文档齐全", "pending"),
        ],
    }

    # 为每个验收记录添加检查清单
    for acceptance_id, record in zip(inserted_ids, acceptance_records):
        template = checklist_templates.get(record["acceptance_type"], checklist_templates["FAT"])
        
        # 根据状态设置不同的检查结果
        if record["status"] == "signed" or record["status"] == "passed":
            # 已通过的：大部分通过
            statuses = ["pass", "pass", "pass", "pass", "pass", "pass", "pass", "pass"]
        elif record["status"] == "failed":
            # 失败的：有失败项
            statuses = ["pass", "pass", "fail", "fail", "pass", "pass", "pass", "na"]
        elif record["status"] == "in_progress":
            # 进行中：部分完成
            statuses = ["pass", "pass", "pass", "pending", "pending", "pending", "pending", "pending"]
        else:
            # 草稿：全部待检
            statuses = ["pending"] * 8

        for i, (item_no, category, check_item, expected_result, default_status) in enumerate(template):
            status = statuses[i] if i < len(statuses) else default_status
            actual_result = "符合要求" if status == "pass" else ("不符合要求" if status == "fail" else None)
            checked_by = "李工" if status != "pending" else None

            cursor.execute("""
                INSERT INTO acceptance_checklist (
                    acceptance_id, item_no, category, check_item, expected_result,
                    actual_result, status, remarks, checked_by, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acceptance_id,
                item_no,
                category,
                check_item,
                expected_result,
                actual_result,
                status,
                None,
                checked_by,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S") if checked_by else None,
            ))

    conn.commit()
    print("  ✓ 创建检查清单项")

    # 问题数据
    issues_data = [
        # 记录 2 (SAT, in_progress) - 2 个问题
        {
            "acceptance_idx": 1,
            "issue_no": 1,
            "severity": "major",
            "description": "设备运行噪音偏大",
            "root_cause": "风机轴承需要润滑",
            "solution": "添加润滑油，调整风机转速",
            "status": "fixing",
            "responsible": "陈工",
            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "acceptance_idx": 1,
            "issue_no": 2,
            "severity": "minor",
            "description": "部分线缆标识脱落",
            "root_cause": "标签粘贴不牢",
            "solution": "重新粘贴标签，使用更强粘性标签",
            "status": "resolved",
            "responsible": "陈工",
            "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "resolved_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        # 记录 4 (SAT, failed) - 3 个关键问题
        {
            "acceptance_idx": 3,
            "issue_no": 1,
            "severity": "critical",
            "description": "安全光幕响应时间超标",
            "root_cause": "光幕控制器固件版本过旧",
            "solution": "升级光幕控制器固件到最新版本",
            "status": "open",
            "responsible": "吴工",
            "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        },
        {
            "acceptance_idx": 3,
            "issue_no": 2,
            "severity": "critical",
            "description": "急停回路存在延迟",
            "root_cause": "继电器触点老化",
            "solution": "更换所有急停回路继电器",
            "status": "open",
            "responsible": "吴工",
            "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        },
        {
            "acceptance_idx": 3,
            "issue_no": 3,
            "severity": "major",
            "description": "触摸屏偶尔无响应",
            "root_cause": "触摸屏驱动兼容性问题",
            "solution": "更新触摸屏驱动程序",
            "status": "fixing",
            "responsible": "吴工",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        },
    ]

    # 插入问题
    for issue in issues_data:
        acceptance_id = inserted_ids[issue["acceptance_idx"]]
        cursor.execute("""
            INSERT INTO acceptance_issues (
                acceptance_id, issue_no, severity, description, root_cause,
                solution, status, responsible, due_date, resolved_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            acceptance_id,
            issue["issue_no"],
            issue["severity"],
            issue["description"],
            issue["root_cause"],
            issue["solution"],
            issue["status"],
            issue["responsible"],
            issue["due_date"],
            issue.get("resolved_date"),
        ))

    conn.commit()
    print("  ✓ 创建问题记录")

    # 打印统计
    print("\n种子数据创建完成！")
    print(f"  - 验收记录：{len(inserted_ids)} 条")
    
    cursor.execute("SELECT COUNT(*) FROM acceptance_checklist")
    checklist_count = cursor.fetchone()[0]
    print(f"  - 检查清单项：{checklist_count} 条")
    
    cursor.execute("SELECT COUNT(*) FROM acceptance_issues")
    issues_count = cursor.fetchone()[0]
    print(f"  - 问题记录：{issues_count} 条")

    conn.close()

if __name__ == "__main__":
    seed_acceptance_data()
