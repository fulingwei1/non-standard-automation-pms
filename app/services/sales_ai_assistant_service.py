# -*- coding: utf-8 -*-
"""
AI sales assistant service with graceful fallback behavior.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.sales import Customer, Opportunity, Quote
from app.services.ai_client_service import AIClientService
from app.services.ai_structured_output import extract_json_payload


class SalesAIAssistantService:
    """销售助手服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
        self.ai_model = self.ai_client.default_model

    def recommend_scripts(
        self,
        customer_id: int,
        opportunity_id: Optional[int] = None,
        scenario_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """推荐销售话术。"""
        customer = self._get_customer(customer_id)
        opportunity = self._get_opportunity(opportunity_id)
        target_scenario = scenario_type or "初次接触"

        fallback = self._fallback_scripts(customer_id, opportunity_id, target_scenario)
        prompt = f"""你是一名非标自动化行业销售教练，请根据客户和商机信息推荐销售话术。

场景：{target_scenario}
客户信息：
{json.dumps(self._serialize_customer(customer), ensure_ascii=False, indent=2, default=str)}
商机信息：
{json.dumps(self._serialize_opportunity(opportunity), ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON：
{{
  "scenario": "{target_scenario}",
  "recommended_scripts": [
    {{
      "title": "话术标题",
      "content": "可直接说给客户听的话术",
      "match_score": 90
    }}
  ]
}}

要求：
1. 输出 2-4 条话术。
2. 话术要贴近非标自动化设备销售场景。
3. 只输出合法 JSON。"""

        payload = self._generate_json(prompt)
        scripts = self._normalize_scripts(payload)
        if scripts:
            return {
                "customer_id": customer_id,
                "opportunity_id": opportunity_id,
                "scenario": payload.get("scenario") or target_scenario,
                "recommended_scripts": scripts,
                "total_matched": len(scripts),
            }
        return fallback

    def generate_proposal(self, opportunity_id: int, proposal_type: str) -> Dict[str, Any]:
        """生成方案草稿。"""
        opportunity = self._get_opportunity(opportunity_id)
        latest_quote = (
            self.db.query(Quote)
            .filter(Quote.opportunity_id == opportunity_id)
            .order_by(desc(Quote.created_at))
            .first()
        )
        fallback = self._fallback_proposal(opportunity_id, proposal_type)
        prompt = f"""你是一名非标自动化解决方案经理，请生成 {proposal_type} 类型的方案草稿。

商机信息：
{json.dumps(self._serialize_opportunity(opportunity), ensure_ascii=False, indent=2, default=str)}
报价信息：
{json.dumps(self._serialize_quote(latest_quote), ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON：
{{
  "title": "方案标题",
  "generated_content": {{
    "sections": [
      {{"title": "1. 项目概述", "content": "正文"}}
    ]
  }},
  "reference_projects": [
    {{"name": "案例名称", "similarity": "85%"}}
  ]
}}

要求：
1. technical 方案偏技术架构与验收，business 方案偏商务条款与交付。
2. 输出 3-5 个章节。
3. 只输出合法 JSON。"""

        payload = self._generate_json(prompt)
        sections = self._normalize_sections(payload)
        if sections:
            result = {
                "opportunity_id": opportunity_id,
                "proposal_type": proposal_type,
                "title": str(payload.get("title") or fallback["title"]).strip(),
                "generated_content": {"sections": sections},
            }
            if proposal_type == "technical":
                result["reference_projects"] = self._normalize_reference_projects(
                    payload.get("reference_projects")
                ) or fallback.get("reference_projects", [])
            return result
        return fallback

    def analyze_competitor(
        self, competitor_name: str, product_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """竞品分析。"""
        fallback = self._fallback_competitor(competitor_name, product_category)
        prompt = f"""你是一名非标自动化行业销售策略顾问，请输出对竞品的标准分析框架。

竞品名称：{competitor_name}
产品类别：{product_category or "未指定"}

请仅输出 JSON：
{{
  "competitor_info": {{
    "encounter_count": 0,
    "our_wins": 0,
    "our_losses": 0,
    "win_rate": 0,
    "avg_price": 0,
    "price_range": "",
    "common_tactics": ["策略1"]
  }},
  "our_advantages": ["优势1"],
  "comparison": [
    {{"dimension": "价格", "competitor": "表现", "us": "表现", "advantage": "us/competitor"}}
  ],
  "recommended_strategy": ["建议1"]
}}

要求：
1. 若缺少真实数据，请给出行业通用、谨慎的判断。
2. 只输出合法 JSON。"""

        payload = self._generate_json(prompt)
        if isinstance(payload, dict) and payload.get("competitor_info"):
            return {
                "competitor_name": competitor_name,
                "product_category": product_category,
                "competitor_info": self._normalize_competitor_info(payload.get("competitor_info")),
                "our_advantages": self._ensure_string_list(payload.get("our_advantages")),
                "comparison": self._normalize_comparison(payload.get("comparison")),
                "recommended_strategy": self._ensure_string_list(
                    payload.get("recommended_strategy")
                ),
            }
        return fallback

    def get_negotiation_advice(self, opportunity_id: int) -> Dict[str, Any]:
        """谈判建议。"""
        opportunity = self._get_opportunity(opportunity_id)
        fallback = self._fallback_negotiation(opportunity_id)
        prompt = f"""你是一名非标自动化行业大客户谈判顾问，请基于以下商机给出谈判建议。

商机信息：
{json.dumps(self._serialize_opportunity(opportunity), ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON：
{{
  "customer_traits": {{
    "type": "客户类型",
    "price_sensitivity": "高/中/低",
    "decision_style": "风格",
    "tech_awareness": "高/中/低"
  }},
  "recommended_approach": "整体策略",
  "price_strategy": "价格策略",
  "talking_points": ["要点1"],
  "potential_objections": ["异议1"],
  "counter_strategies": {{"异议1": "应对话术"}}
}}

要求：
1. 只输出合法 JSON。
2. 建议要适用于设备型项目谈判。"""

        payload = self._generate_json(prompt)
        if isinstance(payload, dict) and payload.get("recommended_approach"):
            return {
                "opportunity_id": opportunity_id,
                "customer_traits": payload.get("customer_traits") or fallback["customer_traits"],
                "recommended_approach": str(payload.get("recommended_approach")).strip(),
                "price_strategy": str(payload.get("price_strategy") or "").strip()
                or fallback["price_strategy"],
                "talking_points": self._ensure_string_list(payload.get("talking_points")),
                "potential_objections": self._ensure_string_list(
                    payload.get("potential_objections")
                ),
                "counter_strategies": payload.get("counter_strategies")
                if isinstance(payload.get("counter_strategies"), dict)
                else fallback["counter_strategies"],
            }
        return fallback

    def predict_churn_risk(self, customer_id: int) -> Dict[str, Any]:
        """客户流失风险分析。"""
        customer = self._get_customer(customer_id)
        opportunities = (
            self.db.query(Opportunity)
            .filter(Opportunity.customer_id == customer_id)
            .order_by(desc(Opportunity.updated_at))
            .limit(5)
            .all()
        )
        fallback = self._fallback_churn(customer_id, customer, opportunities)
        prompt = f"""你是一名客户关系健康度分析师，请评估以下客户的流失风险。

客户信息：
{json.dumps(self._serialize_customer(customer), ensure_ascii=False, indent=2, default=str)}
近期商机：
{json.dumps([self._serialize_opportunity(opp) for opp in opportunities], ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON：
{{
  "risk_score": 0,
  "risk_level": "LOW/MEDIUM/HIGH",
  "risk_factors": [
    {{"factor": "风险因子", "detail": "说明", "severity": "HIGH/MEDIUM/LOW"}}
  ],
  "recommended_actions": ["动作1"],
  "analysis_summary": "一句话总结"
}}

要求：
1. risk_score 范围 0-100。
2. 只输出合法 JSON。"""

        payload = self._generate_json(prompt)
        if isinstance(payload, dict) and payload.get("risk_level"):
            risk_level = str(payload.get("risk_level")).upper()
            risk_score = self._clamp_int(payload.get("risk_score"), default=fallback["risk_score"])
            return {
                "customer_id": customer_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_color": self._risk_color(risk_level),
                "risk_factors": self._normalize_risk_factors(payload.get("risk_factors")),
                "recommended_actions": self._ensure_string_list(
                    payload.get("recommended_actions")
                ),
                "analysis_summary": str(payload.get("analysis_summary") or "").strip() or None,
            }
        return fallback

    def get_churn_risk_list(self, risk_level: Optional[str] = None) -> Dict[str, Any]:
        """获取客户流失风险列表。"""
        customers = self.db.query(Customer).order_by(desc(Customer.updated_at)).limit(20).all()
        risks = []
        for customer in customers:
            risk = self._fallback_churn(customer.id, customer, None)
            risk["customer_name"] = customer.customer_name
            risks.append(risk)
        if risk_level:
            risk_level = risk_level.upper()
            filtered = [item for item in risks if item["risk_level"] == risk_level]
        else:
            filtered = risks

        return {
            "total_count": len(filtered),
            "high_risk_count": len([item for item in risks if item["risk_level"] == "HIGH"]),
            "medium_risk_count": len([item for item in risks if item["risk_level"] == "MEDIUM"]),
            "risk_list": filtered,
        }

    def _get_customer(self, customer_id: Optional[int]) -> Optional[Customer]:
        if not customer_id:
            return None
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def _get_opportunity(self, opportunity_id: Optional[int]) -> Optional[Opportunity]:
        if not opportunity_id:
            return None
        return self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()

    def _has_live_ai(self) -> bool:
        openai_ready = bool(
            self.ai_client.openai_client
            and str(self.ai_client.openai_api_key).startswith(("sk-", "sk-proj-"))
        )
        return bool(openai_ready or self.ai_client.zhipu_client or self.ai_client.kimi_api_key)

    def _generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self._has_live_ai():
            return None
        try:
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model=self.ai_model,
                temperature=0.25,
                max_tokens=1800,
            )
        except Exception:
            return None

        content = (response or {}).get("content")
        model_name = str((response or {}).get("model", ""))
        if not content or model_name.endswith("-mock"):
            return None

        payload = extract_json_payload(str(content))
        return payload if isinstance(payload, dict) else None

    def _serialize_customer(self, customer: Optional[Customer]) -> Dict[str, Any]:
        if not customer:
            return {}
        return {
            "id": getattr(customer, "id", None),
            "customer_name": getattr(customer, "customer_name", None),
            "industry": getattr(customer, "industry", None),
            "customer_level": getattr(customer, "customer_level", None),
            "annual_revenue": float(getattr(customer, "annual_revenue", 0) or 0),
            "credit_level": getattr(customer, "credit_level", None),
            "cooperation_years": getattr(customer, "cooperation_years", None),
            "last_follow_up_at": getattr(customer, "last_follow_up_at", None),
            "payment_terms": getattr(customer, "payment_terms", None),
        }

    def _serialize_opportunity(self, opportunity: Optional[Opportunity]) -> Dict[str, Any]:
        if not opportunity:
            return {}
        return {
            "id": getattr(opportunity, "id", None),
            "opp_code": getattr(opportunity, "opp_code", None),
            "opp_name": getattr(opportunity, "opp_name", None),
            "project_type": getattr(opportunity, "project_type", None),
            "equipment_type": getattr(opportunity, "equipment_type", None),
            "stage": getattr(opportunity, "stage", None),
            "probability": getattr(opportunity, "probability", None),
            "est_amount": float(getattr(opportunity, "est_amount", 0) or 0),
            "budget_range": getattr(opportunity, "budget_range", None),
            "delivery_window": getattr(opportunity, "delivery_window", None),
            "risk_level": getattr(opportunity, "risk_level", None),
            "requirement_maturity": getattr(opportunity, "requirement_maturity", None),
        }

    def _serialize_quote(self, quote: Optional[Quote]) -> Dict[str, Any]:
        if not quote:
            return {}
        return {
            "id": quote.id,
            "quote_code": quote.quote_code,
            "status": quote.status,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
            "total_price": float(quote.total_price or 0) if quote.total_price else 0,
            "items": quote.items,
        }

    def _normalize_scripts(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        scripts = []
        for idx, item in enumerate(payload.get("recommended_scripts") or [], 1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            content = str(item.get("content") or "").strip()
            if not title or not content:
                continue
            scripts.append(
                {
                    "id": idx,
                    "title": title,
                    "content": content,
                    "match_score": self._clamp_int(item.get("match_score"), default=85),
                }
            )
        return scripts

    def _normalize_sections(self, payload: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        if not isinstance(payload, dict):
            return []
        generated_content = payload.get("generated_content")
        if isinstance(generated_content, dict):
            sections = generated_content.get("sections")
        else:
            sections = payload.get("sections")

        normalized = []
        for item in sections or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            content = str(item.get("content") or "").strip()
            if title and content:
                normalized.append({"title": title, "content": content})
        return normalized

    def _normalize_reference_projects(self, value: Any) -> List[Dict[str, str]]:
        normalized = []
        for item in value or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            similarity = str(item.get("similarity") or "").strip()
            if name:
                normalized.append({"name": name, "similarity": similarity or "80%"})
        return normalized

    def _normalize_competitor_info(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return {
            "encounter_count": self._clamp_int(value.get("encounter_count"), default=8),
            "our_wins": self._clamp_int(value.get("our_wins"), default=4),
            "our_losses": self._clamp_int(value.get("our_losses"), default=4),
            "win_rate": float(value.get("win_rate") or 50.0),
            "avg_price": self._clamp_int(value.get("avg_price"), default=2800000),
            "price_range": str(value.get("price_range") or "250万-320万"),
            "common_tactics": self._ensure_string_list(value.get("common_tactics")),
        }

    def _normalize_comparison(self, value: Any) -> List[Dict[str, str]]:
        comparison = []
        for item in value or []:
            if not isinstance(item, dict):
                continue
            dimension = str(item.get("dimension") or "").strip()
            competitor = str(item.get("competitor") or "").strip()
            us = str(item.get("us") or "").strip()
            advantage = str(item.get("advantage") or "").strip() or "us"
            if dimension:
                comparison.append(
                    {
                        "dimension": dimension,
                        "competitor": competitor,
                        "us": us,
                        "advantage": advantage,
                    }
                )
        return comparison

    def _normalize_risk_factors(self, value: Any) -> List[Dict[str, str]]:
        factors = []
        for item in value or []:
            if not isinstance(item, dict):
                continue
            factor = str(item.get("factor") or "").strip()
            detail = str(item.get("detail") or "").strip()
            severity = str(item.get("severity") or "MEDIUM").upper()
            if factor:
                factors.append({"factor": factor, "detail": detail, "severity": severity})
        return factors

    def _ensure_string_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value:
            return [str(value).strip()]
        return []

    def _clamp_int(self, value: Any, default: int) -> int:
        try:
            number = int(float(value))
        except (TypeError, ValueError):
            return default
        return max(0, min(number, 100))

    def _risk_color(self, risk_level: str) -> str:
        if risk_level == "HIGH":
            return "red"
        if risk_level == "MEDIUM":
            return "orange"
        return "green"

    def _fallback_scripts(
        self, customer_id: int, opportunity_id: Optional[int], target_scenario: str
    ) -> Dict[str, Any]:
        scenarios = {
            "初次接触": [
                {
                    "id": 1,
                    "title": "初次拜访开场白",
                    "content": "您好，我是金凯博自动化的顾问，这次主要想结合贵司产线现状，看看是否有提效和降本的空间。",
                    "match_score": 95,
                },
                {
                    "id": 2,
                    "title": "电话陌拜话术",
                    "content": "您好，我这边专注非标自动化测试与装配设备，想了解一下贵司当前产线是否有升级或替换计划。",
                    "match_score": 88,
                },
            ],
            "需求挖掘": [
                {
                    "id": 3,
                    "title": "需求了解话术",
                    "content": "贵司目前在测试、节拍、人工依赖或良率方面，最希望先解决的是哪一块？",
                    "match_score": 92,
                },
                {
                    "id": 4,
                    "title": "预算探询话术",
                    "content": "为了控制方案范围，我想先了解一下这类项目您预期的预算区间和上线时间。",
                    "match_score": 85,
                },
            ],
            "方案介绍": [
                {
                    "id": 5,
                    "title": "方案价值呈现",
                    "content": "我们的方案重点不是单点设备，而是围绕节拍、稳定性和可复制交付来做整体设计。",
                    "match_score": 90,
                }
            ],
            "价格谈判": [
                {
                    "id": 6,
                    "title": "价格异议处理",
                    "content": "如果只比较初始采购价，确实容易陷入价格战；但从良率、停机和维护成本看，整体投入更值得比较。",
                    "match_score": 93,
                }
            ],
        }
        matched = scenarios.get(target_scenario, scenarios["初次接触"])
        return {
            "customer_id": customer_id,
            "opportunity_id": opportunity_id,
            "scenario": target_scenario,
            "recommended_scripts": matched,
            "total_matched": len(matched),
        }

    def _fallback_proposal(self, opportunity_id: int, proposal_type: str) -> Dict[str, Any]:
        if proposal_type == "technical":
            return {
                "opportunity_id": opportunity_id,
                "proposal_type": "technical",
                "title": "锂电FCT测试设备技术方案",
                "generated_content": {
                    "sections": [
                        {"title": "1. 项目概述", "content": "本项目面向非标自动化测试场景，采用模块化方案设计。"},
                        {"title": "2. 技术方案", "content": "设备配置含测试模块、数据采集与控制单元。"},
                        {"title": "3. 实施方案", "content": "建议分阶段完成需求冻结、设计、制造、调试和验收。"},
                        {"title": "4. 验收标准", "content": "重点关注测试覆盖率、误判率和节拍稳定性。"},
                    ]
                },
                "reference_projects": [
                    {"name": "宁德时代FCT项目", "similarity": "90%"},
                    {"name": "比亚迪EOL项目", "similarity": "75%"},
                ],
            }
        return {
            "opportunity_id": opportunity_id,
            "proposal_type": "business",
            "title": "商务合作方案",
            "generated_content": {
                "sections": [
                    {"title": "1. 合作概述", "content": "围绕客户交付目标，提供方案、实施和售后支持的一体化合作。"},
                    {"title": "2. 报价方案", "content": "报价涵盖设备本体、安装调试、培训及项目管理成本。"},
                    {"title": "3. 交付周期", "content": "建议按标准交付周期推进，关键节点设置联合评审。"},
                    {"title": "4. 付款方式", "content": "建议采用分阶段付款，兼顾项目推进与交付风险。"},
                ]
            },
        }

    def _fallback_competitor(
        self, competitor_name: str, product_category: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "competitor_name": competitor_name,
            "product_category": product_category,
            "competitor_info": {
                "encounter_count": 15,
                "our_wins": 9,
                "our_losses": 6,
                "win_rate": 60.0,
                "avg_price": 2800000,
                "price_range": "250万-320万",
                "common_tactics": ["低价策略", "快速交付", "品牌影响力"],
            },
            "our_advantages": [
                "技术实力强，定制化能力高",
                "行业经验丰富，交付方法成熟",
                "售后服务响应快",
                "可结合智能化能力做差异化",
            ],
            "comparison": [
                {"dimension": "价格", "competitor": "较低", "us": "中等", "advantage": "competitor"},
                {"dimension": "技术", "competitor": "一般", "us": "强", "advantage": "us"},
                {"dimension": "交付", "competitor": "快", "us": "标准", "advantage": "competitor"},
                {"dimension": "服务", "competitor": "一般", "us": "优", "advantage": "us"},
            ],
            "recommended_strategy": [
                "强调技术优势和定制化能力，避免单纯价格战",
                "突出同类行业成功案例",
                "明确交付与售后保障机制",
            ],
        }

    def _fallback_negotiation(self, opportunity_id: int) -> Dict[str, Any]:
        return {
            "opportunity_id": opportunity_id,
            "customer_traits": {
                "type": "大客户",
                "price_sensitivity": "中",
                "decision_style": "谨慎",
                "tech_awareness": "高",
            },
            "recommended_approach": "详细方案，数据支撑，建立信任",
            "price_strategy": "标准报价+服务增值包",
            "talking_points": [
                "同类项目成功案例",
                "关键技术与稳定性交付能力",
                "项目经理制与售后服务保障",
            ],
            "potential_objections": ["价格太高", "交付周期太长", "担心技术稳定性"],
            "counter_strategies": {
                "价格太高": "强调总拥有成本和后期运维收益，避免只比初始采购价。",
                "交付周期太长": "拆解关键路径并说明哪些阶段可并行推进。",
                "担心技术稳定性": "用案例、验收标准和试运行计划建立信心。",
            },
        }

    def _fallback_churn(
        self,
        customer_id: int,
        customer: Optional[Customer],
        opportunities: Optional[List[Opportunity]],
    ) -> Dict[str, Any]:
        risk_score = 20
        risk_factors = []
        recommended_actions = ["保持正常联系节奏", "定期发送产品更新"]

        last_follow_up_at = self._parse_datetime(getattr(customer, "last_follow_up_at", None))
        if last_follow_up_at:
            days_since_contact = (datetime.now() - last_follow_up_at).days
            if days_since_contact > 45:
                risk_score += 35
                risk_factors.append(
                    {"factor": "长时间未联系", "detail": f"已{days_since_contact}天未联系", "severity": "HIGH"}
                )
            elif days_since_contact > 20:
                risk_score += 15
                risk_factors.append(
                    {"factor": "联系频率下降", "detail": f"已{days_since_contact}天未联系", "severity": "MEDIUM"}
                )

        stalled_count = 0
        for opportunity in opportunities or []:
            updated_at = getattr(opportunity, "updated_at", None)
            if updated_at and (datetime.now() - updated_at).days > 30:
                stalled_count += 1
        if stalled_count:
            risk_score += min(stalled_count * 10, 25)
            risk_factors.append(
                {
                    "factor": "商机推进停滞",
                    "detail": f"有{stalled_count}个商机超过30天未更新",
                    "severity": "MEDIUM" if stalled_count == 1 else "HIGH",
                }
            )

        if risk_score >= 70:
            risk_level = "HIGH"
            recommended_actions = ["立即安排关键人回访", "重新确认客户优先级与阻塞点", "提供针对性方案优化"]
        elif risk_score >= 40:
            risk_level = "MEDIUM"
            recommended_actions = ["提升联系频率", "补充价值材料", "推动一次正式复盘沟通"]
        else:
            risk_level = "LOW"

        return {
            "customer_id": customer_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": self._risk_color(risk_level),
            "customer_name": customer.customer_name if customer else None,
            "risk_factors": risk_factors,
            "recommended_actions": recommended_actions,
        }

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for candidate in (value, value.replace("Z", "+00:00")):
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                continue
        return None
