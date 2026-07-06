#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入金凯博竞争对手数据（来自《金凯博产品规划分析.xls》）

两个 sheet：
  1. 自动化竞争对手对比：金凯博本体按行业的业务+客户
  2. 费思竞争对手对比：费思泰克（电源/负载）的 14 个对手完整画像

导入到 competitors 表，让竞争分析引擎能引用真实对手弱点。

运行：
    python scripts/import_competitors.py "/Users/flw/Desktop/金凯博/企业和产品介绍/金凯博产品规划分析.xls"
"""
import sqlite3
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import xlrd

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "app.db"


def parse_multiline(val):
    """多行文本转列表（优势/劣势每行一条）。"""
    if not val or not str(val).strip():
        return ""
    lines = [l.strip() for l in str(val).split("\n") if l.strip()]
    return "；".join(lines)


def import_feesi_competitors(ws, conn):
    """导入费思泰克竞争对手（Sheet2，14 个对手完整画像）。"""
    # 读表头（品牌名在行1，列1-14）
    brands = []
    for c in range(1, ws.ncols):
        v = str(ws.cell_value(1, c)).strip()
        if v:
            brands.append((c, v))

    print(f"费思泰克竞争对手: {len(brands)} 个")

    # 各属性行：资金(2)/上市(3)/顺位(4)/产品(5)/优势(6)/劣势(7)/国内收入(8)
    for col_idx, brand in brands:
        if col_idx >= ws.ncols:
            continue

        funding = str(ws.cell_value(2, col_idx)).strip() if ws.nrows > 2 else ""
        listed = str(ws.cell_value(3, col_idx)).strip() if ws.nrows > 3 else ""
        rank = str(ws.cell_value(4, col_idx)).strip() if ws.nrows > 4 else ""
        products = str(ws.cell_value(5, col_idx)).strip() if ws.nrows > 5 else ""
        strengths = parse_multiline(ws.cell_value(6, col_idx)) if ws.nrows > 6 else ""
        weaknesses = parse_multiline(ws.cell_value(7, col_idx)) if ws.nrows > 7 else ""
        revenue = str(ws.cell_value(8, col_idx)).strip() if ws.nrows > 8 else ""

        # 价格水平推断（顺位 1-2 高，3-4 中，5-6 低）
        try:
            rank_num = float(rank)
            price_level = "高" if rank_num <= 2 else ("中" if rank_num <= 4 else "低")
        except (ValueError, TypeError):
            price_level = "中"

        # 构造应对策略（基于对手弱点）
        counter = ""
        if weaknesses:
            counter = f"针对{brand}的弱点（{weaknesses[:60]}），强调我方在这些方面的优势"

        conn.execute(
            """INSERT OR REPLACE INTO competitors
            (name, competitor_type, strengths, weaknesses, good_at, price_level,
             counter_strategy, encounter_count, is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (
                brand,
                f"电源/负载厂商（{funding}，{listed}，市场顺位{rank}）",
                strengths or "未知",
                weaknesses or "未知",
                products or "电源/负载",
                price_level,
                counter,
            ),
        )
    conn.commit()
    print(f"费思泰克对手导入完成")


def import_automation_business(ws, conn):
    """导入金凯博自动化业务概况（Sheet1，存成参考信息）。"""
    print("\n金凯博自动化业务分布:")
    for r in range(1, ws.nrows):
        industry = str(ws.cell_value(r, 1)).strip()
        products = str(ws.cell_value(r, 2)).strip()
        customers = str(ws.cell_value(r, 3)).strip()
        if industry or products:
            print(f"  行业: {industry} | 产品: {products[:30]} | 客户: {customers[:30]}")

    # 金凯博自己的信息不导入 competitors 表（那是对手库）
    # 但打印出来确认数据完整
    print("（金凯博自身业务信息已读取，不导入对手库）")


def main():
    xls_path = sys.argv[1] if len(sys.argv) > 1 else "/Users/flw/Desktop/金凯博/企业和产品介绍/金凯博产品规划分析.xls"
    if not Path(xls_path).exists():
        print(f"文件不存在: {xls_path}")
        sys.exit(1)

    wb = xlrd.open_workbook(xls_path)
    conn = sqlite3.connect(DB_PATH)

    # 清空旧数据（重新导入）
    conn.execute("DELETE FROM competitors")

    # Sheet1: 自动化业务（参考，不导入对手库）
    if "自动化竞争对手对比" in wb.sheet_names():
        import_automation_business(wb.sheet_by_name("自动化竞争对手对比"), conn)

    # Sheet2: 费思竞争对手（导入）
    if "费思竞争对手对比" in wb.sheet_names():
        import_feesi_competitors(wb.sheet_by_name("费思竞争对手对比"), conn)

    count = conn.execute("SELECT COUNT(*) FROM competitors").fetchone()[0]
    print(f"\n完成：competitors 表现有 {count} 条对手数据")

    # 抽样验证
    print("\n抽样:")
    for row in conn.execute("SELECT name, competitor_type, weaknesses FROM competitors LIMIT 5"):
        print(f"  · {row[0]}: {row[1][:30]} | 弱点: {row[2][:50]}")

    conn.close()


if __name__ == "__main__":
    main()
