"""
报价对标分析模块。

让 AI 做方案时自动对标：
1. 案例报价（"瑞诺BMS ¥75.8万"）
2. 采购成本（"继电器模块 ¥715/套，48个样本"）
3. 标准模块价格（"电控柜+PLC ¥98000"）

产出：报价合理性分析 + 成本穿透 + 毛利预测
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService

logger = logging.getLogger("presale.benchmark")


def analyze_cost_benchmark(
    db: Session,
    ai: AIClientService,
    requirement_text: str,
    parsed: Dict[str, Any],
    deep_solution: Dict[str, Any],
    similar_cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    报价对标分析主入口。

    把 AI 方案里的报价/成本，和案例库+采购库做对比，
    告诉销售"这个报价合不合理/毛利多少/和类似项目比偏高还是偏低"。
    """
    # 1. 从方案里提取报价档位和成本分解
    tiers = deep_solution.get("tiers", [])
    cost_breakdown = deep_solution.get("cost_breakdown", [])
    equipment = deep_solution.get("equipment_selection", [])

    # 2. 查案例报价（类似项目的真实报价）
    case_prices = _get_case_prices(db, similar_cases)

    # 3. 查关键部件采购成本
    component_costs = _get_component_costs(db, equipment)

    # 4. AI 综合分析
    return _analyze_with_ai(
        ai, requirement_text, parsed,
        tiers, cost_breakdown, equipment,
        case_prices, component_costs,
    )


def _get_case_prices(db: Session, cases: List[Dict]) -> str:
    """查类似案例的真实报价。"""
    if not cases:
        return "（无相似案例报价数据）"

    lines = ["类似历史项目的真实报价："]
    for c in cases[:5]:
        amount = c.get("project_amount")
        if amount:
            won = "已签单" if c.get("is_won") == "是" else ""
            lines.append(
                f"- {c.get('case_name', '')[:30]}：¥{float(amount):,.0f} {won}"
            )
    return "\n".join(lines)


def _get_component_costs(db: Session, equipment: List[Dict]) -> str:
    """查关键部件的采购成本。"""
    if not equipment:
        return "（无设备选型数据）"

    lines = ["关键部件的历史采购成本："]
    for eq in equipment[:8]:
        item_name = eq.get("item", "")
        if not item_name:
            continue
        # 搜索标准成本库
        rows = db.execute(text(
            "SELECT cost_name, standard_cost, source_description FROM standard_costs "
            "WHERE is_active=1 AND (cost_name LIKE :kw OR specification LIKE :kw) "
            "ORDER BY standard_cost DESC LIMIT 3"
        ), {"kw": f"%{item_name[:8]}%"}).all()

        if rows:
            for r in rows:
                src = r[2] or ""
                cv_flag = ""
                if "CV=" in src:
                    try:
                        cv_val = float(src.split("CV=")[1].split("%")[0].split(",")[0])
                        if cv_val == 0:
                            cv_flag = "（✓价格稳定）"
                        elif cv_val > 50:
                            cv_flag = f"（⚠波动{cv_val}%）"
                    except Exception:
                        pass
                lines.append(f"- {r[0][:25]}：¥{float(r[1]):,.0f}/{r[0][-2:] if '/' in r[0] else '件'} {cv_flag}")
        else:
            lines.append(f"- {item_name[:25]}：（无历史采购数据）")

    return "\n".join(lines)


def _analyze_with_ai(
    ai: AIClientService,
    requirement_text: str,
    parsed: Dict,
    tiers: List,
    cost_breakdown: List,
    equipment: List,
    case_prices: str,
    component_costs: str,
) -> Dict[str, Any]:
    """AI 综合分析报价合理性。"""
    # 浓缩方案报价信息
    tiers_text = json.dumps(tiers[:3], ensure_ascii=False, default=str)
    cost_text = json.dumps(cost_breakdown[:5], ensure_ascii=False, default=str)
    eq_text = json.dumps(
        [{"item": e.get("item", ""), "qty": e.get("qty", "")} for e in equipment[:5]],
        ensure_ascii=False,
    )

    prompt = (
        "你是金凯博自动化的资深报价专家。分析当前方案报价的合理性，"
        "对比历史案例报价和采购成本，给出专业的报价建议。\n\n"
        f"## 客户需求\n{requirement_text[:200]}\n\n"
        f"## 方案报价档位\n{tiers_text}\n\n"
        f"## 成本分解\n{cost_text}\n\n"
        f"## 设备选型\n{eq_text}\n\n"
        f"## {case_prices}\n\n"
        f"## {component_costs}\n\n"
        "## 输出要求\n"
        "严格输出 JSON：\n"
        "{\n"
        '  "benchmark_analysis": "对标分析（当前报价 vs 历史案例，偏高/偏低/合理）",\n'
        '  "benchmarks": [\n'
        '    {"metric": "对比维度（如：标准型报价 vs 历史均价）", "current": "当前值", "historical": "历史值", "deviation": "偏差%", "verdict": "合理/偏高/偏低"}\n'
        "  ],\n"
        '  "cost_penetration": "成本穿透分析（报价里的关键部件成本 vs 采购均价，毛利空间）",\n'
        '  "margin_prediction": {"standard_margin": "标准型预估毛利率%", "risk_margin": "风险点（哪些成本可能超支）"},\n'
        '  "pricing_advice": "报价建议（该坚持/可让步/必须加价的点）",\n'
        '  "confidence_factors": ["影响报价信心的因素（如：案例样本少/部件价格波动大/旧设备改造不确定）"]\n'
        "}\n"
        "要求：基于历史数据真实分析，没有数据的维度标 null。deviation 算出具体百分比。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=1500)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        result["ai_model"] = resp.get("model")
        return result
    except Exception as e:
        logger.warning("报价对标分析失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "benchmarks": []}


def _step_cost_benchmark(
    db: Session,
    ai: AIClientService,
    requirement_text: str,
    parsed: Dict[str, Any],
    deep_solution: Dict[str, Any],
    similar_cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Step 8.6: 报价对标分析。"""
    try:
        return analyze_cost_benchmark(
            db, ai, requirement_text, parsed,
            deep_solution, similar_cases,
        )
    except Exception as e:
        logger.warning("Step8.6 报价对标失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "benchmarks": []}
