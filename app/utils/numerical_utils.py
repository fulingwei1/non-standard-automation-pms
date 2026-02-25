# -*- coding: utf-8 -*-
"""
数值计算工具模块 - 精确计算与业务规则

提供EVM、套件率、工时、报价含税等纯函数计算工具。
所有函数使用 Decimal 保证精度，适合单元测试。

新增函数覆盖 D3 测试组缺失的业务函数：
  - calc_spi_safe      : PV=0 时返回 1.0（防除零）
  - calc_cpi           : 成本绩效指数
  - is_cost_overrun    : CPI < 1 判定
  - calc_cumulative_kit_rate : 分批到货累计套件率
  - calc_hourly_rate   : 时薪 = 月薪 / (21.75 × 8)
  - calc_price_with_vat: 含税价格
  - calc_price_breakdown: 报价分解（硬件+人工+外协+利润）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 精度常量
# ---------------------------------------------------------------------------

PLACES_6 = Decimal("0.000001")
PLACES_4 = Decimal("0.0001")
PLACES_2 = Decimal("0.01")

# 国家规定月均工作日（劳动法）
MONTHLY_WORK_DAYS = Decimal("21.75")
DAILY_WORK_HOURS = Decimal("8")


# ---------------------------------------------------------------------------
# 1. EVM — 进度/成本绩效指数（防除零版本）
# ---------------------------------------------------------------------------

def calc_spi_safe(
    ev: float | int | Decimal,
    pv: float | int | Decimal,
    zero_pv_default: float | Decimal = Decimal("1.0"),
) -> Decimal:
    """
    计算进度绩效指数 (SPI = EV / PV)，PV=0 时返回约定默认值 1.0。

    业务约定：尚无计划基准时认为进度正常（SPI=1）。

    Args:
        ev: 挣得价值（Earned Value）
        pv: 计划价值（Planned Value）
        zero_pv_default: PV=0 时返回的默认值（默认 1.0）

    Returns:
        SPI（Decimal），精度 6 位
    """
    earned = Decimal(str(ev))
    planned = Decimal(str(pv))

    if planned == 0:
        return Decimal(str(zero_pv_default)).quantize(PLACES_6)

    spi = earned / planned
    return spi.quantize(PLACES_6)


def calc_cpi(
    ev: float | int | Decimal,
    ac: float | int | Decimal,
) -> Decimal:
    """
    计算成本绩效指数 (CPI = EV / AC)。

    Args:
        ev: 挣得价值（Earned Value）
        ac: 实际成本（Actual Cost）

    Returns:
        CPI（Decimal），精度 6 位

    Raises:
        ValueError: AC <= 0
    """
    earned = Decimal(str(ev))
    actual = Decimal(str(ac))

    if actual <= 0:
        raise ValueError("实际成本 (AC) 必须大于 0")

    cpi = earned / actual
    return cpi.quantize(PLACES_6)


def is_cost_overrun(cpi: float | Decimal) -> bool:
    """
    判断是否成本超支。

    规则：CPI < 1.0 表示花费多于完成的工作价值，即成本超支。

    Args:
        cpi: 成本绩效指数

    Returns:
        True 表示成本超支
    """
    return Decimal(str(cpi)) < Decimal("1.0")


def calc_eac(
    bac: float | int | Decimal,
    ev: float | int | Decimal,
    ac: float | int | Decimal,
) -> Decimal:
    """
    计算完工估算 EAC = AC + (BAC - EV) / CPI。

    当 CPI=0 时退化为 EAC = AC + (BAC - EV)。

    Returns:
        EAC（Decimal），精度 2 位
    """
    b = Decimal(str(bac))
    e = Decimal(str(ev))
    a = Decimal(str(ac))

    try:
        cpi = calc_cpi(e, a)
    except ValueError:
        cpi = Decimal("1")

    if cpi == 0:
        eac = a + (b - e)
    else:
        eac = a + (b - e) / cpi

    return eac.quantize(PLACES_2)


def calc_vac(
    bac: float | int | Decimal,
    eac: float | int | Decimal,
) -> Decimal:
    """
    计算完工偏差 VAC = BAC - EAC。

    Returns:
        VAC（Decimal），精度 2 位
    """
    return (Decimal(str(bac)) - Decimal(str(eac))).quantize(PLACES_2)


# ---------------------------------------------------------------------------
# 2. 套件率（Kit Rate）
# ---------------------------------------------------------------------------

def calc_cumulative_kit_rate(
    batches: Sequence[Tuple[float | int | Decimal, float | int | Decimal]],
) -> Decimal:
    """
    计算分批到货的累计套件率。

    业务背景：同一 BOM 需求（例如 100 件）分批到货，每批为一次领料记录。
    每个批次为 (本批实际到货量, BOM 总需求量) 的元组。

    公式：累计套件率 = Σ(actual_i) / bom_total_required
          其中 bom_total_required 取 batches[0][1]（所有批次对应同一个需求量）

    示例：
        batches=[(60, 100), (30, 100)]
        → 累计到货 = 60+30 = 90，BOM需求 = 100
        → 累计套件率 = 90/100 = 0.90

    Args:
        batches: 批次列表，每项 (本批到货量, BOM总需求量)
                 BOM总需求量在各批次中应保持一致

    Returns:
        累计套件率（Decimal），精度 6 位

    Raises:
        ValueError: batches 为空或 BOM 需求量 <= 0
    """
    if not batches:
        raise ValueError("批次列表不能为空")

    total_actual = Decimal("0")
    bom_required = Decimal(str(batches[0][1]))   # 取第一批的 BOM 需求量

    if bom_required <= 0:
        raise ValueError("BOM 需求量必须大于 0")

    for actual, _ in batches:
        total_actual += Decimal(str(actual))

    rate = total_actual / bom_required
    return rate.quantize(PLACES_6)


# ---------------------------------------------------------------------------
# 3. 工时计算
# ---------------------------------------------------------------------------

def calc_hourly_rate(monthly_salary: float | int | Decimal) -> Decimal:
    """
    计算时薪。

    公式：时薪 = 月薪 / (21.75天 × 8小时)

    参考：《关于职工全年月平均工作时间和工资折算问题的通知》
          （劳社部发〔2008〕3号）

    Args:
        monthly_salary: 月薪（元）

    Returns:
        时薪（Decimal），精度 4 位

    Raises:
        ValueError: 月薪 <= 0
    """
    salary = Decimal(str(monthly_salary))

    if salary <= 0:
        raise ValueError("月薪必须大于 0")

    divisor = MONTHLY_WORK_DAYS * DAILY_WORK_HOURS  # 174 小时
    hourly = salary / divisor
    return hourly.quantize(PLACES_4)


# ---------------------------------------------------------------------------
# 4. 报价含税计算
# ---------------------------------------------------------------------------

def calc_price_with_vat(
    price: float | int | Decimal,
    vat_rate: float | Decimal = Decimal("0.13"),
) -> Decimal:
    """
    计算含税价格。

    公式：含税价 = 不含税价 × (1 + 税率)

    中国增值税标准税率 13%（2019年税改后）。

    Args:
        price:    不含税价格（元）
        vat_rate: 增值税率（默认 0.13 即 13%）

    Returns:
        含税价格（Decimal），精度 2 位

    Raises:
        ValueError: 价格 < 0 或税率 < 0
    """
    p = Decimal(str(price))
    r = Decimal(str(vat_rate))

    if p < 0:
        raise ValueError("价格不能为负数")
    if r < 0:
        raise ValueError("税率不能为负数")

    tax_included = p * (Decimal("1") + r)
    return tax_included.quantize(PLACES_2)


def calc_price_breakdown(
    hardware: float | int | Decimal,
    labor: float | int | Decimal,
    outsource: float | int | Decimal,
    margin_rate: float | Decimal,
) -> Dict[str, Decimal]:
    """
    计算报价分解（含利润）。

    逻辑：
        成本合计 = 硬件 + 人工 + 外协
        含利润报价 = 成本合计 / (1 - margin_rate)
        利润 = 报价 - 成本合计

    Args:
        hardware:     硬件成本（元）
        labor:        人工成本（元）
        outsource:    外协费用（元）
        margin_rate:  目标毛利率（0~1），例如 0.30 表示 30%

    Returns:
        包含以下键的字典：
          hardware, labor, outsource, cost_subtotal, price, profit, margin_rate_actual

    Raises:
        ValueError: margin_rate >= 1 或 margin_rate < 0
    """
    h = Decimal(str(hardware))
    l_ = Decimal(str(labor))
    o = Decimal(str(outsource))
    m = Decimal(str(margin_rate))

    if m < 0 or m >= 1:
        raise ValueError("毛利率必须在 [0, 1) 区间")

    cost_subtotal = h + l_ + o
    # 毛利率公式：margin = profit / price  →  price = cost / (1 - margin)
    price = cost_subtotal / (Decimal("1") - m)
    profit = price - cost_subtotal

    return {
        "hardware": h.quantize(PLACES_2),
        "labor": l_.quantize(PLACES_2),
        "outsource": o.quantize(PLACES_2),
        "cost_subtotal": cost_subtotal.quantize(PLACES_2),
        "price": price.quantize(PLACES_2),
        "profit": profit.quantize(PLACES_2),
        "margin_rate_actual": (profit / price).quantize(PLACES_6),
    }


# ---------------------------------------------------------------------------
# 5. 纯函数分页工具（不依赖 SQLAlchemy）
# ---------------------------------------------------------------------------

@dataclass
class PageResult:
    """分页结果数据类"""
    items: List = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0
    items_count: int = 0   # 当前页实际条数


def paginate_pure(
    total: int,
    page: int,
    page_size: int,
    items: List | None = None,
) -> PageResult:
    """
    纯函数分页计算，不依赖数据库。

    Args:
        total:      总记录数
        page:       当前页码（从 1 开始）
        page_size:  每页条数
        items:      当前页数据（可选，默认自动裁剪传入的 items）

    Returns:
        PageResult
    """
    if total <= 0:
        return PageResult(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            items_count=0,
        )

    total_pages = (total + page_size - 1) // page_size

    # 计算当前页实际条数
    if page > total_pages:
        items_count = 0
        page_items = []
    else:
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        items_count = end - start
        if items is not None:
            page_items = items[start:end]
        else:
            page_items = []

    return PageResult(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items_count=items_count,
    )
