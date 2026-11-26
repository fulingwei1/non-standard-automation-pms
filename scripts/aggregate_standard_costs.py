#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前弹药库 P4：从历史报价明细聚合标准件价格库

把 quote_items 里高频出现的报价项（如"电控柜与PLC程序""视觉检测工站主体"）
按 item_name 归一化聚合，生成标准成本库（standard_costs）：
  - 出现 >= N 次的 item_name 才入库（保证统计意义）
  - standard_cost = 中位数（比均值抗异常值）
  - 记录样本数/价格区间/标准差，便于判断可信度

跑完后，智能体报价对标能力就有真实数据底座。

运行：
    python scripts/aggregate_standard_costs.py             # dry-run 看会聚合出什么
    python scripts/aggregate_standard_costs.py --apply     # 写入 standard_costs
    python scripts/aggregate_standard_costs.py --apply --min-samples 3  # 提高门槛
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from datetime import date
from pathlib import Path
from statistics import median, pstdev

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agg_std_cost")


def aggregate(conn: sqlite3.Connection, min_samples: int):
    """从 quote_items 按 item_name 聚合标准成本。"""
    rows = conn.execute(
        """
        SELECT item_name, unit_price, qty, cost_category, unit, specification
        FROM quote_items
        WHERE unit_price IS NOT NULL AND unit_price > 0
          AND item_name IS NOT NULL AND TRIM(item_name) != ''
        """
    ).fetchall()

    # 按 item_name 分组
    groups: dict[str, list] = {}
    for r in rows:
        name = r["item_name"].strip()
        groups.setdefault(name, []).append(r)

    # 聚合：只保留出现 >= min_samples 次的
    results = []
    for name, items in groups.items():
        if len(items) < min_samples:
            continue
        prices = [float(r["unit_price"]) for r in items]
        # 过滤极端异常值（价格 > 10倍中位数的视为脏数据）
        med = median(prices)
        clean = [p for p in prices if med / 10 <= p <= med * 10] or prices
        results.append({
            "item_name": name,
            "category": items[0]["cost_category"] or "设备成本",
            "unit": items[0]["unit"] or "套",
            "spec": items[0]["specification"] or "",
            "source": "HISTORICAL_QUOTE",
            "sample_count": len(clean),
            "median_price": round(median(clean), 2),
            "avg_price": round(sum(clean) / len(clean), 2),
            "min_price": round(min(clean), 2),
            "max_price": round(max(clean), 2),
            "std_dev": round(pstdev(clean), 2) if len(clean) > 1 else 0,
            "cv": round(pstdev(clean) / med * 100, 1) if med and len(clean) > 1 else 0,  # 变异系数%
        })

    # 按样本数排序（高频的在前）
    results.sort(key=lambda x: x["sample_count"], reverse=True)
    return results


