# -*- coding: utf-8 -*-
"""
技术评估服务单元测试

测试内容：
- evaluate: 执行技术评估
- _get_active_scoring_rule: 获取启用的评分规则
- _calculate_scores: 计算五维分数
- _score_dimension: 计算单个维度分数
- _match_value: 匹配字段值
- _check_veto_rules: 检查一票否决规则
- _match_similar_cases: 匹配相似案例
- _calculate_similarity: 计算相似度
- _generate_decision: 生成决策建议
- _generate_risks: 生成风险列表
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.services.technical_assessment_service import TechnicalAssessmentService


# ============================================================================
# Mock 辅助类
# ============================================================================


class MockScoringRule:
    """模拟评分规则"""

    def __init__(self, rule_id: int, rules_json: str, is_active: bool = True):
        self.id = rule_id
        self.rules_json = rules_json
        self.is_active = is_active
        self.created_at = datetime.now()


class MockFailureCase:
    """模拟失败案例"""

    def __init__(
        self,
        case_code: str,
        project_name: str,
        industry: str = None,
        product_types: str = None,
        takt_time_s: float = None,
        budget_status: str = None,
        customer_project_status: str = None,
        spec_status: str = None,
        core_failure_reason: str = None,
        early_warning_signals: str = None,
        lesson_learned: str = None,
    ):
        self.case_code = case_code
        self.project_name = project_name
        self.industry = industry
        self.product_types = product_types
        self.takt_time_s = takt_time_s
        self.budget_status = budget_status
        self.customer_project_status = customer_project_status
        self.spec_status = spec_status
        self.core_failure_reason = core_failure_reason
        self.early_warning_signals = early_warning_signals
        self.lesson_learned = lesson_learned


class MockTechnicalAssessment:
    """模拟技术评估"""

    def __init__(self, assessment_id: int, total_score: int = 0):
        self.id = assessment_id
        self.total_score = total_score


# ============================================================================
# 初始化测试
# ============================================================================


@pytest.mark.unit
class TestTechnicalAssessmentServiceInit:
    """测试服务初始化"""

    def test_init(self):
        """测试初始化"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)
        assert service.db == db


# ============================================================================
# _get_active_scoring_rule 测试
# ============================================================================


@pytest.mark.unit
class TestGetActiveScoringRule:
    """测试获取启用的评分规则"""

    def test_get_active_scoring_rule_found(self):
        """测试找到启用的评分规则"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        mock_rule = MockScoringRule(1, '{"evaluation_criteria": {}}')
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
        mock_rule
        )

        result = service._get_active_scoring_rule()
        assert result == mock_rule

    def test_get_active_scoring_rule_not_found(self):
        """测试未找到启用的评分规则"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
        None
        )

        result = service._get_active_scoring_rule()
        assert result is None


# ============================================================================
# _calculate_scores 测试
# ============================================================================


@pytest.mark.unit
class TestCalculateScores:
    """测试计算五维分数"""

    def test_calculate_scores_empty_data(self):
        """测试空数据"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {}
        rules_config = {"evaluation_criteria": {}, "scales": {}}

        dimension_scores, total_score = service._calculate_scores(
        requirement_data, rules_config
        )

        assert dimension_scores["technology"] == 0
        assert dimension_scores["business"] == 0
        assert dimension_scores["resource"] == 0
        assert dimension_scores["delivery"] == 0
        assert dimension_scores["customer"] == 0
        assert total_score == 0

    def test_calculate_scores_with_data(self):
        """测试有数据的评分"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_maturity": "high", "budget_status": "confirmed"}
        rules_config = {
        "evaluation_criteria": {
        "tech_maturity": {
        "field": "tech_maturity",
        "max_points": 10,
        "options": [{"value": "high", "points": 10}],
        },
        "budget_status": {
        "field": "budget_status",
        "max_points": 10,
        "options": [{"value": "confirmed", "points": 10}],
        },
        },
        "scales": {},
        }

        dimension_scores, total_score = service._calculate_scores(
        requirement_data, rules_config
        )

        # 应该有一些分数
        assert total_score >= 0


# ============================================================================
# _score_dimension 测试
# ============================================================================


