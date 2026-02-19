# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 线索评分计算 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.lead_priority_scoring.level_determination import LevelDeterminationMixin
    from app.services.lead_priority_scoring.constants import ScoringConstants
    from app.services.lead_priority_scoring.lead_scoring import LeadScoringMixin
    HAS_LEAD = True
except Exception:
    HAS_LEAD = False

pytestmark = pytest.mark.skipif(not HAS_LEAD, reason="lead_scoring 导入失败")


class ConcreteLeadScoring(LevelDeterminationMixin):
    """用于测试的具体实现类"""
    pass


class TestLevelDetermination:
    def setup_method(self):
        self.scorer = ConcreteLeadScoring()

    def test_determine_priority_p1(self):
        """高分且高紧急度 -> P1"""
        result = self.scorer._determine_priority_level(total_score=85, urgency_score=9)
        assert result == "P1"

    def test_determine_priority_p2_high_score(self):
        """高分低紧急度 -> P2"""
        result = self.scorer._determine_priority_level(total_score=75, urgency_score=5)
        assert result == "P2"

    def test_determine_priority_p3_low_score_high_urgency(self):
        """低分高紧急度 -> P3"""
        result = self.scorer._determine_priority_level(total_score=60, urgency_score=9)
        assert result == "P3"

    def test_determine_priority_p4_low_both(self):
        """低分低紧急度 -> P4"""
        result = self.scorer._determine_priority_level(total_score=50, urgency_score=4)
        assert result == "P4"

    def test_determine_importance_high(self):
        """总分>=80 -> HIGH"""
        result = self.scorer._determine_importance_level(85)
        assert result == "HIGH"

    def test_determine_importance_medium(self):
        """总分60-79 -> MEDIUM"""
        result = self.scorer._determine_importance_level(65)
        assert result == "MEDIUM"

    def test_determine_importance_low(self):
        """总分<60 -> LOW"""
        result = self.scorer._determine_importance_level(40)
        assert result == "LOW"

    def test_determine_urgency_high(self):
        """紧急分>=8 -> HIGH"""
        result = self.scorer._determine_urgency_level(8)
        assert result == "HIGH"

    def test_determine_urgency_medium(self):
        """紧急分5-7 -> MEDIUM"""
        result = self.scorer._determine_urgency_level(6)
        assert result == "MEDIUM"

    def test_determine_urgency_low(self):
        """紧急分<5 -> LOW"""
        result = self.scorer._determine_urgency_level(3)
        assert result == "LOW"


class TestScoringConstants:
    def test_customer_importance_a_grade(self):
        """A级客户应有最高分"""
        score_a = ScoringConstants.CUSTOMER_IMPORTANCE_SCORES.get("A", 0)
        score_e = ScoringConstants.CUSTOMER_IMPORTANCE_SCORES.get("E", 0)
        assert score_a > score_e

    def test_contract_amount_scores_sorted(self):
        """金额评分应按金额降序排列"""
        amounts = [item[0] for item in ScoringConstants.CONTRACT_AMOUNT_SCORES]
        assert amounts == sorted(amounts, reverse=True)

    def test_win_rate_scores_exist(self):
        """中标概率评分表存在"""
        assert len(ScoringConstants.WIN_RATE_SCORES) > 0


class TestLeadScoringMixin:
    def test_calculate_lead_priority_not_found(self):
        """线索不存在时抛出ValueError"""
        class ConcreteMixin(LeadScoringMixin):
            def __init__(self):
                self.db = MagicMock()

        scorer = ConcreteMixin()
        scorer.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="不存在"):
            scorer.calculate_lead_priority(999)

    def test_calculate_lead_priority_returns_dict(self):
        """评分返回包含必要字段的字典"""
        class ConcreteMixin(LeadScoringMixin):
            def __init__(self):
                self.db = MagicMock()
            def _calculate_customer_importance(self, lead): return 15
            def _calculate_contract_amount_score(self, lead): return 20
            def _calculate_win_rate_score(self, lead): return 15
            def _calculate_requirement_maturity_score(self, lead): return 12
            def _calculate_urgency_score(self, lead): return 7
            def _calculate_relationship_score(self, lead): return 8
            def _get_customer_level_description(self, lead): return "B级客户"
            def _get_contract_amount_description(self, lead): return "50-100万"
            def _get_win_rate_description(self, lead): return "60-80%"
            def _get_requirement_maturity_description(self, lead): return "较明确"
            def _get_urgency_description(self, lead): return "较紧急"
            def _get_relationship_description(self, lead): return "良好"
            def _determine_priority_level(self, total, urgency): return "P2"
            def _determine_importance_level(self, total): return "MEDIUM"
            def _determine_urgency_level(self, urgency): return "MEDIUM"

        scorer = ConcreteMixin()
        mock_lead = MagicMock()
        mock_lead.id = 1
        mock_lead.lead_code = "LEAD-001"
        scorer.db.query.return_value.filter.return_value.first.return_value = mock_lead

        result = scorer.calculate_lead_priority(1)
        assert result["lead_id"] == 1
        assert result["total_score"] == 77
        assert result["max_score"] == 100
        assert "scores" in result
        assert result["is_key_lead"] is True  # 77 >= 70
        assert result["priority_level"] == "P2"