def aggregate_from_purchase(conn: sqlite3.Connection, min_samples: int):
    """从 purchase_material_costs 按 material_name 聚合标准成本（真实采购价）。"""
    rows = conn.execute(
        """
        SELECT material_name, unit_cost, unit, specification, brand, supplier_name
        FROM purchase_material_costs
        WHERE unit_cost IS NOT NULL AND unit_cost > 0
          AND material_name IS NOT NULL AND TRIM(material_name) != ''
        """
    ).fetchall()

    # 按 material_name 分组
    groups: dict[str, list] = {}
    for r in rows:
        name = r["material_name"].strip()
        groups.setdefault(name, []).append(r)

    results = []
    for name, items in groups.items():
        if len(items) < min_samples:
            continue
        prices = [float(r["unit_cost"]) for r in items]
        med = median(prices)
        clean = [p for p in prices if med / 10 <= p <= med * 10] or prices
        suppliers = {r["supplier_name"] for r in items if r["supplier_name"]}
        results.append({
            "item_name": name,
            "category": "采购件",
            "unit": items[0]["unit"] or "套",
            "spec": items[0]["specification"] or "",
            "source": "PURCHASE_HISTORY",
            "sample_count": len(clean),
            "median_price": round(median(clean), 2),
            "avg_price": round(sum(clean) / len(clean), 2),
            "min_price": round(min(clean), 2),
            "max_price": round(max(clean), 2),
            "std_dev": round(pstdev(clean), 2) if len(clean) > 1 else 0,
            "cv": round(pstdev(clean) / med * 100, 1) if med and len(clean) > 1 else 0,
            "supplier_count": len(suppliers),
        })

    results.sort(key=lambda x: x["sample_count"], reverse=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="从历史报价聚合标准件价格库")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--apply", action="store_true", help="写入 standard_costs（默认 dry-run）")
    parser.add_argument("--min-samples", type=int, default=3, help="最少出现次数（默认3）")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # 清占位数据 + 旧的聚合结果（重新聚合，避免脏数据残留）
    if args.apply:
        deleted = conn.execute(
            "DELETE FROM standard_costs WHERE cost_name LIKE 'standard_costs_cost_name_%' "
            "OR cost_source IN ('HISTORICAL_QUOTE', 'PURCHASE_HISTORY')"
        ).rowcount
        if deleted:
            logger.info("清理 %s 条旧聚合/占位数据", deleted)

    quote_results = aggregate(conn, args.min_samples)
    purchase_results = aggregate_from_purchase(conn, args.min_samples)
    results = quote_results + purchase_results
    logger.info(
        f"聚合出 {len(results)} 个标准成本项 "
        f"（报价{len(quote_results)} + 采购{len(purchase_results)}，min_samples={args.min_samples}）"
    )

    if not args.apply:
        logger.info("（dry-run 模式，不写库）")
        for r in results[:15]:
            cv_flag = "⚠高波动" if r["cv"] > 50 else ""
            src_tag = "采购" if r["source"] == "PURCHASE_HISTORY" else "报价"
            print(
                f"  [{r['sample_count']}次|{src_tag}] {r['item_name'][:28]:<28} "
                f"中位{r['median_price']:>12} 均{r['avg_price']:>12} "
                f"区间{r['min_price']}~{r['max_price']} CV={r['cv']}% {cv_flag}"
            )
        if len(results) > 15:
            print(f"  ... 还有 {len(results) - 15} 项")
        return

    # 写入 standard_costs
    today = date.today().isoformat()
    inserted = 0
    for r in results:
        # cost_code 用来源前缀 + 序号，避免报价和采购同名冲突
        src_prefix = "PH" if r["source"] == "PURCHASE_HISTORY" else "SC"
        cost_code = f"{src_prefix}-{r['item_name'][:20].replace(' ', '')}"
        # source_description 记录统计信息，供对标时判断可信度
        source_desc = (
            f"{'采购价聚合' if r['source'] == 'PURCHASE_HISTORY' else '历史报价聚合'}："
            f"样本{r['sample_count']}，中位{r['median_price']}，"
            f"区间{r['min_price']}~{r['max_price']}，CV={r['cv']}%"
        )
        # upsert（按 cost_code 存在则更新）
        existing = conn.execute(
            "SELECT id FROM standard_costs WHERE cost_code = ?", (cost_code,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE standard_costs SET cost_name=?, cost_category=?, specification=?, "
                "unit=?, standard_cost=?, cost_source=?, source_description=?, "
                "effective_date=?, is_active=1 WHERE cost_code=?",
                (r["item_name"], r["category"], r["spec"], r["unit"], r["median_price"],
                 r["source"], source_desc, today, cost_code),
            )
        else:
            conn.execute(
                "INSERT INTO standard_costs (cost_code, cost_name, cost_category, specification, "
                "unit, standard_cost, currency, cost_source, source_description, effective_date, "
                "version, is_active, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?, 'CNY',?,?, ?,1,1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (cost_code, r["item_name"], r["category"], r["spec"], r["unit"],
                 r["median_price"], r["source"], source_desc, today),
            )
        inserted += 1

    conn.commit()
    conn.close()
    logger.info(f"已写入 {inserted} 条标准成本到 standard_costs")


if __name__ == "__main__":
    main()
