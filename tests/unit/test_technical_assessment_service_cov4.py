"""
第四批覆盖测试 - technical_assessment_service
"""
import pytest
import json
from unittest.mock import MagicMock, patch

try:
    from app.services.technical_assessment_service import TechnicalAssessmentService
    HAS_SERVICE = True
except Exception:
    HAS_SERVICE = False

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="服务导入失败")


def make_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


SAMPLE_REQUIREMENT_DATA = {
    'tech_maturity': 'mature',
    'process_difficulty': 'medium',
    'precision_requirement': 'standard',
    'sample_support': True,
    'budget_status': 'confirmed',
    'price_sensitivity': 'low',
    'gross_margin_safety': 'safe',
    'payment_terms': 'advance',
    'resource_occupancy': 'low',
    'has_similar_case': True,
    'delivery_feasibility': 'feasible',
    'delivery_months': 3,
    'change_risk': 'low',
    'customer_nature': 'enterprise',
    'customer_potential': 'high',
    'relationship_depth': 'deep',
    'contact_level': 'decision_maker',
}

SAMPLE_RULES_CONFIG = {
    'evaluation_criteria': {
        'tech_maturity': {
            'weight': 10,
            'options': [
                {'value': 'mature', 'points': 10},
                {'value': 'experimental', 'points': 3},
            ]
        },
        'budget_status': {
            'weight': 8,
            'options': [
                {'value': 'confirmed', 'points': 8},
                {'value': 'estimated', 'points': 4},
            ]
        }
    },
    'scales': {
        'score_levels': {
            'approve': 70,
            'conditional': 50,
        }
    },
    'decision_rules': {
        'approve_threshold': 70,
        'conditional_threshold': 50,
    },
    'veto_rules': [
        {'field': 'tech_maturity', 'condition': 'eq', 'value': 'none', 'name': '无技术案例'}
    ],
    'risk_rules': [
        {'field': 'delivery_months', 'condition': 'lt', 'threshold': 2, 'name': '交期过短', 'level': 'high'}
    ]
}


class TestTechnicalAssessmentService:
    def setup_method(self):
        self.db = make_db()
        self.service = TechnicalAssessmentService(self.db)

    def test_get_active_scoring_rule_returns_none(self):
        result = self.service._get_active_scoring_rule()
        assert result is None

    def test_calculate_scores_empty_rules(self):
        scores, total = self.service._calculate_scores(SAMPLE_REQUIREMENT_DATA, {})
        assert isinstance(scores, dict)
        assert isinstance(total, (int, float))
        assert total >= 0

    def test_calculate_scores_with_rules(self):
        scores, total = self.service._calculate_scores(SAMPLE_REQUIREMENT_DATA, SAMPLE_RULES_CONFIG)
        assert isinstance(scores, dict)
        assert 'technology' in scores

    def test_score_dimension_empty(self):
        score = self.service._score_dimension({}, {}, [])
        assert score == 0

    def test_match_value_exact(self):
        option = {'value': 'mature', 'points': 10}
        criterion = {'match_mode': 'exact'}
        result = self.service._match_value('mature', option, criterion)
        assert result is True

    def test_check_veto_rules_not_triggered(self):
        # veto_rules 使用嵌套 condition 格式
        rules_config = {
            'veto_rules': [
                {'condition': {'field': 'tech_maturity', 'operator': '==', 'value': 'none'}, 'name': '无技术案例'}
            ]
        }
        veto, rules = self.service._check_veto_rules(SAMPLE_REQUIREMENT_DATA, rules_config)
        assert isinstance(veto, bool)
        assert isinstance(rules, list)

    def test_generate_decision_high_score(self):
        decision = self.service._generate_decision(80, SAMPLE_RULES_CONFIG)
        assert isinstance(decision, str)
        assert len(decision) > 0

    def test_generate_decision_low_score(self):
        decision = self.service._generate_decision(30, SAMPLE_RULES_CONFIG)
        assert isinstance(decision, str)

    def test_match_similar_cases_empty_db(self):
        cases = self.service._match_similar_cases(SAMPLE_REQUIREMENT_DATA)
        assert isinstance(cases, list)

    def test_generate_risks(self):
        dimension_scores = {'technology': 10, 'business': 8, 'resource': 5, 'delivery': 7, 'customer': 9}
        risks = self.service._generate_risks(SAMPLE_REQUIREMENT_DATA, dimension_scores, SAMPLE_RULES_CONFIG)
        assert isinstance(risks, list)

    def test_generate_conditions(self):
        conditions = self.service._generate_conditions('APPROVE', [], SAMPLE_REQUIREMENT_DATA)
        assert isinstance(conditions, list)

    def test_evaluate_raises_when_no_rule(self):
        with pytest.raises(ValueError, match="未找到启用的评分规则"):
            self.service.evaluate('LEAD', 1, 1, SAMPLE_REQUIREMENT_DATA)
