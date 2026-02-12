# -*- coding: utf-8 -*-
"""PerformanceCalculator 单元测试"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.engineer_performance.performance_calculator import PerformanceCalculator


class TestPerformanceCalculator(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.calc = PerformanceCalculator(self.db)

    def _mock_query(self):
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        return mock_query

    # --- calculate_grade ---
    def test_grade_s(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("90")), "S")

    def test_grade_a(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("75")), "A")

    def test_grade_b(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("65")), "B")

    def test_grade_c(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("50")), "C")

    def test_grade_d(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("30")), "D")

    def test_grade_boundary_85(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("85")), "S")

    def test_grade_boundary_70(self):
        self.assertEqual(self.calc.calculate_grade(Decimal("70")), "A")

    # --- calculate_dimension_score ---
    def test_calculate_dimension_score_invalid_period(self):
        mock_query = self._mock_query()
        mock_query.first.return_value = None

        with self.assertRaises(ValueError):
            self.calc.calculate_dimension_score(1, 999, "mechanical")

    def test_calculate_dimension_score_unknown_job_type(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1)
        mock_query.first.return_value = period

        with self.assertRaises(ValueError):
            self.calc.calculate_dimension_score(1, 1, "unknown_type")

    # --- _calculate_mechanical_score ---
    def test_mechanical_score_no_reviews(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-06-30")
        mock_query.first.return_value = period
        mock_query.all.return_value = []  # no design reviews
        mock_query.count.return_value = 0  # no debug issues, no contributions

        result = self.calc.calculate_dimension_score(1, 1, "mechanical")
        self.assertIsNotNone(result.technical_score)
        self.assertIsNotNone(result.collaboration_score)

    def test_mechanical_score_with_reviews(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-06-30")

        review1 = MagicMock(is_first_pass=True)
        review2 = MagicMock(is_first_pass=False)

        # Sequence: period query, design reviews, debug issues count, contributions count, collaboration ratings
        mock_query.first.return_value = period
        mock_query.all.side_effect = [
            [review1, review2],  # design reviews
            [],  # collaboration ratings
        ]
        mock_query.count.side_effect = [2, 1]  # debug issues, contributions

        result = self.calc.calculate_dimension_score(1, 1, "mechanical")
        self.assertIsNotNone(result.technical_score)

    # --- _calculate_test_score ---
    def test_test_score_no_bugs(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-06-30")
        mock_query.first.return_value = period
        mock_query.all.side_effect = [
            [],  # bugs
            [],  # collaboration
        ]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "test")
        self.assertIsNotNone(result.technical_score)

    def test_test_score_with_bugs(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-06-30")

        bug1 = MagicMock(status="resolved", fix_duration_hours=2)
        bug2 = MagicMock(status="open", fix_duration_hours=None)

        mock_query.first.return_value = period
        mock_query.all.side_effect = [
            [bug1, bug2],  # bugs
            [],  # collaboration
        ]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "test")
        self.assertIsNotNone(result.technical_score)

    # --- _calculate_electrical_score ---
    def test_electrical_score(self):
        mock_query = self._mock_query()
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-06-30")
        mock_query.first.return_value = period
        mock_query.all.side_effect = [
            [],  # plc programs
            [],  # collaboration
        ]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "electrical")
        self.assertIsNotNone(result.technical_score)

    # --- _get_collaboration_avg ---
    def test_collaboration_avg_no_ratings(self):
        mock_query = self._mock_query()
        mock_query.all.return_value = []

        result = self.calc._get_collaboration_avg(1, 1)
        self.assertEqual(result, Decimal("75"))

    def test_collaboration_avg_with_ratings(self):
        mock_query = self._mock_query()
        rating = MagicMock()
        rating.communication_score = 4
        rating.response_score = 4
        rating.delivery_score = 3
        rating.interface_score = 3
        mock_query.all.return_value = [rating]

        result = self.calc._get_collaboration_avg(1, 1)
        # (4+4+3+3) / (1*4) * 20 = 14/4*20 = 70
        self.assertEqual(result, Decimal("70"))

    # --- calculate_total_score ---
    def test_calculate_total_score_normal(self):
        from app.schemas.engineer_performance import EngineerDimensionScore
        scores = EngineerDimensionScore(
            technical_score=Decimal("80"),
            execution_score=Decimal("70"),
            cost_quality_score=Decimal("75"),
            knowledge_score=Decimal("60"),
            collaboration_score=Decimal("85"),
        )
        config = MagicMock()
        config.technical_weight = 30
        config.execution_weight = 25
        config.cost_quality_weight = 20
        config.knowledge_weight = 15
        config.collaboration_weight = 10

        result = self.calc.calculate_total_score(scores, config)
        # 80*0.3 + 70*0.25 + 75*0.2 + 60*0.15 + 85*0.1 = 24+17.5+15+9+8.5 = 74
        self.assertEqual(result, Decimal("74.00"))

    def test_calculate_total_score_solution(self):
        from app.schemas.engineer_performance import EngineerDimensionScore
        scores = EngineerDimensionScore(
            technical_score=Decimal("80"),
            execution_score=Decimal("70"),
            cost_quality_score=Decimal("75"),
            knowledge_score=Decimal("60"),
            collaboration_score=Decimal("85"),
            solution_success_score=Decimal("90"),
        )
        config = MagicMock()

        result = self.calc.calculate_total_score(scores, config, job_type="solution")
        # 80*0.25 + 90*0.3 + 70*0.2 + 60*0.15 + 85*0.1 = 20+27+14+9+8.5 = 78.5
        self.assertEqual(result, Decimal("78.50"))


if __name__ == "__main__":
    unittest.main()
