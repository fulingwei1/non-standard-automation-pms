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
    FailureCase,
    Lead,
    Opportunity,
    ScoringRule,
    TechnicalAssessment,
)


class TechnicalAssessmentService:
    """技术评估服务"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, source_type: str, source_id: int, evaluator_id: int,
                 requirement_data: Dict[str, Any], ai_analysis: Optional[str] = None) -> TechnicalAssessment:
        """
        执行技术评估

        Args:
            source_type: 来源类型 (LEAD/OPPORTUNITY)
            source_id: 来源ID
            evaluator_id: 评估人ID
            requirement_data: 需求数据字典

        Returns:
            TechnicalAssessment: 评估结果对象
        """
        # 获取评分规则
        scoring_rule = self._get_active_scoring_rule()
        if not scoring_rule:
            raise ValueError("未找到启用的评分规则")

        rules_config = json.loads(scoring_rule.rules_json)

        # 计算评分
        dimension_scores, total_score = self._calculate_scores(requirement_data, rules_config)

        # 检查一票否决
        veto_triggered, veto_rules = self._check_veto_rules(requirement_data, rules_config)

        # 匹配相似案例
        similar_cases = self._match_similar_cases(requirement_data)

        # 生成决策建议
        decision = self._generate_decision(total_score, rules_config)

        # 生成风险列表
        risks = self._generate_risks(requirement_data, dimension_scores, rules_config)

        # 生成立项条件
        conditions = self._generate_conditions(decision, risks, requirement_data)

        # 创建评估记录
        assessment = TechnicalAssessment(
            source_type=source_type,
            source_id=source_id,
            evaluator_id=evaluator_id,
            status=AssessmentStatusEnum.COMPLETED,
            total_score=total_score,
            dimension_scores=json.dumps(dimension_scores, ensure_ascii=False),
            veto_triggered=veto_triggered,
            veto_rules=json.dumps(veto_rules, ensure_ascii=False) if veto_rules else None,
            decision=decision,
            risks=json.dumps(risks, ensure_ascii=False),
            similar_cases=json.dumps(similar_cases, ensure_ascii=False) if similar_cases else None,
            conditions=json.dumps(conditions, ensure_ascii=False) if conditions else None,
            ai_analysis=ai_analysis,
            evaluated_at=datetime.now()
        )

        self.db.add(assessment)
        self.db.flush()

        # 更新来源对象的评估关联
        self._update_source_assessment(source_type, source_id, assessment.id)

        return assessment

    def _get_active_scoring_rule(self) -> Optional[ScoringRule]:
        """获取启用的评分规则"""
        return self.db.query(ScoringRule).filter(
            ScoringRule.is_active
        ).order_by(ScoringRule.created_at.desc()).first()

    def _calculate_scores(self, requirement_data: Dict[str, Any],
                          rules_config: Dict[str, Any]) -> tuple:
        """
        计算五维分数

        Returns:
            tuple: (dimension_scores字典, total_score总分)
        """
        evaluation_criteria = rules_config.get('evaluation_criteria', {})
        scales = rules_config.get('scales', {})
        scales.get('score_levels', {})

        dimension_scores = {
            'technology': 0,      # 技术维度
            'business': 0,        # 商务维度
            'resource': 0,        # 资源维度
            'delivery': 0,        # 交付维度
            'customer': 0         # 客户关系维度
        }

        # 技术维度评分
        tech_score = self._score_dimension(requirement_data, evaluation_criteria,
                                          ['tech_maturity', 'process_difficulty',
                                           'precision_requirement', 'sample_support'])
        dimension_scores['technology'] = tech_score

        # 商务维度评分
        business_score = self._score_dimension(requirement_data, evaluation_criteria,
                                              ['budget_status', 'price_sensitivity',
                                               'gross_margin_safety', 'payment_terms'])
        dimension_scores['business'] = business_score

        # 资源维度评分
        resource_score = self._score_dimension(requirement_data, evaluation_criteria,
                                               ['resource_occupancy', 'has_similar_case'])
        dimension_scores['resource'] = resource_score

        # 交付维度评分
        delivery_score = self._score_dimension(requirement_data, evaluation_criteria,
                                               ['delivery_feasibility', 'delivery_months',
                                                'change_risk'])
        dimension_scores['delivery'] = delivery_score

        # 客户关系维度评分
        customer_score = self._score_dimension(requirement_data, evaluation_criteria,
                                              ['customer_nature', 'customer_potential',
                                               'relationship_depth', 'contact_level'])
        dimension_scores['customer'] = customer_score

        # 计算总分（加权平均，每个维度20分）
        total_score = sum(dimension_scores.values())

        return dimension_scores, total_score

    def _score_dimension(self, requirement_data: Dict[str, Any],
                        evaluation_criteria: Dict[str, Any],
                        criteria_keys: List[str]) -> int:
        """计算单个维度的分数"""
        total_points = 0
        max_points = 0

        for key in criteria_keys:
            if key not in evaluation_criteria:
                continue

            criterion = evaluation_criteria[key]
            field_name = criterion.get('field', key)
            max_points += criterion.get('max_points', 10)

            # 获取字段值
            field_value = requirement_data.get(field_name)
            if not field_value:
                continue

            # 查找匹配的选项
            options = criterion.get('options', [])
            for option in options:
                option_value = option.get('value')
                if field_value == option_value or self._match_value(field_value, option, criterion):
                    points = option.get('points', 0)
                    total_points += points
                    break

        # 转换为20分制
        if max_points > 0:
            normalized_score = int((total_points / max_points) * 20)
        else:
            normalized_score = 0

        return normalized_score

    def _match_value(self, field_value: Any, option: Dict[str, Any],
                    criterion: Dict[str, Any]) -> bool:
        """匹配字段值（支持关键词匹配）"""
        match_mode = criterion.get('match_mode', 'exact')

        if match_mode == 'exact':
            return str(field_value) == str(option.get('value', ''))
        elif match_mode == 'contains':
            keywords = option.get('keywords', [])
            field_str = str(field_value).lower()
            return any(kw.lower() in field_str for kw in keywords)

        return False

    def _check_veto_rules(self, requirement_data: Dict[str, Any],
                         rules_config: Dict[str, Any]) -> tuple:
        """
        检查一票否决规则

        Returns:
            tuple: (是否触发, 触发的规则列表)
        """
        veto_rules_config = rules_config.get('veto_rules', [])
        triggered_rules = []

        for rule in veto_rules_config:
            condition = rule.get('condition', {})
            field = condition.get('field')
            operator = condition.get('operator', '==')
            value = condition.get('value')

            if not field or field not in requirement_data:
                continue

            field_value = requirement_data[field]
            triggered = False

            if operator == '==' and str(field_value) == str(value):
                triggered = True
            elif operator == '!=' and str(field_value) != str(value):
                triggered = True
            elif operator == 'in' and field_value in value:
                triggered = True
            elif operator == 'not_in' and field_value not in value:
                triggered = True

            if triggered:
                triggered_rules.append({
                    'rule_name': rule.get('name', ''),
                    'reason': rule.get('reason', ''),
                    'condition': condition
                })

        return len(triggered_rules) > 0, triggered_rules

    def _match_similar_cases(self, requirement_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """匹配相似失败案例"""
        similar_cases = []

        # 获取关键匹配字段
        industry = requirement_data.get('industry')
        requirement_data.get('productTypes') or requirement_data.get('product_type')
        requirement_data.get('targetTakt') or requirement_data.get('takt_time_s')
        requirement_data.get('budgetStatus') or requirement_data.get('budget_status')

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
                similar_cases.append({
                    'case_code': case.case_code,
                    'project_name': case.project_name,
                    'similarity_score': similarity_score,
                    'core_failure_reason': case.core_failure_reason,
                    'early_warning_signals': json.loads(case.early_warning_signals) if case.early_warning_signals else [],
                    'lesson_learned': case.lesson_learned
                })

        # 按相似度排序
        similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)

        return similar_cases[:3]  # 返回前3个最相似的案例

    def _calculate_similarity(self, requirement_data: Dict[str, Any],
                            failure_case: FailureCase) -> float:
        """计算相似度分数（0-1）"""
        score = 0.0
        factors = 0

        # 行业匹配
        if requirement_data.get('industry') == failure_case.industry:
            score += 0.3
        factors += 0.3

        # 产品类型匹配
        req_product_types = requirement_data.get('productTypes') or requirement_data.get('product_type')
        if req_product_types and failure_case.product_types:
            case_product_types = json.loads(failure_case.product_types) if isinstance(failure_case.product_types, str) else failure_case.product_types
            if isinstance(req_product_types, str):
                req_product_types = json.loads(req_product_types) if req_product_types.startswith('[') else [req_product_types]

            if any(pt in case_product_types for pt in req_product_types):
                score += 0.2
        factors += 0.2

        # 节拍匹配（±20%范围内）
        req_takt = requirement_data.get('targetTakt') or requirement_data.get('takt_time_s')
        if req_takt and failure_case.takt_time_s:
            if abs(float(req_takt) - float(failure_case.takt_time_s)) / float(failure_case.takt_time_s) <= 0.2:
                score += 0.2
        factors += 0.2

        # 预算状态匹配
        req_budget = requirement_data.get('budgetStatus') or requirement_data.get('budget_status')
        if req_budget and failure_case.budget_status and req_budget == failure_case.budget_status:
            score += 0.1
        factors += 0.1

        # 客户项目状态匹配
        req_status = requirement_data.get('customerProjectStatus') or requirement_data.get('customer_project_status')
        if req_status and failure_case.customer_project_status and req_status == failure_case.customer_project_status:
            score += 0.1
        factors += 0.1

        # 规范状态匹配
        req_spec = requirement_data.get('specStatus') or requirement_data.get('spec_status')
        if req_spec and failure_case.spec_status and req_spec == failure_case.spec_status:
            score += 0.1
        factors += 0.1

        return score / factors if factors > 0 else 0.0

    def _generate_decision(self, total_score: int,
                          rules_config: Dict[str, Any]) -> str:
        """生成决策建议"""
        decision_thresholds = rules_config.get('scales', {}).get('decision_thresholds', [])

        for threshold in decision_thresholds:
            min_score = threshold.get('min_score', 0)
            if total_score >= min_score:
                decision = threshold.get('decision', '暂缓')
                # 映射到枚举值
                decision_map = {
                    '推荐立项': AssessmentDecisionEnum.RECOMMEND.value,
                    '有条件立项': AssessmentDecisionEnum.CONDITIONAL.value,
                    '暂缓': AssessmentDecisionEnum.DEFER.value,
                    '不建议立项': AssessmentDecisionEnum.NOT_RECOMMEND.value
                }
                return decision_map.get(decision, AssessmentDecisionEnum.DEFER.value)

        return AssessmentDecisionEnum.DEFER.value

    def _generate_risks(self, requirement_data: Dict[str, Any],
                       dimension_scores: Dict[str, int],
                       rules_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成风险列表"""
        risks = []

        # 检查各维度风险
        for dimension, score in dimension_scores.items():
            if score < 10:  # 低于10分视为高风险
                risks.append({
                    'dimension': dimension,
                    'level': 'HIGH',
                    'description': f'{dimension}维度评分较低({score}分)，存在较高风险'
                })
            elif score < 15:  # 10-15分为中等风险
                risks.append({
                    'dimension': dimension,
                    'level': 'MEDIUM',
                    'description': f'{dimension}维度评分一般({score}分)，需要关注'
                })

        # 检查需求成熟度
        req_maturity = requirement_data.get('requirementMaturity') or requirement_data.get('requirement_maturity')
        if req_maturity and req_maturity < 3:
            risks.append({
                'dimension': 'requirement',
                'level': 'HIGH',
                'description': f'需求成熟度较低({req_maturity}级)，存在需求变更风险'
            })

        # 检查是否有SOW/接口文档
        if not requirement_data.get('hasSOW') and not requirement_data.get('has_sow'):
            risks.append({
                'dimension': 'requirement',
                'level': 'MEDIUM',
                'description': '缺少客户SOW/URS文档，需求可能不明确'
            })

        return risks

    def _generate_conditions(self, decision: str, risks: List[Dict[str, Any]],
                            requirement_data: Dict[str, Any]) -> List[str]:
        """生成立项条件"""
        conditions = []

        if decision == AssessmentDecisionEnum.CONDITIONAL.value:
            # 有条件立项，需要列出条件
            high_risks = [r for r in risks if r.get('level') == 'HIGH']
            for risk in high_risks:
                conditions.append(f"解决{risk.get('description')}")

            # 检查未决事项
            source_type = requirement_data.get('source_type')
            source_id = requirement_data.get('source_id')
            if source_type and source_id:
                from app.models.sales import OpenItem
                blocking_items = self.db.query(OpenItem).filter(
                    and_(
                        OpenItem.source_type == source_type,
                        OpenItem.source_id == source_id,
                        OpenItem.blocks_quotation,
                        OpenItem.status != 'CLOSED'
                    )
                ).all()

                if blocking_items:
                    conditions.append(f"解决{len(blocking_items)}个阻塞报价的未决事项")

        return conditions

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

