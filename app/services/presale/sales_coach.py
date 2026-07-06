# -*- coding: utf-8 -*-
"""
销售教练引擎（Sales Coach）。

让 AI 像金凯博的老法师一样，手把手教新手销售：
  - 客户线索解读：这个客户/需求的关键点是什么、该问什么
  - 技术门槛提示：这个需求的技术难点在哪、我们能不能做
  - 案例弹药：我们做过类似的吗、客户行业我们熟不熟
  - 对手预警：这个项目可能遇到谁、怎么打
  - 注意事项：哪些坑要避免、哪些信息必须确认

与售前智能体的区别：
  - 售前智能体产出"给客户看的方案"
  - 销售教练产出"给销售看的指导"——教销售怎么沟通、怎么赢

四种模式：
  1. lead_analysis（线索解读）：销售刚接到客户，不知道怎么开始
  2. meeting_prep（会前准备）：要去见客户了，该准备什么
  3. field_qa（现场答疑）：客户问了技术问题，快速给专业回答
  4. review_coaching（复盘辅导）：沟通完了，哪里做得好/哪里漏了
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService

logger = logging.getLogger("presale.coach")


def coach_sales(
    db: Session,
    ai: AIClientService,
    sales_input: str,
    mode: str = "lead_analysis",
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    销售教练主入口。

    Args:
        sales_input: 销售输入（客户线索/问题/会议记录）
        mode: lead_analysis / meeting_prep / field_qa / review_coaching
        history: 对话历史（多轮辅导）
    """
    # 1. 查相关数据（案例/产品/对手）
    context = _gather_context(db, sales_input)

    # 2. 按模式选 prompt
    prompt_builder = MODE_PROMPTS.get(mode, MODE_PROMPTS["lead_analysis"])
    prompt = prompt_builder(sales_input, context, history or [])

    # 3. AI 生成指导
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.4, max_tokens=2500)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        result["mode"] = mode
        result["ai_model"] = resp.get("model")
        return result
    except Exception as e:
        logger.warning("销售教练失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "mode": mode}


def _gather_context(db: Session, sales_input: str) -> str:
    """查相关案例/产品/对手，给教练当参考。"""
    lines = []

    # 查相似案例
    cases = db.execute(text(
        "SELECT case_name, industry, equipment_type, customer_name, technical_highlights, lessons_learned "
        "FROM presale_knowledge_case WHERE is_public=1 "
        "AND case_name NOT LIKE '%_name_%' "
        f"AND (case_name LIKE '%{sales_input[:15]}%' OR equipment_type LIKE '%{sales_input[:10]}%' "
        f"OR industry LIKE '%{sales_input[:8]}%') LIMIT 5"
    )).all()
    if cases:
        lines.append("相关历史案例：")
        for c in cases:
            lines.append(f"- {c[0]}（{c[2] or ''}/{c[1] or ''}）客户:{c[3] or ''}")
            if c[4]:
                lines.append(f"  技术：{c[4][:60]}")
            if c[5]:
                lines.append(f"  教训：{c[5][:60]}")

    # 查优势产品
    products = db.execute(text(
        "SELECT product_code, product_name, description FROM advantage_products "
        f"WHERE is_active=1 AND (product_name LIKE '%{sales_input[:10]}%' OR description LIKE '%{sales_input[:10]}%') LIMIT 5"
    )).all()
    if products:
        lines.append("\n金凯博相关产品：")
        for p in products:
            lines.append(f"- {p[1]}（{p[0]}）：{(p[2] or '')[:50]}")

    # 查对手
    competitors = db.execute(text(
        "SELECT name, weaknesses, counter_strategy FROM competitors "
        f"WHERE is_active=1 AND (good_at LIKE '%{sales_input[:8]}%' OR name LIKE '%{sales_input[:6]}%') LIMIT 3"
    )).all()
    if competitors:
        lines.append("\n可能遇到的竞争对手：")
        for c in competitors:
            lines.append(f"- {c[0]}：弱点={c[1] or ''}；怎么打={c[2] or ''}")

    return "\n".join(lines) if lines else "（无直接匹配的历史数据）"


# ============= 四种模式的 prompt =============

def _lead_analysis_prompt(sales_input: str, context: str, history: list) -> str:
    return (
        "你是金凯博自动化测试公司的资深销售总监（10年+非标自动化行业经验），"
        "正在手把手教一个新手销售。销售刚接到一个客户线索，不知道怎么开始。\n\n"
        f"## 销售的输入\n{sales_input}\n\n"
        f"## 参考数据\n{context}\n\n"
        "## 输出要求（严格JSON）\n"
        "{\n"
        '  "quick_read": "30秒快速解读：这个客户/需求是什么情况（一句话让销售不懵）",\n'
        '  "what_to_ask": [\n'
        '    {"question": "必须问客户的问题（带选项）", "why": "为什么必须问这个", "priority": "必问/重要"}\n'
        "  ],\n"
        '  "tech_basics": "技术入门：这个需求的技术原理是什么（用销售能懂的大白话解释，不用专业术语）",\n'
        '  "our_strength": "我们在这种需求上有什么优势/案例（给销售信心）",\n'
        '  "red_flags": ["⚠️ 注意事项/坑（这种项目容易出什么问题）"],\n'
        '  "next_steps": ["具体下一步：销售该做什么（1.打回访电话问XX 2.准备XX资料 3.约技术交流会）"],\n'
        '  "talking_points": "给销售的开场话术（打电话/微信第一句话怎么说）"\n'
        "}\n"
        "要求：what_to_ask 至少 5 个问题，覆盖技术参数/产能/预算/时间/决策人；"
        "tech_basics 要像教小白一样解释；talking_points 要像真人说的口语。"
    )


def _meeting_prep_prompt(sales_input: str, context: str, history: list) -> str:
    return (
        "你是金凯博的资深销售总监。销售要去见客户了，你帮他做会前准备。\n\n"
        f"## 销售的输入（客户信息/需求）\n{sales_input}\n\n"
        f"## 参考数据\n{context}\n\n"
        "## 输出要求（严格JSON）\n"
        "{\n"
        '  "client_analysis": "客户分析：这个行业/这类客户的特点、关注什么、采购流程",\n'
        '  "meeting_objectives": ["本次会议目标（3-5个，按优先级）"],\n'
        '  "must_bring": ["必须带的资料/样品（方案PPT/案例/产品手册等）"],\n'
        '  "anticipated_questions": [\n'
        '    {"question": "客户可能问的问题", "how_to_answer": "该怎么回答", "difficulty": "easy/hard"}\n'
        "  ],\n"
        '  "competitive_alert": "对手预警：这种项目可能遇到哪个对手、我们的差异点",\n'
        '  "opening_pitch": "开场白（前3分钟怎么说，建立专业形象）",\n'
        '  "closing_strategy": "收尾策略（怎么约定下一步/怎么要决策）"\n'
        "}\n"
        "anticipated_questions 至少 5 个；opening_pitch 要口语化。"
    )


def _field_qa_prompt(sales_input: str, context: str, history: list) -> str:
    return (
        "你是金凯博的技术专家。销售在客户现场被问到了技术问题，需要快速给出专业回答。\n"
        "注意：回答要让销售能直接转述给客户，不能太长，要专业且有信心。\n\n"
        f"## 客户的问题\n{sales_input}\n\n"
        f"## 参考数据\n{context}\n\n"
        "## 输出要求（严格JSON）\n"
        "{\n"
        '  "direct_answer": "直接回答（销售能转述给客户的版本，2-3句话，专业且自信）",\n'
        '  "technical_detail": "技术细节（如果客户追问，更深层的解释）",\n'
        '  "our_advantage": "借机强调我们的优势（回答完顺便秀肌肉）",\n'
        '  "if_not_sure": "如果真答不上来的话术（诚实但有策略地处理）"\n'
        "}\n"
        "direct_answer 必须能在30秒内说完，口语化。"
    )


def _review_coaching_prompt(sales_input: str, context: str, history: list) -> str:
    return (
        "你是金凯博的销售总监。销售刚和客户沟通完，你帮他复盘。\n\n"
        f"## 销售的沟通记录/感受\n{sales_input}\n\n"
        f"## 参考数据\n{context}\n\n"
        "## 输出要求（严格JSON）\n"
        "{\n"
        '  "what_went_well": ["做得好的地方（鼓励销售）"],\n'
        '  "what_was_missed": [\n'
        '    {"missed": "漏掉的关键信息/问题", "importance": "high/medium", "how_to_follow_up": "怎么补救（下次问or电话补问）"}\n'
        "  ],\n"
        '  "client_read": "客户状态研判：意向度/决策周期/可能的顾虑",\n'
        '  "improvement_points": ["这个销售可以提升的地方（帮他成长）"],\n'
        '  "next_actions": ["下一步行动（带时间节点）"]\n'
        "}\n"
        "要具体、有建设性，像真人师傅一样既鼓励又指出问题。"
    )


MODE_PROMPTS = {
    "lead_analysis": _lead_analysis_prompt,
    "meeting_prep": _meeting_prep_prompt,
    "field_qa": _field_qa_prompt,
    "review_coaching": _review_coaching_prompt,
}

MODE_DESCRIPTIONS = {
    "lead_analysis": "线索解读（刚接到客户，不知道怎么开始）",
    "meeting_prep": "会前准备（要去见客户了）",
    "field_qa": "现场答疑（客户问了技术问题）",
    "review_coaching": "复盘辅导（沟通完了，总结提升）",
}
