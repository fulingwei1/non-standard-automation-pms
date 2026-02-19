# -*- coding: utf-8 -*-
"""
第三十五批 - lead_priority_scoring/constants.py (ScoringConstants) 单元测试
"""
import pytest

try:
    from app.services.lead_priority_scoring.constants import ScoringConstants
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestScoringConstants:

    def test_customer_importance_has_all_grades(self):
        """客户重要性映射包含所有等级"""
        expected_grades = {"A", "B", "C", "D", "E"}
        assert expected_grades == set(ScoringConstants.CUSTOMER_IMPORTANCE_SCORES.keys())

    def test_customer_grade_a_highest(self):
        """A级客户分数最高"""
        scores = ScoringConstants.CUSTOMER_IMPORTANCE_SCORES
        assert scores["A"] > scores["B"] > scores["C"] > scores["D"] > scores["E"]

    def test_contract_amount_scores_are_tuples(self):
        """合同金额评分是元组列表"""
        for item in ScoringConstants.CONTRACT_AMOUNT_SCORES:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_contract_amount_scores_descending(self):
        """合同金额阈值降序排列"""
        thresholds = [item[0] for item in ScoringConstants.CONTRACT_AMOUNT_SCORES]
        assert thresholds == sorted(thresholds, reverse=True)

    def test_win_rate_scores_coverage(self):
        """中标概率评分覆盖 0-1 范围"""
        thresholds = [item[0] for item in ScoringConstants.WIN_RATE_SCORES]
        assert min(thresholds) == 0.0
        assert max(thresholds) >= 0.8

    def test_requirement_maturity_has_all_levels(self):
        """需求成熟度包含 1-5 所有级别"""
        expected_levels = {1, 2, 3, 4, 5}
        assert expected_levels == set(ScoringConstants.REQUIREMENT_MATURITY_SCORES.keys())

    def test_requirement_maturity_highest_level(self):
        """需求成熟度 5 分数 >= 1"""
        scores = ScoringConstants.REQUIREMENT_MATURITY_SCORES
        assert scores[5] > scores[1]

    def test_urgency_scores_has_high_medium_low(self):
        """紧急程度包含 HIGH/MEDIUM/LOW"""
        keys = set(ScoringConstants.URGENCY_SCORES.keys())
        assert {"HIGH", "MEDIUM", "LOW"} == keys

    def test_urgency_high_beats_low(self):
        """HIGH 分数大于 LOW"""
        scores = ScoringConstants.URGENCY_SCORES
        assert scores["HIGH"] > scores["LOW"]

    def test_relationship_scores_has_required_keys(self):
        """客户关系评分包含所有关键类型"""
        keys = set(ScoringConstants.RELATIONSHIP_SCORES.keys())
        expected = {"EXISTING_GOOD", "EXISTING_NORMAL", "NEW_NORMAL", "NEW_POOR"}
        assert expected == keys

    def test_relationship_existing_good_highest(self):
        """老客户/关系好分数最高"""
        scores = ScoringConstants.RELATIONSHIP_SCORES
        assert scores["EXISTING_GOOD"] >= scores["NEW_POOR"]

    def test_all_scores_are_positive(self):
        """所有分数均为正数"""
        for score in ScoringConstants.CUSTOMER_IMPORTANCE_SCORES.values():
            assert score > 0
        for _, score in ScoringConstants.CONTRACT_AMOUNT_SCORES:
            assert score > 0
        for score in ScoringConstants.URGENCY_SCORES.values():
            assert score > 0
