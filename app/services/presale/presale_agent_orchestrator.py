# -*- coding: utf-8 -*-
"""
售前智能体编排器（M3）

把分散的售前 AI 能力串成一条固定主干流程，给销售/售前工程师一键生成完整售前分析。

6 步固定主干（MVP 版，不做自主 Agent 循环——那是 P1 的事）：
  1. 需求理解   AI 把自然语言需求拆成结构化字段（设备类型/行业/关键指标/规模/特殊要求）
  2. 弹药检索   用结构化字段调 AmmoLibraryService.search_ammo，召回相似案例+报价区间
  3. 方案生成   AI 基于需求+检索到的案例，生成初步技术方案（架构/关键模块/测试策略）
  4. BOM 模板   推荐标准模块 + 估算关键部件清单
  5. 报价区间   从弹药库 quote_range 给出同类设备历史报价/毛利/交期区间
  6. 风险提示   AI 结合案例的 lessons_learned + 需求特点，给关键风险和验收难点

特点：
  - 每步独立可恢复：失败不影响其他步（某步 AI 失败只返回 error，整体不挂）
  - 渐进式返回：通过 ai_job_service 的 progress 字段反映进度（10/25/40/55/70/85/100）
  - 复用现成地基：AIClientService + AmmoLibraryService（M1 产物）
  - 不碰死代码 PresaleAIWorkflowLog（那个绑 ticket_id 太重，留到有 ticket 上下文时再用）

注册为 ai_job_service 的 "presale_agent" handler。
端点：POST /ai-jobs/presale-agent
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.services.ai_client_service import AIClientService
from app.services.presale.ammo_library_service import AmmoLibraryService

logger = logging.getLogger("presale.agent")


# 设备类型白名单（用于校验 AI 抽取结果，对齐 backfill 脚本）
EQUIPMENT_TYPES = {
    "ICT测试", "FCT测试", "EOL测试", "烧录设备", "老化设备", "视觉检测",
    "ICT测试设备", "FCT测试设备", "EOL测试设备", "AOI检测设备",
    "BMS测试", "电驱测试", "功率器件测试", "压缩机测试", "电子负载",
}


def run_presale_agent(
    db,
    params: Dict[str, Any],
    user_id: Optional[int] = None,
    job_id: Optional[int] = None,
    enable_deep_risk: bool = False,
) -> Dict[str, Any]:
    """
    售前智能体主入口（注册为 ai_job handler）。

    params:
        requirement_text: str       客户原始需求（必填）
        customer_id: int            可选，关联客户（用于检索该客户历史）
        industry_hint: str          可选，行业提示
        equipment_hint: str         可选，设备类型提示
        enable_deep_risk: bool      可选，True 时启用 Step7 自主风险深挖（ReAct）
    job_id:
        ai_generation_jobs.id，用于埋点关联（可选）
    """
    started = time.time()
    requirement_text = (params.get("requirement_text") or "").strip()
    if not requirement_text:
        raise ValueError("requirement_text 不能为空")

    customer_id = params.get("customer_id")
    industry_hint = params.get("industry_hint")
    equipment_hint = params.get("equipment_hint")
    # enable_deep_risk / enable_deep_solution 可来自 params
    if not enable_deep_risk:
        enable_deep_risk = bool(params.get("enable_deep_risk", False))
    enable_deep_solution = bool(params.get("enable_deep_solution", False))

    ai = AIClientService()
    ammo = AmmoLibraryService(db)

    result: Dict[str, Any] = {
        "requirement_text": requirement_text,
        "customer_id": customer_id,
        "steps": {},
        "timings": {},
    }

    metric_status = "SUCCESS"
    metric_error = None
    try:
        # ============= Step 1: 需求理解 =============
        t0 = time.time()
        step1 = _step_understand_requirement(ai, requirement_text, industry_hint, equipment_hint)
        result["steps"]["understand_requirement"] = step1
        result["timings"]["understand_requirement"] = round(time.time() - t0, 2)
        _log_step(1, "需求理解", step1)

        # 从结构化结果取检索用的 industry/equipment_type
        parsed = step1.get("parsed", {})
        industry = parsed.get("industry") or industry_hint
        equipment_type = _normalize_equipment(parsed.get("equipment_type") or equipment_hint)

        # ============= Step 2: 弹药检索 =============
        t0 = time.time()
        step2 = _step_retrieve_ammo(ammo, requirement_text, industry, equipment_type)
        result["steps"]["retrieve_ammo"] = step2
        result["timings"]["retrieve_ammo"] = round(time.time() - t0, 2)
        _log_step(2, "弹药检索", {"cases": len(step2.get("similar_cases", [])),
                                  "quote_samples": step2.get("quote_range", {}).get("sample_count")})

        # ============= Step 3: 方案生成 =============
        t0 = time.time()
        step3 = _step_generate_solution(ai, parsed, step2.get("similar_cases", []), requirement_text)
        result["steps"]["generate_solution"] = step3
        result["timings"]["generate_solution"] = round(time.time() - t0, 2)
        _log_step(3, "方案生成", {"ok": step3.get("ok", False)})

        # ============= Step 4: BOM 模板推荐 =============
        t0 = time.time()
        step4 = _step_recommend_bom(step2.get("standard_modules", []), parsed, ai)
        result["steps"]["recommend_bom"] = step4
        result["timings"]["recommend_bom"] = round(time.time() - t0, 2)
        _log_step(4, "BOM模板", {"modules": len(step4.get("modules", []))})

        # ============= Step 5: 报价区间 =============
        t0 = time.time()
        step5 = _step_quote_range(ammo, industry, equipment_type, step2.get("quote_range"))
        result["steps"]["quote_range"] = step5
        result["timings"]["quote_range"] = round(time.time() - t0, 2)
        _log_step(5, "报价区间", {"samples": step5.get("sample_count")})

        # ============= Step 6: 风险提示 =============
        t0 = time.time()
        step6 = _step_risk_warnings(ai, parsed, step2.get("similar_cases", []), requirement_text)
        result["steps"]["risk_warnings"] = step6
        result["timings"]["risk_warnings"] = round(time.time() - t0, 2)
        _log_step(6, "风险提示", {"risks": len(step6.get("risks", []))})

        # ============= Step 7: 自主风险深挖（ReAct，可选） =============
        if enable_deep_risk:
            t0 = time.time()
            step7 = _step_deep_risk_analysis(db, ai, parsed, requirement_text, step6)
            result["steps"]["deep_risk_analysis"] = step7
            result["timings"]["deep_risk_analysis"] = round(time.time() - t0, 2)
            _log_step(7, "自主风险深挖", {
                "ok": step7.get("ok"),
                "tool_calls": len(step7.get("tool_calls", [])),
            })

        # ============= Step 8: 深度方案生成（自主多轮，可选） =============
        if enable_deep_solution:
            t0 = time.time()
            step8 = _step_deep_solution(
                db, ai, parsed, requirement_text,
                # 复用前面已查到的产物，避免重复检索
                cases=step2.get("similar_cases", []),
                modules=step2.get("standard_modules", []) or step4.get("modules", []),
                quote_range=step5,
                risks=step6.get("risks", []),
                deep_risks=(step7.get("deep_risks", []) if enable_deep_risk else []),
            )
            result["steps"]["deep_solution"] = step8
            result["timings"]["deep_solution"] = round(time.time() - t0, 2)
            _log_step(8, "深度方案生成", {
                "ok": step8.get("ok"),
                "tool_calls": len(step8.get("tool_calls", [])),
                "subsystems": len(step8.get("subsystems", [])),
            })

        # ============= Step 8.5: 竞争分析（深度方案时自动做） =============
        if enable_deep_solution:
            t0 = time.time()
            from app.services.presale.competitive_analyzer import analyze_competition
            step_comp = analyze_competition(
                db, ai, requirement_text, parsed,
                step8 if step8.get("ok") else {},
                params.get("competitors_hint"),
            )
            result["steps"]["competitive_analysis"] = step_comp
            result["timings"]["competitive_analysis"] = round(time.time() - t0, 2)
            _log_step("8.5", "竞争分析", {
                "ok": step_comp.get("ok"),
                "selling_points": len(step_comp.get("our_selling_points", [])),
            })

        # ============= Step 9: 可视化方案包（整线项目，可选） =============
        # 触发条件：深度方案开启 + 整线项目（project_type 或关键词判断）
        _project_type = (parsed or {}).get("project_type", "")
        is_line = _project_type == "整线" or any(
            kw in requirement_text for kw in ["整线", "自动化线", "产线", "生产线", "DIP线", "SMT线", "工站"]
        )
        if enable_deep_solution and is_line:
            stations_data = step8.get("line_stations", []) if step8.get("ok") else []
            # 即使工位数据为空也尝试（模板会从 equipment/subsystems 兜底）
            t0 = time.time()
            try:
                from app.services.presale.layout_html_generator import (
                    render_layout_html, generate_layout_with_ai,
                    render_spec_html, render_gantt_html, render_response_html_with_ai,
                )
                project_name = requirement_text[:20]
                summary = requirement_text[:80]
                ds_data = step8 if step8.get("ok") else {}

                htmls = {}
                # 布局图
                layout = generate_layout_with_ai(ai, requirement_text, stations_data, project_name)
                if not layout and stations_data:
                    layout = render_layout_html(project_name, summary, stations_data, ds_data.get("customer_equipment_integration", []))
                htmls["layout_html"] = layout or ""
                # 规格书 + 甘特图（模板，快）
                htmls["spec_html"] = render_spec_html(project_name, summary, ds_data, parsed)
                htmls["gantt_html"] = render_gantt_html(project_name, summary, ds_data)
                # 响应表（AI，耗时长，失败不影响）
                try:
                    htmls["response_html"] = render_response_html_with_ai(ai, project_name, requirement_text[:800], ds_data) or ""
                except Exception:
                    htmls["response_html"] = ""

                result["steps"]["layout_html"] = {
                    "ok": True,
                    "html": htmls.get("layout_html", ""),  # 兼容前端
                    **htmls,
                    "method": "ai+template",
                }
                result["timings"]["layout_html"] = round(time.time() - t0, 2)
                _log_step(9, "可视化方案包", {
                    "layout": bool(htmls.get("layout_html")),
                    "spec": bool(htmls.get("spec_html")),
                    "gantt": bool(htmls.get("gantt_html")),
                    "response": bool(htmls.get("response_html")),
                })
            except Exception as e:
                logger.warning("Step9 可视化方案包失败: %s", e)

        result["total_time"] = round(time.time() - started, 2)
        result["summary"] = _build_overall_summary(result)
        logger.info("[售前智能体] 完成 总耗时=%ss 步骤耗时=%s", result["total_time"], result["timings"])
        return result
    except Exception as e:
        metric_status = "FAILED"
        metric_error = str(e)[:500]
        raise
    finally:
        # 无论成功失败都落埋点（失败时 result 可能不完整，尽最大努力记）
        try:
            _record_metric(
                db, result, job_id, user_id, requirement_text,
                started, metric_status, metric_error,
            )
        except Exception as metric_err:
            logger.warning("[售前智能体] 埋点写入失败（不影响主流程）: %s", metric_err)


# ==================== 各步骤实现 ====================

def _step_understand_requirement(
    ai: AIClientService, requirement_text: str,
    industry_hint: Optional[str], equipment_hint: Optional[str],
) -> Dict[str, Any]:
    """Step 1: AI 把自然语言需求拆成结构化字段。"""
    prompt = (
        "你是非标自动化测试设备行业的资深售前工程师。把客户的原始需求拆成结构化字段。\n\n"
        f"客户原始需求：\n\"\"\"\n{requirement_text}\n\"\"\"\n\n"
    )
    if industry_hint or equipment_hint:
        prompt += f"提示信息：行业={industry_hint or '未知'}，设备类型={equipment_hint or '未知'}\n\n"
    prompt += (
        "严格只输出 JSON：\n"
        "{\n"
        '  "industry": "行业（新能源汽车/动力电池/消费电子/通信设备/电子制造/智能家电/汽车电子/医疗电子等）",\n'
        '  "equipment_type": "设备类型（ICT测试/FCT测试/EOL测试/烧录设备/老化设备/视觉检测/BMS测试/电驱测试/功率器件测试等）",\n'
        '  "key_specs": ["关键技术指标，如：800V高压、1000A电流、节拍15s、精度0.1%等"],\n'
        '  "scale": "规模（如：单工位/多工位/产线/实验室级）",\n'
        '  "special_requirements": ["特殊要求，如：高低温环境/防爆/追溯/通讯协议等"],\n'
        '  "acceptance_focus": ["客户可能的验收关注点"],\n'
        '  "confidence": 0.0-1.0\n'
        "}\n"
        "无法判断的字段填 null。key_specs/acceptance_focus 基于需求文本真实抽取，别瞎编。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.2, max_tokens=500)
        parsed = _extract_json(resp.get("content") or "")
        return {
            "ok": True,
            "parsed": parsed,
            "ai_model": resp.get("model"),
        }
    except Exception as e:
        logger.warning("Step1 需求理解失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "parsed": {}}


def _step_retrieve_ammo(
    ammo: AmmoLibraryService, query: str,
    industry: Optional[str], equipment_type: Optional[str],
) -> Dict[str, Any]:
    """Step 2: 调弹药库检索相似案例 + 报价区间。"""
    try:
        r = ammo.search_ammo(query, industry=industry, equipment_type=equipment_type, top_k=5)
        return {
            "ok": True,
            "similar_cases": r.get("similar_cases", []),
            "quote_range": r.get("quote_range", {}),
            "solution_templates": r.get("solution_templates", []),
            "standard_modules": r.get("standard_modules", []),
            "ammo_summary": r.get("summary"),
        }
    except Exception as e:
        logger.warning("Step2 弹药检索失败: %s", e)
        return {"ok": False, "error": str(e)[:200],
                "similar_cases": [], "quote_range": {}, "standard_modules": []}


def _step_generate_solution(
    ai: AIClientService, parsed: Dict[str, Any],
    cases: List[Dict[str, Any]], requirement_text: str,
) -> Dict[str, Any]:
    """Step 3: AI 基于需求+历史案例生成初步技术方案。"""
    cases_brief = "\n".join(
        f"- {c.get('case_name', '')}（{c.get('equipment_type', '')}）：{c.get('technical_highlights', '')[:80]}"
        for c in cases[:3]
    ) or "（无相似历史案例）"

    prompt = (
        "你是非标自动化测试设备售前工程师。基于客户需求和相似历史案例，生成初步技术方案。\n\n"
        f"客户需求：{requirement_text}\n\n"
        f"需求结构化：{parsed}\n\n"
        f"相似历史案例：\n{cases_brief}\n\n"
        "严格只输出 JSON：\n"
        "{\n"
        '  "architecture": "系统架构概述（2-3句，如：基于PXIe的模块化测试平台+高压安全回路+上位机软件）",\n'
        '  "key_modules": ["关键模块/子系统，如：高压电源/电子负载/数据采集/安全互锁/上位机"],\n'
        '  "test_strategy": "测试策略与流程概述",\n'
        '  "key_equipment": ["关键设备/仪器选型建议，如：可编程直流电源/功率分析仪/示波器"],\n'
        '  "software": "软件/控制系统方案概述",\n'
        '  "differentiation": "相比通用方案的差异化点"\n'
        "}\n"
        "方案必须基于需求里的技术指标（电压/电流/节拍等），别空泛。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.4, max_tokens=800)
        sol = _extract_json(resp.get("content") or "")
        return {"ok": True, "solution": sol, "ai_model": resp.get("model")}
    except Exception as e:
        logger.warning("Step3 方案生成失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "solution": {}}


def _step_recommend_bom(
    modules: List[Dict[str, Any]], parsed: Dict[str, Any], ai: AIClientService,
) -> Dict[str, Any]:
    """Step 4: 基于标准模块库 + 需求，推荐 BOM 模板（轻量，不强 AI）。"""
    # 标准模块直接复用 step2 检索结果，补一个总成本估算
    total_ref = sum((m.get("ref_cost") or 0) for m in modules)
    return {
        "ok": True,
        "modules": modules,
        "ref_cost_sum": total_ref,
        "note": (
            f"基于标准模块库推荐 {len(modules)} 个模块，参考成本合计 {total_ref} 元"
            if modules else "无匹配标准模块，建议人工评估"
        ),
    }


def _step_quote_range(
    ammo: AmmoLibraryService, industry: Optional[str],
    equipment_type: Optional[str], step2_range: Dict[str, Any],
) -> Dict[str, Any]:
    """Step 5: 报价区间（直接复用 step2 已查的，必要时补查精确区间）。"""
    if step2_range and step2_range.get("sample_count"):
        return {"ok": True, **step2_range}
    # step2 没数据（可能 industry/equipment 都没过滤命中），补一次无过滤全局查
    try:
        qr = ammo.quote_range(industry=industry, equipment_type=equipment_type)
        return {"ok": True, **qr}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _step_risk_warnings(
    ai: AIClientService, parsed: Dict[str, Any],
    cases: List[Dict[str, Any]], requirement_text: str,
) -> Dict[str, Any]:
    """Step 6: AI 结合案例教训 + 需求特点，给关键风险和验收难点。"""
    lessons = "\n".join(
        f"- {c.get('case_name', '')}：{c.get('lessons_learned', '')[:100]}"
        for c in cases[:3] if c.get("lessons_learned")
    ) or "（无历史教训数据）"

    prompt = (
        "你是非标自动化测试设备的资深交付/质量专家。基于客户需求和相似项目的教训，"
        "列出关键风险和验收难点。\n\n"
        f"客户需求：{requirement_text}\n"
        f"结构化需求：{parsed}\n\n"
        f"历史项目教训：\n{lessons}\n\n"
        "严格只输出 JSON：\n"
        "{\n"
        '  "risks": [\n'
        '    {"category": "技术|供应链|验收|安全|成本", "description": "风险描述", "severity": "high|medium|low", "mitigation": "应对建议"}\n'
        '  ],\n'
        '  "acceptance_challenges": ["验收难点1", "验收难点2"],\n'
        '  "must_confirm": ["报价前必须向客户确认的关键问题"]\n'
        "}\n"
        "风险要具体到这个设备类型，别给通用废话。至少给 3 条 risks。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.4, max_tokens=800)
        risk = _extract_json(resp.get("content") or "")
        return {"ok": True, **risk, "ai_model": resp.get("model")}
    except Exception as e:
        logger.warning("Step6 风险提示失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "risks": []}


def _step_deep_risk_analysis(
    db, ai: AIClientService, parsed: Dict[str, Any],
    requirement_text: str, step6_risks: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Step 7: 自主风险深挖（ReAct + tool calling）。

    让模型自主决定调用哪些工具（search_ammo/case_lessons/quote_range/standard_modules），
    多轮深挖风险：查类似项目验收难点、查供应链、查成本风险，给出比 Step6 更深的风险分析。

    Step6 失败时本步作为兜底；Step6 成功时本步作为深化（补充 Step6 没覆盖的）。
    """
    from app.services.presale.presale_tool_registry import ToolRegistry

    try:
        registry = ToolRegistry(db)
        tools = registry.get_openai_tools()

        # 用 Step6 已识别的风险作为起点，让模型深化
        step6_brief = ""
        if step6_risks.get("ok"):
            risks = step6_risks.get("risks", [])
            step6_brief = "初步识别的风险：" + "; ".join(
                r.get("description", "")[:50] for r in risks[:4]
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是非标自动化测试设备的资深交付专家。用提供的工具自主检索历史项目数据，"
                    "深挖风险。你可以多轮调用工具，直到挖出足够信息。"
                    "最后必须输出 JSON：{\"deep_risks\":[{\"category\",\"description\",\"severity\",\"evidence\",\"mitigation\"}],"
                    "\"supply_chain_warnings\":[\"\"],\"cost_risks\":[\"\"]}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"客户需求：{requirement_text}\n"
                    f"结构化：{parsed}\n"
                    f"{step6_brief}\n\n"
                    "请用工具查：1)类似项目的验收难点和教训 2)这类设备的报价区间和毛利（成本风险）"
                    "3)标准模块和关键部件。然后给出比初步风险更深的分析，特别是供应链和成本维度。"
                ),
            },
        ]

        def _executor(tool_name, args):
            return registry.execute(tool_name, args)

        result = ai.chat_with_tools(
            messages=messages,
            tools=tools,
            tool_executor=_executor,
            max_rounds=4,
        )

        # 解析最终内容为 JSON
        deep = _extract_json(result.get("content") or "")
        return {
            "ok": True,
            "deep_risks": deep.get("deep_risks", []),
            "supply_chain_warnings": deep.get("supply_chain_warnings", []),
            "cost_risks": deep.get("cost_risks", []),
            "tool_calls": result.get("tool_calls", []),
            "rounds": result.get("rounds", 0),
            "raw_content": (result.get("content") or "")[:500],
            "error": result.get("error"),
        }
    except Exception as e:
        logger.warning("Step7 自主风险深挖失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "deep_risks": [], "tool_calls": []}


def _step_deep_solution(
    db, ai: AIClientService, parsed: Dict[str, Any], requirement_text: str,
    cases: List[Dict[str, Any]], modules: List[Dict[str, Any]],
    quote_range: Dict[str, Any], risks: List[Dict[str, Any]],
    deep_risks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Step 8: 深度方案生成（自主多轮 ReAct）。

    与 Step3（单次 prompt 出初稿）的区别：
      - 模型自主多轮调工具补全资料（查类似案例的架构、查标准模块成本、查报价对标）
      - 复用前面步骤已查到的产物（案例/模块/报价/风险），避免重复检索
      - 输出结构更完整：系统架构 + 子系统拆解 + 设备选型 + 成本分解 + 实施阶段 + 依据证据
      - 给出多个可选方案档位（经济型/标准型/高端型）及差异说明

    产出可直接作为正式售前方案的技术底稿。
    """
    from app.services.presale.presale_tool_registry import ToolRegistry

    try:
        registry = ToolRegistry(db)
        tools = registry.get_openai_tools()

        # 把前面已查到的资料浓缩给模型，让它知道"这些已经有了，不用重复查，缺的再查"
        known_context = _summarize_prior_context(cases, modules, quote_range, risks, deep_risks)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是非标自动化测试设备行业的资深方案架构师。用工具自主补全资料后，"
                    "产出一份完整、细致、可落地的高级售前技术方案。"
                    "你可以多轮调用工具查缺补漏（类似案例的技术细节、标准模块成本、报价对标）。"
                    "最后必须输出严格 JSON，结构如下：\n"
                    "{\n"
                    '  "solution_overview": "方案总述（3-5句，说清做什么、怎么做、客户价值）",\n'
                    '  "system_architecture": "系统架构（技术路线+拓扑，如 PXIe/CompactRIO/工控机+PLC）",\n'
                    '  "subsystems": [{"name":"子系统名","function":"功能描述","key_components":["关键组件"],'
                    '"ref_cost":"参考成本区间","notes":"设计要点"}],\n'
                    '  "equipment_selection": [{"item":"设备/仪器","spec":"规格要求","brand_suggestion":"品牌建议",'
                    '"reason":"选型依据"}],\n'
                    '  "test_strategy": "测试流程与策略（工位/节拍/数据流）",\n'
                    '  "software_design": "软件与控制系统方案",\n'
                    '  "cost_breakdown": [{"category":"类别（机械/电气/视觉/软件/集成）","amount":"金额",'
                    '"ratio":"占比","note":"说明"}],\n'
                    '  "tiers": [{"tier":"经济型/标准型/高端型","diff":"差异","price":"报价",'
                    '"suitable":"适合场景"}],\n'
                    '  "implementation_phases": [{"phase":"阶段","duration":"周期","deliverables":"交付物"}],\n'
                    '  "evidence": ["本方案的依据，引用历史案例/报价/模块数据"],\n'
                    '  "differentiation": "相比通用方案的差异化卖点",\n'
                    '  "assumptions": ["需要客户确认的前提假设"]\n'
                    "}\n"
                    "要求：所有金额/成本要参考工具查到的真实数据；evidence 必须引用具体历史数据；"
                    "subsystems 至少 4 个；equipment_selection 至少 5 项；tiers 给 3 档。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"客户需求：{requirement_text}\n"
                    f"结构化需求：{parsed}\n\n"
                    f"已掌握的资料（你可以基于这些，缺的用工具补查）：\n{known_context}\n\n"
                    "请先用工具补查必要信息（如还不清楚类似项目的架构细节、关键设备规格、"
                    "标准模块成本），然后输出完整方案 JSON。"
                ),
            },
        ]

        def _executor(tool_name, args):
            return registry.execute(tool_name, args)

        result = ai.chat_with_tools(
            messages=messages,
            tools=tools,
            tool_executor=_executor,
            max_rounds=5,
            max_tokens=3000,
        )

        sol = _extract_json(result.get("content") or "")
        return {
            "ok": True,
            **sol,
            "tool_calls": result.get("tool_calls", []),
            "rounds": result.get("rounds", 0),
            "raw_content": (result.get("content") or "")[:500],
            "error": result.get("error"),
        }
    except Exception as e:
        logger.warning("Step8 深度方案生成失败: %s", e)
        return {"ok": False, "error": str(e)[:200], "tool_calls": [], "subsystems": []}


def _summarize_prior_context(
    cases: List[Dict[str, Any]], modules: List[Dict[str, Any]],
    quote_range: Dict[str, Any], risks: List[Dict[str, Any]],
    deep_risks: List[Dict[str, Any]],
) -> str:
    """把前面步骤已查到的资料浓缩成模型可读的上下文（避免重复检索）。"""
    lines = []
    if cases:
        lines.append("相似历史案例：")
        for c in cases[:4]:
            lines.append(
                f"  - {c.get('case_name','')}（{c.get('equipment_type','')}）："
                f"{c.get('technical_highlights','')[:80]}"
            )
    if modules:
        total = sum((m.get("ref_cost") or 0) for m in modules)
        lines.append(
            f"标准模块（合计参考成本 {total}）："
            + "、".join(f"{m.get('module_name','')}({m.get('ref_cost',0)})" for m in modules[:6])
        )
    if quote_range and quote_range.get("sample_count"):
        p = quote_range.get("price", {})
        m = quote_range.get("margin_pct", {})
        lines.append(
            f"历史报价：{p.get('min')}~{p.get('max')}元（中位{p.get('median')}），"
            f"毛利中位{m.get('median')}%，样本{quote_range.get('sample_count')}"
        )
    if risks:
        lines.append("已识别风险：" + "; ".join(r.get("description", "")[:40] for r in risks[:4]))
    if deep_risks:
        lines.append(
            "深度风险（含供应链/成本）：" + "; ".join(
                r.get("description", "")[:40] for r in deep_risks[:3]
            )
        )
    return "\n".join(lines) if lines else "（前面步骤无可用资料，请用工具自行查全）"


# ==================== 工具函数 ====================

def _extract_json(content: str) -> Dict[str, Any]:
    """从大模型输出里提取 JSON（容错 ```json 包裹）。"""
    import json
    import re
    if not content:
        return {}
    content = content.strip().strip("`")
    if content.startswith("json"):
        content = content[4:].strip()
    try:
        return json.loads(content)
    except Exception:
        pass
    # 尝试提取 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 兜底：抓第一个 {...}
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


def _normalize_equipment(eq: Optional[str]) -> Optional[str]:
    """设备类型归一化（白名单校验）。"""
    if not eq:
        return None
    return eq if eq in EQUIPMENT_TYPES else eq  # 宽松：AI 可能抽出新类型，先放行


def _log_step(step: int, name: str, brief: Any) -> None:
    logger.info("[售前智能体] Step%d %s 完成: %s", step, name, brief)


def _revise_solution_with_ai(
    ai: AIClientService,
    current_solution: Dict[str, Any],
    change_request: str,
    requirement_text: str,
) -> tuple:
    """
    销售提修改建议，agent 理解后修改方案的对应部分。

    Args:
        current_solution: 当前完整方案 JSON（含 steps）
        change_request: 销售的修改建议（如"报价调低10%""加个老化工位""PLC换成西门子"）
        requirement_text: 原始需求（给 AI 上下文）

    Returns:
        (revised_solution, changes_summary)
        revised_solution: 修改后的完整方案 JSON
        changes_summary: 本次改了什么的文字摘要
    """
    # 把方案浓缩成文本给 AI（完整 JSON 太长）
    steps = current_solution.get("steps", {})
    ds = steps.get("deep_solution", {})
    solution_text = json.dumps(
        {
            "报价档位": ds.get("tiers", []),
            "子系统": (ds.get("subsystems") or ds.get("line_stations", []))[:6],
            "设备选型": (ds.get("equipment_selection") or [])[:6],
            "成本分解": ds.get("cost_breakdown", []),
            "风险": steps.get("risk_warnings", {}).get("risks", [])[:4],
            "整线布局": ds.get("line_layout", ""),
            "报价区间": steps.get("quote_range", {}).get("price", {}),
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    prompt = (
        "你是售前方案修改助手。销售对当前方案提出了修改建议，请理解建议并修改方案的对应部分。\n\n"
        f"## 原始客户需求\n{requirement_text[:200]}\n\n"
        f"## 当前方案（浓缩）\n{solution_text}\n\n"
        f"## 销售的修改建议\n{change_request}\n\n"
        "## 要求\n"
        "1. 理解建议意图（调价/加设备/换品牌/改工艺/改风险等）\n"
        "2. 只改建议涉及的部分，其他保持不变\n"
        "3. 修改要合理（如调低报价要相应调整成本分解；加设备要更新工位和成本）\n"
        "4. 输出严格 JSON：\n"
        "{\n"
        '  "changes_summary": "用2-3句话说明本次改了什么（如：将标准型报价从665万调低10%至598万，相应调减电气系统成本）",\n'
        '  "modified_parts": {\n'
        '    "tiers": [修改后的三档报价],\n'
        '    "subsystems": [修改后的子系统/工位],\n'
        '    "equipment_selection": [修改后的设备选型],\n'
        '    "cost_breakdown": [修改后的成本分解],\n'
        '    "risks": [修改后的风险],\n'
        '    "line_layout": "修改后的布局（如有改动）"\n'
        "  }\n"
        "}\n"
        "只输出 JSON，modified_parts 里只放有改动的字段，没改的不要放。"
    )
    try:
        resp = ai.generate_solution(prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=2000)
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        modification = json.loads(raw)
        changes_summary = modification.get("changes_summary", "已根据建议修改")

        # 把修改应用到完整方案
        revised = _apply_modification(current_solution, modification.get("modified_parts", {}))
        return revised, changes_summary
    except Exception as e:
        logger.warning("方案迭代修改失败: %s", e)
        return current_solution, f"修改失败（{e}），方案未变"


def _apply_modification(solution: Dict[str, Any], modified_parts: Dict[str, Any]) -> Dict[str, Any]:
    """把 agent 的修改应用到完整方案 JSON（深拷贝，只覆盖有改动的字段）。"""
    import copy
    revised = copy.deepcopy(solution)
    steps = revised.get("steps", {})
    ds = steps.get("deep_solution", {})
    if not ds.get("ok"):
        # 单设备方案，用 generate_solution
        ds = steps.get("generate_solution", {}).get("solution", {})
        target_key = "generate_solution"
    else:
        target_key = "deep_solution"

    for field, new_val in modified_parts.items():
        if not new_val:
            continue
        if field in ("tiers", "subsystems", "equipment_selection", "cost_breakdown", "line_layout", "capacity_analysis"):
            steps[target_key][field] = new_val
        elif field == "risks":
            steps["risk_warnings"]["risks"] = new_val

    revised["steps"] = steps
    return revised


def _build_overall_summary(result: Dict[str, Any]) -> str:
    """一句话总览，给前端顶部展示。"""
    steps = result.get("steps", {})
    parts = []
    parsed = steps.get("understand_requirement", {}).get("parsed", {})
    if parsed.get("equipment_type"):
        parts.append(f"{parsed['equipment_type']}")
    if parsed.get("industry"):
        parts.append(f"（{parsed['industry']}）")

    qr = steps.get("quote_range", {})
    if qr.get("sample_count"):
        price = qr.get("price", {})
        parts.append(
            f"历史报价 {price.get('min')}~{price.get('max')}元（中位{price.get('median')}）"
        )

    risks = steps.get("risk_warnings", {}).get("risks", [])
    if risks:
        parts.append(f"识别 {len(risks)} 项关键风险")

    return " ".join(parts) if parts else "售前分析完成"


def _record_metric(
    db, result: Dict[str, Any], job_id: Optional[int], user_id: Optional[int],
    requirement_text: str, started: float, status: str, error: Optional[str],
) -> None:
    """落埋点到 presale_agent_metrics（成功失败都记）。"""
    from app.models.presale_agent_metric import PresaleAgentMetric
    from datetime import datetime

    steps = result.get("steps", {})
    timings = result.get("timings", {})
    parsed = steps.get("understand_requirement", {}).get("parsed", {}) if steps else {}

    # 方案初稿周期 = 需求理解 + 弹药检索 + 方案生成 三步耗时
    solution_draft_time = (
        timings.get("understand_requirement", 0)
        + timings.get("retrieve_ammo", 0)
        + timings.get("generate_solution", 0)
    )
    # 报价周期 = 从启动到 quote_range 步完成
    quote_time = (
        solution_draft_time
        + timings.get("recommend_bom", 0)
        + timings.get("quote_range", 0)
    )
    total_time = round(time.time() - started, 2) if not result.get("total_time") else result["total_time"]

    # 各步骤成功标志
    steps_ok = {k: bool(v.get("ok")) if isinstance(v, dict) else False for k, v in steps.items()}

    cited_cases = 0
    quote_samples = 0
    if status == "SUCCESS":
        cited_cases = len(steps.get("retrieve_ammo", {}).get("similar_cases", []))
        quote_samples = steps.get("quote_range", {}).get("sample_count", 0) or 0

    metric = PresaleAgentMetric(
        job_id=job_id,
        created_by=user_id,
        requirement_text=requirement_text[:500],
        industry=parsed.get("industry"),
        equipment_type=parsed.get("equipment_type"),
        total_time=total_time,
        solution_draft_time=round(solution_draft_time, 2),
        quote_time=round(quote_time, 2),
        steps_ok=steps_ok,
        cited_case_count=cited_cases,
        quote_sample_count=quote_samples,
        status=status,
        error=error,
    )
    db.add(metric)
    db.commit()
    logger.info(
        "[售前智能体] 埋点已落 metric_id=%s status=%s total=%ss draft=%ss quote=%ss",
        metric.id, status, total_time, round(solution_draft_time, 2), round(quote_time, 2),
    )
