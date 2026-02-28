#!/usr/bin/env python3
"""
种子数据：项目模板（ICT/FCT/EOL三种设备类型）
包含：项目模板 + WBS模板 + WBS任务 + 里程碑模板
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ============================================================================
# 项目模板定义
# ============================================================================
PROJECT_TEMPLATES = [
    {
        "id": 1,
        "template_code": "TPL-ICT",
        "template_name": "ICT在线测试设备项目模板",
        "description": "适用于ICT（In-Circuit Test）在线测试设备项目。包含标准9阶段WBS、里程碑和BOM框架。",
        "project_type": "standard",
        "product_category": "ICT",
        "industry": "electronics",
    },
    {
        "id": 2,
        "template_code": "TPL-FCT",
        "template_name": "FCT功能测试设备项目模板",
        "description": "适用于FCT（Functional Circuit Test）功能测试设备项目。重点在软件开发和测试程序编写。",
        "project_type": "standard",
        "product_category": "FCT",
        "industry": "electronics",
    },
    {
        "id": 3,
        "template_code": "TPL-EOL",
        "template_name": "EOL终检设备项目模板",
        "description": "适用于EOL（End of Line）终检设备项目。重点在多工位集成和产线对接。",
        "project_type": "standard",
        "product_category": "EOL",
        "industry": "automotive",
    },
]

# ============================================================================
# WBS 模板定义
# ============================================================================
WBS_TEMPLATES = [
    {"id": 1, "template_code": "WBS-ICT", "template_name": "ICT设备标准WBS", "project_type": "standard", "equipment_type": "ICT", "version_no": "1.0"},
    {"id": 2, "template_code": "WBS-FCT", "template_name": "FCT设备标准WBS", "project_type": "standard", "equipment_type": "FCT", "version_no": "1.0"},
    {"id": 3, "template_code": "WBS-EOL", "template_name": "EOL设备标准WBS", "project_type": "standard", "equipment_type": "EOL", "version_no": "1.0"},
]

# ============================================================================
# WBS 任务模板 (task_name, stage, default_owner_role, plan_days, weight)
# ============================================================================
COMMON_TASKS = [
    # S1 需求阶段
    ("需求评审与确认", "S1", "PM", 3, 3.0),
    ("技术可行性分析", "S1", "ME", 5, 4.0),
    ("项目计划编制", "S1", "PM", 3, 3.0),
    # S2 方案设计
    ("总体方案设计", "S2", "ME", 10, 8.0),
    ("电气原理图设计", "S2", "EE", 8, 6.0),
    ("软件架构设计", "S2", "SW", 5, 4.0),
    ("方案评审", "S2", "PM", 2, 3.0),
    # S3 采购备料
    ("BOM清单编制", "S3", "ME", 3, 3.0),
    ("长周期物料采购", "S3", "PURCHASE", 20, 5.0),
    ("标准件采购", "S3", "PURCHASE", 10, 3.0),
    ("外协加工件下单", "S3", "PURCHASE", 15, 4.0),
    # S4 加工制造
    ("结构件加工", "S4", "ME", 15, 6.0),
    ("电气柜布线", "S4", "EE", 10, 5.0),
    ("线束制作", "S4", "EE", 5, 3.0),
    # S5 装配调试
    ("机械装配", "S5", "ASSEMBLY", 10, 8.0),
    ("电气接线", "S5", "EE", 5, 5.0),
    ("单机调试", "S5", "SW", 8, 8.0),
    ("联调测试", "S5", "SW", 5, 6.0),
    # S6 FAT验收
    ("内部预验收", "S6", "PM", 2, 4.0),
    ("客户FAT验收", "S6", "PM", 3, 8.0),
    ("问题项整改", "S6", "ME", 5, 4.0),
    # S7 包装发运
    ("设备拆解包装", "S7", "ASSEMBLY", 3, 3.0),
    ("物流发运", "S7", "PM", 5, 2.0),
    # S8 SAT验收
    ("现场安装", "S8", "SERVICE", 5, 5.0),
    ("现场调试", "S8", "SW", 10, 8.0),
    ("客户SAT验收", "S8", "PM", 3, 8.0),
    # S9 质保
    ("质保期跟踪", "S9", "SERVICE", 90, 3.0),
    ("项目结项报告", "S9", "PM", 3, 2.0),
]

# ICT 特有任务
ICT_EXTRA_TASKS = [
    ("ICT测试治具设计", "S2", "ME", 8, 7.0),
    ("ICT测试程序开发", "S5", "SW", 10, 8.0),
    ("ICT针床制作", "S4", "ME", 10, 6.0),
    ("假板测试验证", "S5", "SW", 3, 5.0),
]

# FCT 特有任务
FCT_EXTRA_TASKS = [
    ("测试方案与用例设计", "S2", "SW", 8, 7.0),
    ("测试程序开发", "S5", "SW", 15, 10.0),
    ("自动化脚本编写", "S5", "SW", 8, 6.0),
    ("测试覆盖率验证", "S5", "SW", 3, 5.0),
]

# EOL 特有任务
EOL_EXTRA_TASKS = [
    ("产线工位规划", "S2", "ME", 5, 6.0),
    ("MES系统对接方案", "S2", "SW", 5, 5.0),
    ("多工位集成调试", "S5", "SW", 12, 9.0),
    ("产线节拍验证", "S6", "SW", 5, 7.0),
    ("MES数据联调", "S8", "SW", 5, 6.0),
]

TEMPLATE_TASKS = {
    1: COMMON_TASKS + ICT_EXTRA_TASKS,  # ICT
    2: COMMON_TASKS + FCT_EXTRA_TASKS,  # FCT
    3: COMMON_TASKS + EOL_EXTRA_TASKS,  # EOL
}

# ============================================================================
# 里程碑模板 (milestone_name, milestone_type, stage_code, is_key, offset_days)
# ============================================================================
COMMON_MILESTONES = [
    ("需求确认", "REVIEW", "S1", True, 0),
    ("方案评审通过", "REVIEW", "S2", True, 25),
    ("BOM发布", "DELIVERY", "S3", False, 30),
    ("关键物料到齐", "DELIVERY", "S3", True, 55),
    ("机械装配完成", "DELIVERY", "S4", False, 70),
    ("单机调试通过", "REVIEW", "S5", True, 90),
    ("FAT验收通过", "ACCEPTANCE", "S6", True, 100),
    ("设备发运", "DELIVERY", "S7", False, 110),
    ("SAT验收通过", "ACCEPTANCE", "S8", True, 130),
    ("项目结项", "REVIEW", "S9", True, 220),
]

ICT_MILESTONES = [
    ("ICT治具设计完成", "DELIVERY", "S2", False, 20),
    ("针床制作完成", "DELIVERY", "S4", True, 65),
    ("ICT程序调通", "REVIEW", "S5", True, 85),
]

FCT_MILESTONES = [
    ("测试用例评审", "REVIEW", "S2", False, 22),
    ("测试程序完成", "DELIVERY", "S5", True, 88),
    ("覆盖率达标", "REVIEW", "S5", False, 92),
]

EOL_MILESTONES = [
    ("工位规划评审", "REVIEW", "S2", False, 18),
    ("多工位联调通过", "REVIEW", "S5", True, 92),
    ("产线节拍达标", "ACCEPTANCE", "S6", True, 105),
    ("MES联调通过", "REVIEW", "S8", False, 125),
]

TEMPLATE_MILESTONES = {
    1: COMMON_MILESTONES + ICT_MILESTONES,
    2: COMMON_MILESTONES + FCT_MILESTONES,
    3: COMMON_MILESTONES + EOL_MILESTONES,
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear existing templates
    cur.execute("DELETE FROM wbs_template_tasks")
    cur.execute("DELETE FROM wbs_templates")
    cur.execute("DELETE FROM project_templates")
    print("✅ 清空旧模板数据")

    # Insert project templates
    for t in PROJECT_TEMPLATES:
        config = {
            "default_stages": ["S1","S2","S3","S4","S5","S6","S7","S8","S9"],
            "wbs_template_code": f"WBS-{t['product_category']}",
            "milestones": TEMPLATE_MILESTONES[t["id"]],
        }
        cur.execute("""
            INSERT INTO project_templates 
            (id, template_code, template_name, description, project_type, product_category, 
             industry, default_stage, default_status, default_health, template_config, 
             is_active, usage_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'S1', 'ST01', 'H1', ?, 1, 0, ?, ?)
        """, (t["id"], t["template_code"], t["template_name"], t["description"],
              t["project_type"], t["product_category"], t["industry"],
              json.dumps(config, ensure_ascii=False), NOW, NOW))
    print(f"✅ 插入 {len(PROJECT_TEMPLATES)} 个项目模板")

    # Insert WBS templates
    for w in WBS_TEMPLATES:
        cur.execute("""
            INSERT INTO wbs_templates 
            (id, template_code, template_name, project_type, equipment_type, version_no, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (w["id"], w["template_code"], w["template_name"], w["project_type"],
              w["equipment_type"], w["version_no"], NOW, NOW))
    print(f"✅ 插入 {len(WBS_TEMPLATES)} 个WBS模板")

    # Insert WBS template tasks
    task_id = 1
    total_tasks = 0
    for template_id, tasks in TEMPLATE_TASKS.items():
        for i, (name, stage, role, days, weight) in enumerate(tasks):
            cur.execute("""
                INSERT INTO wbs_template_tasks 
                (id, template_id, task_name, stage, default_owner_role, plan_days, weight, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, template_id, name, stage, role, days, weight, NOW, NOW))
            task_id += 1
            total_tasks += 1
    print(f"✅ 插入 {total_tasks} 个WBS模板任务")

    conn.commit()
    conn.close()

    print()
    print("📋 模板概览:")
    for t in PROJECT_TEMPLATES:
        tid = t["id"]
        tasks = TEMPLATE_TASKS[tid]
        milestones = TEMPLATE_MILESTONES[tid]
        print(f"  {t['template_code']}: {t['template_name']}")
        print(f"    - {len(tasks)} 个WBS任务, {len(milestones)} 个里程碑")
        print(f"    - 特有任务: {len(tasks) - len(COMMON_TASKS)} 个")


if __name__ == "__main__":
    main()
