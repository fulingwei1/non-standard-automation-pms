# -*- coding: utf-8 -*-
"""
PerformanceCalculator 综合单元测试

测试覆盖:
- __init__: 初始化服务
- calculate_grade: 根据分数计算等级
- calculate_dimension_score: 计算工程师五维得分
- _calculate_mechanical_score: 计算机械工程师得分
- _calculate_test_score: 计算测试工程师得分
- _calculate_electrical_score: 计算电气工程师得分
- _calculate_solution_score: 计算方案工程师得分
- _get_collaboration_avg: 获取协作评价平均分
- calculate_total_score: 计算加权总分
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime
from decimal import Decimal

import pytest


class TestPerformanceCalculatorInit:
    """测试 PerformanceCalculator 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        calculator = PerformanceCalculator(mock_db)

        assert calculator.db == mock_db

    def test_has_grade_rules(self):
        """测试包含等级规则"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        calculator = PerformanceCalculator(mock_db)

        assert 'S' in calculator.GRADE_RULES
        assert 'A' in calculator.GRADE_RULES
        assert 'B' in calculator.GRADE_RULES
        assert 'C' in calculator.GRADE_RULES
        assert 'D' in calculator.GRADE_RULES


class TestCalculateGrade:
    """测试 calculate_grade 方法"""

    def test_returns_s_for_high_score(self):
        """测试高分返回S等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('90'))

        assert result == 'S'

    def test_returns_a_for_good_score(self):
        """测试良好分数返回A等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('75'))

        assert result == 'A'

    def test_returns_b_for_passing_score(self):
        """测试及格分数返回B等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('65'))

        assert result == 'B'

    def test_returns_c_for_low_score(self):
        """测试低分返回C等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('50'))

        assert result == 'C'

    def test_returns_d_for_failing_score(self):
        """测试不及格分数返回D等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('30'))

        assert result == 'D'

    def test_returns_d_for_zero(self):
        """测试零分返回D等级"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        result = calculator.calculate_grade(Decimal('0'))

        assert result == 'D'


class TestCalculateDimensionScore:
    """测试 calculate_dimension_score 方法"""

    def test_raises_for_missing_period(self):
        """测试考核周期不存在时抛出异常"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        calculator = PerformanceCalculator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_dimension_score(1, 999, 'mechanical')

        assert "考核周期不存在" in str(exc_info.value)

    def test_calls_mechanical_score_for_mechanical_type(self):
        """测试机械岗位调用机械计算方法"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_period = MagicMock()
        mock_period.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_period

        calculator = PerformanceCalculator(mock_db)
        calculator._calculate_mechanical_score = MagicMock(return_value=MagicMock())

        calculator.calculate_dimension_score(1, 1, 'mechanical')

        calculator._calculate_mechanical_score.assert_called_once()

    def test_calls_test_score_for_test_type(self):
        """测试测试岗位调用测试计算方法"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_period = MagicMock()
        mock_period.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_period

        calculator = PerformanceCalculator(mock_db)
        calculator._calculate_test_score = MagicMock(return_value=MagicMock())

        calculator.calculate_dimension_score(1, 1, 'test')

        calculator._calculate_test_score.assert_called_once()

    def test_calls_electrical_score_for_electrical_type(self):
        """测试电气岗位调用电气计算方法"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_period = MagicMock()
        mock_period.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_period

        calculator = PerformanceCalculator(mock_db)
        calculator._calculate_electrical_score = MagicMock(return_value=MagicMock())

        calculator.calculate_dimension_score(1, 1, 'electrical')

        calculator._calculate_electrical_score.assert_called_once()

    def test_calls_solution_score_for_solution_type(self):
        """测试方案岗位调用方案计算方法"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_period = MagicMock()
        mock_period.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_period

        calculator = PerformanceCalculator(mock_db)
        calculator._calculate_solution_score = MagicMock(return_value=MagicMock())

        calculator.calculate_dimension_score(1, 1, 'solution')

        calculator._calculate_solution_score.assert_called_once()

    def test_raises_for_unknown_job_type(self):
        """测试未知岗位类型抛出异常"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_period = MagicMock()
        mock_period.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_period

        calculator = PerformanceCalculator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_dimension_score(1, 1, 'unknown')

        assert "未知的岗位类型" in str(exc_info.value)


class TestCalculateMechanicalScore:
    """测试 _calculate_mechanical_score 方法"""

    def test_calculates_score_with_reviews(self):
        """测试有设计评审时计算得分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_review1 = MagicMock()
        mock_review1.is_first_pass = True

        mock_review2 = MagicMock()
        mock_review2.is_first_pass = False

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_review1, mock_review2]
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('80'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_mechanical_score(1, mock_period)

        assert result is not None
        assert hasattr(result, 'technical_score')

    def test_uses_default_for_no_reviews(self):
        """测试无评审时使用默认值"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('75'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_mechanical_score(1, mock_period)

        assert result is not None


class TestCalculateTestScore:
    """测试 _calculate_test_score 方法"""

    def test_calculates_score_with_bugs(self):
        """测试有Bug记录时计算得分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_bug1 = MagicMock()
        mock_bug1.status = 'resolved'
        mock_bug1.fix_duration_hours = 2

        mock_bug2 = MagicMock()
        mock_bug2.status = 'open'
        mock_bug2.fix_duration_hours = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_bug1, mock_bug2]
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('80'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_test_score(1, mock_period)

        assert result is not None
        assert hasattr(result, 'technical_score')

    def test_uses_default_for_no_bugs(self):
        """测试无Bug时使用默认值"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('75'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_test_score(1, mock_period)

        assert result is not None


class TestCalculateElectricalScore:
    """测试 _calculate_electrical_score 方法"""

    def test_calculates_score_with_plc_programs(self):
        """测试有PLC程序时计算得分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_program1 = MagicMock()
        mock_program1.is_first_pass = True

        mock_program2 = MagicMock()
        mock_program2.is_first_pass = False

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_program1, mock_program2]
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('80'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_electrical_score(1, mock_period)

        assert result is not None
        assert hasattr(result, 'technical_score')

    def test_uses_default_for_no_programs(self):
        """测试无程序时使用默认值"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('75'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_electrical_score(1, mock_period)

        assert result is not None


class TestCalculateSolutionScore:
    """测试 _calculate_solution_score 方法"""

    def test_calculates_score_with_solutions(self):
        """测试有方案时计算得分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_solution = MagicMock()
        mock_solution.opportunity_id = 1
        mock_solution.review_status = 'APPROVED'
        mock_solution.ticket_id = 1
        mock_solution.created_at = datetime(2024, 6, 1)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_solution]
        mock_query.count.return_value = 1
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('80'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_solution_score(1, mock_period)

        assert result is not None
        assert hasattr(result, 'solution_success_score')

    def test_uses_default_for_no_solutions(self):
        """测试无方案时使用默认值"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        calculator = PerformanceCalculator(mock_db)
        calculator._get_collaboration_avg = MagicMock(return_value=Decimal('75'))

        mock_period = MagicMock()
        mock_period.start_date = date(2024, 1, 1)
        mock_period.end_date = date(2024, 12, 31)
        mock_period.id = 1

        result = calculator._calculate_solution_score(1, mock_period)

        assert result is not None


class TestGetCollaborationAvg:
    """测试 _get_collaboration_avg 方法"""

    def test_returns_default_for_no_ratings(self):
        """测试无评价时返回默认值"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        calculator = PerformanceCalculator(mock_db)

        result = calculator._get_collaboration_avg(1, 1)

        assert result == Decimal('75')

    def test_calculates_average(self):
        """测试计算平均分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()

        mock_rating = MagicMock()
        mock_rating.communication_score = 4
        mock_rating.response_score = 5
        mock_rating.delivery_score = 4
        mock_rating.interface_score = 5

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rating]

        calculator = PerformanceCalculator(mock_db)

        result = calculator._get_collaboration_avg(1, 1)

        # (4+5+4+5) / 4 * 20 = 90
        assert result == Decimal('90')


class TestCalculateTotalScore:
    """测试 calculate_total_score 方法"""

    def test_calculates_weighted_total(self):
        """测试计算加权总分"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        dimension_scores = MagicMock()
        dimension_scores.technical_score = Decimal('80')
        dimension_scores.execution_score = Decimal('75')
        dimension_scores.cost_quality_score = Decimal('70')
        dimension_scores.knowledge_score = Decimal('65')
        dimension_scores.collaboration_score = Decimal('85')
        dimension_scores.solution_success_score = None

        config = MagicMock()
        config.technical_weight = 30
        config.execution_weight = 25
        config.cost_quality_weight = 20
        config.knowledge_weight = 15
        config.collaboration_weight = 10

        result = calculator.calculate_total_score(dimension_scores, config)

        # 80*0.3 + 75*0.25 + 70*0.2 + 65*0.15 + 85*0.1 = 24+18.75+14+9.75+8.5 = 75
        assert result == Decimal('75')

    def test_uses_solution_weights_for_solution_engineer(self):
        """测试方案工程师使用特殊权重"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        dimension_scores = MagicMock()
        dimension_scores.technical_score = Decimal('80')
        dimension_scores.execution_score = Decimal('75')
        dimension_scores.cost_quality_score = Decimal('70')
        dimension_scores.knowledge_score = Decimal('65')
        dimension_scores.collaboration_score = Decimal('85')
        dimension_scores.solution_success_score = Decimal('90')

        config = MagicMock()

        result = calculator.calculate_total_score(dimension_scores, config, job_type='solution')

        # 80*0.25 + 90*0.30 + 75*0.20 + 65*0.15 + 85*0.10 = 20+27+15+9.75+8.5 = 80.25
        assert result == Decimal('80.25')

    def test_handles_zero_weights(self):
        """测试处理零权重"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        dimension_scores = MagicMock()
        dimension_scores.technical_score = Decimal('100')
        dimension_scores.execution_score = Decimal('0')
        dimension_scores.cost_quality_score = Decimal('0')
        dimension_scores.knowledge_score = Decimal('0')
        dimension_scores.collaboration_score = Decimal('0')
        dimension_scores.solution_success_score = None

        config = MagicMock()
        config.technical_weight = 100
        config.execution_weight = 0
        config.cost_quality_weight = 0
        config.knowledge_weight = 0
        config.collaboration_weight = 0

        result = calculator.calculate_total_score(dimension_scores, config)

        assert result == Decimal('100')


class TestGradeRules:
    """测试等级划分规则"""

    def test_s_grade_boundary(self):
        """测试S等级边界"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        assert calculator.calculate_grade(Decimal('85')) == 'S'
        assert calculator.calculate_grade(Decimal('100')) == 'S'

    def test_a_grade_boundary(self):
        """测试A等级边界"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        assert calculator.calculate_grade(Decimal('70')) == 'A'
        assert calculator.calculate_grade(Decimal('84')) == 'A'

    def test_b_grade_boundary(self):
        """测试B等级边界"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        assert calculator.calculate_grade(Decimal('60')) == 'B'
        assert calculator.calculate_grade(Decimal('69')) == 'B'

    def test_c_grade_boundary(self):
        """测试C等级边界"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        assert calculator.calculate_grade(Decimal('40')) == 'C'
        assert calculator.calculate_grade(Decimal('59')) == 'C'

    def test_d_grade_boundary(self):
        """测试D等级边界"""
        from app.services.engineer_performance.performance_calculator import PerformanceCalculator

        mock_db = MagicMock()
        calculator = PerformanceCalculator(mock_db)

        assert calculator.calculate_grade(Decimal('0')) == 'D'
        assert calculator.calculate_grade(Decimal('39')) == 'D'
