# -*- coding: utf-8 -*-
"""
第八批覆盖率测试 - 项目健康度计算器
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.health_calculator import HealthCalculator
    HAS_HC = True
except Exception:
    HAS_HC = False

pytestmark = pytest.mark.skipif(not HAS_HC, reason="health_calculator 导入失败")


def make_project(**kwargs):
    """构造 mock 项目对象"""
    proj = MagicMock()
    proj.status = kwargs.get("status", "ST10")
    proj.id = kwargs.get("id", 1)
    return proj


class TestHealthCalculatorClosed:
    """已完结项目测试"""

    def test_closed_status_st30(self):
        """ST30 状态返回 H4"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST30")
        result = calc.calculate_health(proj)
        assert result == "H4"

    def test_closed_status_st99(self):
        """ST99（取消）状态返回 H4"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST99")
        result = calc.calculate_health(proj)
        assert result == "H4"


class TestHealthCalculatorBlocked:
    """阻塞状态项目测试"""

    def test_blocked_status_st14(self):
        """缺料阻塞 ST14 返回 H3"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST14")
        # 阻塞判断内部可能还查DB，mock掉
        with patch.object(calc, '_is_blocked', return_value=True):
            result = calc.calculate_health(proj)
        assert result == "H3"

    def test_blocked_status_st19(self):
        """技术阻塞 ST19 返回 H3"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST19")
        with patch.object(calc, '_is_blocked', return_value=True):
            result = calc.calculate_health(proj)
        assert result == "H3"


class TestHealthCalculatorRisk:
    """有风险项目测试"""

    def test_has_risks_returns_h2(self):
        """有风险时返回 H2"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST10")
        with patch.object(calc, '_is_blocked', return_value=False):
            with patch.object(calc, '_has_risks', return_value=True):
                result = calc.calculate_health(proj)
        assert result == "H2"


class TestHealthCalculatorNormal:
    """正常项目测试"""

    def test_no_risk_returns_h1(self):
        """无风险时返回 H1"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST10")
        with patch.object(calc, '_is_blocked', return_value=False):
            with patch.object(calc, '_has_risks', return_value=False):
                result = calc.calculate_health(proj)
        assert result == "H1"

    def test_is_closed_false_for_active(self):
        """ST10 不是已完结"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST10")
        assert calc._is_closed(proj) is False

    def test_is_closed_true_for_st30(self):
        """ST30 是已完结"""
        db = MagicMock()
        calc = HealthCalculator(db)
        proj = make_project(status="ST30")
        assert calc._is_closed(proj) is True
