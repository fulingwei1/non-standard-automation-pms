#!/usr/bin/env python3
"""
种子数据：项目成员分配（含资源冲突）
给5个demo项目分配工程师，制造跨项目时间重叠冲突
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 项目ID -> 分配列表 [(user_id, role_code, allocation_pct, start_date, end_date)]
ALLOCATIONS = {
    # 比亚迪ICT在线测试 (2025-09-01 ~ 2026-03-01)
    1: [
        (10, "PM", 100, "2025-09-01", "2026-03-01"),      # 陈亮 - 项目经理
        (12, "ME", 80, "2025-09-15", "2026-01-15"),        # 于振华 - 机械设计 ⚡冲突
        (13, "EE", 60, "2025-10-01", "2026-02-01"),        # 王俊 - 电气设计 ⚡冲突
        (19, "SW", 50, "2025-11-01", "2026-02-15"),        # 周伟 - 软件 ⚡冲突
        (8, "ASSEMBLY", 80, "2025-12-01", "2026-02-01"),   # 常雄 - 装配
        (9, "TEST", 60, "2026-01-15", "2026-03-01"),       # 高勇 - 测试
    ],
    # 宁德时代EOL检测 (2025-10-15 ~ 2026-04-15)
    2: [
        (11, "PM", 100, "2025-10-15", "2026-04-15"),       # 谭章斌 - 项目经理
        (12, "ME", 60, "2025-10-15", "2026-01-30"),        # 于振华 - 机械 ⚡与项目1冲突!
        (13, "EE", 80, "2025-11-01", "2026-03-01"),        # 王俊 - 电气 ⚡与项目1冲突!
        (19, "SW", 60, "2025-12-01", "2026-03-15"),        # 周伟 - 软件 ⚡与项目1冲突!
        (9, "TEST", 80, "2026-02-01", "2026-04-15"),       # 高勇 - 测试 ⚡与项目1冲突!
        (17, "ASSEMBLY", 100, "2026-01-01", "2026-03-01"), # 刘强 - 装配
    ],
    # 华为5G老化测试 (2025-11-01 ~ 2026-02-28)
    3: [
        (10, "PM", 30, "2025-11-01", "2026-02-28"),        # 陈亮 - 兼任PM ⚡与项目1冲突!
        (12, "ME", 40, "2025-11-15", "2026-02-15"),        # 于振华 - ⚡三项目冲突!
        (17, "ASSEMBLY", 80, "2025-12-01", "2026-02-28"),  # 刘强 - ⚡与项目2冲突!
        (14, "SERVICE", 50, "2026-01-15", "2026-02-28"),   # 王志红 - 客服
    ],
    # 立讯连接器视觉检测 (2025-12-01 ~ 2026-06-01)
    4: [
        (11, "PM", 30, "2026-01-01", "2026-06-01"),        # 谭章斌 - 兼任 ⚡与项目2冲突!
        (19, "SW", 80, "2026-03-01", "2026-06-01"),        # 周伟 - 主力软件（3月后接棒）
        (13, "EE", 100, "2026-03-01", "2026-06-01"),       # 王俊 - 电气设计
        (9, "TEST", 60, "2026-04-01", "2026-06-01"),       # 高勇 - 测试
    ],
    # 小米手机FCT测试 (2026-02-01 ~ 2026-07-30)
    5: [
        (10, "PM", 100, "2026-03-15", "2026-07-30"),       # 陈亮 - 项目经理（项目1结束后）
        (12, "ME", 100, "2026-02-15", "2026-05-30"),       # 于振华 - ⚡与项目3冲突!
        (8, "ASSEMBLY", 100, "2026-04-01", "2026-07-01"),  # 常雄 - 装配
        (20, "SERVICE", 40, "2026-06-01", "2026-07-30"),   # 吴芳 - 客服
    ],
}


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear existing
    cur.execute("DELETE FROM project_members")
    print("✅ 清空 project_members")

    member_id = 1
    total = 0
    for project_id, members in ALLOCATIONS.items():
        for user_id, role_code, alloc_pct, start, end in members:
            cur.execute("""
                INSERT INTO project_members 
                (id, project_id, user_id, role_code, allocation_pct, start_date, end_date,
                 is_lead, is_active, reporting_to_pm, dept_manager_notified, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 0, ?, ?)
            """, (member_id, project_id, user_id, role_code, alloc_pct, start, end,
                  1 if role_code == "PM" else 0, NOW, NOW))
            member_id += 1
            total += 1

    conn.commit()
    conn.close()
    print(f"✅ 插入 {total} 条项目成员分配记录")
    print()
    print("⚡ 预设冲突:")
    print("  于振华(ME): 项目1+2+3 三重冲突 (11月-1月, 总分配180%)")
    print("  王俊(EE): 项目1+2 双重冲突 (11月-2月, 总分配140%)")
    print("  周伟(SW): 项目1+2 双重冲突 (12月-2月, 总分配110%)")
    print("  陈亮(PM): 项目1+3 双重冲突 (11月-2月, 总分配130%)")
    print("  高勇(TEST): 项目1+2 双重冲突 (2月, 总分配140%)")
    print("  刘强(装配): 项目2+3 双重冲突 (1月-2月, 总分配180%)")
    print("  谭章斌(PM): 项目2+4 双重冲突 (1月起, 总分配130%)")


if __name__ == "__main__":
    main()
