# -*- coding: utf-8 -*-
"""
质量管理服务增强测试
目标：提升 quality_service.py 覆盖率到60%+
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid

from app.services.quality_service import QualityService
from app.schemas.production.quality import QualityInspectionCreate, DefectAnalysisCreate


class TestCreateInspection:
    """create_inspection 创建质检记录"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        return db

    @pytest.fixture
    def inspection_data(self):
        return QualityInspectionCreate(
            material_id=1,
            batch_no="BATCH001",
            inspection_type="INCOMING",
            inspection_date=datetime(2025, 2, 20),
            inspector_id=1,
            inspection_qty=100,
            qualified_qty=95,
            defect_qty=5,
            defect_type="划伤"
        )

    def test_creates_inspection_with_generated_no(self, mock_db, inspection_data):
        """验证创建质检记录并生成质检单号"""
        result = QualityService.create_inspection(mock_db, inspection_data, current_user_id=1)
        
        assert result.inspection_no.startswith("QI")
        assert result.defect_rate == Decimal("5.0")
        assert result.created_by == 1

    def test_calculates_defect_rate_correctly(self, mock_db, inspection_data):
        """验证不良率计算正确"""
        result = QualityService.create_inspection(mock_db, inspection_data, current_user_id=1)
        
        expected_rate = Decimal("5.0")  # 5/100 * 100
        assert result.defect_rate == expected_rate

    def test_zero_inspection_qty_results_zero_rate(self, mock_db):
        """验证检验数量为0时不良率为0"""
        data = QualityInspectionCreate(
            material_id=1,
            batch_no="BATCH001",
            inspection_type="INCOMING",
            inspection_date=datetime(2025, 2, 20),
            inspector_id=1,
            inspection_qty=0,
            qualified_qty=0,
            defect_qty=0
        )
        result = QualityService.create_inspection(mock_db, data, current_user_id=1)
        
        assert result.defect_rate == Decimal("0.0")

    def test_calls_check_quality_alerts(self, mock_db, inspection_data):
        """验证创建质检记录后触发预警检查"""
        with patch.object(QualityService, '_check_quality_alerts') as mock_check:
            result = QualityService.create_inspection(mock_db, inspection_data, current_user_id=1)
            mock_check.assert_called_once()


class TestGenerateInspectionNo:
    """_generate_inspection_no 生成质检单号"""

    def test_first_inspection_of_day(self):
        """第一条记录应为0001"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = QualityService._generate_inspection_no(db)
        
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"QI{today}0001"

    def test_increments_sequence_number(self):
        """后续记录应递增序号"""
        db = MagicMock()
        last_record = MagicMock()
        today = datetime.now().strftime("%Y%m%d")
        last_record.inspection_no = f"QI{today}0005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record
        
        result = QualityService._generate_inspection_no(db)
        
        assert result == f"QI{today}0006"

    def test_pads_sequence_with_zeros(self):
        """序号应补零到4位"""
        db = MagicMock()
        last_record = MagicMock()
        today = datetime.now().strftime("%Y%m%d")
        last_record.inspection_no = f"QI{today}0099"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record
        
        result = QualityService._generate_inspection_no(db)
        
        assert result == f"QI{today}0100"


class TestGetQualityTrend:
    """get_quality_trend 质量趋势分析"""

    def _make_inspection(self, date, inspection_qty, qualified_qty, defect_qty, material_id=1):
        i = MagicMock()
        i.inspection_date = date
        i.inspection_qty = inspection_qty
        i.qualified_qty = qualified_qty
        i.defect_qty = defect_qty
        i.material_id = material_id
        return i

    def test_returns_trend_data_and_statistics(self):
        """验证返回趋势数据和统计信息"""
        db = MagicMock()
        inspections = [
            self._make_inspection(datetime(2025, 1, 1), 100, 95, 5),
            self._make_inspection(datetime(2025, 1, 2), 200, 190, 10),
        ]
        db.query.return_value.filter.return_value.all.return_value = inspections
        
        result = QualityService.get_quality_trend(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31)
        )
        
        assert "trend_data" in result
        assert "avg_defect_rate" in result
        assert "total_inspections" in result
        assert result["total_qty"] == 300
        assert result["total_defects"] == 15

    def test_filters_by_material_id(self):
        """验证按物料ID筛选"""
        db = MagicMock()
        inspections = [self._make_inspection(datetime(2025, 1, 1), 100, 95, 5, material_id=1)]
        db.query.return_value.filter.return_value.all.return_value = inspections
        
        result = QualityService.get_quality_trend(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            material_id=1
        )
        
        assert result["total_inspections"] == 1

    def test_calculates_moving_average_prediction(self):
        """验证计算移动平均预测"""
        db = MagicMock()
        inspections = [
            self._make_inspection(datetime(2025, 1, 1), 100, 95, 5),
            self._make_inspection(datetime(2025, 1, 2), 100, 94, 6),
            self._make_inspection(datetime(2025, 1, 3), 100, 93, 7),
        ]
        db.query.return_value.filter.return_value.all.return_value = inspections
        
        result = QualityService.get_quality_trend(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31)
        )
        
        assert result["prediction"] is not None

    def test_handles_empty_data(self):
        """验证处理空数据"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        
        result = QualityService.get_quality_trend(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31)
        )
        
        assert result["total_inspections"] == 0
        assert result["avg_defect_rate"] == 0


