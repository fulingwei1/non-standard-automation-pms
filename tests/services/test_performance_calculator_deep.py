# -*- coding: utf-8 -*-
"""
PerformanceCalculator 深度覆盖测试 - N5组
重点：solution工程师五维得分计算、边界等级、复杂分支
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.engineer_performance.performance_calculator import PerformanceCalculator


def _make_mock_query(db):
    """构造可链式调用的 mock query"""
    mock_query = MagicMock()
    db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.in_.return_value = mock_query
    return mock_query


class TestCalculateGradeBoundaries(unittest.TestCase):
    """等级边界值精确测试"""

    def setUp(self):
        self.calc = PerformanceCalculator(MagicMock())

    def test_grade_boundary_84_is_A(self):
        """84分应为A级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("84")), "A")

    def test_grade_boundary_85_is_S(self):
        """85分应为S级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("85")), "S")

    def test_grade_boundary_60_is_B(self):
        """60分应为B级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("60")), "B")

    def test_grade_boundary_59_is_C(self):
        """59分应为C级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("59")), "C")

    def test_grade_boundary_40_is_C(self):
        """40分应为C级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("40")), "C")

    def test_grade_boundary_39_is_D(self):
        """39分应为D级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("39")), "D")

    def test_grade_100_is_S(self):
        """满分100应为S级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("100")), "S")

    def test_grade_0_is_D(self):
        """0分应为D级"""
        self.assertEqual(self.calc.calculate_grade(Decimal("0")), "D")


class TestCalculateMechanicalScoreEdgeCases(unittest.TestCase):
    """机械工程师分数计算边界测试"""

    def setUp(self):
        self.db = MagicMock()
        self.calc = PerformanceCalculator(self.db)

    def test_mechanical_with_debug_issues_penalty(self):
        """有调试问题时扣分逻辑"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        review1 = MagicMock(is_first_pass=True)
        review2 = MagicMock(is_first_pass=True)

        mock_query.first.return_value = period
        mock_query.all.side_effect = [
            [review1, review2],  # design_reviews (100% pass)
            [],                  # collaboration ratings
        ]
        mock_query.count.side_effect = [5, 2]  # 5 debug issues, 2 contributions

        result = self.calc.calculate_dimension_score(1, 1, "mechanical")
        # 5 debug issues × 5 = 25分扣减
        self.assertIsNotNone(result.technical_score)
        self.assertEqual(result.knowledge_score, Decimal("70"))  # 50 + 2*10

    def test_mechanical_high_first_pass_rate_capped_at_120(self):
        """技术分最高上限测试（超过85%时按比例，但上限120）"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        # 全部通过
        reviews = [MagicMock(is_first_pass=True) for _ in range(10)]
        mock_query.first.return_value = period
        mock_query.all.side_effect = [reviews, []]
        mock_query.count.side_effect = [0, 0]  # 无调试问题，无贡献

        result = self.calc.calculate_dimension_score(1, 1, "mechanical")
        # first_pass_rate=100, technical_score = min(100/85*100, 120) = min(117.6, 120) = 117.6
        self.assertGreater(result.technical_score, Decimal("100"))

    def test_mechanical_zero_debug_issues_no_penalty(self):
        """无调试问题时不扣分"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")
        review = MagicMock(is_first_pass=True)
        mock_query.first.return_value = period
        mock_query.all.side_effect = [[review], []]
        mock_query.count.side_effect = [0, 0]

        result = self.calc.calculate_dimension_score(1, 1, "mechanical")
        self.assertIsNotNone(result.technical_score)
        self.assertGreater(result.technical_score, Decimal("0"))


class TestCalculateTestScoreEdgeCases(unittest.TestCase):
    """测试工程师分数边界测试"""

    def setUp(self):
        self.db = MagicMock()
        self.calc = PerformanceCalculator(self.db)

    def test_test_score_fast_fix_bonus(self):
        """平均修复时间<4小时时获得加分"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        bug1 = MagicMock(status="resolved", fix_duration_hours=2.0)
        bug2 = MagicMock(status="closed", fix_duration_hours=1.5)

        mock_query.first.return_value = period
        mock_query.all.side_effect = [[bug1, bug2], []]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "test")
        # 所有bug已解决，resolve_rate=100%，avg_fix_time=1.75<4，+10分 → 技术分应>100
        self.assertGreater(result.technical_score, Decimal("100"))

    def test_test_score_slow_fix_penalty(self):
        """平均修复时间>8小时时扣分"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        bug1 = MagicMock(status="resolved", fix_duration_hours=10.0)
        bug2 = MagicMock(status="resolved", fix_duration_hours=12.0)

        mock_query.first.return_value = period
        mock_query.all.side_effect = [[bug1, bug2], []]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "test")
        # avg_fix_time=11.0>8，-10分 → 技术分=100-10=90
        self.assertEqual(result.technical_score, Decimal("90.00"))

    def test_test_score_knowledge_from_modules(self):
        """代码模块贡献计入知识分"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        mock_query.first.return_value = period
        mock_query.all.side_effect = [[], []]
        mock_query.count.return_value = 3  # 3 code modules

        result = self.calc.calculate_dimension_score(1, 1, "test")
        # knowledge_score = min(50 + 3*15, 100) = min(95, 100) = 95
        self.assertEqual(result.knowledge_score, Decimal("95"))


