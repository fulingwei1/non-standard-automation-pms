# -*- coding: utf-8 -*-
"""
技术评估服务

提供技术评估的核心功能：
1. 评分计算（基于评分规则）
2. 相似案例匹配
3. 评估结果生成
4. 一票否决检查
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.enums import (
    AssessmentDecisionEnum,
    AssessmentSourceTypeEnum,
    AssessmentStatusEnum,
)
from app.models.sales import (
    AssessmentRisk,
    AssessmentTemplate,
    FailureCase,
    Lead,
    Opportunity,
    RiskStatusEnum,
    ScoringRule,
    TechnicalAssessment,
)

TEMPLATE_DIMENSION_MAP = {
    "TECHNICAL": "technology",
    "TECHNOLOGY": "technology",
    "COMMERCIAL": "business",
    "BUSINESS": "business",
    "RESOURCE": "resource",
    "RESOURCES": "resource",
    "TIMELINE": "delivery",
    "DELIVERY": "delivery",
    "CUSTOMER": "customer",
    "RELATIONSHIP": "customer",
    "RISK": "risk",
}

DEFAULT_SCORING_RULE_CONFIG: Dict[str, Any] = {
    "evaluation_criteria": {
        "tech_maturity": {
            "field": "tech_maturity",
            "aliases": ["techMaturity"],
            "max_points": 10,
            "options": [
                {"value": "mature", "points": 10},
                {"value": "high", "points": 10},
                {"value": "medium", "points": 6},
                {"value": "low", "points": 2},
                {"value": "成熟", "points": 10},
                {"value": "一般", "points": 6},
                {"value": "不成熟", "points": 2},
            ],
        },
        "process_difficulty": {
            "field": "process_difficulty",
            "aliases": ["processDifficulty"],
            "max_points": 10,
            "options": [
                {"value": "standard", "points": 10},
                {"value": "medium", "points": 6},
                {"value": "high", "points": 3},
                {"value": "标准", "points": 10},
                {"value": "中等", "points": 6},
                {"value": "复杂", "points": 3},
            ],
        },
        "precision_requirement": {
            "field": "precision_requirement",
            "aliases": ["precisionRequirement"],
            "max_points": 10,
            "options": [
                {"value": "normal", "points": 10},
                {"value": "high", "points": 6},
                {"value": "extreme", "points": 3},
                {"value": "常规", "points": 10},
                {"value": "高精度", "points": 6},
                {"value": "极高精度", "points": 3},
            ],
        },
        "sample_support": {
            "field": "sample_support",
            "aliases": ["sampleSupport"],
            "max_points": 10,
            "options": [
                {"value": "available", "points": 10},
                {"value": "limited", "points": 5},
                {"value": "none", "points": 0},
                {"value": "可提供", "points": 10},
                {"value": "有限", "points": 5},
                {"value": "无", "points": 0},
            ],
        },
        "budget_status": {
            "field": "budget_status",
            "aliases": ["budgetStatus"],
            "max_points": 10,
            "options": [
                {"value": "confirmed", "points": 10},
                {"value": "rough", "points": 5},
                {"value": "unknown", "points": 1},
                {"value": "明确", "points": 10},
                {"value": "粗略", "points": 5},
                {"value": "未知", "points": 1},
            ],
        },
        "price_sensitivity": {
            "field": "price_sensitivity",
            "aliases": ["priceSensitivity"],
            "max_points": 10,
            "options": [
                {"value": "low", "points": 10},
                {"value": "medium", "points": 6},
                {"value": "high", "points": 2},
                {"value": "低", "points": 10},
                {"value": "中", "points": 6},
                {"value": "高", "points": 2},
            ],
        },
        "gross_margin_safety": {
            "field": "gross_margin_safety",
            "aliases": ["grossMarginSafety"],
            "max_points": 10,
            "options": [
                {"value": "safe", "points": 10},
                {"value": "tight", "points": 5},
                {"value": "risk", "points": 1},
                {"value": "安全", "points": 10},
                {"value": "偏紧", "points": 5},
                {"value": "有风险", "points": 1},
            ],
        },
        "payment_terms": {
            "field": "payment_terms",
            "aliases": ["paymentTerms"],
            "max_points": 10,
            "options": [
                {"value": "good", "points": 10},
                {"value": "normal", "points": 6},
                {"value": "poor", "points": 2},
                {"value": "好", "points": 10},
                {"value": "一般", "points": 6},
                {"value": "差", "points": 2},
            ],
        },
        "resource_occupancy": {
            "field": "resource_occupancy",
            "aliases": ["resourceOccupancy"],
            "max_points": 10,
            "options": [
                {"value": "available", "points": 10},
                {"value": "tight", "points": 5},
                {"value": "unavailable", "points": 0},
                {"value": "可安排", "points": 10},
                {"value": "紧张", "points": 5},
                {"value": "不可安排", "points": 0},
            ],
        },
        "has_similar_case": {
            "field": "has_similar_case",
            "aliases": ["hasSimilarCase"],
            "max_points": 10,
            "options": [
                {"value": "yes", "points": 10},
                {"value": True, "points": 10},
                {"value": "partial", "points": 5},
                {"value": "no", "points": 0},
                {"value": False, "points": 0},
                {"value": "有", "points": 10},
                {"value": "部分", "points": 5},
                {"value": "无", "points": 0},
            ],
        },
        "delivery_feasibility": {
            "field": "delivery_feasibility",
            "aliases": ["deliveryFeasibility"],
            "max_points": 10,
            "options": [
                {"value": "feasible", "points": 10},
                {"value": "tight", "points": 5},
                {"value": "risky", "points": 1},
                {"value": "可交付", "points": 10},
                {"value": "偏紧", "points": 5},
                {"value": "风险高", "points": 1},
            ],
        },
        "delivery_months": {
            "field": "delivery_months",
            "aliases": ["deliveryMonths"],
            "max_points": 10,
            "options": [
                {"value": 3, "points": 10},
                {"value": "3", "points": 10},
                {"value": 4, "points": 8},
                {"value": "4", "points": 8},
                {"value": 6, "points": 6},
                {"value": "6", "points": 6},
                {"value": 9, "points": 3},
                {"value": "9", "points": 3},
            ],
        },
        "change_risk": {
            "field": "change_risk",
            "aliases": ["changeRisk"],
            "max_points": 10,
            "options": [
                {"value": "low", "points": 10},
                {"value": "medium", "points": 6},
                {"value": "high", "points": 2},
                {"value": "低", "points": 10},
                {"value": "中", "points": 6},
                {"value": "高", "points": 2},
            ],
        },
        "customer_nature": {
            "field": "customer_nature",
            "aliases": ["customerNature"],
            "max_points": 10,
            "options": [
                {"value": "strategic", "points": 10},
                {"value": "key", "points": 8},
                {"value": "normal", "points": 5},
                {"value": "战略客户", "points": 10},
                {"value": "重点客户", "points": 8},
                {"value": "普通客户", "points": 5},
            ],
        },
        "customer_potential": {
            "field": "customer_potential",
            "aliases": ["customerPotential"],
            "max_points": 10,
            "options": [
                {"value": "high", "points": 10},
                {"value": "medium", "points": 6},
                {"value": "low", "points": 2},
                {"value": "高", "points": 10},
                {"value": "中", "points": 6},
                {"value": "低", "points": 2},
            ],
        },
        "relationship_depth": {
            "field": "relationship_depth",
            "aliases": ["relationshipDepth"],
            "max_points": 10,
            "options": [
                {"value": "deep", "points": 10},
                {"value": "normal", "points": 6},
                {"value": "new", "points": 3},
                {"value": "深", "points": 10},
                {"value": "一般", "points": 6},
                {"value": "新接触", "points": 3},
            ],
        },
        "contact_level": {
            "field": "contact_level",
            "aliases": ["contactLevel"],
            "max_points": 10,
            "options": [
                {"value": "decision_maker", "points": 10},
                {"value": "influencer", "points": 6},
                {"value": "operator", "points": 3},
                {"value": "决策层", "points": 10},
                {"value": "影响者", "points": 6},
                {"value": "执行层", "points": 3},
            ],
        },
    },
    "scales": {
        "decision_thresholds": [
            {"min_score": 80, "decision": "推荐立项"},
            {"min_score": 60, "decision": "有条件立项"},
            {"min_score": 40, "decision": "暂缓"},
            {"min_score": 0, "decision": "不建议立项"},
        ]
    },
    "veto_rules": [],
}


class TechnicalAssessmentService:
    """技术评估服务"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate(
        self,
        source_type: str,
        source_id: int,
        evaluator_id: int,
        requirement_data: Dict[str, Any],
        ai_analysis: Optional[str] = None,
        assessment_id: Optional[int] = None,
    ) -> TechnicalAssessment:
        """
        执行技术评估

        Args:
            source_type: 来源类型 (LEAD/OPPORTUNITY)
            source_id: 来源ID
            evaluator_id: 评估人ID
            requirement_data: 需求数据字典
            assessment_id: 已申请的评估记录ID；传入时更新该记录

        Returns:
            TechnicalAssessment: 评估结果对象
        """
        assessment = None
        if assessment_id is not None:
            assessment = (
                self.db.query(TechnicalAssessment)
                .filter(
                    TechnicalAssessment.id == assessment_id,
                    TechnicalAssessment.source_type == source_type,
                    TechnicalAssessment.source_id == source_id,
                )
                .first()
            )
            if not assessment:
                raise ValueError("技术评估申请不存在或来源不匹配")

        if assessment is None:
            assessment = TechnicalAssessment(source_type=source_type, source_id=source_id)
            self.db.add(assessment)

        template = self._get_template_for_assessment(assessment)
        item_scores = None
        if template and template.items:
            template_result = self._calculate_template_scores(requirement_data, template)
            rules_config = self._rules_config_from_template(template)
            dimension_scores = template_result["dimension_scores"]
            total_score = template_result["total_score"]
            item_scores = template_result["item_scores"]
            item_veto_rules = template_result["veto_rules"]
            veto_triggered, veto_rules = self._check_veto_rules(requirement_data, rules_config)
            if item_veto_rules:
                veto_rules.extend(item_veto_rules)
                veto_triggered = True
        else:
            # 获取评分规则；未配置时使用系统默认规则，避免新环境评估流程卡死。
            rules_config = self._get_scoring_rules_config()
            dimension_scores, total_score = self._calculate_scores(requirement_data, rules_config)
            veto_triggered, veto_rules = self._check_veto_rules(requirement_data, rules_config)

        similar_cases = self._match_similar_cases(requirement_data)
        decision = self._generate_decision(total_score, rules_config)
        if veto_triggered:
            decision = AssessmentDecisionEnum.NOT_RECOMMEND.value
        risks = self._generate_risks(requirement_data, dimension_scores, rules_config)
        conditions = self._generate_conditions(decision, risks, requirement_data)

        assessment.evaluator_id = evaluator_id
        assessment.status = AssessmentStatusEnum.COMPLETED.value
        assessment.total_score = total_score
        assessment.dimension_scores = json.dumps(dimension_scores, ensure_ascii=False)
        assessment.veto_triggered = veto_triggered
        assessment.veto_rules = json.dumps(veto_rules, ensure_ascii=False) if veto_rules else None
        assessment.decision = decision
        assessment.risks = json.dumps(risks, ensure_ascii=False)
        assessment.similar_cases = (
            json.dumps(similar_cases, ensure_ascii=False) if similar_cases else None
        )
        assessment.conditions = json.dumps(conditions, ensure_ascii=False) if conditions else None
        assessment.ai_analysis = ai_analysis
        assessment.item_scores = json.dumps(item_scores, ensure_ascii=False) if item_scores else None
        assessment.evaluated_at = datetime.now()
        assessment.auto_generated = False

        self.db.flush()
        self._sync_structured_risks(assessment.id, evaluator_id, risks)
        self._sync_presale_ticket_assessment(assessment)

        # 更新来源对象的评估关联
        self._update_source_assessment(source_type, source_id, assessment.id)

        return assessment

    def _get_active_scoring_rule(self) -> Optional[ScoringRule]:
        """获取启用的评分规则"""
        return (
            self.db.query(ScoringRule)
            .filter(ScoringRule.is_active)
            .order_by(ScoringRule.created_at.desc())
            .first()
        )

    def _get_scoring_rules_config(self) -> Dict[str, Any]:
        """获取评分规则配置，未启用规则时返回系统默认规则。"""
        scoring_rule = self._get_active_scoring_rule()
        if scoring_rule:
            return json.loads(scoring_rule.rules_json)
        return DEFAULT_SCORING_RULE_CONFIG

    def _get_template_for_assessment(
        self,
        assessment: TechnicalAssessment,
    ) -> Optional[AssessmentTemplate]:
        if not assessment.template_id:
            return None

        return (
            self.db.query(AssessmentTemplate)
            .filter(AssessmentTemplate.id == assessment.template_id)
            .first()
        )

    def _rules_config_from_template(self, template: AssessmentTemplate) -> Dict[str, Any]:
        thresholds = template.score_thresholds or {}
        if isinstance(thresholds, dict) and isinstance(thresholds.get("decision_thresholds"), list):
            decision_thresholds = thresholds["decision_thresholds"]
        else:
            decision_thresholds = [
                {"min_score": thresholds.get("excellent", 90), "decision": "推荐立项"},
                {"min_score": thresholds.get("good", 75), "decision": "有条件立项"},
                {"min_score": thresholds.get("fair", 60), "decision": "暂缓"},
                {"min_score": thresholds.get("poor", 0), "decision": "不建议立项"},
            ]

        return {
            "scales": {"decision_thresholds": decision_thresholds},
            "veto_rules": template.veto_rules or [],
        }

    def _calculate_template_scores(
        self,
        requirement_data: Dict[str, Any],
        template: AssessmentTemplate,
    ) -> Dict[str, Any]:
        dimension_scores: Dict[str, int] = {}
        dimension_points: Dict[str, float] = {}
        dimension_max_points: Dict[str, float] = {}
        item_scores: List[Dict[str, Any]] = []
        veto_rules: List[Dict[str, Any]] = []

        items = sorted(
            template.items,
            key=lambda item: (str(item.dimension or ""), item.sort_order or 0, item.id or 0),
        )
        for item in items:
            criteria = self._normalize_template_criteria(item.scoring_criteria)
            field_name = criteria.get("field") or item.item_code
            field_value = self._get_requirement_value(
                requirement_data,
                field_name,
                criteria.get("aliases", []),
            )
            max_score = int(item.max_score or 10)
            score = self._score_template_item(field_value, criteria, max_score)
            weight = float(item.weight or 1)
            dimension = self._normalize_template_dimension(item.dimension)

            dimension_points[dimension] = dimension_points.get(dimension, 0.0) + score * weight
            dimension_max_points[dimension] = (
                dimension_max_points.get(dimension, 0.0) + max_score * weight
            )
            item_scores.append(
                {
                    "item_id": item.id,
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "dimension": dimension,
                    "field": field_name,
                    "value": field_value,
                    "score": score,
                    "max_score": max_score,
                    "weight": weight,
                }
            )

            if item.is_veto_item and item.veto_threshold is not None and score <= item.veto_threshold:
                veto_rules.append(
                    {
                        "rule_name": item.item_name,
                        "reason": f"{item.item_name}评分 {score} 低于否决阈值 {item.veto_threshold}",
                        "condition": {
                            "item_code": item.item_code,
                            "score": score,
                            "veto_threshold": item.veto_threshold,
                        },
                    }
                )

        for dimension, points in dimension_points.items():
            max_points = dimension_max_points.get(dimension, 0)
            dimension_scores[dimension] = int(round((points / max_points) * 20)) if max_points else 0

        return {
            "dimension_scores": dimension_scores,
            "total_score": self._calculate_template_total_score(template, dimension_scores),
            "item_scores": item_scores,
            "veto_rules": veto_rules,
        }

    def _normalize_template_criteria(self, criteria: Any) -> Dict[str, Any]:
        if criteria is None:
            return {}
        if isinstance(criteria, dict):
            return criteria
        if isinstance(criteria, list):
            return {"options": criteria}
        if isinstance(criteria, str):
            try:
                parsed = json.loads(criteria)
            except json.JSONDecodeError:
                return {}
            return self._normalize_template_criteria(parsed)
        return {}

    def _score_template_item(
        self,
        field_value: Any,
        criteria: Dict[str, Any],
        max_score: int,
    ) -> int:
        if field_value is None:
            return 0

        for option in criteria.get("options", []):
            if not isinstance(option, dict):
                continue
            option_value = option.get("value")
            if field_value == option_value or self._match_value(field_value, option, criteria):
                return self._clamp_score(option.get("score", option.get("points", 0)), max_score)

        for level in criteria.get("levels", []):
            if self._match_template_level(field_value, level):
                return self._clamp_score(level.get("score", level.get("points", 0)), max_score)

        return self._clamp_score(criteria.get("default_score", 0), max_score)

    def _match_template_level(self, field_value: Any, level: Any) -> bool:
        if not isinstance(level, dict):
            return False

        operator = level.get("operator")
        expected = level.get("value")
        if operator and expected is not None:
            try:
                numeric_field = float(field_value)
                numeric_expected = float(expected)
            except (TypeError, ValueError):
                numeric_field = None
                numeric_expected = None

            if operator == "==" and str(field_value) == str(expected):
                return True
            if operator == "!=" and str(field_value) != str(expected):
                return True
            if numeric_field is None or numeric_expected is None:
                return False
            if operator == ">=":
                return numeric_field >= numeric_expected
            if operator == ">":
                return numeric_field > numeric_expected
            if operator == "<=":
                return numeric_field <= numeric_expected
            if operator == "<":
                return numeric_field < numeric_expected

        minimum = level.get("min")
        maximum = level.get("max")
        if minimum is not None or maximum is not None:
            try:
                numeric_field = float(field_value)
            except (TypeError, ValueError):
                return False
            if minimum is not None and numeric_field < float(minimum):
                return False
            if maximum is not None and numeric_field > float(maximum):
                return False
            return True

        return False

    def _clamp_score(self, score: Any, max_score: int) -> int:
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            numeric_score = 0
        return int(round(max(0, min(numeric_score, max_score))))

    def _normalize_template_dimension(self, dimension: Any) -> str:
        value = str(dimension or "").strip()
        return TEMPLATE_DIMENSION_MAP.get(value.upper(), value.lower() or "assessment")

    def _calculate_template_total_score(
        self,
        template: AssessmentTemplate,
        dimension_scores: Dict[str, int],
    ) -> int:
        if not dimension_scores:
            return 0

        raw_weights = template.dimension_weights or {}
        normalized_weights = {}
        if isinstance(raw_weights, dict):
            for key, value in raw_weights.items():
                try:
                    normalized_weights[self._normalize_template_dimension(key)] = float(value)
                except (TypeError, ValueError):
                    continue

        total_weight = 0.0
        weighted_score = 0.0
        for dimension, score in dimension_scores.items():
            weight = normalized_weights.get(dimension, 1.0)
            total_weight += weight
            weighted_score += (score / 20) * 100 * weight

        return int(round(weighted_score / total_weight)) if total_weight else 0

    def _calculate_scores(
        self, requirement_data: Dict[str, Any], rules_config: Dict[str, Any]
    ) -> tuple:
        """
        计算五维分数

        Returns:
            tuple: (dimension_scores字典, total_score总分)
        """
        evaluation_criteria = rules_config.get("evaluation_criteria", {})
        scales = rules_config.get("scales", {})
        scales.get("score_levels", {})

        dimension_scores = {
            "technology": 0,  # 技术维度
            "business": 0,  # 商务维度
            "resource": 0,  # 资源维度
            "delivery": 0,  # 交付维度
            "customer": 0,  # 客户关系维度
        }

        # 技术维度评分
        tech_score = self._score_dimension(
            requirement_data,
            evaluation_criteria,
            ["tech_maturity", "process_difficulty", "precision_requirement", "sample_support"],
        )
        dimension_scores["technology"] = tech_score

        # 商务维度评分
        business_score = self._score_dimension(
            requirement_data,
            evaluation_criteria,
            ["budget_status", "price_sensitivity", "gross_margin_safety", "payment_terms"],
        )
        dimension_scores["business"] = business_score

        # 资源维度评分
        resource_score = self._score_dimension(
            requirement_data, evaluation_criteria, ["resource_occupancy", "has_similar_case"]
        )
        dimension_scores["resource"] = resource_score

        # 交付维度评分
        delivery_score = self._score_dimension(
            requirement_data,
            evaluation_criteria,
            ["delivery_feasibility", "delivery_months", "change_risk"],
        )
        dimension_scores["delivery"] = delivery_score

        # 客户关系维度评分
        customer_score = self._score_dimension(
            requirement_data,
            evaluation_criteria,
            ["customer_nature", "customer_potential", "relationship_depth", "contact_level"],
        )
        dimension_scores["customer"] = customer_score

        # 计算总分（加权平均，每个维度20分）
        total_score = sum(dimension_scores.values())

        return dimension_scores, total_score

    def _score_dimension(
        self,
        requirement_data: Dict[str, Any],
        evaluation_criteria: Dict[str, Any],
        criteria_keys: List[str],
    ) -> int:
        """计算单个维度的分数"""
        total_points = 0
        max_points = 0

        for key in criteria_keys:
            if key not in evaluation_criteria:
                continue

            criterion = evaluation_criteria[key]
            field_name = criterion.get("field", key)
            max_points += criterion.get("max_points", 10)

            # 获取字段值
            field_value = self._get_requirement_value(
                requirement_data,
                field_name,
                criterion.get("aliases", []),
            )
            if field_value is None:
                continue

            # 查找匹配的选项
            options = criterion.get("options", [])
            for option in options:
                option_value = option.get("value")
                if field_value == option_value or self._match_value(field_value, option, criterion):
                    points = option.get("points", 0)
                    total_points += points
                    break

        # 转换为20分制
        if max_points > 0:
            normalized_score = int((total_points / max_points) * 20)
        else:
            normalized_score = 0

        return normalized_score

    def _get_requirement_value(
        self,
        requirement_data: Dict[str, Any],
        field_name: str,
        aliases: Optional[List[str]] = None,
    ) -> Any:
        for key in [field_name, *(aliases or [])]:
            if key in requirement_data and requirement_data[key] not in (None, ""):
                return requirement_data[key]
        return None

    def _match_value(
        self, field_value: Any, option: Dict[str, Any], criterion: Dict[str, Any]
    ) -> bool:
        """匹配字段值（支持关键词匹配）"""
        match_mode = criterion.get("match_mode", "exact")

        if match_mode == "exact":
            return str(field_value) == str(option.get("value", ""))
        elif match_mode == "contains":
            keywords = option.get("keywords", [])
            field_str = str(field_value).lower()
            return any(kw.lower() in field_str for kw in keywords)

        return False

    def _check_veto_rules(
        self, requirement_data: Dict[str, Any], rules_config: Dict[str, Any]
    ) -> tuple:
        """
        检查一票否决规则

        Returns:
            tuple: (是否触发, 触发的规则列表)
        """
        veto_rules_config = rules_config.get("veto_rules", [])
        triggered_rules = []

        for rule in veto_rules_config:
            condition = rule.get("condition", {})
            field = condition.get("field")
            operator = condition.get("operator", "==")
            value = condition.get("value")

            if not field or field not in requirement_data:
                continue

            field_value = requirement_data[field]
            triggered = False

            if operator == "==" and str(field_value) == str(value):
                triggered = True
            elif operator == "!=" and str(field_value) != str(value):
                triggered = True
            elif operator == "in" and field_value in value:
                triggered = True
            elif operator == "not_in" and field_value not in value:
                triggered = True

            if triggered:
                triggered_rules.append(
                    {
                        "rule_name": rule.get("name", ""),
                        "reason": rule.get("reason", ""),
                        "condition": condition,
                    }
                )

        return len(triggered_rules) > 0, triggered_rules

    def _match_similar_cases(self, requirement_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """匹配相似失败案例"""
        similar_cases = []

        # 获取关键匹配字段
        industry = requirement_data.get("industry")
        requirement_data.get("productTypes") or requirement_data.get("product_type")
        requirement_data.get("targetTakt") or requirement_data.get("takt_time_s")
        requirement_data.get("budgetStatus") or requirement_data.get("budget_status")

        # 查询失败案例
        query = self.db.query(FailureCase)

        conditions = []
        if industry:
            conditions.append(FailureCase.industry == industry)

        if conditions:
            query = query.filter(or_(*conditions))

        failure_cases = query.limit(5).all()

        for case in failure_cases:
            similarity_score = self._calculate_similarity(requirement_data, case)
            if similarity_score > 0.3:  # 相似度阈值
                similar_cases.append(
                    {
                        "case_code": case.case_code,
                        "project_name": case.project_name,
                        "similarity_score": similarity_score,
                        "core_failure_reason": case.core_failure_reason,
                        "early_warning_signals": (
                            json.loads(case.early_warning_signals)
                            if case.early_warning_signals
                            else []
                        ),
                        "lesson_learned": case.lesson_learned,
                    }
                )

        # 按相似度排序
        similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_cases[:3]  # 返回前3个最相似的案例

    def _calculate_similarity(
        self, requirement_data: Dict[str, Any], failure_case: FailureCase
    ) -> float:
        """计算相似度分数（0-1）"""
        score = 0.0
        factors = 0

        # 行业匹配
        if requirement_data.get("industry") == failure_case.industry:
            score += 0.3
        factors += 0.3

        # 产品类型匹配
        req_product_types = requirement_data.get("productTypes") or requirement_data.get(
            "product_type"
        )
        if req_product_types and failure_case.product_types:
            case_product_types = (
                json.loads(failure_case.product_types)
                if isinstance(failure_case.product_types, str)
                else failure_case.product_types
            )
            if isinstance(req_product_types, str):
                req_product_types = (
                    json.loads(req_product_types)
                    if req_product_types.startswith("[")
                    else [req_product_types]
                )

            if any(pt in case_product_types for pt in req_product_types):
                score += 0.2
        factors += 0.2

        # 节拍匹配（±20%范围内）
        req_takt = requirement_data.get("targetTakt") or requirement_data.get("takt_time_s")
        if req_takt and failure_case.takt_time_s:
            if (
                abs(float(req_takt) - float(failure_case.takt_time_s))
                / float(failure_case.takt_time_s)
                <= 0.2
            ):
                score += 0.2
        factors += 0.2

        # 预算状态匹配
        req_budget = requirement_data.get("budgetStatus") or requirement_data.get("budget_status")
        if req_budget and failure_case.budget_status and req_budget == failure_case.budget_status:
            score += 0.1
        factors += 0.1

        # 客户项目状态匹配
        req_status = requirement_data.get("customerProjectStatus") or requirement_data.get(
            "customer_project_status"
        )
        if (
            req_status
            and failure_case.customer_project_status
            and req_status == failure_case.customer_project_status
        ):
            score += 0.1
        factors += 0.1

        # 规范状态匹配
        req_spec = requirement_data.get("specStatus") or requirement_data.get("spec_status")
        if req_spec and failure_case.spec_status and req_spec == failure_case.spec_status:
            score += 0.1
        factors += 0.1

        return score / factors if factors > 0 else 0.0

    def _generate_decision(self, total_score: int, rules_config: Dict[str, Any]) -> str:
        """生成决策建议"""
        decision_thresholds = rules_config.get("scales", {}).get("decision_thresholds", [])

        for threshold in decision_thresholds:
            min_score = threshold.get("min_score", 0)
            if total_score >= min_score:
                decision = threshold.get("decision", "暂缓")
                # 映射到枚举值
                decision_map = {
                    "推荐立项": AssessmentDecisionEnum.RECOMMEND.value,
                    "有条件立项": AssessmentDecisionEnum.CONDITIONAL.value,
                    "暂缓": AssessmentDecisionEnum.DEFER.value,
                    "不建议立项": AssessmentDecisionEnum.NOT_RECOMMEND.value,
                }
                return decision_map.get(decision, AssessmentDecisionEnum.DEFER.value)

        return AssessmentDecisionEnum.DEFER.value

    def _generate_risks(
        self,
        requirement_data: Dict[str, Any],
        dimension_scores: Dict[str, int],
        rules_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """生成风险列表"""
        risks = []

        # 检查各维度风险
        for dimension, score in dimension_scores.items():
            if score < 10:  # 低于10分视为高风险
                risks.append(
                    {
                        "dimension": dimension,
                        "level": "HIGH",
                        "description": f"{dimension}维度评分较低({score}分)，存在较高风险",
                    }
                )
            elif score < 15:  # 10-15分为中等风险
                risks.append(
                    {
                        "dimension": dimension,
                        "level": "MEDIUM",
                        "description": f"{dimension}维度评分一般({score}分)，需要关注",
                    }
                )

        # 检查需求成熟度
        req_maturity = requirement_data.get("requirementMaturity") or requirement_data.get(
            "requirement_maturity"
        )
        if req_maturity and req_maturity < 3:
            risks.append(
                {
                    "dimension": "requirement",
                    "level": "HIGH",
                    "description": f"需求成熟度较低({req_maturity}级)，存在需求变更风险",
                }
            )

        # 检查是否有SOW/接口文档
        if not requirement_data.get("hasSOW") and not requirement_data.get("has_sow"):
            risks.append(
                {
                    "dimension": "requirement",
                    "level": "MEDIUM",
                    "description": "缺少客户SOW/URS文档，需求可能不明确",
                }
            )

        return risks

    def _sync_structured_risks(
        self,
        assessment_id: int,
        evaluator_id: int,
        risks: List[Dict[str, Any]],
    ) -> None:
        """将评估生成的JSON风险同步到可跟踪的结构化风险表。"""
        if not isinstance(assessment_id, int) or assessment_id <= 0 or not risks:
            return

        risk_code_prefix = self._assessment_risk_code_prefix()
        risk_code_seq = self._next_assessment_risk_code_seq(risk_code_prefix)
        for risk in risks:
            description = str(risk.get("description") or "").strip()
            if not description:
                continue

            existing_risk = (
                self.db.query(AssessmentRisk.id)
                .filter(
                    AssessmentRisk.assessment_id == assessment_id,
                    AssessmentRisk.risk_description == description,
                )
                .first()
            )
            if existing_risk:
                continue

            dimension = str(risk.get("dimension") or "assessment")
            probability, impact = self._risk_probability_and_impact(risk.get("level"))
            structured_risk = AssessmentRisk(
                assessment_id=assessment_id,
                risk_code=f"{risk_code_prefix}{risk_code_seq:04d}",
                risk_title=f"{dimension}维度风险",
                risk_category=dimension,
                risk_description=description,
                probability=probability,
                impact=impact,
                owner_id=evaluator_id,
                status=RiskStatusEnum.OPEN,
            )
            structured_risk.risk_score = structured_risk.calculate_risk_score()
            structured_risk.risk_level = self._risk_level_from_score(structured_risk.risk_score)
            self.db.add(structured_risk)
            risk_code_seq += 1

    def _risk_probability_and_impact(self, level: Any) -> tuple[str, str]:
        level_value = str(level or "").upper()
        if level_value == "LOW":
            return "LOW", "LOW"
        if level_value == "MEDIUM":
            return "LOW", "MEDIUM"
        if level_value == "CRITICAL":
            return "HIGH", "MEDIUM"
        return "MEDIUM", "MEDIUM"

    def _risk_level_from_score(self, risk_score: int) -> str:
        if risk_score >= 6:
            return "CRITICAL"
        if risk_score >= 4:
            return "HIGH"
        if risk_score >= 2:
            return "MEDIUM"
        return "LOW"

    def _assessment_risk_code_prefix(self) -> str:
        today = datetime.now()
        return f"RSK{today.strftime('%Y%m%d')}"

    def _next_assessment_risk_code_seq(self, prefix: str) -> int:
        last_risk = (
            self.db.query(AssessmentRisk)
            .filter(AssessmentRisk.risk_code.like(f"{prefix}%"))
            .order_by(AssessmentRisk.risk_code.desc())
            .first()
        )
        return int(last_risk.risk_code[-4:]) + 1 if last_risk else 1

    def _generate_conditions(
        self, decision: str, risks: List[Dict[str, Any]], requirement_data: Dict[str, Any]
    ) -> List[str]:
        """生成立项条件"""
        conditions = []

        if decision == AssessmentDecisionEnum.CONDITIONAL.value:
            # 有条件立项，需要列出条件
            high_risks = [r for r in risks if r.get("level") == "HIGH"]
            for risk in high_risks:
                conditions.append(f"解决{risk.get('description')}")

            # 检查未决事项
            source_type = requirement_data.get("source_type")
            source_id = requirement_data.get("source_id")
            if source_type and source_id:
                from app.models.sales import OpenItem

                blocking_items = (
                    self.db.query(OpenItem)
                    .filter(
                        and_(
                            OpenItem.source_type == source_type,
                            OpenItem.source_id == source_id,
                            OpenItem.blocks_quotation,
                            OpenItem.status != "CLOSED",
                        )
                    )
                    .all()
                )

                if blocking_items:
                    conditions.append(f"解决{len(blocking_items)}个阻塞报价的未决事项")

        return conditions

    def _sync_presale_ticket_assessment(self, assessment: TechnicalAssessment) -> None:
        """将技术评估完成状态同步到关联或同来源的售前工单。"""
        from app.models.presale import PresaleSupportTicket, TicketStatusEnum

        if not assessment.id:
            return

        completion_conditions = [PresaleSupportTicket.current_assessment_id == assessment.id]
        conditions = list(completion_conditions)
        if assessment.presale_ticket_id:
            completion_conditions.append(PresaleSupportTicket.id == assessment.presale_ticket_id)
            conditions.append(PresaleSupportTicket.id == assessment.presale_ticket_id)
        else:
            source_condition = None
            if assessment.source_type == AssessmentSourceTypeEnum.LEAD.value:
                source_condition = PresaleSupportTicket.lead_id == assessment.source_id
            elif assessment.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
                source_condition = PresaleSupportTicket.opportunity_id == assessment.source_id

            if source_condition is not None:
                source_tickets = (
                    self.db.query(PresaleSupportTicket)
                    .filter(
                        source_condition,
                        PresaleSupportTicket.status.notin_(("CANCELLED", "CLOSED")),
                    )
                    .all()
                )
                if len(source_tickets) == 1:
                    conditions.append(PresaleSupportTicket.id == source_tickets[0].id)

        tickets = self.db.query(PresaleSupportTicket).filter(or_(*conditions)).all()
        if not tickets:
            return

        completed_at = datetime.now()
        terminal_statuses = {TicketStatusEnum.CANCELLED.value, TicketStatusEnum.CLOSED.value}
        completion_ticket_ids = {
            ticket.id
            for ticket in self.db.query(PresaleSupportTicket.id)
            .filter(or_(*completion_conditions))
            .all()
        }
        for ticket in tickets:
            ticket.assessment_status = AssessmentStatusEnum.COMPLETED.value
            ticket.current_assessment_id = assessment.id
            if ticket.id in completion_ticket_ids and ticket.status not in terminal_statuses:
                ticket.status = TicketStatusEnum.COMPLETED.value
                ticket.complete_time = ticket.complete_time or completed_at

        if not assessment.presale_ticket_id and len(tickets) == 1:
            assessment.presale_ticket_id = tickets[0].id

    def _update_source_assessment(self, source_type: str, source_id: int, assessment_id: int):
        """更新来源对象的评估关联"""
        if source_type == AssessmentSourceTypeEnum.LEAD.value:
            lead = self.db.query(Lead).filter(Lead.id == source_id).first()
            if lead:
                lead.assessment_id = assessment_id
                lead.assessment_status = AssessmentStatusEnum.COMPLETED.value
        elif source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
            opportunity = self.db.query(Opportunity).filter(Opportunity.id == source_id).first()
            if opportunity:
                opportunity.assessment_id = assessment_id
                opportunity.assessment_status = AssessmentStatusEnum.COMPLETED.value

        self.db.commit()
