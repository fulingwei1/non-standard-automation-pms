#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回填 purchase_material_costs 无日期记录的 purchase_date

数据源:从 PDF 文件名 + 目录路径提取日期(OCR 失败的扫描件,文件名里自带日期)
匹配策略:供应商名 → PDF 文件名关键词匹配 → 提取日期 → 回填

运行:
    python scripts/backfill_purchase_dates.py --dry-run   # 看能补多少
    python scripts/backfill_purchase_dates.py --apply     # 写入
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import logging
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT_DIR / "data" / "app.db"
PROG_FILE = Path("/Users/flw/.lark-cli-events/state/purchase_extract_progress.txt")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_date")


def extract_date_from_pdf(pdf_path: str) -> str | None:
    """从 PDF 路径+文件名提取日期,返回 YYYY-MM-DD 或 None"""
    p = Path(pdf_path)
    fname = p.name
    parts = p.parts

    # 1. 时间戳文件名(14位数字: 20250409144203275.pdf)
    m = re.search(r'(\d{4})(\d{2})(\d{2})\d{6}\.pdf$', fname, re.I)
    if m:
        y, mo, d = m.groups()
        if 2020 <= int(y) <= 2026 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{y}-{mo}-{d}"

    # 2. 文件名含完整日期 YYYY-MM-DD / YYYY.MM.DD / YYYY年MM月DD日
    m = re.search(r'(20\d{2})[\.\-/年](\d{1,2})[\.\-/月\.](\d{1,2})', fname)
    if m:
        y, mo, d = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{y}-{int(mo):02d}-{int(d):02d}"

    # 从路径提取年份(金采购合同24-26/2024/05/)
    year = None
    month = None
    for part in parts:
        if re.match(r'^20(2[3-6])$', part):
            year = part
        elif re.match(r'^(0?[1-9]|1[0-2])$', part):
            month = part.zfill(2)

    # 3. 文件名含 MM-DD(如 9-29, 3-26),配合路径年份
    m = re.search(r'(?<!\d)(\d{1,2})[\-/](\d{1,2})(?!\d)', fname)
    if m and year:
        mo, d = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{year}-{int(mo):02d}-{int(d):02d}"

    # 4. 文件名含 MMDD(4位连写,如 0418),配合路径年份
    m = re.search(r'(?<!\d)(\d{2})(\d{2})(?!\d)', fname)
    if m and year:
        mo, d = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{year}-{mo}-{d}"

    # 5. 只有路径年月(没有文件名日期),用月中15号
    if year and month:
        return f"{year}-{month}-15"

    # 6. 只有路径年份(没有月份),用年中7月1号
    if year:
        return f"{year}-07-01"

    return None


def build_supplier_pdf_map(pdf_paths: list[str]) -> dict[str, list[tuple[str, str]]]:
    """构建 供应商名 → [(pdf_path, date)] 映射"""
    # 从文件名提取供应商关键词
    sup_map = defaultdict(list)

    for pdf in pdf_paths:
        date = extract_date_from_pdf(pdf)
        if not date:
            continue
        fname = Path(pdf).name
        # 提取供应商关键词(文件名开头的中文部分,去掉数字/日期/回签等)
        # 常见模式: "智力昌合同3-26.pdf" / "方博-金凯博合同-9-29.pdf" / "海派合同3-3.pdf"
        # 去掉日期、数字、常见后缀
        kw = re.sub(r'\d+', '', fname)
        for suffix in ['合同回签.pdf', '回签.pdf', '回传.pdf', '合同.pdf', '.pdf', '回签', '回传',
                        '金凯博', '变更合同', '合同', '订单', '购销', '沟通联络函', '电子公司',
                        '成型机', '技术文件', '深圳', '深圳市']:
            kw = kw.replace(suffix, '')
        kw = kw.strip('- _．')
        if len(kw) >= 2:
            sup_map[kw].append((pdf, date))

    return sup_map


