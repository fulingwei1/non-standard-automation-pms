#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前弹药库：从采购合同 PDF 抽取核心要素（试点版）

流程：pymupdf 提取文本 → AI 抽结构化要素（供应商/物料/金额/数量/日期/条款）
扫描件（文本为空）用 tesseract OCR 兜底。

试点目的：验证从合同 PDF 抽要素的准确率，确认后再全量。

运行：
    python scripts/extract_purchase_from_pdf.py --dir <目录> --limit 5 --dry-run
    python scripts/extract_purchase_from_pdf.py --file <某.pdf>          # 单份详细看
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import subprocess
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extract_pdf")

DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"


def extract_text_pymupdf(pdf_path: str, max_pages: int = 5) -> str:
    """用 pymupdf 提取文字。返回前几页文本。"""
    try:
        import fitz

        doc = fitz.open(pdf_path)
        texts = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            t = page.get_text()
            if t:
                texts.append(t)
        doc.close()
        return "\n".join(texts)
    except Exception as e:
        logger.debug(f"pymupdf 失败 {pdf_path}: {e}")
        return ""


def extract_text_ocr(pdf_path: str, max_pages: int = 2) -> str:
    """扫描件兜底：pymupdf 转图片 → tesseract OCR。慢，仅扫描件用。"""
    try:
        import fitz

        doc = fitz.open(pdf_path)
        texts = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            # 转成 PNG（dpi=200 平衡清晰度和速度）
            pix = page.get_pixmap(dpi=200)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                pix.save(tmp.name)
                # tesseract 中文+英文
                result = subprocess.run(
                    ["tesseract", tmp.name, "stdout", "-l", "chi_sim+eng"],
                    capture_output=True, text=True, timeout=20,
                )
                if result.stdout:
                    texts.append(result.stdout)
                os.unlink(tmp.name)
        doc.close()
        return "\n".join(texts)
    except Exception as e:
        logger.debug(f"OCR 失败 {pdf_path}: {e}")
        return ""


def extract_text(pdf_path: str) -> tuple[str, str]:
    """提取文本，返回 (text, method)。method=pymupdf/ocr/empty。"""
    text = extract_text_pymupdf(pdf_path)
    if len(text) > 100:
        return text, "pymupdf"
    # 文字型提取不够，尝试 OCR
    text = extract_text_ocr(pdf_path)
    if len(text) > 50:
        return text, "ocr"
    return "", "empty"


def extract_elements_with_ai(text: str, filename: str) -> dict:
    """用 AI 从合同文本抽取结构化采购要素。"""
    from app.services.ai_client_service import AIClientService

    # 文本过长截断（AI token 限制）
    text = text[:3000]
    ai = AIClientService()
    prompt = (
        "你是采购数据抽取助手。从下面的采购合同文本中抽取结构化信息。"
        "严格只输出 JSON，字段如下：\n"
        "{\n"
        '  "supplier_name": "供应商（卖方）名称",\n'
        '  "buyer_name": "采购方（买方）名称",\n'
        '  "contract_no": "合同编号",\n'
        '  "sign_date": "签订日期(YYYY-MM-DD格式，解析不出来就null)",\n'
        '  "items": [\n'
        '    {"name":"物料/设备名称","spec":"规格型号","brand":"品牌","quantity":数字,"unit":"单位",'
        '"unit_price":数字,"total_price":数字}\n'
        '  ],\n'
        '  "total_amount": "合同总金额(数字)",\n'
        '  "currency": "币种(默认CNY)",\n'
        '  "payment_terms": "付款方式",\n'
        '  "warranty": "质保期",\n'
        '  "delivery_terms": "交付/运输条款",\n'
        '  "lead_time_days": 交期天数(数字,解析不出null)\n'
        "}\n"
        "注意：金额只取数字（去掉'元'/'￥'/千分位）；物料可能有多个都抽；"
        "OCR 可能有错字，根据上下文合理推断（如'△博士'→'工博士'）；"
        "如果某字段确实抽不出来填 null，不要编造。\n\n"
        f"文件名：{filename}\n"
        f"合同文本：\n\"\"\"\n{text}\n\"\"\""
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.1, max_tokens=1000)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"AI 抽取失败: {e}")
        return {"_error": str(e)[:100]}


def collect_pdfs(directory: str, limit: int = 5) -> list[str]:
    """收集目录下的 PDF（递归），按文件名排序，限前 N 个。"""
    pdfs = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, f))
    pdfs.sort()
    return pdfs[:limit] if limit > 0 else pdfs


