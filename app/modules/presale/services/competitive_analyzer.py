# -*- coding: utf-8 -*-
"""
售前竞争分析引擎。

基于三个数据源产出竞争分析：
  ① 金凯博优势产品库（advantage_products，133条，我方真实技术实力）
  ② 竞争对手库（competitors，对手的弱点+应对策略）
  ③ 项目需求（客户要什么，匹配我们的什么优势）

产出：
  - 我方技术卖点（基于优势产品库，针对这个项目）
  - 选我们的理由（vs 对手）
  - 销售话术（应对价格/技术/交期质疑）
  - 对手弱点（怎么打）
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService

logger = logging.getLogger("presale.competitive")


def analyze_competition(
    db: Session,
    ai: AIClientService,
    requirement_text: str,
    parsed: Dict[str, Any],
    deep_solution: Dict[str, Any],
    competitors_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    竞争分析主入口。

    Args:
        competitors_hint: 销售已知的竞争对手（如"这次对手是XX公司和YY公司"）
    """
    # 1. 查优势产品库（匹配项目需求）
    our_products = _query_advantage_products(db, requirement_text, parsed)

    # 2. 查竞争对手库
    competitors = _query_competitors(db)

    # 3. AI 综合分析
    return _analyze_with_ai(ai, requirement_text, parsed, deep_solution, our_products, competitors, competitors_hint)


def _query_advantage_products(db: Session, requirement_text: str, parsed: Dict) -> str:
    """查优势产品库，返回给 AI 的文本摘要。"""
    eq = parsed.get("equipment_type", "")
    keyword = eq or requirement_text[:20]
    rows = db.execute(text(
        "SELECT product_code, product_name, description, test_types, max_throughput_uph "
        "FROM advantage_products WHERE is_active=1 "
        "AND (product_name LIKE :kw OR description LIKE :kw OR test_types LIKE :kw) "
        "LIMIT 10"
    ), {"kw": f"%{keyword}%"}).all()

    if not rows:
        # 关键词没匹配，取全量前 8
        rows = db.execute(text(
            "SELECT product_code, product_name, description, test_types, max_throughput_uph "
            "FROM advantage_products WHERE is_active=1 LIMIT 8"
        )).all()

    if not rows:
        return "（优势产品库暂无数据）"

    lines = ["金凯博优势产品库（我方真实技术实力）："]
    for r in rows:
        desc = f" - {r[2][:40]}" if r[2] else ""
        uph = f" UPH{r[4]}" if r[4] else ""
        lines.append(f"- {r[1]}（{r[0]}）{desc}{uph}")
    return "\n".join(lines)


def _query_competitors(db: Session) -> str:
    """查竞争对手库。"""
    rows = db.execute(text(
        "SELECT name, short_name, competitor_type, strengths, weaknesses, "
        "price_level, counter_strategy FROM competitors WHERE is_active=1"
    )).all()

    if not rows:
        return "（竞争对手库暂无数据，请基于行业通用竞品画像分析）"

    lines = ["已知竞争对手（从库中匹配）："]
    for r in rows:
        lines.append(
            f"- {r[0]}（{r[1] or ''}，类型:{r[2] or ''}）"
            f"\n  优势：{r[3] or '未知'}"
            f"\n  弱点：{r[4] or '未知'}"
            f"\n  价格水平：{r[5] or '未知'}"
            f"\n  应对策略：{r[6] or '未知'}"
        )
    return "\n".join(lines)


def _analyze_with_ai(
    ai: AIClientService,
    requirement_text: str,
    parsed: Dict,
    deep_solution: Dict,
    our_products: str,
    competitors: str,
    competitors_hint: Optional[str],
) -> Dict[str, Any]:
    """AI 综合产出竞争分析。"""
    # 浓缩方案关键信息
    ds = deep_solution or {}
    solution_brief = json.dumps({
        "架构": ds.get("system_architecture", ""),
        "报价档位": ds.get("tiers", [])[:3],
        "交付周期": ds.get("implementation_phases", [])[:3],
    }, ensure_ascii=False, default=str)

    hint_text = f"\n销售补充：{competitors_hint}" if competitors_hint else ""

    prompt = (
        "你是金凯博自动化测试公司的资深销售总监 + 竞争情报专家。"
        "基于客户需求、我方优势产品库、竞争对手信息，产出针对性的竞争分析。\n\n"
        f"## 客户需求\n{requirement_text[:300]}\n\n"
        f"## 结构化需求\n行业:{parsed.get('industry','')} 设备:{parsed.get('equipment_type','')}\n\n"
        f"## 我方方案概要\n{solution_brief}\n\n"
        f"{our_products}\n\n"
        f"{competitors}{hint_text}\n\n"
        "## 输出要求\n"
        "严格输出 JSON：\n"
        "{\n"
        '  "our_selling_points": [\n'
        '    {"point": "卖点（如：双工位并行设计UPH提升50%）", "evidence": "依据（引用优势产品型号/案例）", '
        '"customer_value": "对客户的价值"}\n'
        "  ],\n"
        '  "why_choose_us": [\n'
        '    {"reason": "选我们的理由", "vs_competitor": "相比对手的优势（对手做不到/做得差的）"}\n'
        "  ],\n"
        '  "sales_scripts": {\n'
        '    "price_objection": "应对价格质疑的话术（客户说太贵了怎么回）",\n'
        '    "technical_objection": "应对技术质疑的话术（客户质疑技术能力怎么回）",\n'
        '    "delivery_objection": "应对交期质疑的话术（客户说对手更快怎么回）",\n'
        '    "opening": "开场白（30秒讲清我们是谁+为什么选我们）"\n'
        "  },\n"
        '  "competitor_weaknesses": [\n'
        '    {"competitor": "对手名/类型", "weakness": "弱点", "how_to_exploit": "怎么利用这个弱点"}\n'
        "  ],\n"
        '  "must_emphasize": ["本次竞标必须重点强调的3个点"]\n'
        "}\n\n"
        "要求：\n"
        "1. our_selling_points 必须引用我方优势产品库的具体型号/能力，不能空泛\n"
        "2. 如果有竞争对手库数据，why_choose_us 要针对性对比（vs 具体对手）；没有就 vs 通用对手画像\n"
        "3. sales_scripts 的话术要像真人销售说的，口语化，不是书面语\n"
        "4. must_emphasize 只给最关键的 3 个，不要贪多\n"
        "5. 竞争对手库无数据时，基于行业通用画像分析（外资大厂交期长/小厂质量不稳/价格杀手售后差）"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.4, max_tokens=2000)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        result["ai_model"] = resp.get("model")
        return result
    except Exception as e:
        logger.warning("竞争分析失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "our_selling_points": [], "sales_scripts": {}}