@pytest.mark.unit
class TestScoreDimension:
    """测试计算单个维度分数"""

    def test_score_dimension_no_criteria(self):
        """测试无评分标准"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_maturity": "high"}
        evaluation_criteria = {}
        criteria_keys = ["tech_maturity"]

        result = service._score_dimension(
        requirement_data, evaluation_criteria, criteria_keys
        )
        assert result == 0

    def test_score_dimension_with_match(self):
        """测试有匹配的评分"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_maturity": "high"}
        evaluation_criteria = {
        "tech_maturity": {
        "field": "tech_maturity",
        "max_points": 10,
        "options": [
        {"value": "low", "points": 2},
        {"value": "medium", "points": 5},
        {"value": "high", "points": 10},
        ],
        }
        }
        criteria_keys = ["tech_maturity"]

        result = service._score_dimension(
        requirement_data, evaluation_criteria, criteria_keys
        )
        assert result == 20  # 10/10 * 20 = 20

    def test_score_dimension_no_match(self):
        """测试无匹配的评分"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_maturity": "unknown"}
        evaluation_criteria = {
        "tech_maturity": {
        "field": "tech_maturity",
        "max_points": 10,
        "options": [{"value": "high", "points": 10}],
        }
        }
        criteria_keys = ["tech_maturity"]

        result = service._score_dimension(
        requirement_data, evaluation_criteria, criteria_keys
        )
        assert result == 0


# ============================================================================
# _match_value 测试
# ============================================================================


@pytest.mark.unit
class TestMatchValue:
    """测试匹配字段值"""

    def test_match_value_exact_match(self):
        """测试精确匹配"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        result = service._match_value(
        "high", {"value": "high"}, {"match_mode": "exact"}
        )
        assert result is True

    def test_match_value_exact_no_match(self):
        """测试精确匹配不匹配"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        result = service._match_value(
        "high", {"value": "low"}, {"match_mode": "exact"}
        )
        assert result is False

    def test_match_value_contains_match(self):
        """测试包含匹配"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        result = service._match_value(
        "high precision", {"keywords": ["high", "precision"]}, {"match_mode": "contains"}
        )
        assert result is True

    def test_match_value_contains_no_match(self):
        """测试包含匹配不匹配"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        result = service._match_value(
        "low precision", {"keywords": ["high"]}, {"match_mode": "contains"}
        )
        assert result is False

    def test_match_value_default_mode(self):
        """测试默认匹配模式"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        # 默认为exact模式
        result = service._match_value("high", {"value": "high"}, {})
        assert result is True


# ============================================================================
# _check_veto_rules 测试
# ============================================================================


@pytest.mark.unit
class TestCheckVetoRules:
    """测试检查一票否决规则"""

    def test_check_veto_rules_no_rules(self):
        """测试无否决规则"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"field1": "value1"}
        rules_config = {"veto_rules": []}

        triggered, rules = service._check_veto_rules(requirement_data, rules_config)

        assert triggered is False
        assert rules == []

    def test_check_veto_rules_triggered_equal(self):
        """测试触发等于条件"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_risk": "unacceptable"}
        rules_config = {
        "veto_rules": [
        {
        "name": "技术风险一票否决",
        "reason": "技术风险不可接受",
        "condition": {
        "field": "tech_risk",
        "operator": "==",
        "value": "unacceptable",
        },
        }
        ]
        }

        triggered, rules = service._check_veto_rules(requirement_data, rules_config)

        assert triggered is True
        assert len(rules) == 1
        assert rules[0]["rule_name"] == "技术风险一票否决"

    def test_check_veto_rules_not_triggered(self):
        """测试未触发"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"tech_risk": "acceptable"}
        rules_config = {
        "veto_rules": [
        {
        "name": "技术风险一票否决",
        "reason": "技术风险不可接受",
        "condition": {
        "field": "tech_risk",
        "operator": "==",
        "value": "unacceptable",
        },
        }
        ]
        }

        triggered, rules = service._check_veto_rules(requirement_data, rules_config)

        assert triggered is False
        assert rules == []

    def test_check_veto_rules_in_operator(self):
        """测试in操作符"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"status": "rejected"}
        rules_config = {
        "veto_rules": [
        {
        "name": "状态否决",
        "reason": "状态不允许",
        "condition": {
        "field": "status",
        "operator": "in",
        "value": ["rejected", "cancelled"],
        },
        }
        ]
        }

        triggered, rules = service._check_veto_rules(requirement_data, rules_config)

        assert triggered is True


# ============================================================================
# _calculate_similarity 测试
# ============================================================================


