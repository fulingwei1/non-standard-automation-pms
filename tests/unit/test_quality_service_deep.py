# -*- coding: utf-8 -*-
"""
N1组深度覆盖: QualityService
补充 create_inspection, complete_rework_order, batch_tracing,
_check_quality_alerts, generate_inspection_no 等核心分支
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.quality_service import QualityService


# ============================================================
# Helper builders
# ============================================================

def _make_inspection(**kwargs):
    insp = MagicMock()
    insp.id = kwargs.get("id", 1)
    insp.inspection_no = kwargs.get("inspection_no", "QI202501010001")
    insp.inspection_date = kwargs.get("inspection_date", datetime(2025, 1, 1))
    insp.material_id = kwargs.get("material_id", 1)
    insp.inspection_qty = kwargs.get("inspection_qty", 100)
    insp.qualified_qty = kwargs.get("qualified_qty", 95)
    insp.defect_qty = kwargs.get("defect_qty", 5)
    insp.defect_type = kwargs.get("defect_type", "划伤")
    insp.defect_rate = kwargs.get("defect_rate", Decimal("5.0"))
    insp.measured_value = kwargs.get("measured_value", None)
    insp.spec_upper_limit = kwargs.get("spec_upper_limit", None)
    insp.spec_lower_limit = kwargs.get("spec_lower_limit", None)
    insp.batch_no = kwargs.get("batch_no", "BATCH001")
    insp.inspection_type = kwargs.get("inspection_type", "IQC")
    return insp


def _make_rework_order(**kwargs):
    ro = MagicMock()
    ro.id = kwargs.get("id", 1)
    ro.rework_order_no = kwargs.get("rework_order_no", "RW202501010001")
    ro.status = kwargs.get("status", "PENDING")
    ro.quality_inspection_id = kwargs.get("quality_inspection_id", 1)
    return ro


def _make_db_with_inspections(inspections):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = inspections
    return db


# ============================================================
# 1. _generate_inspection_no
# ============================================================

class TestGenerateInspectionNo:
    def test_first_record_of_day(self):
        """当天无记录时序号从0001开始"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        no = QualityService._generate_inspection_no(db)
        today = datetime.now().strftime("%Y%m%d")
        assert no == f"QI{today}0001"

    def test_increments_from_last_record(self):
        """已有记录时序号自增"""
        db = MagicMock()
        last = MagicMock()
        last.inspection_no = "QI202501010005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last
        no = QualityService._generate_inspection_no(db)
        assert no.endswith("0006")


# ============================================================
# 2. create_inspection
# ============================================================

class TestCreateInspection:
    def test_defect_rate_calculated(self):
        """创建时自动计算不良率"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []  # no alert rules

        from app.schemas.production.quality import QualityInspectionCreate
        inspection_data = MagicMock(spec=QualityInspectionCreate)
        inspection_data.inspection_qty = 200
        inspection_data.defect_qty = 10
        inspection_data.model_dump.return_value = {
            "inspection_qty": 200,
            "defect_qty": 10,
            "qualified_qty": 190,
        }

        with patch("app.services.quality_service.save_obj") as mock_save:
            result = QualityService.create_inspection(db, inspection_data, current_user_id=1)

        mock_save.assert_called_once()
        # 不良率 = 10/200*100 = 5.0
        assert result.defect_rate == Decimal("5.0")

    def test_zero_inspection_qty_no_division_error(self):
        """检验数量为0时不良率应为0"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        from app.schemas.production.quality import QualityInspectionCreate
        inspection_data = MagicMock(spec=QualityInspectionCreate)
        inspection_data.inspection_qty = 0
        inspection_data.defect_qty = 0
        inspection_data.model_dump.return_value = {
            "inspection_qty": 0,
            "defect_qty": 0,
            "qualified_qty": 0,
        }

        with patch("app.services.quality_service.save_obj"):
            result = QualityService.create_inspection(db, inspection_data, current_user_id=1)
        assert result.defect_rate == Decimal("0.0")


# ============================================================
# 3. _generate_analysis_no / _generate_rework_order_no
# ============================================================

