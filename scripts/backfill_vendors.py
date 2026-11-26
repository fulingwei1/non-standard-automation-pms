#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反向填充 vendors 主数据表

从 purchase_material_costs 的交易数据重建供应商主数据:
  - 把 370 个真实供应商写入 vendors 表
  - 从 supplier_profile_view 带上采购总额/首次末次/城市等画像信息
  - 回填 purchase_material_costs.supplier_id 建立关联

运行:
    python scripts/backfill_vendors.py --dry-run   # 看会填什么
    python scripts/backfill_vendors.py --apply     # 写入
"""
from __future__ import annotations

import argparse
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT_DIR / "data" / "app.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_vendors")


def classify_vendor_type(supplier_name: str, materials: str) -> str:
    """根据供应商名和采购物料推断 vendor_type"""
    name = supplier_name or ""
    mats = materials or ""
    if any(k in name for k in ["机器人","机械","装备","设备","自动化","智能"]):
        return "EQUIPMENT"
    if any(k in name for k in ["电子","电路","PCB","芯片","半导体","科技"]):
        return "ELECTRONIC"
    if any(k in name for k in ["五金","钣金","机械加工","模具","金属","钢材"]):
        return "HARDWARE"
    if any(k in name for k in ["软件","信息","数据","系统"]):
        return "SOFTWARE"
    if any(k in name for k in ["物流","运输","货运"]):
        return "LOGISTICS"
    return "MATERIAL"


def classify_supplier_level(total_purchase: float, item_count: int) -> str:
    """根据采购规模分级 A/B/C/D"""
    if total_purchase >= 1000000 or item_count >= 50:
        return "A"  # 战略供应商
    if total_purchase >= 200000 or item_count >= 20:
        return "B"  # 重点供应商
    if total_purchase >= 20000 or item_count >= 5:
        return "C"  # 一般供应商
    return "D"  # 偶发供应商


def main():
    parser = argparse.ArgumentParser(description="反向填充 vendors 主数据表")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("需要 --dry-run 或 --apply")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 从 supplier_profile_view 拿供应商画像
    cur.execute("""
        SELECT supplier_name, item_count, unique_materials, total_purchase,
               avg_item_price, avg_leadtime_days, active_months, city,
               sole_source_materials, first_purchase, last_purchase
        FROM supplier_profile_view
        ORDER BY total_purchase DESC
    """)
    suppliers = cur.fetchall()
    logger.info(f"从采购数据重建供应商: {len(suppliers)} 个")

    # 2. 拿每个供应商采购最多的物料类型(用于 vendor_type 推断)
    cur.execute("""
        SELECT supplier_name, GROUP_CONCAT(material_name) AS materials
        FROM purchase_material_costs
        WHERE supplier_name IS NOT NULL AND supplier_name != ''
        GROUP BY supplier_name
    """)
    mat_map = {r["supplier_name"]: r["materials"] for r in cur.fetchall()}

    # 3. 查现有 vendors 表已有的供应商(避免重复)
    cur.execute("SELECT supplier_name FROM vendors")
    existing = {r["supplier_name"] for r in cur.fetchall()}

    # 4. 清占位数据(DEMO 保留)
    if args.apply:
        deleted = cur.execute(
            "DELETE FROM vendors WHERE supplier_name LIKE 'vendors_supplier_name_%' "
            "OR supplier_name LIKE '自动化_E2E_%'"
        ).rowcount
        if deleted:
            logger.info(f"清理 {deleted} 条占位/测试数据")

    # 5. 找最大 supplier_code 序号
    cur.execute("SELECT supplier_code FROM vendors WHERE supplier_code LIKE 'SUP-%' ORDER BY supplier_code DESC LIMIT 1")
    row = cur.fetchone()
    next_seq = 1
    if row:
        try:
            next_seq = int(row["supplier_code"].replace("SUP-", "")) + 1
        except ValueError:
            next_seq = 1

    # 6. 写入
    now = datetime.now().isoformat(timespec="seconds")
    inserted = 0
    skipped = 0
    supplier_id_map = {}  # supplier_name → vendor.id

    for sup in suppliers:
        name = sup["supplier_name"]
        if name in existing:
            skipped += 1
            # 拿已存在的 id 用于回填
            cur.execute("SELECT id FROM vendors WHERE supplier_name=?", (name,))
            r = cur.fetchone()
            if r:
                supplier_id_map[name] = r["id"]
            continue

        materials = mat_map.get(name, "")
        vtype = classify_vendor_type(name, materials)
        level = classify_supplier_level(sup["total_purchase"], sup["item_count"])

        # supplier_code
        code = f"SUP-{next_seq:05d}"
        next_seq += 1

        # 短名(去掉有限公司等后缀)
        short_name = name.replace("深圳市", "").replace("深圳", "")
        for suffix in ["有限公司", "股份有限公司", "有限责任公司", "科技有限公司"]:
            short_name = short_name.replace(suffix, "")
        short_name = short_name[:20] if len(short_name) > 20 else short_name

        # remark 记录画像信息(方便人工核实)
        remark = (
            f"采购画像: {sup['item_count']}次/{sup['unique_materials']}种物料/"
            f"¥{sup['total_purchase']:.0f}/活跃{sup['active_months']}月/"
            f"独占{sup['sole_source_materials']}种/{sup['city']}"
        )

        # address 填城市
        city = sup["city"] if sup["city"] != "其他" else None

        if args.apply:
            cur.execute("""
                INSERT INTO vendors (
                    supplier_code, supplier_name, supplier_short_name,
                    vendor_type, supplier_level, status,
                    cooperation_start, last_order_date,
                    remark, address, created_at, updated_at
                ) VALUES (?,?,?,?,?, 'ACTIVE', ?, ?, ?, ?, ?, ?)
            """, (
                code, name, short_name or None,
                vtype, level,
                sup["first_purchase"], sup["last_purchase"],
                remark, city, now, now
            ))
            supplier_id_map[name] = cur.lastrowid

        inserted += 1

    if args.apply:
        conn.commit()
    logger.info(f"写入: {inserted} 个, 跳过(已存在): {skipped} 个")

    # 7. 回填 purchase_material_costs.supplier_id
    if args.apply and supplier_id_map:
        updated = 0
        for name, vid in supplier_id_map.items():
            cur.execute(
                "UPDATE purchase_material_costs SET supplier_id=? WHERE supplier_name=? AND supplier_id IS NULL",
                (vid, name)
            )
            updated += cur.rowcount
        conn.commit()
        logger.info(f"回填 supplier_id: {updated} 条采购记录关联到 vendors")

    # 8. 验证
    cur.execute("SELECT COUNT(*) FROM vendors")
    total_vendors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM purchase_material_costs WHERE supplier_id IS NOT NULL")
    linked = cur.fetchone()[0]
    cur.execute("""
        SELECT supplier_level, COUNT(*) FROM vendors
        WHERE supplier_code LIKE 'SUP-%' OR supplier_code LIKE 'DEMO%'
        GROUP BY supplier_level ORDER BY supplier_level
    """)
    levels = cur.fetchall()

    logger.info(f"vendors 表总数: {total_vendors}")
    logger.info(f"采购记录关联 supplier_id: {linked} / 5148")
    logger.info(f"供应商分级: " + ", ".join(f"{l['supplier_level']}={l[1]}" for l in levels))

    if args.dry_run:
        # 打印 top10 新增供应商
        logger.info("=== dry-run: top10 新增供应商预览 ===")
        for sup in suppliers[:10]:
            materials = mat_map.get(sup["supplier_name"], "")
            vtype = classify_vendor_type(sup["supplier_name"], materials)
            level = classify_supplier_level(sup["total_purchase"], sup["item_count"])
            print(f"  [{level}/{vtype}] {sup['supplier_name'][:30]:<30} "
                  f"¥{sup['total_purchase']:>10.0f} {sup['item_count']:>4}次 {sup['city']}")

    conn.close()


if __name__ == "__main__":
    main()
