# -*- coding: utf-8 -*-
"""
数值计算工具全面测试

测试 app/utils/numerical_utils.py 中的所有函数
"""
import pytest
from decimal import Decimal
from app.utils.numerical_utils import (
    calc_spi_safe,
    calc_cpi,
    is_cost_overrun,
    calc_eac,
    calc_vac,
    calc_cumulative_kit_rate,
    calc_hourly_rate,
    calc_price_with_vat,
    calc_price_breakdown,
    paginate_pure,
    PageResult,
    PLACES_2,
    PLACES_4,
    PLACES_6,
)


class TestCalcSpiSafe:
    """测试进度绩效指数计算（防除零版本）"""

    def test_normal_calculation(self):
        """正常计算 SPI"""
        result = calc_spi_safe(ev=100, pv=80)
        assert result == Decimal("1.250000")
    
    def test_pv_zero_returns_default(self):
        """PV为0时返回默认值"""
        result = calc_spi_safe(ev=100, pv=0)
        assert result == Decimal("1.000000")
    
    def test_custom_zero_pv_default(self):
        """自定义零PV默认值"""
        result = calc_spi_safe(ev=100, pv=0, zero_pv_default=0.5)
        assert result == Decimal("0.500000")
    
    def test_with_float_inputs(self):
        """浮点数输入"""
        result = calc_spi_safe(ev=100.5, pv=50.25)
        assert result == Decimal("2.000000")
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_spi_safe(
            ev=Decimal("100"),
            pv=Decimal("80")
        )
        assert result == Decimal("1.250000")
    
    def test_zero_ev(self):
        """EV为0的情况"""
        result = calc_spi_safe(ev=0, pv=100)
        assert result == Decimal("0.000000")
    
    def test_negative_values(self):
        """负值处理"""
        result = calc_spi_safe(ev=-50, pv=100)
        assert result == Decimal("-0.500000")
    
    def test_precision(self):
        """精度测试"""
        result = calc_spi_safe(ev=1, pv=3)
        assert len(str(result).split('.')[-1]) <= 6


class TestCalcCpi:
    """测试成本绩效指数计算"""

    def test_normal_calculation(self):
        """正常计算 CPI"""
        result = calc_cpi(ev=100, ac=80)
        assert result == Decimal("1.250000")
    
    def test_cost_overrun(self):
        """成本超支情况"""
        result = calc_cpi(ev=80, ac=100)
        assert result == Decimal("0.800000")
    
    def test_ac_zero_raises_error(self):
        """AC为0时抛出异常"""
        with pytest.raises(ValueError, match="实际成本.*必须大于 0"):
            calc_cpi(ev=100, ac=0)
    
    def test_ac_negative_raises_error(self):
        """AC为负数时抛出异常"""
        with pytest.raises(ValueError, match="实际成本.*必须大于 0"):
            calc_cpi(ev=100, ac=-50)
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_cpi(
            ev=Decimal("150.50"),
            ac=Decimal("100.25")
        )
        assert isinstance(result, Decimal)
    
    def test_precision(self):
        """精度测试"""
        result = calc_cpi(ev=1, ac=3)
        assert len(str(result).split('.')[-1]) <= 6


class TestIsCostOverrun:
    """测试成本超支判定"""

    def test_cost_overrun_true(self):
        """CPI < 1 表示成本超支"""
        assert is_cost_overrun(0.9) is True
        assert is_cost_overrun(0.5) is True
    
    def test_cost_overrun_false(self):
        """CPI >= 1 表示成本正常或节约"""
        assert is_cost_overrun(1.0) is False
        assert is_cost_overrun(1.5) is False
    
    def test_with_decimal(self):
        """Decimal输入"""
        assert is_cost_overrun(Decimal("0.9")) is True
        assert is_cost_overrun(Decimal("1.1")) is False
    
    def test_boundary_value(self):
        """边界值测试"""
        assert is_cost_overrun(0.999999) is True
        assert is_cost_overrun(1.000001) is False


