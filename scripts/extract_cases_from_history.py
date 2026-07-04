#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
售前弹药库 M1.2b：从历史项目抽取案例入库

把"已交付"的项目变成售前"弹药"。对每个后期项目（stage ∈ S7/S8/S9）：
  1. JOIN 客户/报价/报价明细/BOM，拼成完整项目上下文
  2. 调 AIClientService 让 AI 抽取结构化案例：
     technical_highlights / success_factors / lessons_learned / tags / project_summary
  3. 写入 presale_knowledge_case，带 source_project_id 关联回原项目

幂等：source_project_id 已存在的项目跳过（--force 强制重抽）。

运行：
    python scripts/extract_cases_from_history.py                 # dry-run 看会抽什么
    python scripts/extract_cases_from_history.py --apply         # 真正入库
    python scripts/extract_cases_from_history.py --apply --limit 3  # 先试 3 个
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

DEFAULT_DB_PATH = ROOT_DIR / "data" / "app.db"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("extract_cases")

# 后期/已交付阶段（参考 lifecycle.py S7=包装发运/S8=现场安装/S9=质保结项）
LATE_STAGES = ("S7", "S8", "S9")


def load_ai_client():
    try:
        from app.services.ai_client_service import AIClientService
        return AIClientService(), True
    except Exception as e:
        logger.warning(f"AI 客户端不可用: {e}")
        return None, False


def gather_project_context(conn, project: sqlite3.Row) -> dict:
    """JOIN 报价/BOM，拼出项目完整上下文供 AI 抽取。"""
    pid = project["id"]
    ctx = {
        "project_name": project["project_name"],
        "industry": project["industry"],
        "product_category": project["product_category"],
        "customer_name": project["customer_name"],
        "customer_industry": project["customer_industry"],
        "contract_amount": project["contract_amount"],
        "budget_amount": project["budget_amount"],
        "actual_cost": project["actual_cost"],
        "stage": project["stage"],
        "outcome": project["outcome"],
        "description": project["description"],
    }

    # 报价/成本/毛利（通过 customer → opportunity → quote → version 链）
    quote_rows = conn.execute(
        """
        SELECT qv.total_price, qv.cost_total, qv.gross_margin, qv.lead_time_days,
               COUNT(qi.id) AS item_count
        FROM customers c
        JOIN opportunities o ON o.customer_id = c.id
        JOIN quotes q ON q.opportunity_id = o.id
        JOIN quote_versions qv ON qv.quote_id = q.id
        LEFT JOIN quote_items qi ON qi.quote_version_id = qv.id
        WHERE c.id = ? AND qv.total_price > 0
        GROUP BY qv.id
        ORDER BY qv.total_price DESC
        LIMIT 3
        """,
        (project["customer_id"],),
    ).fetchall()
    if quote_rows:
        # 取最高价那版作为代表
        r = quote_rows[0]
        ctx["quote_total_price"] = r["total_price"]
        ctx["quote_cost_total"] = r["cost_total"]
        ctx["quote_gross_margin"] = r["gross_margin"]
        ctx["quote_lead_time_days"] = r["lead_time_days"]
        ctx["quote_item_count"] = r["item_count"]

    # BOM 关键部件（取 top 5 高金额件）
    bom_rows = conn.execute(
        """
        SELECT bi.material_name, bi.specification, bi.quantity, bi.unit_price, bi.amount,
               bi.is_key_item
        FROM bom_headers bh
        JOIN bom_items bi ON bi.bom_id = bh.id
        WHERE bh.project_id = ? AND bi.amount > 0
        ORDER BY bi.amount DESC
        LIMIT 8
        """,
        (pid,),
    ).fetchall()
    if bom_rows:
        ctx["key_components"] = [
            {
                "name": r["material_name"],
                "spec": r["specification"],
                "amount": r["amount"],
            }
            for r in bom_rows
        ]

    return ctx


def extract_with_ai(ai_client, ctx: dict) -> dict:
    """让 AI 从项目上下文抽取结构化案例字段。"""
    ctx_text = json.dumps(ctx, ensure_ascii=False, indent=2, default=str)
    prompt = (
        "你是非标自动化测试设备行业的资深售前/交付专家。"
        "下面是一个已完成项目的信息（含报价、关键部件）。请从中提炼出可复用的售前案例知识。\n\n"
        f"项目数据：\n{ctx_text}\n\n"
        "严格只输出 JSON，字段如下：\n"
        "{\n"
        '  "case_name": "简洁案例名（含设备类型+客户行业，20字内）",\n'
        '  "technical_highlights": "技术亮点（用顿号分隔，如：高压安全防护、多通道并行、自动校准）",\n'
        '  "success_factors": "成功要素（如有依据；项目信息不足就写 generic 的）",\n'
        '  "lessons_learned": "风险/教训（项目信息不足就写该类设备的通用风险）",\n'
        '  "project_summary": "一句话项目摘要（30字内）",\n'
        '  "tags": ["标签1", "标签2", ...],\n'
        '  "quality_score": 0.0到1.0之间的置信度（项目信息越完整越高）\n'
        "}\n"
        "要求：technical_highlights 和 lessons_learned 必须基于项目信息真实推断，"
        "结合设备类型（ICT/FCT/EOL/烧录/老化/视觉检测）的行业常识。"
    )
    try:
        result = ai_client.generate_solution(
            prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=600
        )
        raw = result.get("content") or result.get("text") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        return json.loads(raw)
    except Exception as e:
        logger.debug(f"AI 抽取失败: {e}")
        return {}