class TestCalculateElectricalScoreEdgeCases(unittest.TestCase):
    """电气工程师分数测试"""

    def setUp(self):
        self.db = MagicMock()
        self.calc = PerformanceCalculator(self.db)

    def test_electrical_full_first_pass(self):
        """全部一次调试通过"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        plc_progs = [MagicMock(is_first_pass=True) for _ in range(5)]
        mock_query.first.return_value = period
        mock_query.all.side_effect = [plc_progs, []]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "electrical")
        # first_pass_rate=100, technical_score = min(100/80*100, 120) = min(125, 120) = 120
        self.assertEqual(result.technical_score, Decimal("120.00"))

    def test_electrical_partial_first_pass(self):
        """部分一次调试通过"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")

        # 2/4 = 50% first pass rate → 50/80*100 = 62.5
        plc_progs = [
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=False),
            MagicMock(is_first_pass=False),
        ]
        mock_query.first.return_value = period
        mock_query.all.side_effect = [plc_progs, []]
        mock_query.count.return_value = 0

        result = self.calc.calculate_dimension_score(1, 1, "electrical")
        self.assertEqual(result.technical_score, Decimal("62.50"))


class TestCalculateSolutionScore(unittest.TestCase):
    """方案工程师六维得分计算（重要：此前未覆盖）"""

    def setUp(self):
        self.db = MagicMock()
        self.calc = PerformanceCalculator(self.db)

    def _build_solution_mock(self, solutions=None, templates=0, collaboration_ratings=None):
        """构建 solution 测试 mock"""
        mock_query = _make_mock_query(self.db)
        period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")
        mock_query.first.return_value = period

        actual_solutions = solutions if solutions is not None else []
        actual_ratings = collaboration_ratings if collaboration_ratings is not None else []

        mock_query.all.side_effect = [
            actual_solutions,    # PresaleSolution.all()
            actual_ratings,      # CollaborationRating.all()
        ]
        mock_query.count.return_value = templates  # PresaleSolutionTemplate count
        return mock_query

    def test_solution_no_solutions_uses_defaults(self):
        """无方案时使用默认分值"""
        with patch.dict('sys.modules', {
            'app.models.presale': MagicMock(),
            'app.models.sales': MagicMock(),
        }):
            mock_query = _make_mock_query(self.db)
            period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")
            mock_query.first.return_value = period
            mock_query.all.side_effect = [[], []]
            mock_query.count.return_value = 0

            result = self.calc._calculate_solution_score(1, period)
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.solution_success_score)

    def test_solution_with_templates_knowledge_score(self):
        """方案模板贡献影响知识分"""
        with patch.dict('sys.modules', {
            'app.models.presale': MagicMock(),
            'app.models.sales': MagicMock(),
        }):
            mock_query = _make_mock_query(self.db)
            period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")
            mock_query.first.return_value = period
            mock_query.all.side_effect = [[], []]
            mock_query.count.return_value = 2  # 2 templates → 50 + 2*15 = 80

            result = self.calc._calculate_solution_score(1, period)
            self.assertEqual(result.knowledge_score, Decimal("80"))

    def test_calculate_dimension_score_solution_type(self):
        """通过 calculate_dimension_score 调用方案工程师路径"""
        with patch.dict('sys.modules', {
            'app.models.presale': MagicMock(),
            'app.models.sales': MagicMock(),
        }):
            mock_query = _make_mock_query(self.db)
            period = MagicMock(id=1, start_date="2025-01-01", end_date="2025-12-31")
            mock_query.first.return_value = period
            mock_query.all.side_effect = [[], []]
            mock_query.count.return_value = 0

            result = self.calc.calculate_dimension_score(1, 1, "solution")
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.solution_success_score)