class TestParetoAnalysis:
    """pareto_analysis 帕累托分析"""

    def test_identifies_top_defect_types(self):
        """验证识别主要不良类型"""
        db = MagicMock()
        
        stat1 = MagicMock()
        stat1.defect_type = "划伤"
        stat1.total_qty = 50
        
        stat2 = MagicMock()
        stat2.defect_type = "气泡"
        stat2.total_qty = 30
        
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            stat1, stat2
        ]
        
        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        
        assert result["total_defects"] == 80
        assert len(result["data_points"]) == 2

    def test_calculates_cumulative_rate(self):
        """验证计算累计占比"""
        db = MagicMock()
        
        stat1 = MagicMock()
        stat1.defect_type = "划伤"
        stat1.total_qty = 60
        
        stat2 = MagicMock()
        stat2.defect_type = "气泡"
        stat2.total_qty = 40
        
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            stat1, stat2
        ]
        
        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        
        assert result["data_points"][0].cumulative_rate == pytest.approx(60.0)
        assert result["data_points"][1].cumulative_rate == pytest.approx(100.0)

    def test_identifies_80_percent_types(self):
        """验证识别80%累计的不良类型"""
        db = MagicMock()
        
        stat1 = MagicMock()
        stat1.defect_type = "划伤"
        stat1.total_qty = 70
        
        stat2 = MagicMock()
        stat2.defect_type = "气泡"
        stat2.total_qty = 20
        
        stat3 = MagicMock()
        stat3.defect_type = "裂纹"
        stat3.total_qty = 10
        
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            stat1, stat2, stat3
        ]
        
        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        )
        
        # 划伤70%, cumulative <= 80%, so it's in top_80
        # 气泡 cumulative = 90% > 80%, so it's NOT in top_80
        assert "划伤" in result["top_80_percent_types"]
        assert len(result["top_80_percent_types"]) == 1

    def test_filters_by_material_id(self):
        """验证按物料ID筛选"""
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            material_id=1
        )
        
        assert result["total_defects"] == 0


