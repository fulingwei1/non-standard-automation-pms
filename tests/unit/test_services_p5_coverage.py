# -*- coding: utf-8 -*-
"""
P5 组 - 剩余低覆盖率 service 文件测试（排名 81-123）
覆盖 43 个服务文件，每个文件 3-6 个测试用例
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from contextlib import contextmanager


# ─────────────────────────────────────────────────────────────────
# 1. project_workspace_service – 纯逻辑函数
# ─────────────────────────────────────────────────────────────────
class TestProjectWorkspaceService:
    def _make_project(self, **kwargs):
        p = MagicMock()
        p.id = kwargs.get("id", 1)
        p.project_code = kwargs.get("project_code", "P001")
        p.project_name = kwargs.get("project_name", "Test Project")
        p.stage = kwargs.get("stage", "S1")
        p.status = kwargs.get("status", "ACTIVE")
        p.health = kwargs.get("health", "H1")
        p.progress_pct = kwargs.get("progress_pct", Decimal("50.0"))
        p.contract_amount = kwargs.get("contract_amount", Decimal("100000.0"))
        p.pm_name = kwargs.get("pm_name", "Alice")
        return p

    def test_build_project_basic_info(self):
        from app.services.project_workspace_service import build_project_basic_info
        proj = self._make_project()
        result = build_project_basic_info(proj)
        assert result["project_code"] == "P001"
        assert result["project_name"] == "Test Project"
        assert result["progress_pct"] == 50.0
        assert result["contract_amount"] == 100000.0

    def test_build_project_basic_info_zero_values(self):
        from app.services.project_workspace_service import build_project_basic_info
        proj = self._make_project(progress_pct=None, contract_amount=None)
        result = build_project_basic_info(proj)
        assert result["progress_pct"] == 0.0
        assert result["contract_amount"] == 0.0

    def test_build_team_info_empty(self):
        from app.services.project_workspace_service import build_team_info
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        result = build_team_info(db, 1)
        assert result == []

    def test_build_team_info_with_member(self):
        from app.services.project_workspace_service import build_team_info
        db = MagicMock()
        member = MagicMock()
        member.user_id = 1
        member.user = MagicMock()
        member.user.real_name = "Bob"
        member.user.username = "bob"
        member.role_code = "PM"
        member.allocation_pct = Decimal("80.0")
        member.start_date = date(2025, 1, 1)
        member.end_date = None
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        result = build_team_info(db, 1)
        assert len(result) == 1
        assert result[0]["user_id"] == 1
        assert result[0]["role_code"] == "PM"

    def test_build_bonus_info_exception(self):
        from app.services.project_workspace_service import build_bonus_info
        db = MagicMock()
        # Force exception
        with patch("app.services.project_workspace_service.ProjectBonusService", side_effect=Exception("db error")):
            result = build_bonus_info(db, 1)
        assert result["rules"] == []
        assert result["calculations"] == []

    def test_build_meeting_info_exception(self):
        from app.services.project_workspace_service import build_meeting_info
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectMeetingService", side_effect=Exception("fail")):
            result = build_meeting_info(db, 1)
        assert result["meetings"] == []
        assert result["statistics"] == {}


# ─────────────────────────────────────────────────────────────────
# 2. data_integrity/reminders – RemindersMixin
# ─────────────────────────────────────────────────────────────────
class TestRemindersMixin:
    def _make_mixin(self, db):
        from app.services.data_integrity.reminders import RemindersMixin
        obj = RemindersMixin.__new__(RemindersMixin)
        obj.db = db
        return obj

    def test_get_missing_data_reminders_period_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mixin = self._make_mixin(db)
        result = mixin.get_missing_data_reminders(period_id=999)
        assert result == []

    def test_get_missing_data_reminders_no_missing(self):
        db = MagicMock()
        period = MagicMock()
        period.start_date = date(2025, 1, 1)
        period.end_date = date(2025, 12, 31)
        db.query.return_value.filter.return_value.first.return_value = period
        db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.get_missing_data_reminders(period_id=1)
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────
# 3. advantage_product_import_service – COLUMN_CATEGORY_MAP
# ─────────────────────────────────────────────────────────────────
class TestAdvantageProductImportService:
    def test_column_category_map_structure(self):
        from app.services.advantage_product_import_service import COLUMN_CATEGORY_MAP
        assert 0 in COLUMN_CATEGORY_MAP
        assert COLUMN_CATEGORY_MAP[0]["code"] == "HOME_APPLIANCE"
        assert len(COLUMN_CATEGORY_MAP) == 8

    def test_clear_existing_data(self):
        from app.services.advantage_product_import_service import clear_existing_data
        db = MagicMock()
        db.query.return_value.delete.return_value = 5
        clear_existing_data(db)
        assert db.commit.called

    def test_ensure_categories_exist_no_clear(self):
        from app.services.advantage_product_import_service import ensure_categories_exist
        db = MagicMock()
        existing_cat = MagicMock()
        existing_cat.code = "HOME_APPLIANCE"
        existing_cat.id = 10
        db.query.return_value.all.return_value = [existing_cat]
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.side_effect = lambda x: None
        cat_map, created = ensure_categories_exist(db, clear_existing=False)
        assert isinstance(cat_map, dict)
        assert 0 in cat_map  # HOME_APPLIANCE was mapped to index 0


# ─────────────────────────────────────────────────────────────────
# 4. project_timeline_service
# ─────────────────────────────────────────────────────────────────
class TestProjectTimelineService:
    def test_collect_status_change_events_empty(self):
        from app.services.project_timeline_service import collect_status_change_events
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        events = collect_status_change_events(db, project_id=1)
        assert events == []

    def test_collect_status_change_events_with_log(self):
        from app.services.project_timeline_service import collect_status_change_events
        db = MagicMock()
        log = MagicMock()
        log.change_type = "STAGE_CHANGE"
        log.changed_at = datetime(2025, 1, 1)
        log.old_stage = "S1"
        log.new_stage = "S2"
        log.old_status = None
        log.new_status = None
        log.changer = None
        log.id = 1
        db.query.return_value.filter.return_value.all.return_value = [log]
        events = collect_status_change_events(db, project_id=1)
        assert len(events) == 1
        assert events[0].event_type == "STAGE_CHANGE"

    def test_collect_milestone_events_empty(self):
        from app.services.project_timeline_service import collect_milestone_events
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        events = collect_milestone_events(db, project_id=1)
        assert events == []


# ─────────────────────────────────────────────────────────────────
# 5. strategy/annual_work_service/progress
# ─────────────────────────────────────────────────────────────────
class TestAnnualWorkProgress:
    def test_update_progress_work_not_found(self):
        from app.services.strategy.annual_work_service.progress import update_progress
        db = MagicMock()
        data = MagicMock()
        data.progress_percent = 50
        data.progress_description = "half done"
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=None):
            result = update_progress(db, work_id=999, data=data)
        assert result is None

    def test_update_progress_completed(self):
        from app.services.strategy.annual_work_service.progress import update_progress
        db = MagicMock()
        work = MagicMock()
        work.status = "IN_PROGRESS"
        data = MagicMock()
        data.progress_percent = 100
        data.progress_description = "Done"
        db.refresh.side_effect = lambda x: None
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=work):
            result = update_progress(db, work_id=1, data=data)
        assert work.status == "COMPLETED"
        assert result == work

    def test_update_progress_in_progress(self):
        from app.services.strategy.annual_work_service.progress import update_progress
        db = MagicMock()
        work = MagicMock()
        data = MagicMock()
        data.progress_percent = 50
        data.progress_description = ""
        db.refresh.side_effect = lambda x: None
        with patch("app.services.strategy.annual_work_service.progress.get_annual_work", return_value=work):
            result = update_progress(db, work_id=1, data=data)
        assert work.status == "IN_PROGRESS"


# ─────────────────────────────────────────────────────────────────
# 6. report_data_generation/project_reports
# ─────────────────────────────────────────────────────────────────
class TestProjectReportMixin:
    def test_generate_project_weekly_report_not_found(self):
        from app.services.report_data_generation.project_reports import ProjectReportMixin
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = ProjectReportMixin.generate_project_weekly_report(
            db, project_id=999,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7)
        )
        assert "error" in result

    def test_generate_project_weekly_report_found(self):
        from app.services.report_data_generation.project_reports import ProjectReportMixin
        db = MagicMock()
        proj = MagicMock()
        proj.project_code = "P001"
        proj.project_name = "Test"
        proj.customer_name = "CustA"
        proj.current_stage = "S2"
        proj.health_status = "H1"
        proj.progress = Decimal("60")
        # First query returns project, rest return []
        db.query.return_value.filter.return_value.first.return_value = proj
        db.query.return_value.filter.return_value.between.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.between.return_value.between.return_value.all.return_value = []
        result = ProjectReportMixin.generate_project_weekly_report(
            db, project_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7)
        )
        assert "summary" in result or "project_code" in str(result)


# ─────────────────────────────────────────────────────────────────
# 7. spec_match_service
# ─────────────────────────────────────────────────────────────────
class TestSpecMatchService:
    def test_get_project_requirements_empty(self):
        from app.services.spec_match_service import get_project_requirements
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_project_requirements(db, project_id=1)
        assert result == []

    def test_get_project_requirements_with_data(self):
        from app.services.spec_match_service import get_project_requirements
        db = MagicMock()
        req = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [req]
        result = get_project_requirements(db, project_id=1)
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────────
# 8. data_integrity/check – DataCheckMixin
# ─────────────────────────────────────────────────────────────────
class TestDataCheckMixin:
    def _make_mixin(self, db):
        from app.services.data_integrity.check import DataCheckMixin
        obj = DataCheckMixin.__new__(DataCheckMixin)
        obj.db = db
        return obj

    def test_check_data_completeness_period_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mixin = self._make_mixin(db)
        with pytest.raises(ValueError, match="考核周期不存在"):
            mixin.check_data_completeness(engineer_id=1, period_id=999)

    def test_check_data_completeness_no_profile(self):
        db = MagicMock()
        # First call returns period, second returns None (no profile)
        period = MagicMock()
        period.start_date = date(2025, 1, 1)
        period.end_date = date(2025, 12, 31)
        db.query.return_value.filter.return_value.first.side_effect = [period, None]
        mixin = self._make_mixin(db)
        result = mixin.check_data_completeness(engineer_id=1, period_id=1)
        assert result["completeness_score"] == 0.0
        assert "工程师档案不存在" in result["missing_items"]


# ─────────────────────────────────────────────────────────────────
# 9. resource_waste_analysis/failure_patterns – FailurePatternsMixin
# ─────────────────────────────────────────────────────────────────
class TestFailurePatternsMixin:
    def _make_mixin(self, db):
        from app.services.resource_waste_analysis.failure_patterns import FailurePatternsMixin
        obj = FailurePatternsMixin.__new__(FailurePatternsMixin)
        obj.db = db
        return obj

    def test_analyze_failure_patterns_no_data(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.analyze_failure_patterns()
        assert result["loss_reason_distribution"] == {}
        assert "数据不足" in result["recommendations"][0]

    def test_analyze_failure_patterns_with_date_filter(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.analyze_failure_patterns(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        assert "loss_reason_distribution" in result


# ─────────────────────────────────────────────────────────────────
# 10. purchase_request_from_bom_service
# ─────────────────────────────────────────────────────────────────
class TestPurchaseRequestFromBomService:
    def test_determine_supplier_default(self):
        from app.services.purchase_request_from_bom_service import determine_supplier_for_item
        db = MagicMock()
        item = MagicMock()
        item.supplier_id = None
        item.material_id = None
        result = determine_supplier_for_item(db, item, default_supplier_id=5)
        assert result == 5

    def test_determine_supplier_from_item(self):
        from app.services.purchase_request_from_bom_service import determine_supplier_for_item
        db = MagicMock()
        item = MagicMock()
        item.supplier_id = 7
        item.material_id = None
        result = determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 7

    def test_determine_supplier_zero_when_none(self):
        from app.services.purchase_request_from_bom_service import determine_supplier_for_item
        db = MagicMock()
        item = MagicMock()
        item.supplier_id = None
        item.material_id = None
        result = determine_supplier_for_item(db, item, default_supplier_id=None)
        assert result == 0

    def test_group_items_by_supplier(self):
        from app.services.purchase_request_from_bom_service import group_items_by_supplier
        db = MagicMock()
        item1 = MagicMock()
        item1.supplier_id = 1
        item1.material_id = None
        item2 = MagicMock()
        item2.supplier_id = 2
        item2.material_id = None
        groups = group_items_by_supplier(db, [item1, item2], default_supplier_id=None)
        assert 1 in groups
        assert 2 in groups


# ─────────────────────────────────────────────────────────────────
# 11. engineer_performance/ranking_service – RankingService
# ─────────────────────────────────────────────────────────────────
class TestRankingService:
    def test_get_ranking_returns_empty(self):
        from app.services.engineer_performance.ranking_service import RankingService
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        svc = RankingService(db)
        items, total = svc.get_ranking(period_id=1)
        assert total == 0
        assert items == []

    def test_get_company_summary_no_results(self):
        from app.services.engineer_performance.ranking_service import RankingService
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        svc = RankingService(db)
        result = svc.get_company_summary(period_id=1)
        assert result == {}

    def test_get_ranking_with_filters(self):
        from app.services.engineer_performance.ranking_service import RankingService
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 1
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        svc = RankingService(db)
        items, total = svc.get_ranking(period_id=1, job_type="PM", department_id=2)
        assert isinstance(total, int)


# ─────────────────────────────────────────────────────────────────
# 12. bonus/sales – SalesBonusCalculator
# ─────────────────────────────────────────────────────────────────
class TestSalesBonusCalculator:
    def test_calculate_no_owner(self):
        from app.services.bonus.sales import SalesBonusCalculator
        db = MagicMock()
        calc = SalesBonusCalculator(db)
        contract = MagicMock()
        contract.owner_id = None
        rule = MagicMock()
        rule.trigger_condition = None
        result = calc.calculate(contract, rule)
        assert result is None

    def test_calculate_contract_based(self):
        from app.services.bonus.sales import SalesBonusCalculator
        db = MagicMock()
        db.add.return_value = None
        db.commit.return_value = None
        calc = SalesBonusCalculator(db)
        contract = MagicMock()
        contract.owner_id = 1
        contract.project_id = 10
        contract.contract_code = "C001"
        contract.contract_amount = Decimal("100000")
        rule = MagicMock()
        rule.trigger_condition = None
        rule.id = 1
        rule.coefficient = Decimal("2")  # 2%
        result = calc.calculate(contract, rule, based_on="CONTRACT")
        assert result is not None
        assert result.calculated_amount == Decimal("2000")


# ─────────────────────────────────────────────────────────────────
# 13. strategy/kpi_service/crud
# ─────────────────────────────────────────────────────────────────
class TestKpiServiceCrud:
    def test_get_kpi_returns_none(self):
        from app.services.strategy.kpi_service.crud import get_kpi
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        result = get_kpi(db, kpi_id=999)
        assert result is None

    def test_get_kpi_returns_value(self):
        from app.services.strategy.kpi_service.crud import get_kpi
        db = MagicMock()
        kpi = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = kpi
        result = get_kpi(db, kpi_id=1)
        assert result == kpi

    def test_create_kpi(self):
        from app.services.strategy.kpi_service.crud import create_kpi
        db = MagicMock()
        db.refresh.side_effect = lambda x: None
        data = MagicMock()
        data.csf_id = 1
        data.code = "KPI-001"
        data.name = "KPI Name"
        data.description = "desc"
        data.ipooc_type = "O"
        data.unit = "%"
        data.direction = "UP"
        data.target_value = Decimal("100")
        data.baseline_value = Decimal("0")
        data.excellent_threshold = Decimal("110")
        data.good_threshold = Decimal("100")
        data.warning_threshold = Decimal("80")
        data.data_source_type = "MANUAL"
        data.data_source_config = None
        data.frequency = "MONTHLY"
        data.weight = Decimal("1")
        data.owner_user_id = 1
        result = create_kpi(db, data)
        assert db.add.called
        assert db.commit.called


# ─────────────────────────────────────────────────────────────────
# 14. report_framework/adapters/sales – SalesReportAdapter
# ─────────────────────────────────────────────────────────────────
class TestSalesReportAdapter:
    def test_get_report_code(self):
        from app.services.report_framework.adapters.sales import SalesReportAdapter
        db = MagicMock()
        adapter = SalesReportAdapter(db)
        assert adapter.get_report_code() == "SALES_MONTHLY"

    def test_generate_data_invalid_month_format(self):
        from app.services.report_framework.adapters.sales import SalesReportAdapter
        db = MagicMock()
        adapter = SalesReportAdapter(db)
        with pytest.raises((ValueError, Exception)):
            adapter.generate_data({"month": "invalid-format"})


# ─────────────────────────────────────────────────────────────────
# 15. win_rate_prediction_service/analysis
# ─────────────────────────────────────────────────────────────────
class TestWinRateAnalysis:
    def test_get_win_rate_distribution_empty(self):
        from app.services.win_rate_prediction_service.analysis import get_win_rate_distribution
        service = MagicMock()
        service.db.query.return_value.filter.return_value.all.return_value = []
        result = get_win_rate_distribution(service)
        assert isinstance(result, dict)
        # All counts should be 0
        for level_data in result.values():
            assert level_data["count"] == 0

    def test_get_win_rate_distribution_with_projects(self):
        from app.services.win_rate_prediction_service.analysis import get_win_rate_distribution
        from app.models.enums import LeadOutcomeEnum
        service = MagicMock()
        p1 = MagicMock()
        p1.predicted_win_rate = 0.85
        p1.outcome = LeadOutcomeEnum.WON.value
        p2 = MagicMock()
        p2.predicted_win_rate = 0.30
        p2.outcome = LeadOutcomeEnum.LOST.value
        service.db.query.return_value.filter.return_value.all.return_value = [p1, p2]
        result = get_win_rate_distribution(service)
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────
# 16. ticket_assignment_service
# ─────────────────────────────────────────────────────────────────
class TestTicketAssignmentService:
    def test_get_project_members_empty_project_ids(self):
        from app.services.ticket_assignment_service import get_project_members_for_ticket
        db = MagicMock()
        result = get_project_members_for_ticket(db, project_ids=[])
        assert result == []

    def test_get_project_members_no_members(self):
        from app.services.ticket_assignment_service import get_project_members_for_ticket
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_project_members_for_ticket(db, project_ids=[1, 2])
        assert result == []

    def test_get_project_members_with_exclude(self):
        from app.services.ticket_assignment_service import get_project_members_for_ticket
        db = MagicMock()
        member = MagicMock()
        member.user_id = 5
        member.user = MagicMock()
        member.user.username = "alice"
        member.user.real_name = "Alice"
        member.role_code = "PM"
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [member]
        result = get_project_members_for_ticket(db, project_ids=[1], exclude_user_id=10)
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────
# 17. presale_ai_template_service – PresaleAITemplateService
# ─────────────────────────────────────────────────────────────────
class TestPresaleAITemplateService:
    def test_get_template_not_found(self):
        from app.services.presale_ai_template_service import PresaleAITemplateService
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        result = svc.get_template(template_id=999)
        assert result is None

    def test_delete_template_not_found(self):
        from app.services.presale_ai_template_service import PresaleAITemplateService
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        result = svc.delete_template(template_id=999)
        assert result is False

    def test_delete_template_success(self):
        from app.services.presale_ai_template_service import PresaleAITemplateService
        db = MagicMock()
        template = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = template
        svc = PresaleAITemplateService(db)
        result = svc.delete_template(template_id=1)
        assert result is True
        assert template.is_active == 0

    def test_update_template_not_found(self):
        from app.services.presale_ai_template_service import PresaleAITemplateService
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        with pytest.raises(ValueError, match="not found"):
            svc.update_template(template_id=999, data={"name": "New"})


# ─────────────────────────────────────────────────────────────────
# 18. report_framework/adapters/project – ProjectReportAdapter
# ─────────────────────────────────────────────────────────────────
class TestProjectReportAdapter:
    def test_get_report_code_weekly(self):
        from app.services.report_framework.adapters.project import ProjectReportAdapter
        db = MagicMock()
        adapter = ProjectReportAdapter(db, report_type="weekly")
        assert adapter.get_report_code() == "PROJECT_WEEKLY"

    def test_get_report_code_monthly(self):
        from app.services.report_framework.adapters.project import ProjectReportAdapter
        db = MagicMock()
        adapter = ProjectReportAdapter(db, report_type="monthly")
        assert adapter.get_report_code() == "PROJECT_MONTHLY"

    def test_generate_data_no_project_id(self):
        from app.services.report_framework.adapters.project import ProjectReportAdapter
        db = MagicMock()
        adapter = ProjectReportAdapter(db)
        with pytest.raises(ValueError, match="project_id"):
            adapter.generate_data({})


# ─────────────────────────────────────────────────────────────────
# 19. report_framework/adapters/department – DeptReportAdapter
# ─────────────────────────────────────────────────────────────────
class TestDeptReportAdapter:
    def test_get_report_code_weekly(self):
        from app.services.report_framework.adapters.department import DeptReportAdapter
        db = MagicMock()
        adapter = DeptReportAdapter(db, report_type="weekly")
        assert adapter.get_report_code() == "DEPT_WEEKLY"

    def test_get_report_code_monthly(self):
        from app.services.report_framework.adapters.department import DeptReportAdapter
        db = MagicMock()
        adapter = DeptReportAdapter(db, report_type="monthly")
        assert adapter.get_report_code() == "DEPT_MONTHLY"

    def test_generate_data_no_dept_id(self):
        from app.services.report_framework.adapters.department import DeptReportAdapter
        db = MagicMock()
        adapter = DeptReportAdapter(db)
        with pytest.raises(ValueError, match="department_id"):
            adapter.generate_data({})


# ─────────────────────────────────────────────────────────────────
# 20. data_integrity/export – ExportMixin
# ─────────────────────────────────────────────────────────────────
class TestExportMixin:
    def _make_mixin(self, db):
        from app.services.data_integrity.export import ExportMixin
        obj = ExportMixin.__new__(ExportMixin)
        obj.db = db
        return obj

    def test_export_data_quality_report_json(self):
        db = MagicMock()
        mixin = self._make_mixin(db)
        report_data = {"overall_completeness": 90.0, "reports": []}
        with patch.object(mixin, "generate_data_quality_report", return_value=report_data):
            result = mixin.export_data_quality_report(period_id=1, format="json")
        assert result["overall_completeness"] == 90.0

    def test_export_unsupported_format(self):
        db = MagicMock()
        mixin = self._make_mixin(db)
        report_data = {"key": "val"}
        with patch.object(mixin, "generate_data_quality_report", return_value=report_data):
            result = mixin.export_data_quality_report(period_id=1, format="html")
        # Returns report as-is for unknown format
        assert result == report_data


# ─────────────────────────────────────────────────────────────────
# 21. strategy/annual_work_service/crud
# ─────────────────────────────────────────────────────────────────
class TestAnnualWorkCrud:
    def test_get_annual_work_not_found(self):
        from app.services.strategy.annual_work_service.crud import get_annual_work
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        result = get_annual_work(db, work_id=999)
        assert result is None

    def test_get_annual_work_found(self):
        from app.services.strategy.annual_work_service.crud import get_annual_work
        db = MagicMock()
        work = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = work
        result = get_annual_work(db, work_id=1)
        assert result == work

    def test_create_annual_work(self):
        from app.services.strategy.annual_work_service.crud import create_annual_work
        db = MagicMock()
        db.refresh.side_effect = lambda x: None
        data = MagicMock()
        data.csf_id = 1
        data.code = "W001"
        data.name = "Work 1"
        data.description = "desc"
        data.voc_source = None
        data.pain_point = None
        data.solution = None
        data.year = 2025
        data.priority = 1
        data.start_date = date(2025, 1, 1)
        data.end_date = date(2025, 12, 31)
        data.owner_dept_id = 1
        data.owner_user_id = 1
        result = create_annual_work(db, data)
        assert db.add.called


# ─────────────────────────────────────────────────────────────────
# 22. ecn_notification utils
# ─────────────────────────────────────────────────────────────────
class TestEcnNotificationUtils:
    def test_find_users_by_department_empty_name(self):
        from app.services.ecn_notification.utils import find_users_by_department
        db = MagicMock()
        result = find_users_by_department(db, department_name="")
        assert result == []

    def test_find_users_by_role_empty_code(self):
        from app.services.ecn_notification.utils import find_users_by_role
        db = MagicMock()
        result = find_users_by_role(db, role_code="")
        assert result == []

    def test_find_users_by_department_no_dept(self):
        from app.services.ecn_notification.utils import find_users_by_department
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = find_users_by_department(db, department_name="Engineering")
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────
# 23. data_integrity/report – DataReportMixin
# ─────────────────────────────────────────────────────────────────
class TestDataReportMixin:
    def _make_mixin(self, db):
        from app.services.data_integrity.report import DataReportMixin
        obj = DataReportMixin.__new__(DataReportMixin)
        obj.db = db
        return obj

    def test_generate_data_quality_report_period_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mixin = self._make_mixin(db)
        with pytest.raises(ValueError, match="考核周期不存在"):
            mixin.generate_data_quality_report(period_id=999)

    def test_generate_data_quality_report_no_engineers(self):
        db = MagicMock()
        period = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = period
        db.query.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.generate_data_quality_report(period_id=1)
        assert result["total_engineers"] == 0


# ─────────────────────────────────────────────────────────────────
# 24. excel_template_service
# ─────────────────────────────────────────────────────────────────
class TestExcelTemplateService:
    def test_create_template_excel_returns_streaming(self):
        from app.services.excel_template_service import create_template_excel
        template_data = {"列A": ["示例1"], "列B": ["示例2"]}
        result = create_template_excel(
            template_data=template_data,
            sheet_name="Sheet1",
            column_widths={"A": 20, "B": 30},
            instructions="请按照模板填写",
            filename_prefix="test_template"
        )
        # Should return a StreamingResponse
        from fastapi.responses import StreamingResponse
        assert isinstance(result, StreamingResponse)


# ─────────────────────────────────────────────────────────────────
# 25. template_report/dept_reports – DeptReportMixin
# ─────────────────────────────────────────────────────────────────
class TestDeptReportMixin:
    def test_generate_dept_weekly_dept_not_found(self):
        from app.services.template_report.dept_reports import DeptReportMixin
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportMixin._generate_dept_weekly(
            db, department_id=999,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            sections_config={},
            metrics_config={}
        )
        assert "error" in result

    def test_generate_dept_weekly_empty_users(self):
        from app.services.template_report.dept_reports import DeptReportMixin
        db = MagicMock()
        dept = MagicMock()
        dept.name = "Engineering"
        db.query.return_value.filter.return_value.first.return_value = dept
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = DeptReportMixin._generate_dept_weekly(
            db, department_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            sections_config={},
            metrics_config={}
        )
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────
# 26. report_framework/adapters/analysis – WorkloadAnalysisAdapter
# ─────────────────────────────────────────────────────────────────
class TestWorkloadAnalysisAdapter:
    def test_get_report_code(self):
        from app.services.report_framework.adapters.analysis import WorkloadAnalysisAdapter
        db = MagicMock()
        adapter = WorkloadAnalysisAdapter(db)
        assert adapter.get_report_code() == "WORKLOAD_ANALYSIS"

    def test_cost_analysis_adapter_code(self):
        from app.services.report_framework.adapters.analysis import CostAnalysisAdapter
        db = MagicMock()
        adapter = CostAnalysisAdapter(db)
        assert adapter.get_report_code() == "COST_ANALYSIS"


# ─────────────────────────────────────────────────────────────────
# 27. report_framework/adapters/report_data_generation
# ─────────────────────────────────────────────────────────────────
class TestReportDataGenerationAdapter:
    def test_get_report_code_known(self):
        from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter
        db = MagicMock()
        adapter = ReportDataGenerationAdapter(db, report_type="PROJECT_WEEKLY")
        assert adapter.get_report_code() == "PROJECT_WEEKLY"

    def test_get_report_code_unknown(self):
        from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter
        db = MagicMock()
        adapter = ReportDataGenerationAdapter(db, report_type="CUSTOM_TYPE")
        assert adapter.get_report_code() == "CUSTOM_TYPE"

    def test_report_type_map_has_all_types(self):
        from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter
        expected = {"PROJECT_WEEKLY", "PROJECT_MONTHLY", "DEPT_WEEKLY", "DEPT_MONTHLY",
                    "WORKLOAD_ANALYSIS", "COST_ANALYSIS"}
        actual = set(ReportDataGenerationAdapter.REPORT_TYPE_MAP.keys())
        assert expected == actual


# ─────────────────────────────────────────────────────────────────
# 28. strategy/review/routine_management
# ─────────────────────────────────────────────────────────────────
class TestRoutineManagement:
    def test_get_routine_management_cycle_structure(self):
        from app.services.strategy.review.routine_management import get_routine_management_cycle
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_routine_management_cycle(db, strategy_id=1)
        assert hasattr(result, "cycles") or isinstance(result, (dict, object))
        # Check cycles list exists
        cycles = getattr(result, "cycles", [])
        cycle_types = [c.cycle_type for c in cycles]
        assert "DAILY" in cycle_types
        assert "WEEKLY" in cycle_types
        assert "MONTHLY" in cycle_types


# ─────────────────────────────────────────────────────────────────
# 29. stage_template/helpers – HelpersMixin
# ─────────────────────────────────────────────────────────────────
class TestHelpersMixin:
    def _make_mixin(self, db):
        from app.services.stage_template.helpers import HelpersMixin
        obj = HelpersMixin.__new__(HelpersMixin)
        obj.db = db
        return obj

    def test_clear_default_template(self):
        db = MagicMock()
        mixin = self._make_mixin(db)
        mixin._clear_default_template("SOFTWARE")
        assert db.query.called

    def test_has_circular_dependency_false(self):
        db = MagicMock()
        # Node has no deps
        node = MagicMock()
        node.dependency_node_ids = None
        db.query.return_value.filter.return_value.first.return_value = node
        mixin = self._make_mixin(db)
        result = mixin._has_circular_dependency(
            node_id=1,
            new_dependency_ids=[2, 3],
            template_id=10
        )
        assert result is False

    def test_remove_node_from_dependencies(self):
        db = MagicMock()
        node = MagicMock()
        node.dependency_node_ids = [5, 10, 15]
        db.query.return_value.filter.return_value.all.return_value = [node]
        mixin = self._make_mixin(db)
        mixin._remove_node_from_dependencies(node_id=10)
        assert 10 not in node.dependency_node_ids


# ─────────────────────────────────────────────────────────────────
# 30. template_report/core – TemplateReportCore
# ─────────────────────────────────────────────────────────────────
class TestTemplateReportCore:
    def test_generate_from_template_sets_defaults(self):
        from app.services.template_report.core import TemplateReportCore
        db = MagicMock()
        template = MagicMock()
        template.id = 1
        template.template_code = "T001"
        template.template_name = "Weekly Report"
        template.report_type = "PROJECT_WEEKLY"
        template.sections = {}
        template.metrics_config = {}

        with patch("app.services.template_report.core.ProjectReportMixin") as MockPRM, \
             patch("app.services.template_report.core.DeptReportMixin") as MockDRM, \
             patch("app.services.template_report.core.AnalysisReportMixin") as MockARM:
            result = TemplateReportCore.generate_from_template(
                db, template,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 7)
            )
        assert result["template_id"] == 1
        assert result["template_code"] == "T001"
        assert "period" in result


# ─────────────────────────────────────────────────────────────────
# 31. win_rate_prediction_service/history
# ─────────────────────────────────────────────────────────────────
class TestWinRateHistory:
    def test_get_salesperson_historical_win_rate_no_data(self):
        from app.services.win_rate_prediction_service.history import get_salesperson_historical_win_rate
        service = MagicMock()
        stats = MagicMock()
        stats.total = 0
        stats.won = 0
        service.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = stats
        win_rate, count = get_salesperson_historical_win_rate(service, salesperson_id=1)
        assert win_rate == 0.20  # industry average
        assert count == 0

    def test_get_customer_cooperation_history_by_id(self):
        from app.services.win_rate_prediction_service.history import get_customer_cooperation_history
        service = MagicMock()
        service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        total, won = get_customer_cooperation_history(service, customer_id=1)
        assert total == 0
        assert won == 0


# ─────────────────────────────────────────────────────────────────
# 32. report_data_generation/router – ReportRouterMixin
# ─────────────────────────────────────────────────────────────────
class TestReportRouterMixin:
    def test_generate_report_project_weekly_no_id(self):
        from app.services.report_data_generation.router import ReportRouterMixin
        db = MagicMock()
        result = ReportRouterMixin.generate_report_by_type(db, report_type="PROJECT_WEEKLY")
        assert "error" in result

    def test_generate_report_dept_weekly_no_id(self):
        from app.services.report_data_generation.router import ReportRouterMixin
        db = MagicMock()
        result = ReportRouterMixin.generate_report_by_type(db, report_type="DEPT_WEEKLY")
        assert "error" in result

    def test_generate_report_unknown_type(self):
        from app.services.report_data_generation.router import ReportRouterMixin
        db = MagicMock()
        result = ReportRouterMixin.generate_report_by_type(db, report_type="UNKNOWN_TYPE")
        assert "error" in result or isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────
# 33. bonus/team – TeamBonusCalculator
# ─────────────────────────────────────────────────────────────────
class TestTeamBonusCalculator:
    def test_calculate_zero_coefficient(self):
        from app.services.bonus.team import TeamBonusCalculator
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.side_effect = lambda x: None
        calc = TeamBonusCalculator(db)
        project = MagicMock()
        project.id = 1
        project.contract_amount = Decimal("100000")
        rule = MagicMock()
        rule.id = 1
        rule.coefficient = Decimal("0")
        result = calc.calculate(project, rule)
        assert result is not None

    def test_calculate_with_contributions(self):
        from app.services.bonus.team import TeamBonusCalculator
        db = MagicMock()
        contrib = MagicMock()
        contrib.user_id = 1
        contrib.hours_percentage = Decimal("50")
        db.query.return_value.filter.return_value.all.return_value = [contrib]
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.side_effect = lambda x: None
        calc = TeamBonusCalculator(db)
        project = MagicMock()
        project.id = 1
        project.contract_amount = Decimal("100000")
        rule = MagicMock()
        rule.id = 1
        rule.coefficient = Decimal("5")
        result = calc.calculate(project, rule)
        assert result is not None


# ─────────────────────────────────────────────────────────────────
# 34. presale_ai_export_service – PresaleAIExportService
# ─────────────────────────────────────────────────────────────────
class TestPresaleAIExportService:
    def test_export_to_pdf_not_found(self):
        from app.services.presale_ai_export_service import PresaleAIExportService
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAIExportService(db)
        with pytest.raises(ValueError, match="not found"):
            svc.export_to_pdf(solution_id=999)

    def test_export_to_pdf_success(self, tmp_path):
        from app.services.presale_ai_export_service import PresaleAIExportService
        db = MagicMock()
        solution = MagicMock()
        solution.solution_description = "Test solution"
        solution.architecture_diagram = "diagram data"
        solution.bom_list = [{"item": "part1"}]
        db.query.return_value.filter_by.return_value.first.return_value = solution
        svc = PresaleAIExportService(db)
        svc.export_dir = str(tmp_path)
        filepath = svc.export_to_pdf(solution_id=1)
        assert filepath.endswith(".pdf")
        import os
        assert os.path.exists(filepath)


# ─────────────────────────────────────────────────────────────────
# 35. lead_priority_scoring/ranking – RankingMixin
# ─────────────────────────────────────────────────────────────────
class TestLeadPriorityRanking:
    def _make_mixin(self, db):
        from app.services.lead_priority_scoring.ranking import RankingMixin
        obj = RankingMixin.__new__(RankingMixin)
        obj.db = db
        return obj

    def test_get_priority_ranking_no_leads(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.get_priority_ranking(entity_type="lead")
        assert result == []

    def test_get_priority_ranking_no_opps(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.get_priority_ranking(entity_type="opportunity")
        assert result == []


# ─────────────────────────────────────────────────────────────────
# 36. sales_reminder/base
# ─────────────────────────────────────────────────────────────────
class TestSalesReminderBase:
    def test_find_users_by_role_empty(self):
        from app.services.sales_reminder.base import find_users_by_role
        db = MagicMock()
        result = find_users_by_role(db, role_name="")
        assert result == []

    def test_find_users_by_department_empty(self):
        from app.services.sales_reminder.base import find_users_by_department
        db = MagicMock()
        result = find_users_by_department(db, dept_name="")
        assert result == []

    def test_find_users_by_role_no_roles(self):
        from app.services.sales_reminder.base import find_users_by_role
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = find_users_by_role(db, role_name="SALES_MANAGER")
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────
# 37. resource_waste_analysis/investment – InvestmentAnalysisMixin
# ─────────────────────────────────────────────────────────────────
class TestInvestmentAnalysisMixin:
    def _make_mixin(self, db):
        from app.services.resource_waste_analysis.investment import InvestmentAnalysisMixin
        obj = InvestmentAnalysisMixin.__new__(InvestmentAnalysisMixin)
        obj.db = db
        obj.hourly_rate = Decimal("100")
        return obj

    def test_get_lead_resource_investment_no_logs(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        mixin = self._make_mixin(db)
        result = mixin.get_lead_resource_investment(project_id=1)
        assert result["total_hours"] == 0.0
        assert result["engineer_count"] == 0

    def test_get_lead_resource_investment_with_logs(self):
        db = MagicMock()
        log = MagicMock()
        log.work_hours = 8.0
        log.employee_id = 1
        log.work_date = date(2025, 3, 1)
        log.work_type = "design"
        db.query.return_value.filter.return_value.all.return_value = [log]
        # User query for engineer details
        user = MagicMock()
        user.name = "Alice"
        db.query.return_value.filter.return_value.first.return_value = user
        mixin = self._make_mixin(db)
        result = mixin.get_lead_resource_investment(project_id=1)
        assert result["total_hours"] == 8.0


# ─────────────────────────────────────────────────────────────────
# 38. report_data_generation/core – ReportDataGenerationCore
# ─────────────────────────────────────────────────────────────────
class TestReportDataGenerationCore:
    def test_get_allowed_reports_known_role(self):
        from app.services.report_data_generation.core import ReportDataGenerationCore
        reports = ReportDataGenerationCore.get_allowed_reports("PROJECT_MANAGER")
        assert "PROJECT_WEEKLY" in reports
        assert "PROJECT_MONTHLY" in reports

    def test_get_allowed_reports_unknown_role(self):
        from app.services.report_data_generation.core import ReportDataGenerationCore
        reports = ReportDataGenerationCore.get_allowed_reports("UNKNOWN_ROLE")
        assert reports == []

    def test_check_permission_superuser(self):
        from app.services.report_data_generation.core import ReportDataGenerationCore
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = True
        result = ReportDataGenerationCore.check_permission(db, user, "ANY_REPORT")
        assert result is True

    def test_check_permission_no_roles(self):
        from app.services.report_data_generation.core import ReportDataGenerationCore
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = False
        user.id = 1
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = ReportDataGenerationCore.check_permission(db, user, "PROJECT_WEEKLY")
        assert result is False


# ─────────────────────────────────────────────────────────────────
# 39. glm_service wrapper
# ─────────────────────────────────────────────────────────────────
class TestGlmServiceWrapper:
    def test_get_glm_service_singleton(self):
        from app.services import glm_service as glm_module
        glm_module._glm_service = None  # Reset singleton
        with patch("app.services.glm_service.GLMService") as MockGLM:
            mock_instance = MagicMock()
            MockGLM.return_value = mock_instance
            svc1 = glm_module.get_glm_service()
            svc2 = glm_module.get_glm_service()
        assert svc1 is svc2

    @pytest.mark.asyncio
    async def test_call_glm_api_unavailable(self):
        from app.services import glm_service as glm_module
        glm_module._glm_service = None
        with patch("app.services.glm_service.GLMService") as MockGLM:
            mock_svc = MagicMock()
            mock_svc.is_available.return_value = False
            MockGLM.return_value = mock_svc
            result = await glm_module.call_glm_api("hello")
        assert isinstance(result, str)
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────
# 40. resource_allocation_service/allocation
# ─────────────────────────────────────────────────────────────────
class TestResourceAllocation:
    def test_allocate_resources_with_conflicts(self):
        from app.services.resource_allocation_service.allocation import allocate_resources
        with patch("app.services.resource_allocation_service.allocation.detect_resource_conflicts",
                   return_value=[{"type": "overlap"}]):
            db = MagicMock()
            result = allocate_resources(
                db, project_id=1, machine_id=None,
                suggested_start_date=date(2025, 3, 1),
                suggested_end_date=date(2025, 3, 31)
            )
        assert result["can_allocate"] is False
        assert len(result["conflicts"]) > 0

    def test_allocate_resources_no_conflicts(self):
        from app.services.resource_allocation_service.allocation import allocate_resources
        with patch("app.services.resource_allocation_service.allocation.detect_resource_conflicts",
                   return_value=[]), \
             patch("app.services.resource_allocation_service.allocation.find_available_workstations",
                   return_value=[{"id": 1}]), \
             patch("app.services.resource_allocation_service.allocation.find_available_workers",
                   return_value=[{"id": 10}]):
            db = MagicMock()
            result = allocate_resources(
                db, project_id=1, machine_id=None,
                suggested_start_date=date(2025, 3, 1),
                suggested_end_date=date(2025, 3, 31)
            )
        assert result["can_allocate"] is True
        assert len(result["workstations"]) == 1


# ─────────────────────────────────────────────────────────────────
# 41. bonus/acceptance – AcceptanceBonusTrigger
# ─────────────────────────────────────────────────────────────────
class TestAcceptanceBonusTrigger:
    def test_trigger_calculation_empty_rules(self):
        from app.services.bonus.acceptance import AcceptanceBonusTrigger
        db = MagicMock()
        trigger = AcceptanceBonusTrigger(db)
        project = MagicMock()
        project.id = 1
        acceptance_order = MagicMock()
        with patch("app.services.bonus.acceptance.get_active_rules", return_value=[]), \
             patch("app.services.bonus.acceptance.calculate_sales_bonus", return_value=None), \
             patch("app.services.bonus.acceptance.calculate_presale_bonus", return_value=None), \
             patch("app.services.bonus.acceptance.calculate_project_bonus", return_value=None):
            result = trigger.trigger_calculation(project, acceptance_order)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_trigger_calculation_with_allocations(self):
        from app.services.bonus.acceptance import AcceptanceBonusTrigger
        db = MagicMock()
        trigger = AcceptanceBonusTrigger(db)
        project = MagicMock()
        project.id = 1
        acceptance_order = MagicMock()
        mock_alloc = MagicMock()
        with patch("app.services.bonus.acceptance.get_active_rules", return_value=[MagicMock()]), \
             patch("app.services.bonus.acceptance.calculate_sales_bonus", return_value=mock_alloc), \
             patch("app.services.bonus.acceptance.calculate_presale_bonus", return_value=None), \
             patch("app.services.bonus.acceptance.calculate_project_bonus", return_value=mock_alloc):
            result = trigger.trigger_calculation(project, acceptance_order)
        assert len(result) == 2


# ─────────────────────────────────────────────────────────────────
# 42. strategy/decomposition/stats
# ─────────────────────────────────────────────────────────────────
class TestDecompositionStats:
    def test_get_decomposition_stats_zero_counts(self):
        from app.services.strategy.decomposition.stats import get_decomposition_stats
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 0
        result = get_decomposition_stats(db, strategy_id=1, year=2025)
        assert isinstance(result, dict)
        assert result.get("csf_count", 0) == 0

    def test_get_decomposition_stats_default_year(self):
        from app.services.strategy.decomposition.stats import get_decomposition_stats
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 5
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 10
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 3
        result = get_decomposition_stats(db, strategy_id=1)
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────
# 43. bonus/base – BonusCalculatorBase (check_trigger_condition)
# ─────────────────────────────────────────────────────────────────
class TestBonusCalculatorBase:
    def test_check_trigger_condition_no_condition(self):
        from app.services.bonus.base import BonusCalculatorBase
        db = MagicMock()
        calc = BonusCalculatorBase(db)
        rule = MagicMock()
        rule.trigger_condition = None
        result = calc.check_trigger_condition(rule, {})
        assert result is True

    def test_check_trigger_condition_performance_level_match(self):
        from app.services.bonus.base import BonusCalculatorBase
        db = MagicMock()
        calc = BonusCalculatorBase(db)
        rule = MagicMock()
        rule.trigger_condition = {"performance_level": "EXCELLENT"}
        perf_result = MagicMock()
        perf_result.level = "EXCELLENT"
        result = calc.check_trigger_condition(rule, {"performance_result": perf_result})
        assert result is True

    def test_check_trigger_condition_performance_level_mismatch(self):
        from app.services.bonus.base import BonusCalculatorBase
        db = MagicMock()
        calc = BonusCalculatorBase(db)
        rule = MagicMock()
        rule.trigger_condition = {"performance_level": "EXCELLENT"}
        perf_result = MagicMock()
        perf_result.level = "GOOD"
        result = calc.check_trigger_condition(rule, {"performance_result": perf_result})
        assert result is False

    def test_generate_calculation_code_format(self):
        from app.services.bonus.base import BonusCalculatorBase
        db = MagicMock()
        calc = BonusCalculatorBase(db)
        code = calc.generate_calculation_code()
        assert code.startswith("BC")
        assert len(code) > 10
