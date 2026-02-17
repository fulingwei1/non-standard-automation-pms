# -*- coding: utf-8 -*-
"""
金凯博自动化测试（深圳）— 行业特有场景单元测试

覆盖非标自动化测试行业的典型业务场景：
- ICT项目夹具成本超支预警
- EOL项目节拍不达标预警
- 视觉检测误判率超标处理
- FCT多版本兼容测试矩阵
- 项目延期概率预测
- 套件率（Kit Rate）计算

测试数据来自 tests/fixtures/industry_data.py
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from tests.fixtures.industry_data import (
    SAMPLE_PROJECTS,
    CUSTOMERS,
    SAMPLE_MATERIALS,
    SAMPLE_TIMESHEETS,
    SAMPLE_COSTS,
    KPI_BENCHMARKS,
    PROJECT_TYPES,
    make_mock_project,
    make_mock_db_with_projects,
)

# ─────────────────────────────────────────────────────────────────────────────
# 行业计算辅助函数（内嵌实现，不依赖 app 层，可纯逻辑测试）
# ─────────────────────────────────────────────────────────────────────────────


def check_outsourcing_cost_overrun(budgeted: float, actual: float, threshold: float = 0.10) -> dict:
    """
    外协加工成本超支预警检查
    :param budgeted: 预算金额
    :param actual:   实际金额
    :param threshold: 触发预警的超支比例（默认10%）
    :return: {"overrun": bool, "ratio": float, "amount": float, "level": str}
    """
    if budgeted <= 0:
        return {"overrun": False, "ratio": 0.0, "amount": 0.0, "level": "NORMAL"}
    ratio = (actual - budgeted) / budgeted
    overrun = ratio > threshold
    if not overrun:
        level = "NORMAL"
    elif ratio <= 0.20:
        level = "WARNING"
    elif ratio <= 0.50:
        level = "ALERT"
    else:
        level = "CRITICAL"
    return {
        "overrun": overrun,
        "ratio": ratio,
        "amount": actual - budgeted,
        "level": level,
    }


def check_eol_takt_time(actual_seconds: float, target_seconds: float, tolerance: float = 0.10) -> dict:
    """
    EOL节拍不达标检查
    :param actual_seconds:  实测节拍（秒/件）
    :param target_seconds:  目标节拍
    :param tolerance:       允许超出比例（默认10%）
    :return: {"pass": bool, "ratio": float, "gap_seconds": float}
    """
    ratio = actual_seconds / target_seconds if target_seconds > 0 else 0
    passed = ratio <= (1 + tolerance)
    return {
        "pass": passed,
        "ratio": ratio,
        "gap_seconds": actual_seconds - target_seconds,
        "threshold": target_seconds * (1 + tolerance),
    }


def check_vision_false_positive_rate(
    total_inspected: int, false_positives: int, limit: float = 0.002
) -> dict:
    """
    视觉检测误判率检查（视觉系统行业标准：误判率 < 0.2%）
    :param total_inspected:  总检测件数
    :param false_positives:  误判件数
    :param limit:            误判率上限（默认0.2%）
    """
    if total_inspected == 0:
        return {"compliant": True, "rate": 0.0, "exceeded_by": 0.0}
    rate = false_positives / total_inspected
    compliant = rate <= limit
    return {
        "compliant": compliant,
        "rate": rate,
        "exceeded_by": max(0.0, rate - limit),
        "limit": limit,
    }


def validate_fct_version_matrix(supported_versions: list, required_versions: list) -> dict:
    """
    FCT多版本兼容性矩阵验证
    :param supported_versions: 测试台已支持的版本列表
    :param required_versions:  客户要求兼容的版本列表
    :return: {"compatible": bool, "missing": list, "coverage": float}
    """
    supported_set = set(supported_versions)
    required_set = set(required_versions)
    missing = list(required_set - supported_set)
    coverage = len(required_set - set(missing)) / len(required_set) if required_set else 1.0
    return {
        "compatible": len(missing) == 0,
        "missing": sorted(missing),
        "coverage": coverage,
        "supported_count": len(supported_set & required_set),
        "total_required": len(required_set),
    }


def predict_delay_probability(
    progress_percent: float,
    elapsed_days: int,
    total_planned_days: int,
    risk_factors: list = None,
) -> dict:
    """
    项目延期概率预测（基于进度偏差 + 风险因子）
    - 进度偏差率 SPI < 0.8 时延期风险高
    - 每个高风险因子增加 10% 概率
    """
    expected_progress = elapsed_days / total_planned_days if total_planned_days > 0 else 1.0
    spi = progress_percent / expected_progress if expected_progress > 0 else 1.0  # 进度绩效指数

    # 基础概率：SPI < 1 时有延期风险
    if spi >= 1.0:
        base_prob = 0.05
    elif spi >= 0.9:
        base_prob = 0.15
    elif spi >= 0.8:
        base_prob = 0.35
    elif spi >= 0.7:
        base_prob = 0.60
    else:
        base_prob = 0.85

    # 叠加风险因子（每个高风险项 +10%）
    risk_bonus = len(risk_factors or []) * 0.10
    probability = min(1.0, base_prob + risk_bonus)

    return {
        "delay_probability": probability,
        "spi": round(spi, 3),
        "base_probability": base_prob,
        "risk_bonus": risk_bonus,
        "risk_level": "HIGH" if probability >= 0.60 else ("MEDIUM" if probability >= 0.30 else "LOW"),
    }


def calculate_kit_rate(
    project_bom_items: list,
    received_items: list,
) -> dict:
    """
    套件率计算（Kit Rate）
    = 已到货且数量满足BOM需求的物料数 / BOM总物料数
    :param project_bom_items: [{"material_code": str, "required_qty": int}, ...]
    :param received_items:    [{"material_code": str, "received_qty": int}, ...]
    """
    if not project_bom_items:
        return {"kit_rate": 1.0, "complete_items": 0, "total_items": 0, "shortage_items": []}

    received_map = {item["material_code"]: item["received_qty"] for item in received_items}
    shortage_items = []
    complete_count = 0

    for bom_item in project_bom_items:
        code = bom_item["material_code"]
        required = bom_item["required_qty"]
        received = received_map.get(code, 0)
        if received >= required:
            complete_count += 1
        else:
            shortage_items.append({
                "material_code": code,
                "required": required,
                "received": received,
                "shortage": required - received,
            })

    total = len(project_bom_items)
    kit_rate = complete_count / total

    return {
        "kit_rate": round(kit_rate, 4),
        "complete_items": complete_count,
        "total_items": total,
        "shortage_items": shortage_items,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 1：ICT 夹具外协成本超支预警
# ─────────────────────────────────────────────────────────────────────────────

class TestICTFixtureCostOverrun:
    """ICT 项目夹具外协加工成本超支预警测试"""

    def test_outsourcing_cost_normal_no_alert(self):
        """外协成本未超预算：不触发预警"""
        # PJ250901001：外协预算25000，实际22000（未超）
        result = check_outsourcing_cost_overrun(budgeted=25000, actual=22000)
        assert result["overrun"] is False
        assert result["level"] == "NORMAL"
        assert result["ratio"] < 0.10

    def test_outsourcing_cost_exactly_10_percent_triggers_alert(self):
        """外协超支恰好10.1%时触发预警（边界值测试）"""
        # 预算25000，实际27525（超10.1%）
        result = check_outsourcing_cost_overrun(budgeted=25000, actual=27525)
        assert result["overrun"] is True
        assert result["level"] == "WARNING"
        assert result["amount"] == 2525.0

    def test_ict_project_fixture_overrun_from_sample_data(self):
        """使用真实样例数据验证：ICT外协超12%触发预警"""
        # SAMPLE_COSTS中：外协预算25000，实际28000，超12%
        cost = SAMPLE_COSTS[2]  # 外协加工成本记录
        assert cost["category"] == "外协加工"
        result = check_outsourcing_cost_overrun(
            budgeted=cost["budgeted"], actual=cost["actual"]
        )
        assert result["overrun"] is True
        assert abs(result["ratio"] - 0.12) < 0.001, f"Expected ~12% overrun, got {result['ratio']:.1%}"
        assert result["level"] == "WARNING"
        assert result["amount"] == 3000.0  # 超出3000元

    def test_outsourcing_severe_overrun_is_alert_level(self):
        """外协超支30%时升级为ALERT级别"""
        result = check_outsourcing_cost_overrun(budgeted=25000, actual=32500)  # +30%
        assert result["overrun"] is True
        assert result["level"] == "ALERT"
        assert result["ratio"] == pytest.approx(0.30, abs=0.001)

    def test_outsourcing_critical_overrun_exceeds_50_percent(self):
        """外协超支50%以上升级为CRITICAL"""
        result = check_outsourcing_cost_overrun(budgeted=25000, actual=40000)  # +60%
        assert result["overrun"] is True
        assert result["level"] == "CRITICAL"

    def test_zero_budget_does_not_crash(self):
        """预算为零时不应崩溃"""
        result = check_outsourcing_cost_overrun(budgeted=0, actual=5000)
        assert result["overrun"] is False  # 无法判断，返回正常


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 2：EOL 节拍不达标预警
# ─────────────────────────────────────────────────────────────────────────────

class TestEOLTaktTimeAlert:
    """EOL 终线测试节拍不达标预警测试"""

    def test_eol_takt_time_within_target_passes(self):
        """节拍符合要求：测试节拍 = 43s，目标45s，通过"""
        result = check_eol_takt_time(actual_seconds=43.0, target_seconds=45.0)
        assert result["pass"] is True
        assert result["ratio"] < 1.0
        assert result["gap_seconds"] < 0

    def test_eol_takt_time_exactly_at_target_passes(self):
        """节拍恰好等于目标（45s）：通过"""
        # SAMPLE_PROJECTS[2]：德赛西威EOL，节拍45秒/件
        result = check_eol_takt_time(actual_seconds=45.0, target_seconds=45.0)
        assert result["pass"] is True
        assert result["ratio"] == pytest.approx(1.0)

    def test_eol_takt_time_110_percent_threshold_fails(self):
        """节拍超出目标10%触发预警：实测49.5s vs 目标45s（超10%）"""
        result = check_eol_takt_time(actual_seconds=49.5, target_seconds=45.0)
        assert result["pass"] is False
        assert result["ratio"] == pytest.approx(1.10, abs=0.001)
        assert result["gap_seconds"] == pytest.approx(4.5)

    def test_eol_takt_time_slightly_over_limit_fails(self):
        """节拍超出10.1%，触发预警"""
        result = check_eol_takt_time(actual_seconds=49.6, target_seconds=45.0)
        assert result["pass"] is False
        # 预警阈值 = 45 * 1.1 = 49.5
        assert result["threshold"] == pytest.approx(49.5)

    def test_eol_takt_time_actual_from_desai_project(self):
        """德赛西威EOL项目实测场景：目标45s，实测52s（超15.6%）必须报警"""
        target = 45.0  # 来自 SAMPLE_PROJECTS[2].description
        actual = 52.0  # 联调阶段实测值
        result = check_eol_takt_time(actual_seconds=actual, target_seconds=target)
        assert result["pass"] is False
        assert result["ratio"] == pytest.approx(52.0 / 45.0, abs=0.001)
        assert result["gap_seconds"] == pytest.approx(7.0)

    def test_eol_4_station_aggregate_takt_check(self):
        """4工位总节拍验证：各工位节拍均满足45s/件"""
        station_takt_times = [42.0, 44.0, 43.5, 41.0]  # 4个工位的实测节拍
        target = 45.0
        results = [check_eol_takt_time(t, target) for t in station_takt_times]
        # 所有工位均应通过
        assert all(r["pass"] for r in results), "All stations should pass takt time check"
        bottleneck = max(station_takt_times)
        assert bottleneck <= target * 1.1, "Bottleneck station must be within 10% of target"


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 3：视觉检测误判率
# ─────────────────────────────────────────────────────────────────────────────

class TestVisionInspectionFalsePositiveRate:
    """视觉检测系统误判率超标处理测试"""

    def test_vision_false_positive_within_limit(self):
        """误判率0.15%（<0.2%上限）：合规"""
        # 蓝思科技摄像头模组：检测10000件，误判15件
        result = check_vision_false_positive_rate(
            total_inspected=10000, false_positives=15
        )
        assert result["compliant"] is True
        assert result["rate"] == pytest.approx(0.0015)
        assert result["exceeded_by"] == pytest.approx(0.0)

    def test_vision_false_positive_exactly_at_limit(self):
        """误判率恰好等于0.2%上限：合规（边界）"""
        result = check_vision_false_positive_rate(
            total_inspected=10000, false_positives=20
        )
        assert result["compliant"] is True
        assert result["rate"] == pytest.approx(0.002)

    def test_vision_false_positive_exceeds_limit(self):
        """误判率0.25%超上限：不合规，需停机调整"""
        # 实际场景：调试初期光源未调好，误判率偏高
        result = check_vision_false_positive_rate(
            total_inspected=10000, false_positives=25
        )
        assert result["compliant"] is False
        assert result["exceeded_by"] == pytest.approx(0.0005)  # 超出0.05%

    def test_vision_project_lansi_actual_scenario(self):
        """蓝思科技实际场景：手机摄像头模组检测，每班8000件，误判22件"""
        result = check_vision_false_positive_rate(
            total_inspected=8000, false_positives=22, limit=0.002
        )
        rate = 22 / 8000
        assert result["compliant"] is (rate <= 0.002)
        assert result["rate"] == pytest.approx(rate, abs=1e-6)

    def test_vision_zero_false_positive_is_compliant(self):
        """误判率为0：完全合规"""
        result = check_vision_false_positive_rate(total_inspected=5000, false_positives=0)
        assert result["compliant"] is True
        assert result["rate"] == 0.0

    def test_vision_empty_batch_does_not_crash(self):
        """空批次（0件）：不崩溃，返回合规"""
        result = check_vision_false_positive_rate(total_inspected=0, false_positives=0)
        assert result["compliant"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 4：FCT 多版本兼容测试矩阵
# ─────────────────────────────────────────────────────────────────────────────

class TestFCTVersionCompatibilityMatrix:
    """FCT 功能测试台多版本兼容性验证"""

    def test_fct_full_version_coverage(self):
        """立讯AirPods场景：支持所有要求版本，矩阵通过"""
        # AirPods Pro主板版本：P3.0 / P3.1 / P3.2
        supported = ["P3.0", "P3.1", "P3.2", "P3.3"]
        required = ["P3.0", "P3.1", "P3.2"]
        result = validate_fct_version_matrix(supported, required)
        assert result["compatible"] is True
        assert result["missing"] == []
        assert result["coverage"] == pytest.approx(1.0)

    def test_fct_missing_one_version_fails(self):
        """缺少一个版本时矩阵不通过"""
        supported = ["P3.0", "P3.1"]
        required = ["P3.0", "P3.1", "P3.2"]
        result = validate_fct_version_matrix(supported, required)
        assert result["compatible"] is False
        assert "P3.2" in result["missing"]
        assert result["coverage"] == pytest.approx(2 / 3, abs=0.001)

    def test_fct_multiple_versions_missing(self):
        """FCT台缺失多个版本：需要返工升级"""
        supported = ["V1.0"]
        required = ["V1.0", "V2.0", "V3.0", "V4.0"]
        result = validate_fct_version_matrix(supported, required)
        assert result["compatible"] is False
        assert len(result["missing"]) == 3
        assert result["coverage"] == pytest.approx(0.25)

    def test_fct_byd_adas_version_matrix(self):
        """比亚迪ADAS域控制器ICT兼容8个版本：覆盖率100%"""
        # 来自 SAMPLE_PROJECTS[0]："兼容8个测试点版本"
        supported_versions = [f"HW_V{i}.0" for i in range(1, 9)]   # HW_V1.0 ~ HW_V8.0
        required_versions = [f"HW_V{i}.0" for i in range(1, 9)]
        result = validate_fct_version_matrix(supported_versions, required_versions)
        assert result["compatible"] is True
        assert result["supported_count"] == 8
        assert result["total_required"] == 8

    def test_fct_version_matrix_missing_list_sorted(self):
        """缺失版本列表应按字典序排列，便于工程师确认"""
        supported = ["V1.0", "V3.0"]
        required = ["V1.0", "V2.0", "V3.0", "V4.0"]
        result = validate_fct_version_matrix(supported, required)
        assert result["missing"] == ["V2.0", "V4.0"]  # 已排序


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 5：项目延期概率预测
# ─────────────────────────────────────────────────────────────────────────────

class TestProjectDelayProbabilityPrediction:
    """基于历史数据的项目延期概率预测"""

    def test_on_track_project_low_delay_probability(self):
        """进度正常（SPI≥1.0）：延期概率<10%"""
        # 项目进行到50%时，计划完成50%，实际完成55%
        result = predict_delay_probability(
            progress_percent=0.55,
            elapsed_days=45,
            total_planned_days=90,
        )
        assert result["delay_probability"] < 0.10
        assert result["risk_level"] == "LOW"
        assert result["spi"] >= 1.0

    def test_slightly_behind_project_medium_risk(self):
        """进度稍落后（SPI≈0.88）：中等延期风险"""
        result = predict_delay_probability(
            progress_percent=0.44,  # 应完成50%，实际44%
            elapsed_days=45,
            total_planned_days=90,
        )
        assert 0.15 <= result["delay_probability"] < 0.60
        assert result["risk_level"] in ("LOW", "MEDIUM")

    def test_vision_project_delayed_high_risk(self):
        """蓝思视觉项目（DELAYED状态）：进度落后+多风险因子→高概率"""
        # SAMPLE_PROJECTS[3]：视觉项目，状态DELAYED，当前S6
        # 已用90天（90/92 ≈ 97.8%），实际进度60%
        result = predict_delay_probability(
            progress_percent=0.60,
            elapsed_days=90,
            total_planned_days=92,  # 2025-11-01 到 2026-01-31
            risk_factors=["光源方案验证", "算法误判率调优"],
        )
        assert result["delay_probability"] >= 0.60
        assert result["risk_level"] == "HIGH"

    def test_risk_factors_increase_probability(self):
        """高风险因子应增加延期概率"""
        base = predict_delay_probability(0.50, 45, 90)
        with_risk = predict_delay_probability(0.50, 45, 90, risk_factors=["物料延期", "方案变更"])
        assert with_risk["delay_probability"] > base["delay_probability"]

    def test_spi_calculation_accuracy(self):
        """验证 SPI（进度绩效指数）计算正确性"""
        # 计划30天完成30%，实际完成24% → SPI = 0.8
        result = predict_delay_probability(0.24, 30, 100)
        # expected_progress = 30/100 = 0.30, SPI = 0.24/0.30 = 0.80
        assert result["spi"] == pytest.approx(0.800, abs=0.001)

    def test_probability_capped_at_100_percent(self):
        """延期概率上限为100%，不应超过"""
        result = predict_delay_probability(
            progress_percent=0.10,
            elapsed_days=85,
            total_planned_days=90,
            risk_factors=["f1", "f2", "f3", "f4", "f5"],
        )
        assert result["delay_probability"] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 6：套件率（Kit Rate）计算
# ─────────────────────────────────────────────────────────────────────────────

class TestKitRateCalculation:
    """套件率精确度测试"""

    def test_all_materials_received_kit_rate_100_percent(self):
        """所有物料到齐：套件率=100%"""
        bom = [
            {"material_code": "MAT-NI-001", "required_qty": 1},
            {"material_code": "MAT-NI-002", "required_qty": 4},
            {"material_code": "MAT-KK-001", "required_qty": 10},
        ]
        received = [
            {"material_code": "MAT-NI-001", "received_qty": 1},
            {"material_code": "MAT-NI-002", "received_qty": 4},
            {"material_code": "MAT-KK-001", "received_qty": 12},  # 超量也算到齐
        ]
        result = calculate_kit_rate(bom, received)
        assert result["kit_rate"] == 1.0
        assert result["complete_items"] == 3
        assert result["shortage_items"] == []

    def test_partial_materials_kit_rate_calculation(self):
        """部分物料缺货：套件率精确计算"""
        bom = [
            {"material_code": "MAT-NI-001", "required_qty": 1},
            {"material_code": "MAT-NI-002", "required_qty": 4},
            {"material_code": "MAT-KK-002", "required_qty": 2},  # 缺货
            {"material_code": "MAT-KK-003", "required_qty": 3},  # 缺货
        ]
        received = [
            {"material_code": "MAT-NI-001", "received_qty": 1},
            {"material_code": "MAT-NI-002", "received_qty": 4},
            # MAT-KK-002 和 MAT-KK-003 未到货
        ]
        result = calculate_kit_rate(bom, received)
        assert result["kit_rate"] == pytest.approx(0.5)  # 2/4 = 50%
        assert result["complete_items"] == 2
        assert len(result["shortage_items"]) == 2

    def test_ict_project_kit_rate_from_sample_materials(self):
        """ICT项目真实BOM物料套件率验证（使用 SAMPLE_MATERIALS 数据）"""
        # 比亚迪ADAS ICT系统典型BOM
        bom = [
            {"material_code": "MAT-NI-001", "required_qty": 1},   # NI PXI机箱
            {"material_code": "MAT-NI-002", "required_qty": 6},   # 数字IO板卡
            {"material_code": "MAT-KK-001", "required_qty": 20},  # 气缸
            {"material_code": "MAT-KK-005", "required_qty": 2},   # 伺服驱动器
        ]
        received = [
            {"material_code": "MAT-NI-001", "received_qty": 1},   # 到货
            {"material_code": "MAT-NI-002", "received_qty": 6},   # 到货
            {"material_code": "MAT-KK-001", "received_qty": 20},  # 到货
            # MAT-KK-005 交货期长，未到
        ]
        result = calculate_kit_rate(bom, received)
        assert result["kit_rate"] == pytest.approx(0.75)  # 3/4
        assert result["complete_items"] == 3
        shortage = result["shortage_items"]
        assert len(shortage) == 1
        assert shortage[0]["material_code"] == "MAT-KK-005"

    def test_kit_rate_below_target_triggers_alert(self):
        """套件率低于95%目标：应触发采购预警"""
        bom = [{"material_code": f"M{i:03d}", "required_qty": 1} for i in range(20)]
        received = [{"material_code": f"M{i:03d}", "received_qty": 1} for i in range(18)]  # 18/20
        result = calculate_kit_rate(bom, received)
        assert result["kit_rate"] == pytest.approx(0.90)
        # 低于KPI目标值0.95，应标记需要关注
        assert result["kit_rate"] < KPI_BENCHMARKS["kit_rate_target"]

    def test_kit_rate_shortage_amount_accuracy(self):
        """验证缺货数量计算精度"""
        bom = [{"material_code": "MAT-KK-001", "required_qty": 20}]
        received = [{"material_code": "MAT-KK-001", "received_qty": 14}]
        result = calculate_kit_rate(bom, received)
        assert result["kit_rate"] == pytest.approx(0.0)  # 未达到需求量
        shortage = result["shortage_items"][0]
        assert shortage["shortage"] == 6  # 差6个气缸
        assert shortage["received"] == 14

    def test_empty_bom_returns_full_kit_rate(self):
        """空BOM：套件率视为100%（无需物料）"""
        result = calculate_kit_rate([], [])
        assert result["kit_rate"] == 1.0
        assert result["total_items"] == 0
