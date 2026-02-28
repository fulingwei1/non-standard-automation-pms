#!/usr/bin/env python3
"""
种子数据：项目成本明细（含分类成本，用于毛利率预测）
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 成本类型和典型占比（非标设备行业）
# cost_type: (min_pct, max_pct) of total cost
COST_BREAKDOWN = {
    "material": (0.40, 0.55),     # 材料成本 40-55%
    "labor": (0.20, 0.30),        # 人工成本 20-30%
    "equipment": (0.05, 0.10),    # 设备折旧 5-10%
    "outsource": (0.05, 0.15),    # 外协加工 5-15%
    "travel": (0.02, 0.05),       # 差旅费 2-5%
    "overhead": (0.05, 0.08),     # 管理费用 5-8%
}

# 人工子类
LABOR_SUBCATEGORIES = ["design", "assembly", "testing", "onsite"]  # 设计/装配/调试/现场

# 项目数据: (id, actual_cost, start_date)
PROJECTS = [
    (1, 1875000, "2025-09-01"),   # 比亚迪ICT
    (2, 2400000, "2025-10-15"),   # 宁德时代EOL
    (3, 2880000, "2025-11-01"),   # 华为老化
    (4, 980000, "2025-12-01"),    # 立讯视觉（进行中，成本低）
    (5, 160000, "2026-02-01"),    # 小米FCT（刚开始）
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM project_costs")
    print("✅ 清空 project_costs")

    cost_id = 1
    total_records = 0

    for proj_id, total_cost, start_str in PROJECTS:
        start = datetime.strptime(start_str, "%Y-%m-%d")

        # Distribute cost across types
        remaining = total_cost
        costs = {}
        for i, (ctype, (min_p, max_p)) in enumerate(COST_BREAKDOWN.items()):
            if i == len(COST_BREAKDOWN) - 1:
                costs[ctype] = remaining
            else:
                pct = random.uniform(min_p, max_p)
                amount = round(total_cost * pct, 2)
                costs[ctype] = amount
                remaining -= amount

        for ctype, amount in costs.items():
            if amount <= 0:
                continue

            # Split into multiple records over time
            if ctype == "labor":
                # Split labor into subcategories
                sub_total = amount
                for j, sub in enumerate(LABOR_SUBCATEGORIES):
                    if j == len(LABOR_SUBCATEGORIES) - 1:
                        sub_amount = sub_total
                    else:
                        sub_amount = round(amount * random.uniform(0.15, 0.35), 2)
                        sub_total -= sub_amount

                    days_offset = random.randint(30, 150)
                    cur.execute("""
                        INSERT INTO project_costs 
                        (id, project_id, cost_type, cost_category, amount, cost_date, 
                         description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cost_id, proj_id, "labor", sub,
                          sub_amount,
                          (start + timedelta(days=days_offset)).strftime("%Y-%m-%d"),
                          f"{sub}工时成本", NOW, NOW))
                    cost_id += 1
                    total_records += 1
            else:
                # Split into 2-4 records
                num_records = random.randint(2, 4)
                remaining_amount = amount
                for k in range(num_records):
                    if k == num_records - 1:
                        record_amount = remaining_amount
                    else:
                        record_amount = round(remaining_amount * random.uniform(0.2, 0.5), 2)
                        remaining_amount -= record_amount

                    days_offset = random.randint(10, 180)
                    cur.execute("""
                        INSERT INTO project_costs 
                        (id, project_id, cost_type, cost_category, amount, cost_date,
                         description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cost_id, proj_id, ctype, ctype,
                          record_amount,
                          (start + timedelta(days=days_offset)).strftime("%Y-%m-%d"),
                          f"{ctype}成本", NOW, NOW))
                    cost_id += 1
                    total_records += 1

    conn.commit()
    conn.close()
    print(f"✅ 插入 {total_records} 条成本明细记录")
    print()
    for pid, cost, _ in PROJECTS:
        print(f"  项目{pid}: 总成本 ¥{cost:,.0f}")


if __name__ == "__main__":
    main()
