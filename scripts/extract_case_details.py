#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度提取：从 100 个真实项目的技术方案 Word/PDF 里提取技术亮点和经验教训。

每个项目目录里有：
  - 技术方案.docx/.pdf（含架构/测试项目/技术指标/设备选型）
  - 报价单.xlsx（已有金额）

本脚本：
  1. 遍历 93 个已导入的项目目录
  2. 找到技术方案文件（docx/pdf）
  3. 提取文本（python-docx / pymupdf）
  4. AI 提取结构化信息（技术亮点/测试项目/关键指标/经验教训）
  5. 更新 presale_knowledge_case
"""
import os
import re
import sys
import time
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CASES_DIR = "/Users/flw/Desktop/售前项目汇总-100个匹配案例/售前项目汇总-100个匹配案例"
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

logging_setup = False


def get_logger():
    global logging_setup
    import logging
    if not logging_setup:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        logging_setup = True
    return logging.getLogger("extract_details")


def find_spec_file(dir_path):
    """找技术方案文件（docx/pdf/pptx），优先 docx。"""
    candidates = []
    for root, _, files in os.walk(dir_path):
        for f in files:
            fl = f.lower()
            if any(kw in f for kw in ["方案", "技术", "规格", "要求"]) and not f.startswith("."):
                if fl.endswith(".docx"):
                    candidates.append((10, os.path.join(root, f)))
                elif fl.endswith(".pdf"):
                    candidates.append((5, os.path.join(root, f)))
                elif fl.endswith(".pptx"):
                    candidates.append((3, os.path.join(root, f)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def extract_text_docx(file_path):
    """从 docx 提取文本。"""
    try:
        from docx import Document
        doc = Document(file_path)
        lines = []
        for p in doc.paragraphs:
            t = p.text.strip()
            if t and len(t) > 5:
                lines.append(t)
        # 也提取表格
        for table in doc.tables[:3]:
            for row in table.rows[:10]:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        return "\n".join(lines)[:3000]  # 截断
    except Exception as e:
        return ""


def extract_text_pdf(file_path):
    """从 pdf 提取文本。"""
    try:
        import fitz
        doc = fitz.open(file_path)
        lines = []
        for page in doc[:5]:
            t = page.get_text()
            if t:
                lines.append(t)
        doc.close()
        return "\n".join(lines)[:3000]
    except Exception:
        return ""


def extract_text_pptx(file_path):
    """从 pptx 提取文本。"""
    try:
        from pptx import Presentation
        prs = Presentation(file_path)
        lines = []
        for slide in prs.slides[:10]:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    lines.append(shape.text.strip())
        return "\n".join(lines)[:3000]
    except Exception:
        return ""


def extract_text(file_path):
    """根据文件类型提取文本。"""
    fl = file_path.lower()
    if fl.endswith(".docx"):
        return extract_text_docx(file_path)
    elif fl.endswith(".pdf"):
        return extract_text_pdf(file_path)
    elif fl.endswith(".pptx"):
        return extract_text_pptx(file_path)
    return ""


def extract_with_ai(text, case_name):
    """AI 从技术方案文本提取结构化信息。"""
    from app.services.ai_client_service import AIClientService
    import json

    ai = AIClientService()
    prompt = (
        "你是非标自动化测试设备行业的技术专家。从下面的技术方案文本中提取关键信息。\n\n"
        f"项目名：{case_name}\n"
        f"技术方案文本：\n\"\"\"\n{text[:2500]}\n\"\"\"\n\n"
        "严格只输出 JSON：\n"
        "{\n"
        '  "technical_highlights": "技术亮点（用顿号分隔，如：FPGA+ARM架构、96串电芯模拟、CANFD通讯、高压绝缘检测）",\n'
        '  "test_items": ["测试项目1", "测试项目2", "..."],\n'
        '  "key_specs": "关键技术指标（如：测试点数≥1280、节拍<50ms、精度0.1%）",\n'
        '  "equipment_type_detail": "设备类型细化（如：BMS功能测试/在线FCT/充放电老化/EOL下线检测）",\n'
        '  "lessons_learned": "这类项目的常见风险/难点/经验教训（基于方案内容推断）"\n'
        "}\n"
        "要求：基于文本真实提取，文本里没有的填 null，不要编造。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.2, max_tokens=600)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="深度提取技术方案")
    parser.add_argument("--limit", type=int, default=0, help="最多处理几个（0=全部）")
    parser.add_argument("--apply", action="store_true", help="更新数据库（默认 dry-run）")
    args = parser.parse_args()

    logger = get_logger()
    conn = sqlite3.connect(DB_PATH)

    # 找需要更新的案例（technical_highlights 为空的）
    rows = conn.execute(
        "SELECT id, case_name FROM presale_knowledge_case "
        "WHERE case_name NOT LIKE '%_name_%' "
        "AND (technical_highlights IS NULL OR technical_highlights = '' "
        "OR technical_highlights LIKE '设备类型%') "
        "ORDER BY id"
    ).fetchall()

    logger.info(f"待深度提取的案例：{len(rows)} 条")
    if args.limit > 0:
        rows = rows[:args.limit]
        logger.info(f"限制处理前 {args.limit} 条")

    processed = 0
    updated = 0
    no_file = 0
    no_text = 0
    ai_fail = 0

    for case_id, case_name in rows:
        # 找对应的项目目录
        project_dir = None
        for d in os.listdir(CASES_DIR):
            if case_name[:8] in d:  # 用项目名前8字匹配目录
                project_dir = os.path.join(CASES_DIR, d)
                break

        if not project_dir or not os.path.isdir(project_dir):
            no_file += 1
            continue

        # 找技术方案文件
        spec_file = find_spec_file(project_dir)
        if not spec_file:
            no_file += 1
            continue

        # 提取文本
        text = extract_text(spec_file)
        if not text or len(text) < 50:
            no_text += 1
            continue

        processed += 1
        logger.info(f"[{processed}/{len(rows)}] {case_name[:30]} ← {os.path.basename(spec_file)[:30]}")

        # AI 提取
        result = extract_with_ai(text, case_name)
        if not result.get("ok"):
            ai_fail += 1
            continue

        highlights = result.get("technical_highlights")
        test_items = result.get("test_items", [])
        key_specs = result.get("key_specs")
        lessons = result.get("lessons_learned")

        # 组合技术亮点
        highlight_parts = []
        if highlights:
            highlight_parts.append(highlights)
        if key_specs:
            highlight_parts.append(f"关键指标：{key_specs}")
        if test_items and isinstance(test_items, list):
            highlight_parts.append(f"测试项目：{'、'.join(test_items[:5])}")
        full_highlights = "。".join(highlight_parts) if highlight_parts else None

        if args.apply and full_highlights:
            conn.execute(
                "UPDATE presale_knowledge_case SET technical_highlights=?, lessons_learned=? WHERE id=?",
                (full_highlights[:500], lessons, case_id),
            )
            conn.commit()
            updated += 1
            logger.info(f"  ✓ 更新：{full_highlights[:60]}")
        elif full_highlights:
            logger.info(f"  → （dry-run）{full_highlights[:60]}")

    if args.apply:
        conn.commit()
    conn.close()

    logger.info(f"\n完成：处理 {processed}，更新 {updated}，无文件 {no_file}，无文本 {no_text}，AI失败 {ai_fail}")


if __name__ == "__main__":
    main()