def main():
    parser = argparse.ArgumentParser(description="回填采购记录日期")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true", help="只看不写")
    parser.add_argument("--apply", action="store_true", help="写入数据库")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("需要 --dry-run 或 --apply")

    # 1. 读取进度文件,提取所有 PDF 的日期
    pdf_paths = [l.strip() for l in PROG_FILE.read_text().splitlines() if l.strip()]
    logger.info(f"进度文件: {len(pdf_paths)} 个 PDF")

    pdf_dates = {}
    no_date_pdfs = 0
    for pdf in pdf_paths:
        d = extract_date_from_pdf(pdf)
        if d:
            pdf_dates[pdf] = d
        else:
            no_date_pdfs += 1
    logger.info(f"提取到日期: {len(pdf_dates)} 个, 无法提取: {no_date_pdfs} 个")

    # 2. 构建供应商→PDF映射(用于匹配无日期记录)
    sup_map = build_supplier_pdf_map(pdf_paths)
    logger.info(f"供应商关键词映射: {len(sup_map)} 个")

    # 3. 查数据库无日期记录
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, supplier_name, material_name, purchase_date
        FROM purchase_material_costs
        WHERE purchase_date IS NULL OR purchase_date = ''
    """)
    no_date_rows = cur.fetchall()
    logger.info(f"数据库无日期记录: {len(no_date_rows)} 条")

    # 4. 匹配并回填
    # 策略: 用供应商名匹配 PDF 关键词,取该供应商最早可用的日期
    # (一个供应商多个PDF时,按文件名排序取第一个匹配的)
    matched = 0
    unmatched_suppliers = set()

    # 按供应商分组无日期记录
    sup_rows = defaultdict(list)
    for row in no_date_rows:
        sup_rows[row["supplier_name"]].append(row)

    for supplier, rows in sup_rows.items():
        # 从供应商名提取关键词
        sup_kw = supplier.replace("深圳市", "").replace("深圳", "").replace("有限公司", "")
        sup_kw = sup_kw.replace("股份", "").replace("科技", "").replace("自动化", "")
        sup_kw = sup_kw.replace("设备", "").replace("技术", "").replace("智能", "")
        sup_kw = sup_kw[:4] if len(sup_kw) >= 4 else sup_kw

        # 在映射里找匹配的PDF
        candidate_dates = []
        for kw, pdf_list in sup_map.items():
            if sup_kw and sup_kw in kw:
                candidate_dates.extend([d for _, d in pdf_list])

        if not candidate_dates:
            # 试试用供应商名前3字
            for kw, pdf_list in sup_map.items():
                if supplier[:3] in kw or kw in supplier:
                    candidate_dates.extend([d for _, d in pdf_list])

        if candidate_dates:
            # 取最常见的日期(一个供应商同批次合同日期应该接近)
            from collections import Counter
            most_common_date = Counter(candidate_dates).most_common(1)[0][0]
            for row in rows:
                if args.apply:
                    cur.execute(
                        "UPDATE purchase_material_costs SET purchase_date=? WHERE id=?",
                        (most_common_date, row["id"])
                    )
                matched += 1
        else:
            unmatched_suppliers.add(supplier)

    if args.apply:
        conn.commit()

    logger.info(f"匹配并{'回填' if args.apply else '预览'}: {matched} / {len(no_date_rows)} 条")
    logger.info(f"未匹配的供应商: {len(unmatched_suppliers)} 个")
    if unmatched_suppliers:
        logger.info(f"未匹配供应商样本: {list(unmatched_suppliers)[:10]}")

    # 5. 验证结果
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN purchase_date IS NULL OR purchase_date='' THEN 1 ELSE 0 END) AS no_date,
            SUM(CASE WHEN purchase_date IS NOT NULL AND purchase_date!='' THEN 1 ELSE 0 END) AS has_date
        FROM purchase_material_costs
    """)
    r = cur.fetchone()
    logger.info(f"最终: 总{r['total']}条, 有日期{r['has_date']}条, 无日期{r['no_date']}条")

    conn.close()


if __name__ == "__main__":
    main()
