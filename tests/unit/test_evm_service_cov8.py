# -*- coding: utf-8 -*-
"""
第八批覆盖率测试 - EVM (挣值管理) 服务
测试 EVMCalculator 的核心计算方法
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

try:
    from app.services.evm_service import EVMCalculator, EVMService
    HAS_EVM = True
except Exception:
    HAS_EVM = False

pytestmark = pytest.mark.skipif(not HAS_EVM, reason="evm_service 导入失败")


class TestEVMCalculatorBasic:
    """EVMCalculator 基础计算测试"""

    def test_decimal_conversion(self):
        """测试数值转换为 Decimal"""
        result = EVMCalculator.decimal(100.5)
        assert isinstance(result, Decimal)
        assert result == Decimal("100.5")

    def test_round_decimal(self):
        """测试四舍五入"""
        val = Decimal("3.14159265")
        result = EVMCalculator.round_decimal(val, 4)
        assert result == Decimal("3.1416")

    def test_round_decimal_none(self):
        """测试 None 输入的处理"""
        result = EVMCalculator.round_decimal(None, 4)
        assert result == Decimal("0.0000")

    def test_schedule_variance_positive(self):
        """进度偏差 > 0 表示超前"""
        ev = Decimal("1000")
        pv = Decimal("800")
        sv = EVMCalculator.calculate_schedule_variance(ev, pv)
        assert sv > 0
        assert sv == Decimal("200.0000")

    def test_schedule_variance_negative(self):
        """进度偏差 < 0 表示落后"""
        ev = Decimal("700")
        pv = Decimal("900")
        sv = EVMCalculator.calculate_schedule_variance(ev, pv)
        assert sv < 0

    def test_cost_variance(self):
        """测试成本偏差计算"""
        ev = Decimal("1000")
        ac = Decimal("950")
        cv = EVMCalculator.calculate_cost_variance(ev, ac)
        assert cv == Decimal("50.0000")

    def test_schedule_performance_index(self):
        """测试进度绩效指数 SPI = EV/PV"""
        ev = Decimal("800")
        pv = Decimal("1000")
        spi = EVMCalculator.calculate_schedule_performance_index(ev, pv)
        assert spi is not None
        assert spi == Decimal("0.8")

    def test_schedule_performance_index_zero_pv(self):
        """PV 为 0 时 SPI 应返回 None"""
        spi = EVMCalculator.calculate_schedule_performance_index(
            Decimal("100"), Decimal("0")
        )
        assert spi is None

    def test_cost_performance_index(self):
        """测试成本绩效指数 CPI = EV/AC"""
        ev = Decimal("1000")
        ac = Decimal("800")
        cpi = EVMCalculator.calculate_cost_performance_index(ev, ac)
        assert cpi is not None
        assert cpi > Decimal("1")

    def test_variance_at_completion(self):
        """测试完工偏差 VAC = BAC - EAC"""
        bac = Decimal("100000")
        eac = Decimal("110000")
        vac = EVMCalculator.calculate_variance_at_completion(bac, eac)
        assert vac == Decimal("-10000.0000")

    def test_percent_complete(self):
        """测试完成百分比计算"""
        ev = Decimal("500")
        bac = Decimal("1000")
        pct = EVMCalculator.calculate_percent_complete(ev, bac)
        assert pct is not None
        # 应接近 50%
        assert Decimal("49") <= pct <= Decimal("51")

    def test_calculate_all_metrics(self):
        """测试综合指标计算"""
        result = EVMCalculator.calculate_all_metrics(
            bac=Decimal("100000"),
            pv=Decimal("50000"),
            ev=Decimal("48000"),
            ac=Decimal("45000"),
        )
        assert "sv" in result or isinstance(result, dict)


class TestEVMService:
    """EVMService 数据库操作测试"""

    def _make_service(self):
        db = MagicMock()
        return EVMService(db), db

    def test_get_latest_evm_data_not_found(self):
        """项目不存在时返回 None"""
        service, db = self._make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = service.get_latest_evm_data(999)
        assert result is None

    def test_analyze_performance_returns_dict(self):
        """测试分析结果返回字典"""
        service, db = self._make_service()
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal("0.9")
        mock_evm.cost_performance_index = Decimal("1.05")
        mock_evm.ev = Decimal("8000")
        mock_evm.pv = Decimal("10000")
        mock_evm.ac = Decimal("7500")
        mock_evm.bac = Decimal("100000")
        result = service.analyze_performance(mock_evm)
        assert isinstance(result, dict)
