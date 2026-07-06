# -*- coding: utf-8 -*-
"""
售前需求澄清引擎

让 agent 像老售前工程师一样，主动追问客户需求里缺失的关键信息：
  - 客户说"测 BMS"→ 追问：几串？电压范围？节拍？通讯协议？
  - 客户说"800V 电驱"→ 追问：测控制器还是总成？最大电流？是否需要疲劳老化？
  - 信息够完整 → 直接放行，进入方案生成

核心方法：
  clarify_requirement(session, requirement_text, history)
    → {is_complete, questions, understood, summary, confidence}

会话式：每轮基于已有信息 + 历史，决定还要问什么、还是放行。
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.services.ai_client_service import AIClientService

logger = logging.getLogger("presale.clarifier")

# 金凯博业务的核心需求维度（每个设备类型关心的关键参数不同）
CLARIFY_DIMENSIONS = """
售前测试设备的关键需求维度（不同设备类型重点不同）：
- 测试对象：测什么（PCBA/整机/BMS/电驱/功率器件/外观）？单测还是产线？
- 技术指标：电压/电流范围、节拍(秒)、精度要求、通道数、测试工位数
- 行业与标准：行业（新能源/消费电子/汽车）、是否需符合特定标准（车规/IPC/IEC）
- 接口与通讯：CAN/CANFD/LIN/RS485/MES接口/数据追溯
- 环境与安全：高低温/防爆/高压安全/IP等级
- 规模与交付：单工位/多工位/产线、目标交期、预算范围
- 特殊要求：老化/烧录/视觉检测/自动上下料/换型兼容
"""


def clarify_requirement(
    requirement_text: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    评估需求完整性，必要时生成追问。

    Args:
        requirement_text: 销售本轮输入的需求（首轮是原始需求，后续轮是回答）
        history: 历史对话 [{role: "user"|"assistant", content: "..."}]，首轮为空

    Returns:
        {
            "is_complete": bool,          # 需求是否已完整，可以生成方案了
            "questions": [...],           # 待澄清的问题（is_complete=True 时为空）
            "understood": {...},          # AI 已理解的结构化需求（累积）
            "summary": str,               # 当前需求的一句话总结
            "confidence": float,          # 完整度置信度 0-1
            "next_action": "ask"|"generate",  # 下一步：继续问 or 生成方案
        }
    """
    ai = AIClientService()
    history = history or []

    # 拼对话历史
    dialogue = "\n".join(
        f"{'销售' if m['role']=='user' else '售前顾问'}：{m['content']}"
        for m in history
    )

    prompt = (
        "你是金凯博自动化测试公司的资深售前顾问。"
        "你的任务是评估客户需求是否完整到可以出技术方案，如果不够，追问最关键的问题。\n\n"
        f"{CLARIFY_DIMENSIONS}\n\n"
        "## 评估原则\n"
        "1. 至少要清楚：测试对象 + 1-2个关键技术指标 + 行业/规模。缺这些必须问。\n"
        "2. 每轮最多问 3 个最关键的问题（不要一次问 10 个吓跑客户）。\n"
        "3. 问题要具体、给选项（如'测的是 BMS 控制板还是整个电池包？'，而不是'测什么？'）。\n"
        "4. 基于已有信息问，不重复问已经答过的。\n"
        "5. 客户明确表达'先这样/差不多/你看着办'时，尊重客户，标记 is_complete=true。\n\n"
        "## 对话历史\n"
        f"{dialogue if dialogue else '（首次咨询）'}\n\n"
        f"## 销售本轮输入\n{requirement_text}\n\n"
        "## 输出要求\n"
        "严格输出 JSON：\n"
        "{\n"
        '  "is_complete": true/false,\n'
        '  "confidence": 0.0-1.0（需求完整度），\n'
        '  "understood": {\n'
        '    "test_object": "已明确的测试对象",\n'
        '    "key_specs": ["已明确的关键指标"],\n'
        '    "industry": "行业",\n'
        '    "scale": "规模",\n'
        '    "special_reqs": ["特殊要求"],\n'
        '    "gaps": ["仍缺失的关键信息"]\n'
        "  },\n"
        '  "questions": [\n'
        '    {"question": "具体问题（带选项）", "why": "为什么问这个", "priority": "high/medium/low"}\n'
        "  ],\n"
        '  "summary": "用一句话总结目前已理解的需求",\n'
        '  "reply_to_user": "要回复给销售/客户的话（自然口语，包含问题或确认放行）"\n'
        "}\n"
        "如果 is_complete=true，questions 为空，reply_to_user 应是'需求已比较完整，我开始生成方案'之类。"
    )

    try:
        resp = ai.generate_solution(
            prompt, model="qwen3-coder-plus", temperature=0.3, max_tokens=800
        )
        raw = resp.get("content") or ""
        raw = raw.strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
        result = json.loads(raw)
        result["ok"] = True
        result["next_action"] = "generate" if result.get("is_complete") else "ask"
        result["ai_model"] = resp.get("model")
        logger.info(
            "澄清评估: complete=%s confidence=%s questions=%s",
            result.get("is_complete"),
            result.get("confidence"),
            len(result.get("questions", [])),
        )
        return result
    except Exception as e:
        logger.warning("澄清评估失败: %s", e)
        # 失败时放行（不让澄清阻塞主流程）
        return {
            "ok": False,
            "is_complete": True,
            "confidence": 0.5,
            "understood": {},
            "questions": [],
            "summary": requirement_text,
            "reply_to_user": "（澄清评估暂时不可用，直接生成方案）",
            "next_action": "generate",
            "error": str(e)[:100],
        }


def build_consolidated_requirement(
    requirement_text: str, history: List[Dict[str, str]], understood: Dict[str, Any]
) -> str:
    """
    把多轮澄清后的需求整合成一句完整的需求描述，传给智能体生成方案。

    例如：
      首轮："测BMS"
      澄清后："新能源汽车BMS电池管理系统测试设备，48-96串电芯模拟，绝缘检测，
              CAN/CANFD通讯，节拍60秒，单工位"
    """
    parts = [requirement_text]
    # 追加历史回答
    for m in history:
        if m["role"] == "user":
            parts.append(m["content"])
    # 追加结构化理解
    if understood:
        u_parts = []
        if understood.get("test_object"):
            u_parts.append(f"测试对象：{understood['test_object']}")
        if understood.get("key_specs"):
            u_parts.append(f"关键指标：{'、'.join(understood['key_specs'])}")
        if understood.get("industry"):
            u_parts.append(f"行业：{understood['industry']}")
        if understood.get("scale"):
            u_parts.append(f"规模：{understood['scale']}")
        if understood.get("special_reqs"):
            u_parts.append(f"特殊要求：{'、'.join(understood['special_reqs'])}")
        if u_parts:
            parts.append("【整合】" + "；".join(u_parts))

    return " ".join(parts)
