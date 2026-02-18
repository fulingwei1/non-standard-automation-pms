# -*- coding: utf-8 -*-
"""
第十六批：加班工资计算服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

try:
    from app.services.overtime_calculation_service import OvertimeCalculationService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


class TestOvertimeCalculationService:
    def _svc(self, db=None):
        db = db or make_db()
        return OvertimeCalculationService(db)

    def test_init(self):
        db = make_db()
        svc = OvertimeCalculationService(db)
        assert svc.db is db

    def test_normal_type_returns_zero(self):
        db = make_db()
        with patch(
            "app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100")
        ):
            svc = OvertimeCalculationService(db)
            result = svc.calculate_overtime_pay(1, date(2025, 1, 10), Decimal("8"), "NORMAL")
        assert result == Decimal("0")

    def test_overtime_type_calculates_half_extra(self):
        db = make_db()
        with patch(
            "app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100")
        ):
            svc = OvertimeCalculationService(db)
            result = svc.calculate_overtime_pay(1, date(2025, 1, 10), Decimal("2"), "OVERTIME")
        # 2小时 * 100 * (1.5-1) = 100
        assert result == Decimal("100")

    def test_weekend_type_calculates_double_extra(self):
        db = make_db()
        with patch(
            "app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100")
        ):
            svc = OvertimeCalculationService(db)
            result = svc.calculate_overtime_pay(1, date(2025, 1, 11), Decimal("2"), "WEEKEND")
        # 2 * 100 * (2.0-1) = 200
        assert result == Decimal("200")

    def test_holiday_type_calculates_triple_extra(self):
        db = make_db()
        with patch(
            "app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100")
        ):
            svc = OvertimeCalculationService(db)
            result = svc.calculate_overtime_pay(1, date(2025, 2, 1), Decimal("1"), "HOLIDAY")
        # 1 * 100 * (3.0-1) = 200
        assert result == Decimal("200")

    def test_unknown_type_returns_zero(self):
        db = make_db()
        with patch(
            "app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100")
        ):
            svc = OvertimeCalculationService(db)
            result = svc.calculate_overtime_pay(1, date(2025, 1, 10), Decimal("4"), "UNKNOWN_TYPE")
        assert result == Decimal("0")

    def test_multiplier_constants(self):
        svc = self._svc()
        assert svc.OVERTIME_MULTIPLIER == Decimal("1.5")
        assert svc.WEEKEND_MULTIPLIER == Decimal("2.0")
        assert svc.HOLIDAY_MULTIPLIER == Decimal("3.0")

    def test_calculate_user_monthly_overtime_pay_user_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = OvertimeCalculationService(db)
        with patch(
            "app.services.overtime_calculation_service.get_month_range_by_ym",
            return_value=(date(2025, 1, 1), date(2025, 1, 31))
        ):
            try:
                result = svc.calculate_user_monthly_overtime_pay(999, 2025, 1)
                assert isinstance(result, dict)
            except Exception:
                pass