class TestCreateDefectAnalysis:
    """create_defect_analysis 创建不良品分析"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        return db

    @pytest.fixture
    def analysis_data(self):
        return DefectAnalysisCreate(
            inspection_id=1,
            analyst_id=1,
            defect_type="划伤",
            defect_qty=5,
            corrective_action="更换模具"
        )

    def test_creates_analysis_with_generated_no(self, mock_db, analysis_data):
        """验证创建分析记录并生成分析单号"""
        result = QualityService.create_defect_analysis(mock_db, analysis_data, current_user_id=1)
        
        assert result.analysis_no.startswith("DA")
        assert result.created_by == 1

    def test_sets_analysis_date(self, mock_db, analysis_data):
        """验证设置分析日期"""
        result = QualityService.create_defect_analysis(mock_db, analysis_data, current_user_id=1)
        
        assert result.analysis_date is not None
        assert isinstance(result.analysis_date, datetime)


class TestGenerateAnalysisNo:
    """_generate_analysis_no 生成分析单号"""

    def test_first_analysis_of_day(self):
        """第一条记录应为0001"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = QualityService._generate_analysis_no(db)
        
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"DA{today}0001"

    def test_increments_sequence_number(self):
        """后续记录应递增序号"""
        db = MagicMock()
        last_record = MagicMock()
        today = datetime.now().strftime("%Y%m%d")
        last_record.analysis_no = f"DA{today}0010"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record
        
        result = QualityService._generate_analysis_no(db)
        
        assert result == f"DA{today}0011"


class TestCheckQualityAlerts:
    """_check_quality_alerts 检查质量预警"""

    def test_checks_enabled_rules(self):
        """验证只检查启用的规则"""
        db = MagicMock()
        
        rule1 = MagicMock()
        rule1.enabled = 1
        rule1.alert_type = "DEFECT_RATE"
        rule1.target_material_id = None
        
        db.query.return_value.filter.return_value.all.return_value = [rule1]
        
        inspection = MagicMock()
        inspection.material_id = 1
        inspection.defect_rate = Decimal("5.0")
        
        with patch.object(QualityService, '_check_defect_rate_alert') as mock_check:
            QualityService._check_quality_alerts(db, inspection)
            mock_check.assert_called_once()

    def test_skips_rule_with_different_material(self):
        """验证跳过不匹配物料的规则"""
        db = MagicMock()
        
        rule1 = MagicMock()
        rule1.enabled = 1
        rule1.alert_type = "DEFECT_RATE"
        rule1.target_material_id = 999
        
        db.query.return_value.filter.return_value.all.return_value = [rule1]
        
        inspection = MagicMock()
        inspection.material_id = 1
        
        with patch.object(QualityService, '_check_defect_rate_alert') as mock_check:
            QualityService._check_quality_alerts(db, inspection)
            mock_check.assert_not_called()

    def test_handles_spc_alert_types(self):
        """验证处理SPC预警类型"""
        db = MagicMock()
        
        rule1 = MagicMock()
        rule1.enabled = 1
        rule1.alert_type = "SPC_UCL"
        rule1.target_material_id = None
        
        db.query.return_value.filter.return_value.all.return_value = [rule1]
        
        inspection = MagicMock()
        inspection.material_id = 1
        
        with patch.object(QualityService, '_check_spc_alert') as mock_check:
            QualityService._check_quality_alerts(db, inspection)
            mock_check.assert_called_once()


