# -*- coding: utf-8 -*-
"""
质量服务扩展测试 - 补充更多测试用例
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def _make_db():
    return MagicMock()


def _make_inspection(**kw):
    insp = MagicMock()
    defaults = dict(
        id=1,
        inspection_no="QI202401010001",
        inspection_date=datetime(2024, 1, 15),
        inspection_qty=100,
        qualified_qty=95,
        defect_qty=5,
        defect_rate=Decimal("5.0"),
        defect_type="尺寸偏差",
        batch_no="BATCH-001",
        material_id=10,
        inspection_type="进货检验",
        measured_value=Decimal("10.5"),
        spec_upper_limit=Decimal("11.0"),
        spec_lower_limit=Decimal("10.0"),
        status="PASS",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(insp, k, v)
    return insp


class TestCreateInspection:
    """测试创建质检记录"""

    def test_create_inspection_with_calculation(self):
        """测试创建质检记录并计算不良率"""
        from app.services.quality_service import QualityService
        from app.schemas.production.quality import QualityInspectionCreate

        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        inspection_data = QualityInspectionCreate(
            inspection_date=datetime(2024, 1, 15),
            inspection_qty=200,
            qualified_qty=190,
            defect_qty=10,
            batch_no="BATCH-002",
            material_id=20,
            inspection_type="过程检验",
        )

        result = QualityService.create_inspection(
            db, inspection_data, current_user_id=1
        )

        assert result is not None
        assert result.inspection_no is not None
        assert result.defect_rate == Decimal("5.0")  # 10/200 * 100 = 5%
        db.add.assert_called()
        db.commit.assert_called()

    def test_create_inspection_zero_qty(self):
        """测试检验数量为0时的不良率计算"""
        from app.services.quality_service import QualityService
        from app.schemas.production.quality import QualityInspectionCreate

        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        inspection_data = QualityInspectionCreate(
            inspection_date=datetime(2024, 1, 15),
            inspection_qty=0,
            qualified_qty=0,
            defect_qty=0,
            batch_no="BATCH-003",
            material_id=20,
            inspection_type="过程检验",
        )

        result = QualityService.create_inspection(
            db, inspection_data, current_user_id=1
        )

        assert result.defect_rate == Decimal("0")


class TestGenerateInspectionNo:
    """测试生成质检单号"""

    def test_first_inspection_no(self):
        """测试首个质检单号"""
        from app.services.quality_service import QualityService

        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = QualityService._generate_inspection_no(db)

        today = datetime.now().strftime("%Y%m%d")
        assert result == f"QI{today}0001"

    def test_increment_inspection_no(self):
        """测试递增质检单号"""
        from app.services.quality_service import QualityService

        db = _make_db()
        today = datetime.now().strftime("%Y%m%d")
        last_record = MagicMock()
        last_record.inspection_no = f"QI{today}0005"

        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record

        result = QualityService._generate_inspection_no(db)

        assert result == f"QI{today}0006"


class TestParetoAnalysis:
    """测试帕累托分析"""

    def test_pareto_analysis_with_data(self):
        """测试有数据的帕累托分析"""
        from app.services.quality_service import QualityService

        db = _make_db()

        # 模拟不良类型统计数据
        stat1 = MagicMock()
        stat1.defect_type = "尺寸偏差"
        stat1.total_qty = 50

        stat2 = MagicMock()
        stat2.defect_type = "外观缺陷"
        stat2.total_qty = 30

        stat3 = MagicMock()
        stat3.defect_type = "功能异常"
        stat3.total_qty = 20

        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            stat1, stat2, stat3
        ]

        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)

        result = QualityService.pareto_analysis(db, start, end)

        assert "data_points" in result
        assert result["total_defects"] == 100
        assert len(result["data_points"]) == 3

    def test_pareto_analysis_empty_data(self):
        """测试无数据的帕累托分析"""
        from app.services.quality_service import QualityService

        db = _make_db()
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)

        result = QualityService.pareto_analysis(db, start, end)

        assert result["total_defects"] == 0
        assert len(result["data_points"]) == 0
        assert len(result["top_80_percent_types"]) == 0


class TestQualityTrendWithFilters:
    """测试质量趋势分析（带过滤条件）"""

    def test_trend_with_material_filter(self):
        """测试按物料过滤的质量趋势"""
        from app.services.quality_service import QualityService

        db = _make_db()
        insp = _make_inspection(inspection_qty=100, defect_qty=5)
        db.query.return_value.filter.return_value.all.return_value = [insp]

        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)

        result = QualityService.get_quality_trend(
            db, start, end, material_id=10
        )

        assert result["total_inspections"] == 1

    def test_trend_with_inspection_type_filter(self):
        """测试按检验类型过滤的质量趋势"""
        from app.services.quality_service import QualityService

        db = _make_db()
        insp = _make_inspection(
            inspection_qty=100, defect_qty=5, inspection_type="进货检验"
        )
        db.query.return_value.filter.return_value.all.return_value = [insp]

        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)

        result = QualityService.get_quality_trend(
            db, start, end, inspection_type="进货检验"
        )

        assert result["total_inspections"] == 1


class TestMovingAveragePrediction:
    """测试移动平均预测"""

    def test_calculate_moving_average(self):
        """测试移动平均计算"""
        from app.services.quality_service import QualityService

        data = [5.0, 6.0, 7.0, 8.0, 9.0]
        result = QualityService._calculate_moving_average(data, window=3)

        # 移动平均: [5,6,7]->6, [6,7,8]->7, [7,8,9]->8
        assert len(result) == 3
        assert result[0] == pytest.approx(6.0)
        assert result[1] == pytest.approx(7.0)
        assert result[2] == pytest.approx(8.0)

    def test_moving_average_insufficient_data(self):
        """测试数据不足时的移动平均"""
        from app.services.quality_service import QualityService

        data = [5.0]
        result = QualityService._calculate_moving_average(data, window=3)

        assert len(result) == 0


class TestAggregateByTimeExtended:
    """测试时间聚合（扩展）"""

    def test_aggregate_by_week(self):
        """测试按周聚合"""
        from app.services.quality_service import QualityService

        insp1 = _make_inspection(
            inspection_date=datetime(2024, 1, 8),
            inspection_qty=100,
            qualified_qty=95,
            defect_qty=5,
        )
        insp2 = _make_inspection(
            inspection_date=datetime(2024, 1, 15),
            inspection_qty=80,
            qualified_qty=76,
            defect_qty=4,
        )

        result = QualityService._aggregate_by_time([insp1, insp2], "week")

        # 不同周应该分开
        assert len(result) == 2

    def test_aggregate_empty_list(self):
        """测试空列表聚合"""
        from app.services.quality_service import QualityService

        result = QualityService._aggregate_by_time([], "day")

        assert len(result) == 0


class TestDefectAnalysis:
    """测试不良品分析"""

    def test_create_defect_analysis(self):
        """测试创建不良品分析"""
        from app.services.quality_service import QualityService
        from app.schemas.production.quality import DefectAnalysisCreate

        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        analysis_data = DefectAnalysisCreate(
            inspection_id=1,
            defect_type="尺寸偏差",
            root_cause="设备精度不足",
            corrective_action="调整设备参数",
            preventive_action="定期维护",
        )

        result = QualityService.create_defect_analysis(
            db, analysis_data, current_user_id=1
        )

        assert result is not None
        assert result.analysis_no is not None
        db.add.assert_called()
        db.commit.assert_called()


class TestGenerateAnalysisNo:
    """测试生成分析单号"""

    def test_first_analysis_no(self):
        """测试首个分析单号"""
        from app.services.quality_service import QualityService

        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = QualityService._generate_analysis_no(db)

        today = datetime.now().strftime("%Y%m%d")
        assert result == f"DA{today}0001"

    def test_increment_analysis_no(self):
        """测试递增分析单号"""
        from app.services.quality_service import QualityService

        db = _make_db()
        today = datetime.now().strftime("%Y%m%d")
        last_record = MagicMock()
        last_record.analysis_no = f"DA{today}0003"

        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record

        result = QualityService._generate_analysis_no(db)

        assert result == f"DA{today}0004"


class TestQualityAlert:
    """测试质量预警"""

    def test_check_quality_alerts_no_rules(self):
        """测试无预警规则时不触发"""
        from app.services.quality_service import QualityService

        db = _make_db()
        inspection = _make_inspection()

        # 模拟无启用规则
        db.query.return_value.filter.return_value.all.return_value = []

        # 不应抛出异常
        QualityService._check_quality_alerts(db, inspection)

    def test_check_quality_alerts_with_rule(self):
        """测试有预警规则时触发检查"""
        from app.services.quality_service import QualityService

        db = _make_db()
        inspection = _make_inspection(
            inspection_qty=100, defect_qty=15  # 15% 不良率
        )

        # 模拟有启用的预警规则
        rule = MagicMock()
        rule.id = 1
        rule.alert_type = "DEFECT_RATE"
        rule.enabled = 1
        rule.target_material_id = None
        rule.threshold_value = "10"
        rule.threshold_operator = "GT"
        rule.time_window_hours = 24
        rule.min_sample_size = 1
        rule.last_triggered_at = None
        rule.trigger_count = 0

        db.query.return_value.filter.return_value.all.return_value = [rule]

        with patch.object(
            QualityService, "_check_defect_rate_alert"
        ) as mock_check:
            QualityService._check_quality_alerts(db, inspection)
            mock_check.assert_called_once()


class TestSPCDataPoint:
    """测试SPC数据点"""

    def test_spc_data_point_creation(self):
        """测试SPC数据点创建"""
        from app.schemas.production.quality import SPCDataPoint

        point = SPCDataPoint(
            date=datetime(2024, 1, 15),
            measured_value=10.5,
            ucl=11.0,
            cl=10.5,
            lcl=10.0,
            is_out_of_control=False,
        )

        assert point.measured_value == 10.5
        assert point.is_out_of_control is False


class TestSPCControlLimits:
    """测试SPC控制限"""

    def test_spc_control_limits_exact_5_samples(self):
        """测试刚好5个样本的SPC计算"""
        from app.services.quality_service import QualityService

        db = _make_db()
        # 返回5个样本（刚好够）
        inspections = [
            _make_inspection(measured_value=Decimal(str(v)))
            for v in [10.0, 10.1, 10.2, 10.3, 10.4]
        ]
        db.query.return_value.filter.return_value.all.return_value = inspections

        result = QualityService.calculate_spc_control_limits(
            db=db,
            material_id=10,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

        assert "control_limits" in result
        assert "data_points" in result
        assert result["control_limits"].ucl > result["control_limits"].cl
        assert result["control_limits"].cl > result["control_limits"].lcl