# -*- coding: utf-8 -*-
"""
非标自动化项目核心业务规则

集中封装可纯函数测试的业务规则，供各模块调用和单元测试。
所有函数均为无副作用的纯函数，不依赖数据库。

业务规则来源：
- 公司毛利率管理制度（财务制度 §3.2）
- 生产套件率 KPI 基准（生产管理标准 §5.1）
- 项目进度管理规程（PMO 规程 §4.3）
- 合同收款管理办法（财务制度 §6.1）
- 劳动时间异常监控规定（HR 制度 §2.4）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Literal

# ---------------------------------------------------------------------------
# KPI 基准常量（以字典形式集中管理，方便统一调整）
# ---------------------------------------------------------------------------

KPI_BENCHMARKS = {
    # 毛利率
    "gross_margin_warning": Decimal("0.20"),   # 低于 20% 预警
    "gross_margin_gm_approval": Decimal("0.10"),  # 低于 10% 需总经理审批
    # 套件率
    "kit_rate_target": Decimal("0.95"),         # 套件率目标 95%
    # 进度绩效
    "spi_warning": Decimal("0.90"),             # SPI < 0.9 触发延期预警
    "spi_urgent": Decimal("0.80"),              # SPI < 0.8 触发紧急预警
    # 付款逾期
    "payment_overdue_escalation_days": 30,     # 逾期超 30 天需升级
    # 工时
    "daily_overtime_threshold": Decimal("10"),  # 日工时 > 10h 标记异常
    "monthly_hr_review_threshold": Decimal("220"),  # 月工时 > 220h 触发 HR 关注
}

# ---------------------------------------------------------------------------
# 1. 毛利率计算规则
# ---------------------------------------------------------------------------

def calc_gross_margin(
    contract: float | Decimal,
    hardware: float | Decimal,
    labor: float | Decimal,
    outsource: float | Decimal,
    travel: float | Decimal,
) -> Decimal:
    """
    计算非标项目毛利率。

    公式：毛利率 = (合同金额 - 硬件成本 - 人工成本 - 外协费 - 差旅费) / 合同金额

    Args:
        contract:  合同金额（元）
        hardware:  硬件成本（元）
        labor:     人工成本（元）
        outsource: 外协费（元）
        travel:    差旅费（元）

    Returns:
        毛利率（Decimal），例如 0.17 表示 17%

    Raises:
        ValueError: 合同金额 <= 0
    """
    c = Decimal(str(contract))
    h = Decimal(str(hardware))
    l = Decimal(str(labor))
    o = Decimal(str(outsource))
    t = Decimal(str(travel))

    if c <= 0:
        raise ValueError("合同金额必须大于 0")

    gross_profit = c - h - l - o - t
    margin = gross_profit / c
    # 保留6位有效小数，避免浮点误差干扰断言
    return margin.quantize(Decimal("0.000001"))


def is_warning_required(margin: float | Decimal) -> bool:
    """
    毛利率是否需要预警。

    规则：毛利率 < 20% 触发预警。

    Args:
        margin: 毛利率（0~1 之间的小数）

    Returns:
        True 表示需要预警
    """
    return Decimal(str(margin)) < KPI_BENCHMARKS["gross_margin_warning"]


def requires_gm_approval(margin: float | Decimal) -> bool:
    """
    毛利率是否需要总经理审批。

    规则：毛利率 < 10% 必须由总经理审批。

    Args:
        margin: 毛利率（0~1 之间的小数）

    Returns:
        True 表示需要总经理审批
    """
    return Decimal(str(margin)) < KPI_BENCHMARKS["gross_margin_gm_approval"]


# ---------------------------------------------------------------------------
# 2. 套件率（Kit Rate）计算规则
# ---------------------------------------------------------------------------

def calc_kit_rate(actual_qty: int | float | Decimal, bom_qty: int | float | Decimal) -> Decimal:
    """
    计算套件率。

    公式：套件率 = 实际领料数量 / BOM 需求数量

    Args:
        actual_qty: 实际领料数量
        bom_qty:    BOM 需求数量

    Returns:
        套件率（Decimal）

    Raises:
        ValueError: BOM 需求数量 <= 0
    """
    a = Decimal(str(actual_qty))
    b = Decimal(str(bom_qty))

    if b <= 0:
        raise ValueError("BOM 需求数量必须大于 0")

    kit_rate = a / b
    return kit_rate.quantize(Decimal("0.000001"))


def should_trigger_shortage_alert(kit_rate: float | Decimal) -> bool:
    """
    根据套件率判断是否触发缺料预警。

    规则：套件率 < 95% 触发缺料预警。

    Args:
        kit_rate: 套件率（0~1 之间的小数）

    Returns:
        True 表示应触发缺料预警
    """
    return Decimal(str(kit_rate)) < KPI_BENCHMARKS["kit_rate_target"]


# ---------------------------------------------------------------------------
# 3. 项目延期预警规则（基于 EVM SPI）
# ---------------------------------------------------------------------------

def calc_spi(ev: float | Decimal, pv: float | Decimal) -> Decimal:
    """
    计算进度绩效指数 (SPI = EV / PV)。

    Args:
        ev: 挣得价值（Earned Value）
        pv: 计划价值（Planned Value）

    Returns:
        SPI（Decimal），精度 6 位

    Raises:
        ValueError: PV <= 0
    """
    earned = Decimal(str(ev))
    planned = Decimal(str(pv))

    if planned <= 0:
        raise ValueError("计划价值 (PV) 必须大于 0")

    spi = earned / planned
    return spi.quantize(Decimal("0.000001"))


DelayAlertLevel = Literal["NONE", "WARNING", "URGENT"]


def get_delay_alert_level(spi: float | Decimal) -> DelayAlertLevel:
    """
    根据 SPI 判断延期预警等级。

    规则：
    - SPI >= 0.9 → NONE（正常）
    - 0.8 <= SPI < 0.9 → WARNING（延期预警）
    - SPI < 0.8 → URGENT（紧急预警，需通知 PM）

    Args:
        spi: 进度绩效指数

    Returns:
        延期预警等级字符串
    """
    s = Decimal(str(spi))
    if s < KPI_BENCHMARKS["spi_urgent"]:
        return "URGENT"
    if s < KPI_BENCHMARKS["spi_warning"]:
        return "WARNING"
    return "NONE"


# ---------------------------------------------------------------------------
# 4. 付款节点验证
# ---------------------------------------------------------------------------

@dataclass
class PaymentMilestone:
    """付款里程碑数据类"""
    stage: str              # 付款阶段名称
    ratio: Decimal          # 比例（0~1）
    amount: Decimal         # 金额（元）
    trigger: str = ""       # 触发条件说明


# 标准合同付款结构（可由业务配置覆盖）
STANDARD_PAYMENT_RATIOS: List[dict] = [
    {"stage": "签约款",  "ratio": Decimal("0.30"), "trigger": "合同签订后"},
    {"stage": "到货款",  "ratio": Decimal("0.30"), "trigger": "设备到货后"},
    {"stage": "验收款",  "ratio": Decimal("0.30"), "trigger": "终验通过后"},
    {"stage": "质保款",  "ratio": Decimal("0.10"), "trigger": "质保期满后"},
]


def create_standard_payment_milestones(contract_amount: float | Decimal) -> List[PaymentMilestone]:
    """
    按标准合同付款结构生成付款里程碑列表。

    标准比例：签约 30% + 到货 30% + 验收 30% + 质保 10% = 100%

    Args:
        contract_amount: 合同总金额（元）

    Returns:
        包含四个 PaymentMilestone 对象的列表

    Raises:
        ValueError: 合同金额 <= 0
    """
    total = Decimal(str(contract_amount))
    if total <= 0:
        raise ValueError("合同金额必须大于 0")

    milestones = []
    cumulative = Decimal("0")
    configs = list(STANDARD_PAYMENT_RATIOS)

    for i, cfg in enumerate(configs):
        if i < len(configs) - 1:
            amount = (total * cfg["ratio"]).quantize(Decimal("0.01"))
            cumulative += amount
        else:
            # 最后一期用余额，避免因四舍五入导致合计不等于合同金额
            amount = total - cumulative

        milestones.append(
            PaymentMilestone(
                stage=cfg["stage"],
                ratio=cfg["ratio"],
                amount=amount,
                trigger=cfg["trigger"],
            )
        )

    return milestones


def calc_payment_overdue_days(due_date: date, today: date) -> int:
    """
    计算付款逾期天数。

    Args:
        due_date: 应付款日期
        today:    计算基准日期（通常为 date.today()）

    Returns:
        逾期天数（>= 0），未逾期返回 0
    """
    delta = (today - due_date).days
    return max(0, delta)


def is_overdue_escalation_required(overdue_days: int) -> bool:
    """
    判断逾期付款是否需要升级处理。

    规则：逾期超过 30 天需要升级至管理层跟进。

    Args:
        overdue_days: 逾期天数

    Returns:
        True 表示需要升级
    """
    return overdue_days > KPI_BENCHMARKS["payment_overdue_escalation_days"]


# ---------------------------------------------------------------------------
# 5. 工时异常检测
# ---------------------------------------------------------------------------

def is_daily_overtime(hours: float | Decimal) -> bool:
    """
    判断日工时是否触发异常标记。

    规则：日工时 > 10 小时标记为异常（可能存在漏报/健康风险）。

    Args:
        hours: 当日工时（小时）

    Returns:
        True 表示工时异常
    """
    return Decimal(str(hours)) > KPI_BENCHMARKS["daily_overtime_threshold"]


def should_hr_review(monthly_hours: float | Decimal) -> bool:
    """
    判断月工时是否需要 HR 关注。

    规则：月工时 > 220 小时需通知 HR 进行关注（约合月均每天 10h 以上）。

    Args:
        monthly_hours: 当月累计工时（小时）

    Returns:
        True 表示需要 HR 关注
    """
    return Decimal(str(monthly_hours)) > KPI_BENCHMARKS["monthly_hr_review_threshold"]


# ---------------------------------------------------------------------------
# 6. FAT/SAT 验收判定规则（非标设备交付核心逻辑）
# ---------------------------------------------------------------------------

FATStatus = Literal["PASSED", "CONDITIONAL_PASS", "FAILED"]


@dataclass
class FATResult:
    """FAT验收结果数据类"""
    status: FATStatus          # 验收结论
    can_ship: bool             # 是否允许发货
    failed_items: List[str] = field(default_factory=list)   # 不通过项列表
    conditional_items: List[str] = field(default_factory=list)  # 有条件通过项


def evaluate_fat_result(test_items: List[dict]) -> FATResult:
    """
    评估 FAT（出厂验收测试）结果。

    判定规则（优先级从高到低）：
      1. 任意 CRITICAL 项 FAIL → FAT 失败，禁止发货
      2. 任意 MAJOR 项 FAIL    → FAT 失败，禁止发货
      3. 仅 MINOR 项 FAIL      → 有条件通过，可发货但限期整改
      4. 全部通过              → FAT 通过

    Args:
        test_items: 测试项列表，每项包含：
            - name:   测试项名称（str）
            - result: "PASS" | "FAIL"
            - level:  "CRITICAL" | "MAJOR" | "MINOR"

    Returns:
        FATResult 对象

    Raises:
        ValueError: test_items 为空
    """
    if not test_items:
        raise ValueError("测试项列表不能为空")

    failed_critical: List[str] = []
    failed_major: List[str] = []
    failed_minor: List[str] = []

    for item in test_items:
        if item.get("result") == "FAIL":
            level = item.get("level", "MINOR")
            name = item.get("name", "未知测试项")
            if level == "CRITICAL":
                failed_critical.append(name)
            elif level == "MAJOR":
                failed_major.append(name)
            else:
                failed_minor.append(name)

    all_failed = failed_critical + failed_major + failed_minor

    if failed_critical or failed_major:
        # CRITICAL 或 MAJOR 不通过 → FAT 失败，禁止发货
        return FATResult(
            status="FAILED",
            can_ship=False,
            failed_items=all_failed,
        )
    elif failed_minor:
        # 仅 MINOR 不通过 → 有条件通过（可发货，限期整改）
        return FATResult(
            status="CONDITIONAL_PASS",
            can_ship=True,
            failed_items=[],
            conditional_items=failed_minor,
        )
    else:
        # 全部通过
        return FATResult(
            status="PASSED",
            can_ship=True,
        )


# ---------------------------------------------------------------------------
# 7. 项目最终毛利核算（结项时）
# ---------------------------------------------------------------------------

def calc_final_margin(project_data: dict) -> float:
    """
    计算项目结项毛利率。

    公式：毛利率 = (合同金额 - 所有实际成本之和) / 合同金额

    Args:
        project_data: 项目数据字典，包含：
            - contract_amount: 合同金额（元）
            - costs: 各类成本字典，支持以下键：
                - hardware, labor, outsource, travel（及其他自定义键）

    Returns:
        毛利率（float），例如 0.35 表示 35%

    Raises:
        ValueError: 合同金额 <= 0
    """
    contract = float(project_data["contract_amount"])
    if contract <= 0:
        raise ValueError("合同金额必须大于 0")

    costs = project_data.get("costs", {})
    total_cost = sum(float(v) for v in costs.values())
    gross_profit = contract - total_cost
    return gross_profit / contract


def requires_margin_review(margin: float) -> bool:
    """
    判断毛利率是否需要审查。

    规则：毛利率 < 20% 需要管理层审查（与 is_warning_required 对应，
    供结项核算场景直接调用）。

    Args:
        margin: 毛利率（0~1 之间的小数）

    Returns:
        True 表示需要审查
    """
    return margin < float(KPI_BENCHMARKS["gross_margin_warning"])


# ---------------------------------------------------------------------------
# 8. 工期偏差分析（D6组：交付专项）
# ---------------------------------------------------------------------------

def analyze_delay_root_causes(delays: List[dict]) -> List[dict]:
    """
    分析延期根因，按频次和延误天数排序。

    Args:
        delays: 延期记录列表，每条包含：
            - reason:     延期原因（str）
            - days:       延误天数（int）
            - project_id: 所属项目 ID

    Returns:
        根因统计列表（按频次降序），每条包含：
            - reason:      原因
            - frequency:   出现次数
            - total_days:  累计延误天数
            - avg_days:    平均延误天数
    """
    from collections import defaultdict

    stats: dict = defaultdict(lambda: {"frequency": 0, "total_days": 0})

    for d in delays:
        reason = d.get("reason", "未知原因")
        days = int(d.get("days", 0))
        stats[reason]["frequency"] += 1
        stats[reason]["total_days"] += days

    result = []
    for reason, s in stats.items():
        result.append({
            "reason": reason,
            "frequency": s["frequency"],
            "total_days": s["total_days"],
            "avg_days": round(s["total_days"] / s["frequency"], 1) if s["frequency"] else 0,
        })

    # 按频次降序，频次相同则按总延误天数降序
    result.sort(key=lambda x: (-x["frequency"], -x["total_days"]))
    return result


def recalculate_delivery_date(
    original_delivery: date,
    delay_days: int,
) -> date:
    """
    缺料或其他原因后重新计算交货日期（自然日简单顺延）。

    金凯博实际操作：直接按自然日顺延，不额外扣除节假日
    （节假日补班情况复杂，以自然日为基准更保守稳妥）。

    Args:
        original_delivery: 原始计划交期
        delay_days:        延误天数（>= 0）

    Returns:
        新的交货日期

    Raises:
        ValueError: delay_days < 0
    """
    from datetime import timedelta

    if delay_days < 0:
        raise ValueError("延误天数不能为负数")
    return original_delivery + timedelta(days=delay_days)


# ---------------------------------------------------------------------------
# 9. BOM 套件率计算 & 缺料预警（D6组：交付专项）
# ---------------------------------------------------------------------------

@dataclass
class ShortageAlert:
    """缺料预警数据类"""
    project_id: int
    missing_materials: List[str]          # 缺料物料名称列表
    severity: Literal["CRITICAL", "WARNING", "INFO"]  # 预警等级
    details: List[dict] = field(default_factory=list)  # 缺料明细


def calc_bom_kit_rate(bom_items: List[dict]) -> float:
    """
    按 BOM 清单计算综合套件率。

    算法：以「物料级」最小可满足套件数 / BOM 需求数量之比，
    取所有物料中最低的满足率作为综合套件率（木桶效应）。

    公式：kit_rate = min(available_i / required_i)  for all i

    Args:
        bom_items: BOM 物料列表，每项包含：
            - material: 物料名称
            - required: BOM 需求数量（int）
            - available: 实际可用数量（int）

    Returns:
        综合套件率（float，0~1）

    Raises:
        ValueError: bom_items 为空，或存在 required <= 0
    """
    if not bom_items:
        raise ValueError("BOM 物料列表不能为空")

    rates = []
    for item in bom_items:
        required = item.get("required", 0)
        available = item.get("available", 0)
        if required <= 0:
            raise ValueError(f"物料 '{item.get('material')}' 需求数量必须大于 0")
        # 不能超过1（超配也按满足100%计）
        rate = min(1.0, available / required)
        rates.append(rate)

    return min(rates)


def generate_shortage_alert(
    bom_items: List[dict],
    project_id: int,
) -> ShortageAlert | None:
    """
    根据 BOM 套件率生成缺料预警。

    预警规则：
      - 套件率 < 95%  → 生成预警
      - 存在 available == 0 的物料 → CRITICAL（关键物料缺货）
      - 其余情况          → WARNING（部分缺料）
      - 套件率 >= 95%  → 返回 None（无需预警）

    Args:
        bom_items:  BOM 物料列表
        project_id: 项目 ID

    Returns:
        ShortageAlert 对象，或 None（无缺料）
    """
    kit_rate = calc_bom_kit_rate(bom_items)

    # 套件率满足目标，不预警
    if kit_rate >= 0.95:
        return None

    missing_materials: List[str] = []
    has_zero_stock = False
    details: List[dict] = []

    for item in bom_items:
        required = item.get("required", 0)
        available = item.get("available", 0)
        material = item.get("material", "未知物料")
        if available < required:
            shortage_qty = required - available
            missing_materials.append(material)
            details.append({
                "material": material,
                "required": required,
                "available": available,
                "shortage": shortage_qty,
            })
            if available == 0:
                has_zero_stock = True

    severity: Literal["CRITICAL", "WARNING", "INFO"] = (
        "CRITICAL" if has_zero_stock else "WARNING"
    )

    return ShortageAlert(
        project_id=project_id,
        missing_materials=missing_materials,
        severity=severity,
        details=details,
    )