class TestGenerateOtherNos:
    def test_analysis_no_first_record(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        no = QualityService._generate_analysis_no(db)
        today = datetime.now().strftime("%Y%m%d")
        assert no == f"DA{today}0001"

    def test_analysis_no_increments(self):
        db = MagicMock()
        last = MagicMock()
        last.analysis_no = "DA202501010003"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last
        no = QualityService._generate_analysis_no(db)
        assert no.endswith("0004")

    def test_rework_order_no_first_record(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        no = QualityService._generate_rework_order_no(db)
        today = datetime.now().strftime("%Y%m%d")
        assert no == f"RW{today}0001"

    def test_rework_order_no_increments(self):
        db = MagicMock()
        last = MagicMock()
        last.rework_order_no = "RW202501010009"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last
        no = QualityService._generate_rework_order_no(db)
        assert no.endswith("0010")


# ============================================================
# 4. complete_rework_order
# ============================================================

class TestCompleteReworkOrder:
    def test_complete_success(self):
        """正常完成返工单"""
        db = MagicMock()
        ro = _make_rework_order(status="PENDING")
        db.query.return_value.filter.return_value.first.return_value = ro

        completion_data = {
            "completed_qty": 10,
            "qualified_qty": 9,
            "scrap_qty": 1,
            "actual_hours": 2.0,
            "rework_cost": 500,
            "completion_note": "完成"
        }
        result = QualityService.complete_rework_order(db, rework_order_id=1, completion_data=completion_data)
        assert result.status == "COMPLETED"
        assert result.completed_qty == 10

    def test_complete_not_found_raises(self):
        """返工单不存在时抛出 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="返工单不存在"):
            QualityService.complete_rework_order(db, rework_order_id=999, completion_data={})

    def test_complete_already_done_raises(self):
        """返工单已完成时抛出 ValueError"""
        db = MagicMock()
        ro = _make_rework_order(status="COMPLETED")
        db.query.return_value.filter.return_value.first.return_value = ro
        with pytest.raises(ValueError, match="返工单已完成"):
            QualityService.complete_rework_order(db, rework_order_id=1, completion_data={})


# ============================================================
# 5. batch_tracing
# ============================================================

class TestBatchTracing:
    def test_batch_found(self):
        """批次号存在时返回追溯数据"""
        db = MagicMock()
        insp = _make_inspection(id=1, batch_no="BATCH001")
        # 主查询：inspection
        # 第一次 query...filter...all -> inspections
        # 第二次 query...filter(in_)...all -> defect_analyses
        # 第三次 query...filter(in_)...all -> rework_orders
        db.query.return_value.filter.return_value.all.side_effect = [
            [insp],      # inspections
            [],          # defect_analyses
            [],          # rework_orders
        ]

        result = QualityService.batch_tracing(db, "BATCH001")
        assert result["batch_no"] == "BATCH001"
        assert result["total_inspections"] == 1

    def test_batch_not_found_raises(self):
        """批次号不存在时抛出 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        with pytest.raises(ValueError, match="未找到批次号"):
            QualityService.batch_tracing(db, "NONEXIST")

    def test_batch_defect_rate_calculation(self):
        """批次不良率正确计算"""
        db = MagicMock()
        insp = _make_inspection(inspection_qty=100, defect_qty=5, batch_no="B002")
        db.query.return_value.filter.return_value.all.side_effect = [
            [insp], [], []
        ]
        result = QualityService.batch_tracing(db, "B002")
        assert result["batch_defect_rate"] == pytest.approx(5.0)

    def test_batch_zero_qty_rate_zero(self):
        """检验数量为0时不良率为0"""
        db = MagicMock()
        insp = _make_inspection(inspection_qty=0, defect_qty=0, batch_no="B003")
        db.query.return_value.filter.return_value.all.side_effect = [
            [insp], [], []
        ]
        result = QualityService.batch_tracing(db, "B003")
        assert result["batch_defect_rate"] == pytest.approx(0.0)


# ============================================================
# 6. _check_defect_rate_alert - 各操作符分支
# ============================================================

class TestCheckDefectRateAlert:
    def _make_rule(self, operator, threshold, min_sample=1, target_material=None):
        rule = MagicMock()
        rule.target_material_id = target_material
        rule.time_window_hours = 24
        rule.min_sample_size = min_sample
        rule.threshold_operator = operator
        rule.threshold_value = Decimal(str(threshold))
        rule.trigger_count = 0
        return rule

    def _make_recent_inspections(self, qty, defects):
        insp = MagicMock()
        insp.inspection_qty = qty
        insp.defect_qty = defects
        return insp

    def test_gt_triggered(self):
        """GT: 当前不良率 > 阈值时触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 10)  # 10%
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("GT", 5)  # 阈值5%
        mock_inspection = _make_inspection(material_id=1)

        QualityService._check_defect_rate_alert(db, rule, mock_inspection)
        assert rule.trigger_count == 1
        db.commit.assert_called()

    def test_gt_not_triggered(self):
        """GT: 当前不良率 <= 阈值时不触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 3)  # 3%
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("GT", 5)
        mock_inspection = _make_inspection(material_id=1)

        QualityService._check_defect_rate_alert(db, rule, mock_inspection)
        assert rule.trigger_count == 0

    def test_gte_triggered(self):
        """GTE: 等于阈值时触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 5)  # 5%
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("GTE", 5)
        QualityService._check_defect_rate_alert(db, rule, _make_inspection())
        assert rule.trigger_count == 1

    def test_lte_triggered(self):
        """LTE: 小于等于阈值时触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 2)  # 2%
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("LTE", 5)
        QualityService._check_defect_rate_alert(db, rule, _make_inspection())
        assert rule.trigger_count == 1

    def test_lt_triggered(self):
        """LT: 小于阈值时触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 1)  # 1%
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("LT", 5)
        QualityService._check_defect_rate_alert(db, rule, _make_inspection())
        assert rule.trigger_count == 1

    def test_insufficient_samples_no_trigger(self):
        """样本不足时不触发"""
        db = MagicMock()
        insp = self._make_recent_inspections(100, 10)
        db.query.return_value.filter.return_value.all.return_value = [insp]

        rule = self._make_rule("GT", 5, min_sample=5)  # 需要5个样本，只有1个
        QualityService._check_defect_rate_alert(db, rule, _make_inspection())
        assert rule.trigger_count == 0


# ============================================================
# 7. _check_spc_alert
# ============================================================

class TestCheckSPCAlert:
    def test_no_measured_value_returns_early(self):
        """检验记录无测量值时直接返回"""
        db = MagicMock()
        rule = MagicMock()
        rule.time_window_hours = 24
        rule.target_material_id = None
        rule.min_sample_size = 1
        rule.alert_type = "SPC_UCL"
        rule.trigger_count = 0

        insp = _make_inspection(measured_value=None)
        QualityService._check_spc_alert(db, rule, insp)
        assert rule.trigger_count == 0

    def test_spc_ucl_triggered(self):
        """SPC_UCL: 超出上限时触发"""
        db = MagicMock()
        # 生成历史数据: 均值=10, std=1, UCL=13
        history = []
        for v in [10.0] * 10:
            h = MagicMock()
            h.measured_value = Decimal(str(v))
            history.append(h)
        db.query.return_value.filter.return_value.all.return_value = history

        rule = MagicMock()
        rule.time_window_hours = 24
        rule.target_material_id = None
        rule.min_sample_size = 5
        rule.alert_type = "SPC_UCL"
        rule.trigger_count = 0

        insp = _make_inspection(measured_value=Decimal("1000"))  # 远超UCL
        QualityService._check_spc_alert(db, rule, insp)
        assert rule.trigger_count == 1

    def test_spc_lcl_triggered(self):
        """SPC_LCL: 低于下限时触发"""
        db = MagicMock()
        history = []
        for v in [10.0] * 10:
            h = MagicMock()
            h.measured_value = Decimal(str(v))
            history.append(h)
        db.query.return_value.filter.return_value.all.return_value = history

        rule = MagicMock()
        rule.time_window_hours = 24
        rule.target_material_id = None
        rule.min_sample_size = 5
        rule.alert_type = "SPC_LCL"
        rule.trigger_count = 0

        insp = _make_inspection(measured_value=Decimal("-1000"))  # 远低于LCL
        QualityService._check_spc_alert(db, rule, insp)
        assert rule.trigger_count == 1


# ============================================================
# 8. _aggregate_by_time - week 分支
# ============================================================

class TestAggregateByTimeWeek:
    def test_aggregate_by_week(self):
        inspections = []
        for day in range(7):
            i = MagicMock()
            i.inspection_date = datetime(2025, 1, 6 + day)
            i.inspection_qty = 10
            i.qualified_qty = 9
            i.defect_qty = 1
            inspections.append(i)

        result = QualityService._aggregate_by_time(inspections, "week")
        # 所有日期在同一周
        assert len(result) >= 1


# ============================================================
# 9. pareto_analysis
# ============================================================

class TestParetoAnalysis:
    def test_pareto_returns_structure(self):
        """帕累托分析返回正确结构"""
        db = MagicMock()
        stat1 = MagicMock()
        stat1.defect_type = "划伤"
        stat1.total_qty = 80

        stat2 = MagicMock()
        stat2.defect_type = "气泡"
        stat2.total_qty = 20

        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [stat1, stat2]

        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        assert "data_points" in result
        assert "total_defects" in result
        assert "top_80_percent_types" in result
        assert result["total_defects"] == 100

    def test_pareto_top_80_percent_identified(self):
        """帕累托分析正确识别80%不良类型"""
        db = MagicMock()
        stat1 = MagicMock()
        stat1.defect_type = "划伤"
        stat1.total_qty = 85  # 85%

        stat2 = MagicMock()
        stat2.defect_type = "气泡"
        stat2.total_qty = 15  # 15%

        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [stat1, stat2]

        result = QualityService.pareto_analysis(
            db,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        assert "划伤" in result["top_80_percent_types"]