def fallback_extract(ctx: dict) -> dict:
    """AI 不可用时的规则兜底（质量低，仅占位）。"""
    cat = ctx.get("product_category") or "测试设备"
    ind = ctx.get("industry") or ctx.get("customer_industry") or "通用"
    return {
        "case_name": f"{ind}{cat}项目",
        "technical_highlights": f"{cat}相关技术",
        "project_summary": f"{ctx.get('customer_name', '某客户')}{cat}项目",
        "tags": [cat, ind],
        "quality_score": 0.3,
    }


def main():
    parser = argparse.ArgumentParser(description="从历史项目抽取案例入库")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--apply", action="store_true", help="真正入库（默认 dry-run）")
    parser.add_argument("--force", action="store_true", help="重抽已存在的案例")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--json", type=Path, help="导出抽取结果到 JSON 供 review")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # 选后期项目；排除已抽过的（除非 --force）
    placeholders = ",".join("?" for _ in LATE_STAGES)
    rows = conn.execute(
        f"""
        SELECT p.id, p.project_name, p.customer_name, p.industry, p.product_category,
               p.stage, p.outcome, p.contract_amount, p.budget_amount, p.actual_cost,
               p.description, p.customer_id, c.industry AS customer_industry
        FROM projects p
        LEFT JOIN customers c ON p.customer_id = c.id
        WHERE p.stage IN ({placeholders})
        ORDER BY p.id
        """,
        LATE_STAGES,
    ).fetchall()

    # 过滤已抽过的
    if not args.force:
        existing_ids = {
            r["source_project_id"]
            for r in conn.execute(
                "SELECT DISTINCT source_project_id FROM presale_knowledge_case "
                "WHERE source_project_id IS NOT NULL"
            ).fetchall()
        }
        rows = [r for r in rows if r["id"] not in existing_ids]

    if args.limit > 0:
        rows = rows[: args.limit]

    logger.info(f"待抽取项目: {len(rows)} 条 (apply={args.apply}, force={args.force})")

    ai_client, ai_ok = load_ai_client()
    results = []
    inserted = 0

    for r in rows:
        ctx = gather_project_context(conn, r)
        extracted = extract_with_ai(ai_client, ctx) if ai_ok else {}
        if not extracted:
            extracted = fallback_extract(ctx)

        # 合成最终案例（项目数据优先，AI 补全软性字段）
        case = {
            "case_name": extracted.get("case_name") or ctx["project_name"],
            "source_project_id": r["id"],
            "industry": ctx.get("industry") or ctx.get("customer_industry"),
            "equipment_type": ctx.get("product_category"),
            "customer_name": ctx.get("customer_name"),
            "project_amount": ctx.get("contract_amount") or ctx.get("quote_total_price"),
            "project_summary": extracted.get("project_summary"),
            "technical_highlights": extracted.get("technical_highlights"),
            "success_factors": extracted.get("success_factors"),
            "lessons_learned": extracted.get("lessons_learned"),
            "tags": extracted.get("tags"),
            "quality_score": extracted.get("quality_score", 0.5),
        }

        results.append(case)
        logger.info(
            f"[抽取] 项目#{r['id']} {r['project_name'][:25]} -> "
            f"{case['case_name']} | highlights={bool(case['technical_highlights'])}"
        )

        if args.apply:
            tags_json = json.dumps(case["tags"], ensure_ascii=False) if case["tags"] else None
            conn.execute(
                """
                INSERT INTO presale_knowledge_case
                (case_name, source_project_id, industry, equipment_type, customer_name,
                 project_amount, project_summary, technical_highlights, success_factors,
                 lessons_learned, tags, quality_score, is_public)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    case["case_name"], case["source_project_id"], case["industry"],
                    case["equipment_type"], case["customer_name"], case["project_amount"],
                    case["project_summary"], case["technical_highlights"],
                    case["success_factors"], case["lessons_learned"],
                    tags_json, case["quality_score"],
                ),
            )
            inserted += 1

    if args.apply:
        conn.commit()
        logger.info(f"已入库 {inserted} 条案例")

    conn.close()

    if args.json:
        args.json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"结果已导出到 {args.json}")
    else:
        # 打印前 3 条预览
        for c in results[:3]:
            print(json.dumps(c, ensure_ascii=False, indent=2, default=str))

    logger.info(f"完成: 共处理 {len(results)} 条")


if __name__ == "__main__":
    main()
