#!/usr/bin/env python3
"""
最终聚合：5148 条采购明细 → standard_costs 标准成本库 + 报价区间更新。

按物料名归一化聚合，给 AI 查"这个件我们历史买多少钱"。
"""
import sqlite3
from statistics import median
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

def main():
    conn = sqlite3.connect(DB_PATH)

    # 清理旧的 PURCHASE_HISTORY 数据
    conn.execute("DELETE FROM standard_costs WHERE cost_source='PURCHASE_HISTORY'")
    print("已清理旧的采购聚合数据")

    # 查全部采购数据
    rows = conn.execute("""
        SELECT material_name, brand, unit_cost, lead_time_days, supplier_name, specification, unit
        FROM purchase_material_costs
        WHERE unit_cost IS NOT NULL AND unit_cost > 0
        AND material_name NOT LIKE '%_name_%' AND material_name NOT LIKE 'E2E%'
    """).fetchall()
    print(f"待聚合采购记录: {len(rows)} 条")

    # 按物料名归一化
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[r[0]].append(r)

    print(f"唯一物料数: {len(groups)}")

    today = date.today().isoformat()
    upserted = 0

    for name, items in groups.items():
        prices = [float(r[2]) for r in items]
        # 过滤极端异常值
        med = median(prices)
        clean = [p for p in prices if med / 10 <= p <= med * 10] or prices

        med_price = round(median(clean), 2)
        avg_price = round(sum(clean) / len(clean), 2)
        min_price = round(min(clean), 2)
        max_price = round(max(clean), 2)

        suppliers = list(set(r[4] for r in items if r[4]))[:3]
        lead_times = [r[3] for r in items if r[3]]
        brand = items[0][1] or ""
        spec = items[0][5] or ""
        unit = items[0][6] or "件"

        # 变异系数（价格波动度）
        if len(clean) > 1 and med > 0:
            from statistics import pstdev
            cv = round(pstdev(clean) / med * 100, 1)
        else:
            cv = 0.0

        cost_code = f"PC-{name[:18].replace(' ', '').replace('/', '').replace('*', '')}"

        source_desc = (
            f"采购历史聚合：样本{len(clean)}，中位{med_price}，"
            f"区间{min_price}~{max_price}，CV={cv}%，"
            f"供应商：{'、'.join(suppliers) or '未知'}"
        )

        existing = conn.execute(
            "SELECT id FROM standard_costs WHERE cost_code = ?", (cost_code,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE standard_costs SET cost_name=?, cost_category='PURCHASED', specification=?, "
                "unit=?, standard_cost=?, cost_source='PURCHASE_HISTORY', source_description=?, "
                "effective_date=?, is_active=1 WHERE cost_code=?",
                (name, spec, unit, med_price, source_desc, today, cost_code),
            )
        else:
            conn.execute(
                "INSERT INTO standard_costs (cost_code, cost_name, cost_category, specification, "
                "unit, standard_cost, currency, cost_source, source_description, effective_date, "
                "version, is_active, created_at, updated_at) "
                "VALUES (?,?, 'PURCHASED', ?, ?, ?, 'CNY', 'PURCHASE_HISTORY', ?, ?, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (cost_code, name, spec, unit, med_price, source_desc, today),
            )
        upserted += 1

    conn.commit()

    # 统计
    total_sc = conn.execute("SELECT COUNT(*) FROM standard_costs WHERE is_active=1").fetchone()[0]
    purchase_sc = conn.execute("SELECT COUNT(*) FROM standard_costs WHERE cost_source='PURCHASE_HISTORY'").fetchone()[0]
    quote_sc = conn.execute("SELECT COUNT(*) FROM standard_costs WHERE cost_source='HISTORICAL_QUOTE'").fetchone()[0]

    print(f"\n完成：聚合 {upserted} 个部件级标准成本")
    print(f"standard_costs 总计: {total_sc} 条")
    print(f"  - 采购历史聚合: {purchase_sc} 条")
    print(f"  - 报价历史聚合: {quote_sc} 条")

    # TOP 供应商
    print("\nTOP 10 供应商（按采购次数）:")
    for row in conn.execute("""
        SELECT supplier_name, COUNT(*) cnt, ROUND(AVG(unit_cost),0) avg_price
        FROM purchase_material_costs
        WHERE supplier_name IS NOT NULL AND supplier_name != ''
        AND material_name NOT LIKE '%_name_%' AND material_name NOT LIKE 'E2E%'
        GROUP BY supplier_name ORDER BY cnt DESC LIMIT 10
    """):
        print(f"  {row[0][:25]:<25} {row[1]:>5}次  均价¥{row[2]}")

    # 价格区间最大的物料（采购价格波动大的）
    print("\n采购价格波动最大的物料 TOP 5（CV > 50%）:")
    for row in conn.execute("""
        SELECT cost_name, standard_cost, source_description
        FROM standard_costs WHERE cost_source='PURCHASE_HISTORY'
        AND source_description LIKE '%CV=___%' OR source_description LIKE '%CV=____%'
        ORDER BY CAST(SUBSTR(source_description, INSTR(source_description, 'CV=')+3) AS REAL) DESC
        LIMIT 5
    """):
        print(f"  {row[0][:25]:<25} ¥{row[1]}")

    conn.close()


if __name__ == "__main__":
    main()
