# -*- coding: utf-8 -*-
"""
绩效计算服务单元测试

目标：
1. 只mock外部依赖（db.query等数据库操作）
2. 测试核心业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 覆盖率70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

from app.services.engineer_performance.performance_calculator import PerformanceCalculator
from app.schemas.engineer_performance import EngineerDimensionScore


class TestPerformanceCalculatorGrade(unittest.TestCase):
    """测试等级计算方法"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)

    def test_calculate_grade_s(self):
        """测试S等级（优秀）"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('85')), 'S')
        self.assertEqual(self.calculator.calculate_grade(Decimal('92')), 'S')
        self.assertEqual(self.calculator.calculate_grade(Decimal('100')), 'S')

    def test_calculate_grade_a(self):
        """测试A等级（良好）"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('70')), 'A')
        self.assertEqual(self.calculator.calculate_grade(Decimal('77')), 'A')
        self.assertEqual(self.calculator.calculate_grade(Decimal('84')), 'A')

    def test_calculate_grade_b(self):
        """测试B等级（合格）"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('60')), 'B')
        self.assertEqual(self.calculator.calculate_grade(Decimal('65')), 'B')
        self.assertEqual(self.calculator.calculate_grade(Decimal('69')), 'B')

    def test_calculate_grade_c(self):
        """测试C等级（待改进）"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('40')), 'C')
        self.assertEqual(self.calculator.calculate_grade(Decimal('50')), 'C')
        self.assertEqual(self.calculator.calculate_grade(Decimal('59')), 'C')

    def test_calculate_grade_d(self):
        """测试D等级（不合格）"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('0')), 'D')
        self.assertEqual(self.calculator.calculate_grade(Decimal('20')), 'D')
        self.assertEqual(self.calculator.calculate_grade(Decimal('39')), 'D')

    def test_calculate_grade_boundary(self):
        """测试边界值"""
        self.assertEqual(self.calculator.calculate_grade(Decimal('84.9')), 'A')
        self.assertEqual(self.calculator.calculate_grade(Decimal('85.0')), 'S')
        self.assertEqual(self.calculator.calculate_grade(Decimal('69.9')), 'B')
        self.assertEqual(self.calculator.calculate_grade(Decimal('70.0')), 'A')
        self.assertEqual(self.calculator.calculate_grade(Decimal('59.9')), 'C')
        self.assertEqual(self.calculator.calculate_grade(Decimal('60.0')), 'B')
        self.assertEqual(self.calculator.calculate_grade(Decimal('39.9')), 'D')
        self.assertEqual(self.calculator.calculate_grade(Decimal('40.0')), 'C')


class TestDimensionScoreRouting(unittest.TestCase):
    """测试五维得分计算的路由逻辑"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)

    def test_calculate_dimension_score_period_not_found(self):
        """测试考核周期不存在"""
        # Mock db.query返回空结果
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.calculator.calculate_dimension_score(1, 999, 'mechanical')
        
        self.assertIn("考核周期不存在", str(context.exception))

    def test_calculate_dimension_score_invalid_job_type(self):
        """测试未知岗位类型"""
        # Mock period存在
        mock_period = MagicMock()
        mock_period.id = 1
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_period
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.calculator.calculate_dimension_score(1, 1, 'unknown_job')
        
        self.assertIn("未知的岗位类型", str(context.exception))

    @patch.object(PerformanceCalculator, '_calculate_mechanical_score')
    def test_calculate_dimension_score_mechanical(self, mock_mech_score):
        """测试路由到机械工程师计算"""
        # Mock period
        mock_period = MagicMock()
        mock_period.id = 1
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 3, 31)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_period
        self.db.query.return_value = mock_query

        # Mock返回值
        expected_score = EngineerDimensionScore(
            technical_score=Decimal('80'),
            execution_score=Decimal('75'),
            cost_quality_score=Decimal('70'),
            knowledge_score=Decimal('65'),
            collaboration_score=Decimal('75')
        )
        mock_mech_score.return_value = expected_score

        result = self.calculator.calculate_dimension_score(1, 1, 'mechanical')
        
        mock_mech_score.assert_called_once_with(1, mock_period)
        self.assertEqual(result, expected_score)


