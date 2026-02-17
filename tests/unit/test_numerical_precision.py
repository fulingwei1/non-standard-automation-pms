# -*- coding: utf-8 -*-
"""
D3 组：计算精度 & 数值边界测试
================================

目标：验证所有数值计算的精度和边界情况。

覆盖场景：
  1. EVM（挣值管理）计算精度 — SPI / CPI / EAC / VAC + 除零保护
  2. 套件率精度 — 分批到货 / 超量发货 / 边界
  3. 工时计算精度 — 跨春节工作日 / 时薪公式
  4. 报价含税计算 — 增值税 13% / 报价分解
  5. 分页和数据截断 — 最后一页 / 空集 / 越界

依赖：
  - app/utils/numerical_utils.py  (新增工具函数)
  - app/services/business_rules.py (calc_spi / calc_kit_rate / should_trigger_shortage_alert)
  - app/utils/holiday_utils.py    (get_working_days)

运行：
  pytest tests/unit/test_numerical_precision.py -v
"""

import pytest
from datetime import date
from decimal import Decimal

# ─── 被测模块 ────────────────────────────────────────────────────────────────

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
)

from app.services.business_rules import (
    calc_spi,           # 原版（PV<=0 抛异常）
    calc_kit_rate,      # 套件率原版
    should_trigger_shortage_alert,
)

from app.utils.holiday_utils import get_working_days


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EVM 计算精度
# ═══════════════════════════════════════════════════════════════════════════════

class TestEVMPrecision:
    """EVM（挣值管理）数值精度与边界测试"""

    # ── SPI 精度测试 ─────────────────────────────────────────────────────────

    def test_spi_zero_pv_returns_default_1(self):
        """PV=0 时不应除零崩溃，约定返回 1.0（无计划则视为正常）"""
        spi = calc_spi_safe(ev=0, pv=0)
        assert spi == pytest.approx(1.0, abs=1e-6)

    def test_spi_zero_ev_zero_pv(self):
        """EV 和 PV 均为 0 时 SPI=1（项目未启动，约定正常）"""
        spi = calc_spi_safe(ev=0, pv=0)
        assert float(spi) == pytest.approx(1.0, abs=1e-6)

    def test_spi_decimal_precision(self):
        """小数精度：EV=333.33, PV=333.34 → SPI ≈ 0.9999"""
        spi = calc_spi_safe(ev=333.33, pv=333.34)
        assert float(spi) == pytest.approx(0.9999, abs=0.0001)

    def test_spi_large_numbers(self):
        """超大数精度：EV=1e9, PV=1e9 → SPI=1.0"""
        spi = calc_spi_safe(ev=1_000_000_000, pv=1_000_000_000)
        assert float(spi) == pytest.approx(1.0, abs=1e-6)

    def test_spi_ahead_of_schedule(self):
        """进度超前：EV > PV → SPI > 1"""
        spi = calc_spi_safe(ev=120_000, pv=100_000)
        assert float(spi) == pytest.approx(1.2, abs=1e-4)
        assert float(spi) > 1.0

    def test_spi_behind_schedule(self):
        """进度落后：EV < PV → SPI < 1"""
        spi = calc_spi_safe(ev=80_000, pv=100_000)
        assert float(spi) == pytest.approx(0.8, abs=1e-4)
        assert float(spi) < 1.0

    def test_spi_original_raises_on_zero_pv(self):
        """原版 calc_spi 在 PV=0 时应抛出 ValueError"""
        with pytest.raises(ValueError, match="计划价值"):
            calc_spi(ev=0, pv=0)

    # ── CPI 精度测试 ─────────────────────────────────────────────────────────

    def test_cpi_negative_variance(self):
        """成本超支：EV=80000, AC=100000 → CPI=0.8"""
        cpi = calc_cpi(ev=80_000, ac=100_000)
        assert float(cpi) == pytest.approx(0.8, abs=0.001)

    def test_cpi_cost_saving(self):
        """成本节约：EV=100000, AC=80000 → CPI=1.25"""
        cpi = calc_cpi(ev=100_000, ac=80_000)
        assert float(cpi) == pytest.approx(1.25, abs=0.001)

    def test_cpi_exactly_one(self):
        """成本恰好符合预算：EV=AC → CPI=1.0"""
        cpi = calc_cpi(ev=500_000, ac=500_000)
        assert float(cpi) == pytest.approx(1.0, abs=1e-6)

    def test_cpi_zero_ac_raises(self):
        """AC=0 时应抛出 ValueError（防除零）"""
        with pytest.raises(ValueError, match="实际成本"):
            calc_cpi(ev=50_000, ac=0)

    def test_is_cost_overrun_true(self):
        """CPI < 1 → 成本超支"""
        cpi = calc_cpi(ev=80_000, ac=100_000)
        assert is_cost_overrun(cpi) is True

    def test_is_cost_overrun_false_saving(self):
        """CPI > 1 → 未超支"""
        cpi = calc_cpi(ev=100_000, ac=80_000)
        assert is_cost_overrun(cpi) is False

    def test_is_cost_overrun_exactly_one(self):
        """CPI = 1 → 恰好不超支"""
        assert is_cost_overrun(Decimal("1.0")) is False

    # ── EAC / VAC 精度测试 ──────────────────────────────────────────────────

    def test_eac_standard_formula(self):
        """EAC 标准公式：BAC=1e6, EV=400000, AC=500000 → EAC=1250000"""
        eac = calc_eac(bac=1_000_000, ev=400_000, ac=500_000)
        assert float(eac) == pytest.approx(1_250_000, abs=1)

    def test_vac_overrun(self):
        """VAC < 0 表示预计超出预算"""
        eac = calc_eac(bac=1_000_000, ev=400_000, ac=500_000)
        vac = calc_vac(bac=1_000_000, eac=eac)
        assert float(vac) < 0

    def test_vac_saving(self):
        """VAC > 0 表示预计节约成本"""
        eac = calc_eac(bac=1_000_000, ev=900_000, ac=800_000)
        vac = calc_vac(bac=1_000_000, eac=eac)
        assert float(vac) > 0

    def test_eac_negative_ev(self):
        """EV 为负数时不崩溃（异常项目）"""
        eac = calc_eac(bac=500_000, ev=-10_000, ac=100_000)
        assert isinstance(eac, Decimal)

    def test_cpi_very_small_value(self):
        """极小 CPI：EV=1, AC=1000000 → CPI 极小"""
        cpi = calc_cpi(ev=1, ac=1_000_000)
        assert float(cpi) == pytest.approx(0.000001, abs=1e-9)
        assert is_cost_overrun(cpi) is True


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 套件率精度
# ═══════════════════════════════════════════════════════════════════════════════