class TestCalcEac:
    """测试完工估算计算"""

    def test_normal_calculation(self):
        """正常计算 EAC"""
        result = calc_eac(bac=1000, ev=500, ac=600)
        # EAC = AC + (BAC - EV) / CPI
        # CPI = 500 / 600 = 0.833333
        # EAC = 600 + (1000 - 500) / 0.833333 = 1200
        assert result == Decimal("1200.00")
    
    def test_ac_zero_falls_back(self):
        """AC为0时退化计算"""
        result = calc_eac(bac=1000, ev=500, ac=0)
        # 当AC=0时，使用CPI=1
        assert result == Decimal("500.00")
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_eac(
            bac=Decimal("1000"),
            ev=Decimal("500"),
            ac=Decimal("600")
        )
        assert isinstance(result, Decimal)
    
    def test_precision(self):
        """精度测试（保留2位小数）"""
        result = calc_eac(bac=1000.123, ev=500.456, ac=600.789)
        assert len(str(result).split('.')[-1]) == 2


class TestCalcVac:
    """测试完工偏差计算"""

    def test_positive_vac(self):
        """正偏差（预算剩余）"""
        result = calc_vac(bac=1000, eac=900)
        assert result == Decimal("100.00")
    
    def test_negative_vac(self):
        """负偏差（预算超支）"""
        result = calc_vac(bac=1000, eac=1200)
        assert result == Decimal("-200.00")
    
    def test_zero_vac(self):
        """零偏差"""
        result = calc_vac(bac=1000, eac=1000)
        assert result == Decimal("0.00")
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_vac(
            bac=Decimal("1000.50"),
            eac=Decimal("900.25")
        )
        assert result == Decimal("100.25")


class TestCalcCumulativeKitRate:
    """测试分批到货累计套件率计算"""

    def test_single_batch_full_delivery(self):
        """单批次全量到货"""
        batches = [(100, 100)]
        result = calc_cumulative_kit_rate(batches)
        assert result == Decimal("1.000000")
    
    def test_single_batch_partial_delivery(self):
        """单批次部分到货"""
        batches = [(60, 100)]
        result = calc_cumulative_kit_rate(batches)
        assert result == Decimal("0.600000")
    
    def test_multiple_batches(self):
        """多批次到货"""
        batches = [(60, 100), (30, 100)]
        result = calc_cumulative_kit_rate(batches)
        assert result == Decimal("0.900000")
    
    def test_over_delivery(self):
        """超量到货"""
        batches = [(120, 100)]
        result = calc_cumulative_kit_rate(batches)
        assert result == Decimal("1.200000")
    
    def test_empty_batches_raises_error(self):
        """空批次列表抛出异常"""
        with pytest.raises(ValueError, match="批次列表不能为空"):
            calc_cumulative_kit_rate([])
    
    def test_zero_bom_required_raises_error(self):
        """BOM需求量为0时抛出异常"""
        batches = [(50, 0)]
        with pytest.raises(ValueError, match="BOM 需求量必须大于 0"):
            calc_cumulative_kit_rate(batches)
    
    def test_negative_bom_required_raises_error(self):
        """BOM需求量为负数时抛出异常"""
        batches = [(50, -100)]
        with pytest.raises(ValueError, match="BOM 需求量必须大于 0"):
            calc_cumulative_kit_rate(batches)
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        batches = [(Decimal("60.5"), Decimal("100")), (Decimal("30.5"), Decimal("100"))]
        result = calc_cumulative_kit_rate(batches)
        assert result == Decimal("0.910000")