class TestMechanicalScoreCalculation(unittest.TestCase):
    """测试机械工程师得分计算"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)
        
        # Mock period
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)

    def test_mechanical_score_high_quality(self):
        """测试高质量设计（100%一次通过率，无调试问题）"""
        # Mock设计评审：全部一次通过
        mock_reviews = [
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
        ]
        
        # Mock查询链
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = mock_reviews
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 2
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 100%通过率 -> 100/85*100 = 117.65（限制到120）
        self.assertGreater(result.technical_score, Decimal('100'))
        self.assertEqual(result.knowledge_score, Decimal('70'))  # 50 + 2*10
        self.assertEqual(result.collaboration_score, Decimal('75'))  # 默认值

    def test_mechanical_score_with_debug_issues(self):
        """测试有调试问题的情况"""
        # Mock设计评审：80%通过率
        mock_reviews = [
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=False),  # 1个未通过
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = mock_reviews
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 3  # 3个调试问题
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 80%通过率 -> 80/85*100 = 94.12，减去3*5=15，得79.12
        self.assertLess(result.technical_score, Decimal('95'))
        self.assertGreater(result.technical_score, Decimal('70'))

    def test_mechanical_score_no_design_reviews(self):
        """测试无设计评审记录（使用默认值）"""
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = []
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 5
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 默认85%通过率 -> 85/85*100 = 100
        self.assertEqual(result.technical_score, Decimal('100.0'))
        self.assertEqual(result.knowledge_score, Decimal('100'))  # 50 + 5*10 = 100

    def test_mechanical_score_excessive_debug_issues(self):
        """测试大量调试问题（应该保护到0）"""
        mock_reviews = [MagicMock(is_first_pass=True)]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = mock_reviews
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 50  # 大量问题
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 应该保护到0
        self.assertEqual(result.technical_score, Decimal('0'))


class TestTestEngineerScoreCalculation(unittest.TestCase):
    """测试测试工程师得分计算"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)
        
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)

    def test_test_score_high_performance(self):
        """测试高性能（高解决率+快速修复）"""
        # Mock bugs：全部解决，平均修复时间3小时
        mock_bugs = [
            MagicMock(status='resolved', fix_duration_hours=2),
            MagicMock(status='closed', fix_duration_hours=3),
            MagicMock(status='resolved', fix_duration_hours=4),
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'TestBugRecord' in str(model):
                mock_q.filter.return_value.all.return_value = mock_bugs
            elif 'CodeModule' in str(model):
                mock_q.filter.return_value.count.return_value = 3
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_test_score(1, self.mock_period)
        
        # 100%解决率 -> 100，平均3小时<4 -> +10 = 110
        self.assertEqual(result.technical_score, Decimal('110.0'))
        self.assertEqual(result.knowledge_score, Decimal('95'))  # 50 + 3*15

    def test_test_score_slow_fix(self):
        """测试慢速修复（平均时间>8小时）"""
        mock_bugs = [
            MagicMock(status='resolved', fix_duration_hours=10),
            MagicMock(status='resolved', fix_duration_hours=12),
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'TestBugRecord' in str(model):
                mock_q.filter.return_value.all.return_value = mock_bugs
            elif 'CodeModule' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_test_score(1, self.mock_period)
        
        # 100%解决率 -> 100，平均11小时>8 -> -10 = 90
        self.assertEqual(result.technical_score, Decimal('90.0'))

    def test_test_score_no_bugs(self):
        """测试无bug记录（使用默认值）"""
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'TestBugRecord' in str(model):
                mock_q.filter.return_value.all.return_value = []
            elif 'CodeModule' in str(model):
                mock_q.filter.return_value.count.return_value = 1
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_test_score(1, self.mock_period)
        
        # 默认100%解决率，4小时修复时间，无加减分
        self.assertEqual(result.technical_score, Decimal('100.0'))
        self.assertEqual(result.knowledge_score, Decimal('65'))  # 50 + 1*15

    def test_test_score_partial_resolution(self):
        """测试部分解决（有未解决的bug）"""
        mock_bugs = [
            MagicMock(status='resolved', fix_duration_hours=3),
            MagicMock(status='open', fix_duration_hours=None),
            MagicMock(status='closed', fix_duration_hours=5),
            MagicMock(status='pending', fix_duration_hours=None),
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'TestBugRecord' in str(model):
                mock_q.filter.return_value.all.return_value = mock_bugs
            elif 'CodeModule' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_test_score(1, self.mock_period)
        
        # 2/4 = 50%解决率，平均4小时，无加减分
        self.assertEqual(result.technical_score, Decimal('50.0'))


class TestElectricalScoreCalculation(unittest.TestCase):
    """测试电气工程师得分计算"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)
        
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)

    def test_electrical_score_perfect(self):
        """测试完美表现（100%一次通过）"""
        mock_programs = [
            MagicMock(is_first_pass=True),
            MagicMock(is_first_pass=True),
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'PlcProgramVersion' in str(model):
                mock_q.filter.return_value.all.return_value = mock_programs
            elif 'PlcModuleLibrary' in str(model):
                mock_q.filter.return_value.count.return_value = 2
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_electrical_score(1, self.mock_period)
        
        # 100%通过率 -> 100/80*100 = 125，限制到120
        self.assertEqual(result.technical_score, Decimal('120.0'))
        self.assertEqual(result.knowledge_score, Decimal('80'))  # 50 + 2*15

    def test_electrical_score_no_programs(self):
        """测试无PLC程序记录"""
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'PlcProgramVersion' in str(model):
                mock_q.filter.return_value.all.return_value = []
            elif 'PlcModuleLibrary' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_electrical_score(1, self.mock_period)
        
        # 默认80%通过率 -> 80/80*100 = 100
        self.assertEqual(result.technical_score, Decimal('100.0'))
        self.assertEqual(result.knowledge_score, Decimal('50'))


class TestSolutionScoreSimple(unittest.TestCase):
    """测试方案工程师得分计算（简化版）"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)
        
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)

    def test_solution_score_empty_solutions(self):
        """测试无方案记录（使用默认值）"""
        # 所有query都返回空结果
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            # all()返回空列表
            mock_q.filter.return_value.all.return_value = []
            # count()返回0
            mock_q.filter.return_value.count.return_value = 0
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_solution_score(1, self.mock_period)
        
        # 验证使用默认值
        self.assertEqual(result.solution_success_score, Decimal('60.0'))
        self.assertEqual(result.technical_score, Decimal('60.0'))
        self.assertEqual(result.knowledge_score, Decimal('50'))  # 50 + 0*15
        self.assertEqual(result.execution_score, Decimal('100.0'))  # 默认90%, 90/90*100
        self.assertEqual(result.cost_quality_score, Decimal('75.0'))



class TestCalculateDimensionScoreRouting(unittest.TestCase):
    """测试calculate_dimension_score路由逻辑的完整覆盖"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)
        
        # Mock period
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)

    @patch.object(PerformanceCalculator, '_calculate_test_score')
    def test_route_to_test_engineer(self, mock_test_score):
        """测试路由到测试工程师计算"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = self.mock_period
        self.db.query.return_value = mock_query

        expected_score = EngineerDimensionScore(
            technical_score=Decimal('85'),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal('70'),
            collaboration_score=Decimal('75')
        )
        mock_test_score.return_value = expected_score

        result = self.calculator.calculate_dimension_score(1, 1, 'test')
        
        mock_test_score.assert_called_once()
        self.assertEqual(result, expected_score)

    @patch.object(PerformanceCalculator, '_calculate_electrical_score')
    def test_route_to_electrical_engineer(self, mock_elec_score):
        """测试路由到电气工程师计算"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = self.mock_period
        self.db.query.return_value = mock_query

        expected_score = EngineerDimensionScore(
            technical_score=Decimal('90'),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal('85'),
            collaboration_score=Decimal('75')
        )
        mock_elec_score.return_value = expected_score

        result = self.calculator.calculate_dimension_score(1, 1, 'electrical')
        
        mock_elec_score.assert_called_once()
        self.assertEqual(result, expected_score)

    @patch.object(PerformanceCalculator, '_calculate_solution_score')
    def test_route_to_solution_engineer(self, mock_solution_score):
        """测试路由到方案工程师计算"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = self.mock_period
        self.db.query.return_value = mock_query

        expected_score = EngineerDimensionScore(
            technical_score=Decimal('88'),
            execution_score=Decimal('82'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal('90'),
            collaboration_score=Decimal('80'),
            solution_success_score=Decimal('85')
        )
        mock_solution_score.return_value = expected_score

        result = self.calculator.calculate_dimension_score(1, 1, 'solution')
        
        mock_solution_score.assert_called_once()
        self.assertEqual(result, expected_score)


class TestCollaborationAverage(unittest.TestCase):
    """测试协作评分平均值计算"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)

    def test_collaboration_avg_no_ratings(self):
        """测试无评分记录（返回默认值）"""
        mock_q = MagicMock()
        mock_q.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_q

        result = self.calculator._get_collaboration_avg(1, 1)
        
        self.assertEqual(result, Decimal('75'))

    def test_collaboration_avg_perfect_scores(self):
        """测试满分评价"""
        mock_ratings = [
            MagicMock(communication_score=5, response_score=5, delivery_score=5, interface_score=5),
            MagicMock(communication_score=5, response_score=5, delivery_score=5, interface_score=5),
        ]
        
        mock_q = MagicMock()
        mock_q.filter.return_value.all.return_value = mock_ratings
        self.db.query.return_value = mock_q

        result = self.calculator._get_collaboration_avg(1, 1)
        
        # (5+5+5+5) * 2 / (2 * 4) * 20 = 40 / 8 * 20 = 100
        self.assertEqual(result, Decimal('100.0'))

    def test_collaboration_avg_mixed_scores(self):
        """测试混合评分"""
        mock_ratings = [
            MagicMock(communication_score=4, response_score=5, delivery_score=3, interface_score=4),
            MagicMock(communication_score=5, response_score=4, delivery_score=5, interface_score=3),
            MagicMock(communication_score=3, response_score=4, delivery_score=4, interface_score=5),
        ]
        
        mock_q = MagicMock()
        mock_q.filter.return_value.all.return_value = mock_ratings
        self.db.query.return_value = mock_q

        result = self.calculator._get_collaboration_avg(1, 1)
        
        # 总分：(4+5+3+4) + (5+4+5+3) + (3+4+4+5) = 16 + 17 + 16 = 49
        # 平均：49 / (3 * 4) * 20 = 49 / 12 * 20 = 81.67
        self.assertEqual(result, Decimal('81.67'))

    def test_collaboration_avg_with_none_values(self):
        """测试包含None值的评分"""
        mock_ratings = [
            MagicMock(communication_score=4, response_score=None, delivery_score=3, interface_score=4),
            MagicMock(communication_score=5, response_score=4, delivery_score=None, interface_score=3),
        ]
        
        mock_q = MagicMock()
        mock_q.filter.return_value.all.return_value = mock_ratings
        self.db.query.return_value = mock_q

        result = self.calculator._get_collaboration_avg(1, 1)
        
        # None当作0：(4+0+3+4) + (5+4+0+3) = 11 + 12 = 23
        # 23 / 8 * 20 = 57.5
        self.assertEqual(result, Decimal('57.5'))


class TestTotalScoreCalculation(unittest.TestCase):
    """测试总分计算"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)

    def test_calculate_total_score_normal(self):
        """测试普通工程师总分（使用配置权重）"""
        dimension_scores = EngineerDimensionScore(
            technical_score=Decimal('90'),
            execution_score=Decimal('85'),
            cost_quality_score=Decimal('80'),
            knowledge_score=Decimal('75'),
            collaboration_score=Decimal('88')
        )
        
        # Mock配置：技术30%、执行25%、成本25%、知识10%、协作10%
        mock_config = MagicMock()
        mock_config.technical_weight = 30
        mock_config.execution_weight = 25
        mock_config.cost_quality_weight = 25
        mock_config.knowledge_weight = 10
        mock_config.collaboration_weight = 10

        result = self.calculator.calculate_total_score(dimension_scores, mock_config)
        
        # 90*0.3 + 85*0.25 + 80*0.25 + 75*0.1 + 88*0.1 = 27 + 21.25 + 20 + 7.5 + 8.8 = 84.55
        self.assertEqual(result, Decimal('84.55'))

    def test_calculate_total_score_solution_engineer(self):
        """测试方案工程师总分（使用固定权重）"""
        dimension_scores = EngineerDimensionScore(
            technical_score=Decimal('85'),
            execution_score=Decimal('90'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal('80'),
            collaboration_score=Decimal('88'),
            solution_success_score=Decimal('92')
        )
        
        mock_config = MagicMock()

        result = self.calculator.calculate_total_score(
            dimension_scores, 
            mock_config, 
            job_type='solution'
        )
        
        # 技术25% + 方案成功30% + 执行20% + 知识15% + 协作10%
        # 85*0.25 + 92*0.3 + 90*0.2 + 80*0.15 + 88*0.1 
        # = 21.25 + 27.6 + 18 + 12 + 8.8 = 87.65
        self.assertEqual(result, Decimal('87.65'))

    def test_calculate_total_score_perfect(self):
        """测试完美得分"""
        dimension_scores = EngineerDimensionScore(
            technical_score=Decimal('100'),
            execution_score=Decimal('100'),
            cost_quality_score=Decimal('100'),
            knowledge_score=Decimal('100'),
            collaboration_score=Decimal('100')
        )
        
        mock_config = MagicMock()
        mock_config.technical_weight = 20
        mock_config.execution_weight = 20
        mock_config.cost_quality_weight = 20
        mock_config.knowledge_weight = 20
        mock_config.collaboration_weight = 20

        result = self.calculator.calculate_total_score(dimension_scores, mock_config)
        
        self.assertEqual(result, Decimal('100.0'))

    def test_calculate_total_score_low_performance(self):
        """测试低绩效得分"""
        dimension_scores = EngineerDimensionScore(
            technical_score=Decimal('40'),
            execution_score=Decimal('45'),
            cost_quality_score=Decimal('50'),
            knowledge_score=Decimal('35'),
            collaboration_score=Decimal('42')
        )
        
        mock_config = MagicMock()
        mock_config.technical_weight = 30
        mock_config.execution_weight = 25
        mock_config.cost_quality_weight = 25
        mock_config.knowledge_weight = 10
        mock_config.collaboration_weight = 10

        result = self.calculator.calculate_total_score(dimension_scores, mock_config)
        
        # 40*0.3 + 45*0.25 + 50*0.25 + 35*0.1 + 42*0.1 = 12 + 11.25 + 12.5 + 3.5 + 4.2 = 43.45
        self.assertEqual(result, Decimal('43.45'))


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.db = MagicMock()
        self.calculator = PerformanceCalculator(self.db)

    def test_knowledge_score_cap(self):
        """测试知识沉淀得分上限"""
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)
        
        # Mock大量知识贡献
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = []
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 20  # 很多贡献
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 50 + 20*10 = 250，应该限制到100
        self.assertEqual(result.knowledge_score, Decimal('100'))

    def test_technical_score_floor(self):
        """测试技术得分下限保护"""
        self.mock_period = MagicMock()
        self.mock_period.id = 1
        self.mock_period.start_date = date(2024, 1, 1)
        self.mock_period.end_date = date(2024, 3, 31)
        
        # Mock 0%通过率 + 大量调试问题
        mock_reviews = [
            MagicMock(is_first_pass=False),
            MagicMock(is_first_pass=False),
        ]
        
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if 'DesignReview' in str(model):
                mock_q.filter.return_value.all.return_value = mock_reviews
            elif 'MechanicalDebugIssue' in str(model):
                mock_q.filter.return_value.count.return_value = 100
            elif 'KnowledgeContribution' in str(model):
                mock_q.filter.return_value.count.return_value = 0
            elif 'CollaborationRating' in str(model):
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.db.query.side_effect = mock_query_side_effect

        result = self.calculator._calculate_mechanical_score(1, self.mock_period)
        
        # 应该保护到0，不能为负数
        self.assertGreaterEqual(result.technical_score, Decimal('0'))


if __name__ == "__main__":
    unittest.main()