def main():
    parser = argparse.ArgumentParser(description="从采购合同 PDF 抽取要素")
    parser.add_argument("--dir", type=str, help="合同目录（可多个，逗号分隔）")
    parser.add_argument("--file", type=str, help="单份 PDF")
    parser.add_argument("--limit", type=int, default=0, help="最多处理几份（0=不限）")
    parser.add_argument("--apply", action="store_true", help="写入数据库（默认 dry-run）")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--progress", type=Path, default=Path("/Users/flw/.lark-cli-events/state/purchase_extract_progress.txt"),
                        help="进度文件（断点续跑用）")
    args = parser.parse_args()

    # 收集 PDF（支持多目录逗号分隔）
    if args.file:
        pdfs = [args.file]
    elif args.dir:
        dirs = [d.strip() for d in args.dir.split(",") if d.strip()]
        pdfs = []
        for d in dirs:
            pdfs.extend(collect_pdfs(d, 0))  # 全量收集
        pdfs = sorted(set(pdfs))
        if args.limit > 0:
            pdfs = pdfs[: args.limit]
    else:
        parser.error("需要 --dir 或 --file")

    # 断点续跑：加载已处理文件
    done_files = set()
    if args.progress.exists():
        done_files = {l.strip() for l in args.progress.read_text().splitlines() if l.strip()}
    todo = [p for p in pdfs if p not in done_files]
    logger.info(f"PDF 总数: {len(pdfs)}，已处理: {len(done_files)}，待处理: {len(todo)}")

    if not todo:
        logger.info("全部已处理，退出")
        return

    args.progress.parent.mkdir(parents=True, exist_ok=True)

    results = []
    import sqlite3
    conn = sqlite3.connect(args.db) if args.apply else None

    total = len(pdfs)
    start_idx = len(done_files)
    for i, pdf in enumerate(todo, start_idx + 1):
        fname = os.path.basename(pdf)
        logger.info(f"[{i}/{total}] {fname}")
        try:
            text, method = extract_text(pdf)
        except Exception as e:
            logger.warning(f"  提取异常，跳过: {e}")
            results.append({"file": fname, "method": "error", "elements": None})
            continue
        if not text:
            logger.warning(f"  提取失败（空文本）")
            results.append({"file": fname, "method": "empty", "elements": None})
            continue

        logger.info(f"  提取方法: {method}, 文字长度: {len(text)}")
        try:
            elements = extract_elements_with_ai(text, fname)
        except Exception as e:
            logger.warning(f"  AI抽取异常，跳过: {e}")
            results.append({"file": fname, "method": method, "elements": None})
            continue
        # 防御：AI 偶尔返回 list 而非 dict，跳过
        if not isinstance(elements, dict):
            logger.warning(f"  AI返回格式异常（{type(elements).__name__}），跳过")
            results.append({"file": fname, "method": method, "elements": None})
            # 仍记录进度（避免卡在同一份）
            with args.progress.open("a", encoding="utf-8") as pf:
                pf.write(pdf + "\n")
            continue
        elements["_method"] = method
        elements["_text_len"] = len(text)
        # 防御：把所有 None 值转成空串（AI 返回的 null 会变成 Python None）
        for k, v in list(elements.items()):
            if v is None:
                elements[k] = ""
        results.append({"file": fname, "method": method, "elements": elements})

        # 打印抽取结果（全量模式只打 logger，不逐份 print）
        items = elements.get("items", [])
        verbose = len(todo) <= 50  # 小批量才详细打印
        if verbose:
            print(f"\n{'='*60}")
            print(f"文件: {fname}  ({method}, {len(text)}字)")
            print(f"供应商: {elements.get('supplier_name','')}")
            print(f"合同号: {elements.get('contract_no','')}  日期: {elements.get('sign_date','')}")
            print(f"总金额: {elements.get('total_amount','')}")
            for it in items:
                print(f"  · {it.get('name','')} {it.get('spec','')} ×{it.get('quantity','')}"
                      f"  ¥{it.get('unit_price','')} (合计¥{it.get('total_price','')})")
            if elements.get("payment_terms"):
                print(f"付款: {elements['payment_terms']}")
            if elements.get("warranty"):
                print(f"质保: {elements['warranty']}")
        else:
            sup = elements.get('supplier_name') or ''
            total_amt = elements.get('total_amount') or ''
            logger.info(f"  {method} | 供应商:{sup[:15]} | 物料{len(items)}项 | 总额{total_amt}")

        # 写库（跳过缺单价的物料）
        if args.apply and conn and items:
            inserted = 0
            for it in items:
                price = it.get("unit_price")
                name = it.get("name")
                if not name or price is None:
                    continue  # 跳过缺关键信息的
                try:
                    conn.execute(
                        """INSERT INTO purchase_material_costs
                        (material_name, specification, brand, unit, unit_cost, currency,
                         supplier_name, purchase_date, lead_time_days, is_active,
                         match_priority, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?, ?,?, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                        (
                            name, it.get("spec"), it.get("brand"),
                            it.get("unit") or "套",
                            price, elements.get("currency") or "CNY",
                            elements.get("supplier_name"), elements.get("sign_date"),
                            elements.get("lead_time_days"),
                        ),
                    )
                    inserted += 1
                except Exception as ie:
                    logger.debug(f"写入跳过: {ie}")
            conn.commit()
            if inserted:
                logger.info(f"  已写入 {inserted} 条到 purchase_material_costs")

        # 记录进度（断点续跑用）
        with args.progress.open("a", encoding="utf-8") as pf:
            pf.write(pdf + "\n")

    if conn:
        conn.close()

    # 汇总
    success = sum(1 for r in results if r["elements"] and r["elements"].get("items"))
    logger.info(f"\n汇总: {len(results)} 份处理，{success} 份成功抽取物料")


if __name__ == "__main__":
    main()
