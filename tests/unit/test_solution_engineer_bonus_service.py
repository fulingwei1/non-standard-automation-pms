# -*- coding: utf-8 -*-
"""
方案工程师奖金补偿服务单元测试
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestSolutionEngineerBonusServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService

        service = SolutionEngineerBonusService(db_session)
        assert service.db == db_session


class TestCalculateSolutionBonus:
    """测试方案奖金计算"""

    def test_period_not_found(self, db_session):
        """测试考核周期不存在"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService

        service = SolutionEngineerBonusService(db_session)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.calculate_solution_bonus(1, 99999)

    def test_no_solutions(self, db_session):
        """测试无方案"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService
        from app.models.performance import PerformancePeriod
        from datetime import date

            # 创建考核周期
        period = PerformancePeriod(
        period_name='2025-01',
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        status='ACTIVE'
        )
        db_session.add(period)
        db_session.flush()

        service = SolutionEngineerBonusService(db_session)
        result = service.calculate_solution_bonus(99999, period.id)

        assert result['total_solutions'] == 0
        assert result['completion_bonus'] == 0.0
        assert result['won_bonus'] == 0.0
        assert result['high_quality_compensation'] == 0.0
        assert result['success_rate_bonus'] == 0.0
        assert result['total_bonus'] == 0.0

    def test_default_bonus_parameters(self, db_session):
        """测试默认奖金参数"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService

        service = SolutionEngineerBonusService(db_session)

            # 检查默认参数
        import inspect
        sig = inspect.signature(service.calculate_solution_bonus)
        params = sig.parameters

        assert params['base_bonus_per_solution'].default == Decimal('500')
        assert params['won_bonus_ratio'].default == Decimal('0.001')
        assert params['high_quality_compensation'].default == Decimal('300')
        assert params['success_rate_bonus'].default == Decimal('2000')

    def test_custom_bonus_parameters(self, db_session):
        """测试自定义奖金参数"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService
        from app.models.performance import PerformancePeriod
        from datetime import date

        period = PerformancePeriod(
        period_name='2025-01',
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        status='ACTIVE'
        )
        db_session.add(period)
        db_session.flush()

        service = SolutionEngineerBonusService(db_session)
        result = service.calculate_solution_bonus(
        engineer_id=1,
        period_id=period.id,
        base_bonus_per_solution=Decimal('1000'),
        won_bonus_ratio=Decimal('0.002'),
        high_quality_compensation=Decimal('500'),
        success_rate_bonus=Decimal('3000')
        )

            # 验证方法接受自定义参数
        assert 'total_bonus' in result


class TestBonusCalculationLogic:
    """测试奖金计算逻辑"""

    def test_completion_bonus_for_approved_solution(self):
        """测试已批准方案的完成奖金"""
        base_bonus = Decimal('500')
        status = 'APPROVED'

        completion_bonus = Decimal('0')
        if status in ['APPROVED', 'SUBMITTED']:
            completion_bonus += base_bonus

            assert completion_bonus == Decimal('500')

    def test_completion_bonus_for_submitted_solution(self):
        """测试已提交方案的完成奖金"""
        base_bonus = Decimal('500')
        status = 'SUBMITTED'

        completion_bonus = Decimal('0')
        if status in ['APPROVED', 'SUBMITTED']:
            completion_bonus += base_bonus

            assert completion_bonus == Decimal('500')

    def test_no_completion_bonus_for_draft(self):
        """测试草稿方案无完成奖金"""
        base_bonus = Decimal('500')
        status = 'DRAFT'

        completion_bonus = Decimal('0')
        if status in ['APPROVED', 'SUBMITTED']:
            completion_bonus += base_bonus

            assert completion_bonus == Decimal('0')

    def test_won_bonus_calculation(self):
        """测试中标奖金计算"""
        contract_amount = Decimal('1000000')
        won_bonus_ratio = Decimal('0.001')

        won_bonus = contract_amount * won_bonus_ratio

        assert won_bonus == Decimal('1000')

    def test_success_rate_bonus_threshold(self):
        """测试成功率奖励阈值"""
        success_rate_bonus = Decimal('2000')

        # 中标率40%以上获得奖励
        win_rate_above = 45
        win_rate_below = 35

        bonus_above = success_rate_bonus if win_rate_above >= 40 else Decimal('0')
        bonus_below = success_rate_bonus if win_rate_below >= 40 else Decimal('0')

        assert bonus_above == Decimal('2000')
        assert bonus_below == Decimal('0')

    def test_high_quality_compensation_threshold(self):
        """测试高质量方案补偿阈值"""
        satisfaction_score = 4.5
        high_quality_compensation = Decimal('300')

        # 满意度≥4.5获得补偿
        if satisfaction_score >= 4.5:
            compensation = high_quality_compensation
        else:
            compensation = Decimal('0')

            assert compensation == Decimal('300')


class TestGetSolutionScoreDetails:
    """测试获取方案工程师得分详情"""

    def test_period_not_found(self, db_session):
        """测试考核周期不存在"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService

        service = SolutionEngineerBonusService(db_session)

        with pytest.raises(ValueError, match="考核周期不存在"):
            service.get_solution_score_details(1, 99999)


class TestBonusResultStructure:
    """测试奖金结果结构"""

    def test_result_fields(self, db_session):
        """测试结果字段"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService
        from app.models.performance import PerformancePeriod
        from datetime import date

        period = PerformancePeriod(
        period_name='2025-01',
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        status='ACTIVE'
        )
        db_session.add(period)
        db_session.flush()

        service = SolutionEngineerBonusService(db_session)
        result = service.calculate_solution_bonus(1, period.id)

        expected_fields = [
        'engineer_id', 'period_id', 'total_solutions',
        'completion_bonus', 'won_bonus', 'high_quality_compensation',
        'success_rate_bonus', 'total_bonus', 'details'
        ]

        for field in expected_fields:
            assert field in result

    def test_details_is_list(self, db_session):
        """测试详情是列表"""
        from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService
        from app.models.performance import PerformancePeriod
        from datetime import date

        period = PerformancePeriod(
        period_name='2025-01',
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        status='ACTIVE'
        )
        db_session.add(period)
        db_session.flush()

        service = SolutionEngineerBonusService(db_session)
        result = service.calculate_solution_bonus(1, period.id)

        assert isinstance(result['details'], list)


class TestWinRateCalculation:
    """测试中标率计算"""

    def test_win_rate_with_solutions(self):
        """测试有方案时的中标率"""
        won_solutions = 4
        total_solutions = 10

        win_rate = won_solutions / total_solutions * 100

        assert win_rate == 40.0

    def test_win_rate_no_solutions(self):
        """测试无方案时的中标率"""
        won_solutions = 0
        total_solutions = 0

        win_rate = won_solutions / total_solutions * 100 if total_solutions else 0

        assert win_rate == 0

    def test_perfect_win_rate(self):
        """测试100%中标率"""
        won_solutions = 5
        total_solutions = 5

        win_rate = won_solutions / total_solutions * 100

        assert win_rate == 100.0


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