@pytest.mark.unit
class TestCalculateSimilarity:
    """测试计算相似度"""

    def test_calculate_similarity_same_industry(self):
        """测试相同行业"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"industry": "汽车电子"}
        failure_case = MockFailureCase("CASE-001", "项目A", industry="汽车电子")

        result = service._calculate_similarity(requirement_data, failure_case)

        assert result > 0  # 应该有相似度分数

    def test_calculate_similarity_different_industry(self):
        """测试不同行业"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"industry": "汽车电子"}
        failure_case = MockFailureCase("CASE-001", "项目A", industry="消费电子")

        result = service._calculate_similarity(requirement_data, failure_case)

        # 行业不匹配，相似度较低
        assert result < 0.5

    def test_calculate_similarity_full_match(self):
        """测试完全匹配"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {
        "industry": "汽车电子",
        "productTypes": '["ICT", "FCT"]',
        "targetTakt": 30,
        "budgetStatus": "confirmed",
        "customerProjectStatus": "active",
        "specStatus": "finalized",
        }
        failure_case = MockFailureCase(
        "CASE-001",
        "项目A",
        industry="汽车电子",
        product_types='["ICT", "FCT"]',
        takt_time_s=30,
        budget_status="confirmed",
        customer_project_status="active",
        spec_status="finalized",
        )

        result = service._calculate_similarity(requirement_data, failure_case)

        assert result > 0.5  # 高相似度


# ============================================================================
# _generate_decision 测试
# ============================================================================


@pytest.mark.unit
class TestGenerateDecision:
    """测试生成决策建议"""

    def test_generate_decision_high_score(self):
        """测试高分决策"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        rules_config = {
        "scales": {
        "decision_thresholds": [
        {"min_score": 80, "decision": "推荐立项"},
        {"min_score": 60, "decision": "有条件立项"},
        {"min_score": 40, "decision": "暂缓"},
        {"min_score": 0, "decision": "不建议立项"},
        ]
        }
        }

        result = service._generate_decision(85, rules_config)
        assert result == "RECOMMEND"

    def test_generate_decision_medium_score(self):
        """测试中等分数决策"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        rules_config = {
        "scales": {
        "decision_thresholds": [
        {"min_score": 80, "decision": "推荐立项"},
        {"min_score": 60, "decision": "有条件立项"},
        {"min_score": 40, "decision": "暂缓"},
        {"min_score": 0, "decision": "不建议立项"},
        ]
        }
        }

        result = service._generate_decision(65, rules_config)
        assert result == "CONDITIONAL"

    def test_generate_decision_low_score(self):
        """测试低分决策"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        rules_config = {
        "scales": {
        "decision_thresholds": [
        {"min_score": 80, "decision": "推荐立项"},
        {"min_score": 60, "decision": "有条件立项"},
        {"min_score": 40, "decision": "暂缓"},
        {"min_score": 0, "decision": "不建议立项"},
        ]
        }
        }

        result = service._generate_decision(30, rules_config)
        assert result == "NOT_RECOMMEND"


# ============================================================================
# _generate_risks 测试
# ============================================================================


@pytest.mark.unit
class TestGenerateRisks:
    """测试生成风险列表"""

    def test_generate_risks_high_risk_dimension(self):
        """测试高风险维度"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {}
        dimension_scores = {
        "technology": 5,  # 低于10，高风险
        "business": 15,
        "resource": 15,
        "delivery": 15,
        "customer": 15,
        }
        rules_config = {}

        risks = service._generate_risks(requirement_data, dimension_scores, rules_config)

        high_risk = [r for r in risks if r["level"] == "HIGH"]
        assert len(high_risk) >= 1
        assert any("technology" in r["dimension"] for r in high_risk)

    def test_generate_risks_medium_risk_dimension(self):
        """测试中等风险维度"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {}
        dimension_scores = {
        "technology": 12,  # 10-15，中等风险
        "business": 18,
        "resource": 18,
        "delivery": 18,
        "customer": 18,
        }
        rules_config = {}

        risks = service._generate_risks(requirement_data, dimension_scores, rules_config)

        medium_risk = [r for r in risks if r["level"] == "MEDIUM"]
        assert len(medium_risk) >= 1

    def test_generate_risks_low_requirement_maturity(self):
        """测试低需求成熟度风险"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        requirement_data = {"requirementMaturity": 2}
        dimension_scores = {
        "technology": 18,
        "business": 18,
        "resource": 18,
        "delivery": 18,
        "customer": 18,
        }
        rules_config = {}

        risks = service._generate_risks(requirement_data, dimension_scores, rules_config)

        req_risk = [r for r in risks if r["dimension"] == "requirement"]
        assert len(req_risk) >= 1


# ============================================================================
# evaluate 测试
# ============================================================================


@pytest.mark.unit
class TestEvaluate:
    """测试执行技术评估"""

    def test_evaluate_no_scoring_rule(self):
        """测试无评分规则"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
        None
        )

        with pytest.raises(ValueError, match="未找到启用的评分规则"):
            service.evaluate("LEAD", 1, 1, {})


            # ============================================================================
            # 集成测试
            # ============================================================================


@pytest.mark.unit
class TestTechnicalAssessmentIntegration:
    """测试技术评估集成场景"""

    def test_service_is_importable(self):
        """测试服务可导入"""
        from app.services.technical_assessment_service import TechnicalAssessmentService

        assert TechnicalAssessmentService is not None

    def test_all_methods_exist(self):
        """测试所有方法存在"""
        db = MagicMock(spec=Session)
        service = TechnicalAssessmentService(db)

        assert hasattr(service, "evaluate")
        assert hasattr(service, "_get_active_scoring_rule")
        assert hasattr(service, "_calculate_scores")
        assert hasattr(service, "_score_dimension")
        assert hasattr(service, "_match_value")
        assert hasattr(service, "_check_veto_rules")
        assert hasattr(service, "_match_similar_cases")
        assert hasattr(service, "_calculate_similarity")
        assert hasattr(service, "_generate_decision")
        assert hasattr(service, "_generate_risks")