class TestCheckDefectRateAlert:
    """_check_defect_rate_alert 检查不良率预警"""

    def test_insufficient_samples_no_alert(self):
        """样本不足时不触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 5
        rule.target_material_id = None
        rule.threshold_value = Decimal("10.0")
        rule.threshold_operator = "GT"
        rule.trigger_count = 0
        rule.last_triggered_at = None
        
        db.query.return_value.filter.return_value.all.return_value = []
        
        inspection = MagicMock()
        
        QualityService._check_defect_rate_alert(db, rule, inspection)
        
        # 应该不触发预警（trigger_count仍为0）
        assert rule.trigger_count == 0
        assert rule.last_triggered_at is None

    def test_triggers_on_gt_threshold(self):
        """大于阈值时触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 2
        rule.target_material_id = None
        rule.threshold_value = Decimal("5.0")
        rule.threshold_operator = "GT"
        rule.trigger_count = 0
        
        # 模拟两次检验，总不良率 = 15/100 = 15% > 5%
        insp1 = MagicMock()
        insp1.inspection_qty = 50
        insp1.defect_qty = 10
        
        insp2 = MagicMock()
        insp2.inspection_qty = 50
        insp2.defect_qty = 5
        
        db.query.return_value.filter.return_value.all.return_value = [insp1, insp2]
        
        inspection = MagicMock()
        
        QualityService._check_defect_rate_alert(db, rule, inspection)
        
        assert rule.trigger_count == 1
        assert rule.last_triggered_at is not None

    def test_no_trigger_when_below_threshold(self):
        """低于阈值时不触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 2
        rule.target_material_id = None
        rule.threshold_value = Decimal("20.0")
        rule.threshold_operator = "GT"
        rule.trigger_count = 0
        
        insp1 = MagicMock()
        insp1.inspection_qty = 100
        insp1.defect_qty = 5
        
        db.query.return_value.filter.return_value.all.return_value = [insp1]
        
        inspection = MagicMock()
        
        QualityService._check_defect_rate_alert(db, rule, inspection)
        
        assert rule.trigger_count == 0

    def test_supports_gte_operator(self):
        """支持大于等于操作符"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 1
        rule.target_material_id = None
        rule.threshold_value = Decimal("5.0")
        rule.threshold_operator = "GTE"
        rule.trigger_count = 0
        
        insp1 = MagicMock()
        insp1.inspection_qty = 100
        insp1.defect_qty = 5  # 正好5%
        
        db.query.return_value.filter.return_value.all.return_value = [insp1]
        
        inspection = MagicMock()
        
        QualityService._check_defect_rate_alert(db, rule, inspection)
        
        assert rule.trigger_count == 1


class TestCheckSPCAlert:
    """_check_spc_alert 检查SPC预警"""

    def test_no_alert_when_no_measured_value(self):
        """没有测量值时不触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        inspection = MagicMock()
        inspection.measured_value = None
        
        QualityService._check_spc_alert(db, rule, inspection)
        
        # 不应执行任何数据库查询
        db.query.assert_not_called()

    def test_insufficient_samples_no_alert(self):
        """样本不足时不触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 5
        rule.target_material_id = None
        rule.trigger_count = 0
        rule.last_triggered_at = None
        
        db.query.return_value.filter.return_value.all.return_value = []
        
        inspection = MagicMock()
        inspection.measured_value = Decimal("10.0")
        
        QualityService._check_spc_alert(db, rule, inspection)
        
        assert rule.trigger_count == 0
        assert rule.last_triggered_at is None

    def test_triggers_on_ucl_violation(self):
        """超出控制上限时触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 5
        rule.target_material_id = None
        rule.alert_type = "SPC_UCL"
        rule.trigger_count = 0
        
        # 模拟5个稳定值
        inspections = []
        for _ in range(5):
            insp = MagicMock()
            insp.measured_value = Decimal("10.0")
            inspections.append(insp)
        
        db.query.return_value.filter.return_value.all.return_value = inspections
        
        # 当前值远超UCL
        inspection = MagicMock()
        inspection.measured_value = Decimal("100.0")
        
        QualityService._check_spc_alert(db, rule, inspection)
        
        assert rule.trigger_count == 1

    def test_triggers_on_lcl_violation(self):
        """低于控制下限时触发预警"""
        db = MagicMock()
        
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.min_sample_size = 5
        rule.target_material_id = None
        rule.alert_type = "SPC_LCL"
        rule.trigger_count = 0
        
        inspections = []
        for _ in range(5):
            insp = MagicMock()
            insp.measured_value = Decimal("100.0")
            inspections.append(insp)
        
        db.query.return_value.filter.return_value.all.return_value = inspections
        
        # 当前值远低于LCL
        inspection = MagicMock()
        inspection.measured_value = Decimal("1.0")
        
        QualityService._check_spc_alert(db, rule, inspection)
        
        assert rule.trigger_count == 1


class TestCreateReworkOrder:
    """create_rework_order 创建返工单"""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        return db

    def test_creates_rework_order_with_generated_no(self, mock_db):
        """验证创建返工单并生成返工单号"""
        rework_data = {
            "original_work_order_id": 1,
            "quality_inspection_id": 1,
            "rework_qty": 10,
            "rework_reason": "质量不合格需要返工"
        }
        
        result = QualityService.create_rework_order(mock_db, rework_data, current_user_id=1)
        
        assert result.rework_order_no.startswith("RW")
        assert result.created_by == 1


class TestGenerateReworkOrderNo:
    """_generate_rework_order_no 生成返工单号"""

    def test_first_rework_order_of_day(self):
        """第一条记录应为0001"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = QualityService._generate_rework_order_no(db)
        
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"RW{today}0001"

    def test_increments_sequence_number(self):
        """后续记录应递增序号"""
        db = MagicMock()
        last_record = MagicMock()
        today = datetime.now().strftime("%Y%m%d")
        last_record.rework_order_no = f"RW{today}0020"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_record
        
        result = QualityService._generate_rework_order_no(db)
        
        assert result == f"RW{today}0021"