class TestKitRatePrecision:
    """套件率数值精度与边界测试"""

    # ── 基础套件率 ───────────────────────────────────────────────────────────

    def test_kit_rate_exact_100_percent(self):
        """恰好 100% 套件（全部到货）"""
        rate = calc_kit_rate(actual_qty=100, bom_qty=100)
        assert float(rate) == pytest.approx(1.0, abs=0.001)

    def test_kit_rate_over_delivery(self):
        """超量发货：实际 105，需求 100 → 套件率 1.05"""
        rate = calc_kit_rate(actual_qty=105, bom_qty=100)
        assert float(rate) == pytest.approx(1.05, abs=0.001)

    def test_kit_rate_over_delivery_no_shortage_alert(self):
        """超量发货不应触发缺料预警"""
        rate = calc_kit_rate(actual_qty=105, bom_qty=100)
        assert should_trigger_shortage_alert(rate) is False

    def test_kit_rate_zero_actual(self):
        """实际到货为 0 → 套件率 0（完全缺料）"""
        rate = calc_kit_rate(actual_qty=0, bom_qty=100)
        assert float(rate) == pytest.approx(0.0, abs=0.001)
        assert should_trigger_shortage_alert(rate) is True

    def test_kit_rate_bom_zero_raises(self):
        """BOM 需求为 0 时应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_kit_rate(actual_qty=50, bom_qty=0)

    def test_kit_rate_below_threshold_triggers_alert(self):
        """套件率 < 95% 触发缺料预警"""
        rate = calc_kit_rate(actual_qty=90, bom_qty=100)
        assert float(rate) == pytest.approx(0.90, abs=0.001)
        assert should_trigger_shortage_alert(rate) is True

    def test_kit_rate_exactly_at_threshold(self):
        """套件率恰好 95% → 不触发（边界值，规则是 < 95% 才触发）"""
        rate = calc_kit_rate(actual_qty=95, bom_qty=100)
        assert float(rate) == pytest.approx(0.95, abs=0.001)
        assert should_trigger_shortage_alert(rate) is False

    # ── 分批到货累计套件率 ────────────────────────────────────────────────────

    def test_cumulative_kit_rate_two_batches(self):
        """两批到货 60+30 / 100+100 → 累计 90%"""
        rate = calc_cumulative_kit_rate(batches=[(60, 100), (30, 100)])
        assert float(rate) == pytest.approx(0.90, abs=0.001)

    def test_cumulative_kit_rate_single_batch(self):
        """单批次：60/100 → 60%"""
        rate = calc_cumulative_kit_rate(batches=[(60, 100)])
        assert float(rate) == pytest.approx(0.60, abs=0.001)

    def test_cumulative_kit_rate_full_three_batches(self):
        """三批次合计恰好 100%：30+40+30 / 100 = 1.0"""
        rate = calc_cumulative_kit_rate(batches=[(30, 100), (40, 100), (30, 100)])
        assert float(rate) == pytest.approx(1.0, abs=0.001)

    def test_cumulative_kit_rate_over_delivery(self):
        """分批超量：105/100 → 1.05"""
        rate = calc_cumulative_kit_rate(batches=[(60, 100), (45, 100)])
        assert float(rate) == pytest.approx(1.05, abs=0.001)

    def test_cumulative_kit_rate_empty_batches_raises(self):
        """空批次应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_cumulative_kit_rate(batches=[])

    def test_cumulative_kit_rate_decimal_precision(self):
        """小数精度：3.33+3.33 分两批到货，BOM需求10 → 6.66/10 ≈ 0.666"""
        rate = calc_cumulative_kit_rate(batches=[(3.33, 10), (3.33, 10)])
        assert float(rate) == pytest.approx(0.666, abs=0.001)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 工时计算精度
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorkingDaysPrecision:
    """工作日计算与时薪精度测试"""

    # ── 跨节假日工作日 ────────────────────────────────────────────────────────

    def test_working_days_normal_week(self):
        """普通工作周（5天）"""
        # 2026-03-09(周一) 到 2026-03-13(周五)
        days = get_working_days(date(2026, 3, 9), date(2026, 3, 13))
        assert days == 5

    def test_working_days_includes_weekend_raw(self):
        """全周含周末（7天），工作日仍 5"""
        # 2026-03-09(周一) 到 2026-03-15(周日)
        days = get_working_days(date(2026, 3, 9), date(2026, 3, 15))
        # holiday_utils 的 get_working_days 不跳过周末，只跳过节假日
        # 验证它统计非节假日天数（包含周末）= 7天（3月均无法定节假日）
        assert days == 7

    def test_working_days_across_spring_festival_2026(self):
        """
        跨 2026 年春节（2月15-21日）的工作日计算。

        holiday_utils 中的 get_working_days 统计非法定节假日天数（含周末）。
        2026-02-12(周四) 到 2026-02-22(周日) = 11天
        其中 2/15–2/21 = 7天法定假
        实际非节假日 = 11 - 7 = 4 天（2/12, 2/13, 2/14, 2/22）
        """
        days = get_working_days(date(2026, 2, 12), date(2026, 2, 22))
        # 2/15-2/21 是春节（7天）；11 - 7 = 4
        assert days == 4

    def test_working_days_spring_festival_excluded(self):
        """春节期间全为节假日，工作日=0"""
        # 2026-02-15 到 2026-02-21（春节 7 天全假）
        days = get_working_days(date(2026, 2, 15), date(2026, 2, 21))
        assert days == 0

    def test_working_days_single_day_workday(self):
        """单个工作日"""
        days = get_working_days(date(2026, 3, 9), date(2026, 3, 9))
        assert days == 1

    def test_working_days_single_day_holiday(self):
        """单个节假日：2026-02-17（春节）"""
        days = get_working_days(date(2026, 2, 17), date(2026, 2, 17))
        assert days == 0

    # ── 时薪计算 ─────────────────────────────────────────────────────────────

    def test_hourly_rate_standard(self):
        """时薪 = 月薪 / (21.75 × 8) = 15000 / 174 ≈ 86.21"""
        rate = calc_hourly_rate(15000)
        expected = 15000 / (21.75 * 8)
        assert float(rate) == pytest.approx(expected, abs=0.01)

    def test_hourly_rate_formula(self):
        """任意月薪公式验证"""
        for monthly in [5000, 10000, 20000, 50000]:
            rate = calc_hourly_rate(monthly)
            expected = monthly / (21.75 * 8)
            assert float(rate) == pytest.approx(expected, abs=0.01)

    def test_hourly_rate_zero_raises(self):
        """月薪=0 应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_hourly_rate(0)

    def test_hourly_rate_negative_raises(self):
        """负数月薪应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_hourly_rate(-1000)

    def test_hourly_rate_large_salary(self):
        """超高月薪（100万）也应正常计算"""
        rate = calc_hourly_rate(1_000_000)
        expected = 1_000_000 / (21.75 * 8)
        assert float(rate) == pytest.approx(expected, abs=0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. 报价含税计算
# ═══════════════════════════════════════════════════════════════════════════════

class TestVATAndPriceBreakdown:
    """含税价格与报价分解精度测试"""

    # ── 含税价格 ─────────────────────────────────────────────────────────────

    def test_vat_13_percent(self):
        """含税价 = 不含税价 × 1.13（增值税 13%）"""
        tax_included = calc_price_with_vat(price=280_000, vat_rate=0.13)
        assert float(tax_included) == pytest.approx(316_400, abs=1)

    def test_vat_zero_rate(self):
        """零税率（出口免税）：含税价 = 不含税价"""
        tax_included = calc_price_with_vat(price=100_000, vat_rate=0.0)
        assert float(tax_included) == pytest.approx(100_000, abs=0.01)

    def test_vat_6_percent(self):
        """6% 税率（服务业）：100000 × 1.06 = 106000"""
        tax_included = calc_price_with_vat(price=100_000, vat_rate=0.06)
        assert float(tax_included) == pytest.approx(106_000, abs=1)

    def test_vat_zero_price(self):
        """零价格：含税价也为 0"""
        tax_included = calc_price_with_vat(price=0, vat_rate=0.13)
        assert float(tax_included) == pytest.approx(0, abs=0.01)

    def test_vat_negative_price_raises(self):
        """负数价格应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_price_with_vat(price=-1000, vat_rate=0.13)

    def test_vat_negative_rate_raises(self):
        """负税率应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_price_with_vat(price=100_000, vat_rate=-0.1)

    def test_vat_large_amount(self):
        """大额订单精度：500万 × 1.13 = 565万"""
        tax_included = calc_price_with_vat(price=5_000_000, vat_rate=0.13)
        assert float(tax_included) == pytest.approx(5_650_000, abs=1)

    # ── 报价分解 ─────────────────────────────────────────────────────────────

    def test_price_breakdown_30_margin(self):
        """报价分解：硬件+人工+外协，毛利率 30%"""
        bd = calc_price_breakdown(
            hardware=180_000, labor=60_000, outsource=20_000, margin_rate=0.30
        )
        total = sum([bd["hardware"], bd["labor"], bd["outsource"], bd["profit"]])
        profit = bd["profit"]
        # 毛利率检查
        assert float(profit / total) == pytest.approx(0.30, abs=0.01)

    def test_price_breakdown_cost_subtotal(self):
        """成本合计 = 硬件 + 人工 + 外协"""
        bd = calc_price_breakdown(hardware=100_000, labor=50_000, outsource=10_000, margin_rate=0.20)
        assert float(bd["cost_subtotal"]) == pytest.approx(160_000, abs=0.01)

    def test_price_breakdown_zero_margin(self):
        """毛利率=0：报价=成本，利润=0"""
        bd = calc_price_breakdown(hardware=100_000, labor=0, outsource=0, margin_rate=0.0)
        assert float(bd["profit"]) == pytest.approx(0, abs=0.01)
        assert float(bd["price"]) == pytest.approx(100_000, abs=0.01)

    def test_price_breakdown_margin_rate_100_raises(self):
        """毛利率=1 应抛出 ValueError（分母为零）"""
        with pytest.raises(ValueError):
            calc_price_breakdown(hardware=100_000, labor=0, outsource=0, margin_rate=1.0)

    def test_price_breakdown_negative_margin_raises(self):
        """负毛利率应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_price_breakdown(hardware=100_000, labor=0, outsource=0, margin_rate=-0.1)

    def test_price_breakdown_actual_margin_rate_consistency(self):
        """actual_margin_rate 字段与手工计算一致"""
        bd = calc_price_breakdown(hardware=70_000, labor=20_000, outsource=10_000, margin_rate=0.25)
        margin_check = bd["profit"] / bd["price"]
        assert float(margin_check) == pytest.approx(float(bd["margin_rate_actual"]), abs=1e-5)

    def test_price_breakdown_large_project(self):
        """大型项目精度：千万级报价"""
        bd = calc_price_breakdown(
            hardware=5_000_000, labor=2_000_000, outsource=1_000_000, margin_rate=0.25
        )
        assert float(bd["cost_subtotal"]) == pytest.approx(8_000_000, abs=1)
        # 价格 = 8M / 0.75 ≈ 10666666.67
        assert float(bd["price"]) == pytest.approx(10_666_666.67, abs=1)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. 分页和数据截断
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaginationBoundary:
    """纯函数分页边界测试"""

    # ── 正常分页 ─────────────────────────────────────────────────────────────

    def test_pagination_first_page(self):
        """第一页数据量 = page_size"""
        result = paginate_pure(total=25, page=1, page_size=10)
        assert result.items_count == 10

    def test_pagination_second_page(self):
        """第二页数据量 = page_size"""
        result = paginate_pure(total=25, page=2, page_size=10)
        assert result.items_count == 10

    def test_pagination_last_page(self):
        """最后一页数据量少于 page_size（25 总数，第3页 = 5条）"""
        result = paginate_pure(total=25, page=3, page_size=10)
        assert result.items_count == 5

    def test_pagination_total_pages(self):
        """总页数计算正确：25 / 10 → 3 页"""
        result = paginate_pure(total=25, page=1, page_size=10)
        assert result.total_pages == 3

    # ── 边界：空数据集 ────────────────────────────────────────────────────────

    def test_pagination_empty_total_zero(self):
        """空数据集：total=0 → total_pages=0, items=[]"""
        result = paginate_pure(total=0, page=1, page_size=10)
        assert result.total_pages == 0
        assert result.items == []
        assert result.items_count == 0

    def test_pagination_empty_items_count(self):
        """空数据集 items_count 也为 0"""
        result = paginate_pure(total=0, page=1, page_size=10)
        assert result.items_count == 0

    # ── 边界：恰好整除 ────────────────────────────────────────────────────────

    def test_pagination_exact_multiple(self):
        """恰好整除：30 / 10 = 3 页，第 3 页 10 条"""
        result = paginate_pure(total=30, page=3, page_size=10)
        assert result.total_pages == 3
        assert result.items_count == 10

    def test_pagination_single_item(self):
        """仅 1 条数据：1 页，第1页 1 条"""
        result = paginate_pure(total=1, page=1, page_size=10)
        assert result.total_pages == 1
        assert result.items_count == 1

    def test_pagination_page_beyond_total(self):
        """页码超出总页数：items_count=0"""
        result = paginate_pure(total=10, page=5, page_size=10)
        assert result.items_count == 0
        assert result.items == []

    def test_pagination_page_size_one(self):
        """每页 1 条：第 5 页只有 1 条"""
        result = paginate_pure(total=25, page=5, page_size=1)
        assert result.total_pages == 25
        assert result.items_count == 1

    def test_pagination_large_dataset(self):
        """大数据集：1000 条，每页 7 条，最后一页"""
        result = paginate_pure(total=1000, page=143, page_size=7)
        # 143 * 7 = 1001 > 1000，实际 143 页只有 1000 - 142*7 = 6 条
        assert result.items_count == 6

    def test_pagination_with_items_list(self):
        """传入实际列表时，分页返回正确切片"""
        items = list(range(25))  # [0..24]
        result = paginate_pure(total=25, page=3, page_size=10, items=items)
        assert result.items == [20, 21, 22, 23, 24]
        assert result.items_count == 5

    # ── 元数据字段 ────────────────────────────────────────────────────────────

    def test_pagination_metadata_fields(self):
        """分页结果包含完整元数据"""
        result = paginate_pure(total=100, page=2, page_size=10)
        assert result.total == 100
        assert result.page == 2
        assert result.page_size == 10
        assert result.total_pages == 10