class TestCalcHourlyRate:
    """测试时薪计算"""

    def test_normal_calculation(self):
        """正常计算时薪"""
        # 月薪 10000 / (21.75 * 8) = 57.4713 元/小时
        result = calc_hourly_rate(monthly_salary=10000)
        assert result == Decimal("57.4713")
    
    def test_with_decimal_input(self):
        """Decimal输入"""
        result = calc_hourly_rate(monthly_salary=Decimal("10000"))
        assert isinstance(result, Decimal)
    
    def test_zero_salary_raises_error(self):
        """月薪为0时抛出异常"""
        with pytest.raises(ValueError, match="月薪必须大于 0"):
            calc_hourly_rate(monthly_salary=0)
    
    def test_negative_salary_raises_error(self):
        """月薪为负数时抛出异常"""
        with pytest.raises(ValueError, match="月薪必须大于 0"):
            calc_hourly_rate(monthly_salary=-1000)
    
    def test_precision(self):
        """精度测试（保留4位小数）"""
        result = calc_hourly_rate(monthly_salary=10000.12345)
        assert len(str(result).split('.')[-1]) == 4
    
    def test_low_salary(self):
        """低月薪"""
        result = calc_hourly_rate(monthly_salary=3000)
        assert result == Decimal("17.2414")
    
    def test_high_salary(self):
        """高月薪"""
        result = calc_hourly_rate(monthly_salary=50000)
        assert result == Decimal("287.3563")


class TestCalcPriceWithVat:
    """测试含税价格计算"""

    def test_default_vat_rate(self):
        """默认税率13%"""
        result = calc_price_with_vat(price=100)
        assert result == Decimal("113.00")
    
    def test_custom_vat_rate(self):
        """自定义税率"""
        result = calc_price_with_vat(price=100, vat_rate=0.06)
        assert result == Decimal("106.00")
    
    def test_zero_price(self):
        """价格为0"""
        result = calc_price_with_vat(price=0)
        assert result == Decimal("0.00")
    
    def test_negative_price_raises_error(self):
        """负价格抛出异常"""
        with pytest.raises(ValueError, match="价格不能为负数"):
            calc_price_with_vat(price=-100)
    
    def test_negative_vat_raises_error(self):
        """负税率抛出异常"""
        with pytest.raises(ValueError, match="税率不能为负数"):
            calc_price_with_vat(price=100, vat_rate=-0.13)
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_price_with_vat(
            price=Decimal("100.50"),
            vat_rate=Decimal("0.13")
        )
        assert result == Decimal("113.57")
    
    def test_precision(self):
        """精度测试（保留2位小数）"""
        result = calc_price_with_vat(price=100.123456)
        assert len(str(result).split('.')[-1]) == 2


class TestCalcPriceBreakdown:
    """测试报价分解计算"""

    def test_normal_breakdown(self):
        """正常报价分解"""
        result = calc_price_breakdown(
            hardware=5000,
            labor=3000,
            outsource=2000,
            margin_rate=0.30
        )
        # 成本合计 = 10000
        # 报价 = 10000 / (1 - 0.30) = 14285.71
        # 利润 = 14285.71 - 10000 = 4285.71
        assert result["hardware"] == Decimal("5000.00")
        assert result["labor"] == Decimal("3000.00")
        assert result["outsource"] == Decimal("2000.00")
        assert result["cost_subtotal"] == Decimal("10000.00")
        assert result["price"] == Decimal("14285.71")
        assert result["profit"] == Decimal("4285.71")
        assert result["margin_rate_actual"] == Decimal("0.300000")
    
    def test_zero_margin(self):
        """零利润率"""
        result = calc_price_breakdown(
            hardware=1000,
            labor=0,
            outsource=0,
            margin_rate=0
        )
        assert result["price"] == result["cost_subtotal"]
        assert result["profit"] == Decimal("0.00")
    
    def test_high_margin(self):
        """高利润率"""
        result = calc_price_breakdown(
            hardware=1000,
            labor=0,
            outsource=0,
            margin_rate=0.50
        )
        # 报价 = 1000 / (1 - 0.5) = 2000
        assert result["price"] == Decimal("2000.00")
        assert result["profit"] == Decimal("1000.00")
    
    def test_margin_rate_one_raises_error(self):
        """毛利率为1时抛出异常"""
        with pytest.raises(ValueError, match="毛利率必须在.*区间"):
            calc_price_breakdown(
                hardware=1000,
                labor=0,
                outsource=0,
                margin_rate=1.0
            )
    
    def test_negative_margin_raises_error(self):
        """负毛利率抛出异常"""
        with pytest.raises(ValueError, match="毛利率必须在.*区间"):
            calc_price_breakdown(
                hardware=1000,
                labor=0,
                outsource=0,
                margin_rate=-0.1
            )
    
    def test_margin_over_one_raises_error(self):
        """毛利率大于1时抛出异常"""
        with pytest.raises(ValueError, match="毛利率必须在.*区间"):
            calc_price_breakdown(
                hardware=1000,
                labor=0,
                outsource=0,
                margin_rate=1.5
            )
    
    def test_with_decimal_inputs(self):
        """Decimal输入"""
        result = calc_price_breakdown(
            hardware=Decimal("5000"),
            labor=Decimal("3000"),
            outsource=Decimal("2000"),
            margin_rate=Decimal("0.30")
        )
        assert all(isinstance(v, Decimal) for v in result.values())


