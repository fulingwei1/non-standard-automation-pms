#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应商分析查询工具

从 purchase_material_costs 重建的供应商画像，提供 4 种查询：
  profile   - 供应商画像（采购规模/交期/活跃度/独占物料）
  risk      - 供应链风险（单源依赖/价格波动/交期风险）
  variance  - 物料价格波动（同物料多供应商价差）
  trend     - 物料价格趋势（同物料跨年变化）

依赖视图（已建）：
  - supplier_profile_view
  - material_price_variance_view
  - supply_chain_risk_view

运行：
    python scripts/supplier_analysis.py profile --top 10
    python scripts/supplier_analysis.py risk --level HIGH_RISK_SOLO
    python scripts/supplier_analysis.py variance --material IO模块
    python scripts/supplier_analysis.py trend --material 开关电源
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"


def cmd_profile(conn, args):
    """供应商画像"""
    sql = """
    SELECT supplier_name, item_count, unique_materials, total_purchase,
           avg_item_price, avg_leadtime_days, active_months, city,
           sole_source_materials, first_purchase, last_purchase
    FROM supplier_profile_view
    """
    params = []
    if args.supplier:
        sql += " WHERE supplier_name LIKE ?"
        params.append(f"%{args.supplier}%")
    sql += " ORDER BY total_purchase DESC"
    if args.top:
        sql += f" LIMIT {args.top}"

    rows = conn.execute(sql, params).fetchall()
    print(f"\n=== 供应商画像（top {len(rows)}） ===")
    print(f"{'供应商':<30} {'采购额':>12} {'物料数':>6} {'独占':>4} {'交期':>4} {'活跃月':>6} {'城市':>6}")
    print("-" * 90)
    for r in rows:
        print(f"{r['supplier_name'][:28]:<30} {r['total_purchase']:>12.0f} "
              f"{r['unique_materials']:>6} {r['sole_source_materials']:>4} "
              f"{r['avg_leadtime_days']:>4.0f} {r['active_months']:>6} {r['city']:>6}")


def cmd_risk(conn, args):
    """供应链风险"""
    sql = """
    SELECT material_name, risk_level, avg_price, avg_leadtime,
           long_lead_orders, suppliers, price_stability
    FROM supply_chain_risk_view
    """
    params = []
    if args.level:
        sql += " WHERE risk_level = ?"
        params.append(args.level)
    sql += " ORDER BY avg_price DESC"
    if args.top:
        sql += f" LIMIT {args.top}"

    rows = conn.execute(sql, params).fetchall()
    print(f"\n=== 供应链风险（{args.level or '全部'}，{len(rows)} 项） ===")
    print(f"{'物料':<40} {'风险':>18} {'均价':>10} {'交期':>4} {'价格稳定':>14}")
    print("-" * 95)
    for r in rows:
        print(f"{r['material_name'][:38]:<40} {r['risk_level']:>18} "
              f"{r['avg_price']:>10.0f} {r['avg_leadtime']:>4.0f} "
              f"{r['price_stability']:>14}")


def cmd_variance(conn, args):
    """物料价格波动"""
    sql = """
    SELECT material_name, sample_count, supplier_count, min_price, max_price,
           avg_price, price_spread_pct, sourcing_type
    FROM material_price_variance_view
    """
    params = []
    if args.material:
        sql += " WHERE material_name LIKE ?"
        params.append(f"%{args.material}%")
    sql += " ORDER BY price_spread_pct DESC"
    if args.top:
        sql += f" LIMIT {args.top}"

    rows = conn.execute(sql, params).fetchall()
    print(f"\n=== 物料价格波动（{len(rows)} 项） ===")
    print(f"{'物料':<30} {'样本':>4} {'供应':>4} {'最低':>10} {'最高':>10} {'价差%':>8} {'类型':>12}")
    print("-" * 85)
    for r in rows:
        print(f"{r['material_name'][:28]:<30} {r['sample_count']:>4} "
              f"{r['supplier_count']:>4} {r['min_price']:>10.0f} {r['max_price']:>10.0f} "
              f"{r['price_spread_pct']:>8.0f} {r['sourcing_type']:>12}")


def cmd_trend(conn, args):
    """物料价格趋势（跨年）"""
    if not args.material:
        print("请用 --material 指定物料名")
        return
    sql = """
    SELECT strftime('%Y', purchase_date) AS year,
           ROUND(AVG(unit_cost), 2) AS avg_price,
           COUNT(*) AS samples,
           COUNT(DISTINCT supplier_name) AS suppliers
    FROM purchase_material_costs
    WHERE material_name LIKE ? AND purchase_date IS NOT NULL
    GROUP BY year ORDER BY year
    """
    rows = conn.execute(sql, [f"%{args.material}%"]).fetchall()
    print(f"\n=== '{args.material}' 价格趋势 ===")
    print(f"{'年份':<8} {'均价':>12} {'样本':>6} {'供应商':>8}")
    print("-" * 40)
    for r in rows:
        year = r["year"] or "(空)"
        print(f"{year:<8} {r['avg_price']:>12.2f} {r['samples']:>6} {r['suppliers']:>8}")


def cmd_equipment(conn, args):
    """设备选型库（从采购数据重建的设备级技术参数）"""
    sql = """
    SELECT category, equipment_name, brand, unit_cost, supplier_name,
           specification, supplier_count
    FROM equipment_selection_view
    """
    params = []
    where = []
    if args.category:
        where.append("category = ?")
        params.append(args.category)
    if args.material:
        where.append("equipment_name LIKE ?")
        params.append(f"%{args.material}%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY unit_cost DESC"
    if args.top:
        sql += f" LIMIT {args.top}"

    rows = conn.execute(sql, params).fetchall()
    print(f"\n=== 设备选型库（{len(rows)} 项） ===")
    for r in rows:
        print(f"\n[{r['category']}] {r['equipment_name']}  ¥{r['unit_cost']:.0f}")
        print(f"  品牌: {r['brand'] or '-'}  供应商: {r['supplier_name']}  供应商数: {r['supplier_count']}")
        if r['specification']:
            spec = r['specification'][:150]
            print(f"  参数: {spec}")


def main():
    parser = argparse.ArgumentParser(description="供应商分析查询")
    parser.add_argument("cmd", choices=["profile", "risk", "variance", "trend", "equipment"],
                        help="profile=供应商画像, risk=供应链风险, variance=价格波动, trend=价格趋势, equipment=设备选型库")
    parser.add_argument("--supplier", type=str, help="按供应商名筛选(模糊)")
    parser.add_argument("--material", type=str, help="按物料名筛选(模糊)")
    parser.add_argument("--category", type=str, help="设备分类: 机器人/视觉检测/电源负载/控制采集/运动控制/软件系统/测试设备")
    parser.add_argument("--level", type=str, help="风险等级: HIGH_RISK_SOLO/MEDIUM_RISK_DUAL/LOW_RISK_MULTI")
    parser.add_argument("--top", type=int, default=20, help="返回条数(默认20)")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    cmds = {"profile": cmd_profile, "risk": cmd_risk,
            "variance": cmd_variance, "trend": cmd_trend,
            "equipment": cmd_equipment}
    cmds[args.cmd](conn, args)
    conn.close()


if __name__ == "__main__":
    main()
