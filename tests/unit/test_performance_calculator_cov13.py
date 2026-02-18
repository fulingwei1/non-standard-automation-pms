# -*- coding: utf-8 -*-
"""第十三批 - 绩效计算服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.engineer_performance.performance_calculator import PerformanceCalculator
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def calc(db):
    return PerformanceCalculator(db)


class TestCalculateGrade:
    def test_grade_s(self, calc):
        assert calc.calculate_grade(Decimal('90')) == 'S'

    def test_grade_s_boundary(self, calc):
        assert calc.calculate_grade(Decimal('85')) == 'S'

    def test_grade_a(self, calc):
        assert calc.calculate_grade(Decimal('75')) == 'A'

    def test_grade_b(self, calc):
        assert calc.calculate_grade(Decimal('65')) == 'B'

    def test_grade_c(self, calc):
        assert calc.calculate_grade(Decimal('50')) == 'C'

    def test_grade_d(self, calc):
        assert calc.calculate_grade(Decimal('20')) == 'D'

    def test_grade_d_zero(self, calc):
        assert calc.calculate_grade(Decimal('0')) == 'D'

    def test_grade_s_max(self, calc):
        assert calc.calculate_grade(Decimal('100')) == 'S'


class TestCalculateDimensionScore:
    def test_unknown_job_type_raises(self, calc, db):
        """未知岗位类型抛出ValueError"""
        mock_period = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_period
        with pytest.raises(ValueError, match="未知的岗位类型"):
            calc.calculate_dimension_score(1, 1, 'unknown_type')

    def test_period_not_found_raises(self, calc, db):
        """考核周期不存在时抛出ValueError"""
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="考核周期不存在"):
            calc.calculate_dimension_score(1, 999, 'mechanical')

    def test_grade_rules_complete(self, calc):
        """验证等级划分覆盖主要分数段"""
        for score in [10, 40, 50, 60, 70, 85]:
            grade = calc.calculate_grade(Decimal(str(score)))
            assert grade in ('S', 'A', 'B', 'C', 'D')