class TestCalculateTotalScoreEdgeCases(unittest.TestCase):
    """总分计算边界测试"""

    def setUp(self):
        self.calc = PerformanceCalculator(MagicMock())

    def _make_scores(self, **overrides):
        from app.schemas.engineer_performance import EngineerDimensionScore
        defaults = dict(
            technical_score=Decimal("80"),
            execution_score=Decimal("70"),
            cost_quality_score=Decimal("75"),
            knowledge_score=Decimal("60"),
            collaboration_score=Decimal("85"),
        )
        defaults.update(overrides)
        return EngineerDimensionScore(**defaults)

    def _make_config(self, t=30, e=25, c=20, k=15, co=10):
        cfg = MagicMock()
        cfg.technical_weight = t
        cfg.execution_weight = e
        cfg.cost_quality_weight = c
        cfg.knowledge_weight = k
        cfg.collaboration_weight = co
        return cfg

    def test_total_score_solution_no_solution_score_uses_standard(self):
        """solution类型但无solution_success_score时使用标准计算"""
        scores = self._make_scores(solution_success_score=None)
        config = self._make_config()

        result = self.calc.calculate_total_score(scores, config, job_type="solution")
        # 应当 fallback 到标准加权
        expected = (
            Decimal("80") * 30 / 100 +
            Decimal("70") * 25 / 100 +
            Decimal("75") * 20 / 100 +
            Decimal("60") * 15 / 100 +
            Decimal("85") * 10 / 100
        )
        self.assertEqual(result, Decimal(str(round(expected, 2))))

    def test_total_score_all_zero_weights(self):
        """全0权重时总分应为0"""
        scores = self._make_scores()
        config = self._make_config(t=0, e=0, c=0, k=0, co=0)

        result = self.calc.calculate_total_score(scores, config)
        self.assertEqual(result, Decimal("0"))

    def test_total_score_single_dimension_100_percent(self):
        """单维度100%权重时总分等于该维度分"""
        scores = self._make_scores()
        config = self._make_config(t=100, e=0, c=0, k=0, co=0)

        result = self.calc.calculate_total_score(scores, config)
        self.assertEqual(result, Decimal("80.00"))

    def test_get_collaboration_avg_multiple_ratings(self):
        """多人协作评分取平均"""
        db = MagicMock()
        calc = PerformanceCalculator(db)

        mock_query = _make_mock_query(db)
        r1 = MagicMock(communication_score=5, response_score=5, delivery_score=5, interface_score=5)
        r2 = MagicMock(communication_score=3, response_score=3, delivery_score=3, interface_score=3)
        mock_query.all.return_value = [r1, r2]

        result = calc._get_collaboration_avg(1, 1)
        # r1: 5+5+5+5=20, r2: 3+3+3+3=12, total=32
        # avg = 32 / (2*4) * 20 = 32/8*20 = 80
        self.assertEqual(result, Decimal("80.00"))


if __name__ == "__main__":
    unittest.main()