class TestPaginatePure:
    """测试纯函数分页"""

    def test_normal_pagination(self):
        """正常分页"""
        items = list(range(1, 101))  # 1-100
        result = paginate_pure(total=100, page=1, page_size=10, items=items)
        
        assert result.total == 100
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 10
        assert result.items_count == 10
        assert result.items == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    def test_last_page(self):
        """最后一页"""
        items = list(range(1, 101))
        result = paginate_pure(total=100, page=10, page_size=10, items=items)
        
        assert result.items_count == 10
        assert result.items == [91, 92, 93, 94, 95, 96, 97, 98, 99, 100]
    
    def test_partial_last_page(self):
        """最后一页不足"""
        items = list(range(1, 96))  # 1-95
        result = paginate_pure(total=95, page=10, page_size=10, items=items)
        
        assert result.items_count == 5
        assert result.items == [91, 92, 93, 94, 95]
    
    def test_page_beyond_total(self):
        """页码超出范围"""
        items = list(range(1, 51))
        result = paginate_pure(total=50, page=100, page_size=10, items=items)
        
        assert result.items_count == 0
        assert result.items == []
    
    def test_zero_total(self):
        """总数为0"""
        result = paginate_pure(total=0, page=1, page_size=10)
        
        assert result.total == 0
        assert result.total_pages == 0
        assert result.items_count == 0
        assert result.items == []
    
    def test_negative_total(self):
        """负总数"""
        result = paginate_pure(total=-10, page=1, page_size=10)
        
        assert result.total == 0
        assert result.total_pages == 0
    
    def test_without_items(self):
        """不提供items参数"""
        result = paginate_pure(total=100, page=1, page_size=10)
        
        assert result.items == []
        assert result.items_count == 10
    
    def test_page_size_one(self):
        """每页1条"""
        items = [1, 2, 3, 4, 5]
        result = paginate_pure(total=5, page=3, page_size=1, items=items)
        
        assert result.items_count == 1
        assert result.items == [3]
    
    def test_large_page_size(self):
        """每页数量大于总数"""
        items = [1, 2, 3]
        result = paginate_pure(total=3, page=1, page_size=100, items=items)
        
        assert result.total_pages == 1
        assert result.items_count == 3
        assert result.items == [1, 2, 3]


class TestPageResult:
    """测试PageResult数据类"""

    def test_default_values(self):
        """默认值"""
        page_result = PageResult()
        
        assert page_result.items == []
        assert page_result.total == 0
        assert page_result.page == 1
        assert page_result.page_size == 10
        assert page_result.total_pages == 0
        assert page_result.items_count == 0
    
    def test_custom_values(self):
        """自定义值"""
        page_result = PageResult(
            items=[1, 2, 3],
            total=100,
            page=2,
            page_size=20,
            total_pages=5,
            items_count=3
        )
        
        assert page_result.items == [1, 2, 3]
        assert page_result.total == 100
        assert page_result.page == 2