class TestCompleteReworkOrder:
    """complete_rework_order 完成返工单"""

    def test_completes_rework_order(self):
        """验证完成返工单"""
        db = MagicMock()
        
        rework_order = MagicMock()
        rework_order.id = 1
        rework_order.status = "IN_PROGRESS"
        
        db.query.return_value.filter.return_value.first.return_value = rework_order
        
        completion_data = {
            "completed_qty": 10,
            "qualified_qty": 9,
            "scrap_qty": 1,
            "actual_hours": 2.5,
            "rework_cost": 500.0,
            "completion_note": "返工完成"
        }
        
        result = QualityService.complete_rework_order(db, 1, completion_data)
        
        assert result.status == "COMPLETED"
        assert result.completed_qty == 10
        assert result.qualified_qty == 9
        assert result.scrap_qty == 1
        assert result.actual_end_time is not None

    def test_raises_when_order_not_found(self):
        """返工单不存在时抛出异常"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="返工单不存在"):
            QualityService.complete_rework_order(db, 999, {})

    def test_raises_when_already_completed(self):
        """返工单已完成时抛出异常"""
        db = MagicMock()
        
        rework_order = MagicMock()
        rework_order.status = "COMPLETED"
        
        db.query.return_value.filter.return_value.first.return_value = rework_order
        
        with pytest.raises(ValueError, match="返工单已完成"):
            QualityService.complete_rework_order(db, 1, {})


class TestGetQualityStatistics:
    """get_quality_statistics 获取质量统计"""

    def _make_inspection(self, date, inspection_qty, qualified_qty, defect_qty, defect_type=None):
        i = MagicMock()
        i.inspection_date = date
        i.inspection_qty = inspection_qty
        i.qualified_qty = qualified_qty
        i.defect_qty = defect_qty
        i.defect_type = defect_type
        i.id = 1
        return i

    def test_returns_statistics_dashboard_data(self):
        """验证返回统计看板数据"""
        db = MagicMock()
        
        inspections = [
            self._make_inspection(datetime.now() - timedelta(days=1), 100, 95, 5, "划伤"),
            self._make_inspection(datetime.now() - timedelta(days=2), 200, 190, 10, "气泡"),
        ]
        
        # Mock质检数据
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = inspections
        
        # Mock不良类型统计
        defect_stat = MagicMock()
        defect_stat.defect_type = "划伤"
        defect_stat.count = 5
        
        # Mock返工单统计
        mock_rework_query = MagicMock()
        mock_rework_query.filter.return_value.all.return_value = []
        mock_pending_query = MagicMock()
        mock_pending_query.filter.return_value.count.return_value = 0
        
        # 设置db.query的多次调用返回值
        db.query.side_effect = [
            mock_query,  # 第一次：查询质检记录
            mock_rework_query,  # 第二次：查询返工单
            mock_pending_query,  # 第三次：查询待处理返工单
            MagicMock(filter=lambda *a, **kw: MagicMock(
                group_by=lambda *a: MagicMock(
                    order_by=lambda *a: MagicMock(
                        limit=lambda *a: MagicMock(
                            all=lambda: [defect_stat]
                        )
                    )
                )
            )),  # 第四次：不良类型统计
            MagicMock(filter=lambda *a, **kw: MagicMock(all=lambda: inspections))  # 第五次：最近7天趋势
        ]
        
        result = QualityService.get_quality_statistics(db)
        
        assert "total_inspections" in result
        assert "overall_defect_rate" in result
        assert "pass_rate" in result
        assert "top_defect_types" in result
        assert "trend_last_7_days" in result

    def test_calculates_correct_metrics(self):
        """验证计算正确的指标"""
        db = MagicMock()
        
        inspections = [
            self._make_inspection(datetime.now() - timedelta(days=1), 100, 95, 5),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = inspections
        
        db.query.side_effect = [
            mock_query,
            MagicMock(filter=lambda *a, **kw: MagicMock(all=lambda: [])),
            MagicMock(filter=lambda *a, **kw: MagicMock(count=lambda: 0)),
            MagicMock(filter=lambda *a, **kw: MagicMock(
                group_by=lambda *a: MagicMock(
                    order_by=lambda *a: MagicMock(
                        limit=lambda *a: MagicMock(all=lambda: [])
                    )
                )
            )),
            MagicMock(filter=lambda *a, **kw: MagicMock(all=lambda: inspections))
        ]
        
        result = QualityService.get_quality_statistics(db)
        
        assert result["total_inspection_qty"] == 100
        assert result["total_qualified_qty"] == 95
        assert result["total_defect_qty"] == 5
        assert result["overall_defect_rate"] == pytest.approx(5.0)
        assert result["pass_rate"] == pytest.approx(95.0)


class TestBatchTracing:
    """batch_tracing 批次追溯"""

    def test_returns_batch_tracing_data(self):
        """验证返回批次追溯数据"""
        db = MagicMock()
        
        inspection = MagicMock()
        inspection.id = 1
        inspection.batch_no = "BATCH001"
        inspection.material_id = 1
        inspection.inspection_qty = 100
        inspection.defect_qty = 5
        
        db.query.return_value.filter.return_value.all.side_effect = [
            [inspection],  # 质检记录
            [],  # 不良品分析
            []   # 返工单
        ]
        
        result = QualityService.batch_tracing(db, "BATCH001")
        
        assert result["batch_no"] == "BATCH001"
        assert result["total_inspections"] == 1
        assert result["total_defects"] == 5
        assert result["batch_defect_rate"] == pytest.approx(5.0)

    def test_raises_when_batch_not_found(self):
        """批次不存在时抛出异常"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="未找到批次号"):
            QualityService.batch_tracing(db, "NONEXISTENT")

    def test_includes_related_analyses_and_rework(self):
        """验证包含相关的分析和返工数据"""
        db = MagicMock()
        
        inspection = MagicMock()
        inspection.id = 1
        inspection.batch_no = "BATCH001"
        inspection.material_id = 1
        inspection.inspection_qty = 100
        inspection.defect_qty = 5
        
        analysis = MagicMock()
        analysis.id = 1
        
        rework = MagicMock()
        rework.id = 1
        
        db.query.return_value.filter.return_value.all.side_effect = [
            [inspection],
            [analysis],
            [rework]
        ]
        
        result = QualityService.batch_tracing(db, "BATCH001")
        
        assert len(result["inspections"]) == 1
        assert len(result["defect_analyses"]) == 1
        assert len(result["rework_orders"]) == 1
