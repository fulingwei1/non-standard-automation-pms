# -*- coding: utf-8 -*-
"""Batch tests for remaining untested schema modules to boost coverage."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError


# ==================== management_rhythm ====================
class TestManagementRhythm:
    def test_rhythm_config_create(self):
        from app.schemas.management_rhythm import RhythmConfigCreate
        r = RhythmConfigCreate(rhythm_level="STRATEGIC", cycle_type="QUARTERLY", config_name="季度战略会")
        assert r.is_active == "ACTIVE"

    def test_rhythm_config_update(self):
        from app.schemas.management_rhythm import RhythmConfigUpdate
        r = RhythmConfigUpdate()
        assert r.config_name is None

    def test_rhythm_config_response(self):
        from app.schemas.management_rhythm import RhythmConfigResponse
        now = datetime.now()
        r = RhythmConfigResponse(
            id=1, rhythm_level="STRATEGIC", cycle_type="QUARTERLY",
            config_name="T", description=None, meeting_template=None,
            key_metrics=None, output_artifacts=None, is_active="ACTIVE",
            created_by=None, created_at=now, updated_at=now,
        )
        assert r.id == 1

    def test_strategic_meeting_create(self):
        from app.schemas.management_rhythm import StrategicMeetingCreate
        m = StrategicMeetingCreate(
            rhythm_level="STRATEGIC", cycle_type="QUARTERLY",
            meeting_name="Q1战略会",
            meeting_date=date(2024, 3, 15),
        )
        assert m.meeting_name == "Q1战略会"

    def test_strategic_meeting_update(self):
        from app.schemas.management_rhythm import StrategicMeetingUpdate
        m = StrategicMeetingUpdate()
        assert m.meeting_name is None

    def test_action_item_create(self):
        from app.schemas.management_rhythm import ActionItemCreate
        a = ActionItemCreate(
            meeting_id=1, action_description="完成方案",
            owner_id=1, due_date=date(2024, 7, 1),
        )
        assert a.action_description == "完成方案"

    def test_action_item_update(self):
        from app.schemas.management_rhythm import ActionItemUpdate
        a = ActionItemUpdate()
        assert a.action_description is None

    def test_rhythm_dashboard_response(self):
        from app.schemas.management_rhythm import RhythmDashboardResponse
        d = RhythmDashboardResponse(
            rhythm_level="STRATEGIC", cycle_type="QUARTERLY",
            current_cycle=None, key_metrics_snapshot=None,
            health_status="GREEN", last_meeting_date=None,
            next_meeting_date=None, meetings_count=5,
            completed_meetings_count=3, total_action_items=20,
            completed_action_items=15, overdue_action_items=2,
            completion_rate="75%", snapshot_date=date(2024, 6, 1),
        )
        assert d.rhythm_level == "STRATEGIC"

    def test_meeting_report_config_create(self):
        from app.schemas.management_rhythm import MeetingReportConfigCreate
        c = MeetingReportConfigCreate(
            config_name="月度报告", report_type="MONTHLY",
        )
        assert c.config_name == "月度报告"

    def test_report_metric_definition_create(self):
        from app.schemas.management_rhythm import ReportMetricDefinitionCreate
        m = ReportMetricDefinitionCreate(
            metric_code="M001", metric_name="营收",
            category="FINANCE", data_source="finance",
            calculation_type="SUM",
        )
        assert m.metric_code == "M001"

    def test_meeting_statistics_response(self):
        from app.schemas.management_rhythm import MeetingStatisticsResponse
        s = MeetingStatisticsResponse(
            total_meetings=10, completed_meetings=8,
            scheduled_meetings=1, cancelled_meetings=1,
            total_action_items=20, completed_action_items=15,
            overdue_action_items=2, completion_rate=75.0,
            by_level={"STRATEGIC": 5}, by_cycle={"QUARTERLY": 3},
        )
        assert s.total_meetings == 10

    def test_strategic_meeting_response(self):
        from app.schemas.management_rhythm import StrategicMeetingResponse
        now = datetime.now()
        r = StrategicMeetingResponse(
            id=1, rhythm_level="STRATEGIC", cycle_type="QUARTERLY",
            meeting_name="T", meeting_date=date(2024, 1, 1),
            status="PLANNED", created_at=now, updated_at=now,
            project_id=None, rhythm_config_id=1,
            meeting_type=None, start_time=None, end_time=None,
            location=None, organizer_id=None, organizer_name=None,
            attendees=None, agenda=None, minutes=None,
            decisions=None, strategic_context=None,
            strategic_structure=None, key_decisions=None,
            resource_allocation=None, metrics_snapshot=None,
            attachments=None, created_by=None,
        )
        assert r.id == 1


# ==================== resource_scheduling ====================
class TestResourceScheduling:
    def test_conflict_detection_base(self):
        from app.schemas.resource_scheduling import ResourceConflictDetectionBase
        c = ResourceConflictDetectionBase(
            conflict_code="C001", conflict_name="人员冲突",
            resource_id=1, resource_type="PERSON",
            project_a_id=1, project_b_id=2,
            overlap_start=date(2024, 1, 1),
            overlap_end=date(2024, 2, 1),
            total_allocation=Decimal("150"),
        )
        assert c.conflict_type == "PERSON"

    def test_conflict_detection_create(self):
        from app.schemas.resource_scheduling import ResourceConflictDetectionCreate
        c = ResourceConflictDetectionCreate(
            conflict_code="C001", conflict_name="冲突",
            resource_id=1, resource_type="PERSON",
            project_a_id=1, project_b_id=2,
            overlap_start=date(2024, 1, 1),
            overlap_end=date(2024, 2, 1),
            total_allocation=Decimal("150"),
        )
        assert c.conflict_code == "C001"

    def test_scheduling_suggestion_base(self):
        from app.schemas.resource_scheduling import ResourceSchedulingSuggestionBase
        s = ResourceSchedulingSuggestionBase(
            conflict_id=1, suggestion_code="S001",
            suggestion_name="调整建议",
            solution_type="RESCHEDULE",
            adjustments="调整项目B时间",
            ai_score=Decimal("85"),
        )
        assert s.solution_type == "RESCHEDULE"

    def test_demand_forecast_base(self):
        from app.schemas.resource_scheduling import ResourceDemandForecastBase
        f = ResourceDemandForecastBase(
            forecast_code="F001", forecast_name="Q1预测",
            forecast_period="2024-Q1", resource_type="PERSON",
            forecast_start_date=date(2024, 1, 1),
            forecast_end_date=date(2024, 3, 31),
        )
        assert f.resource_type == "PERSON"

    def test_utilization_analysis_base(self):
        from app.schemas.resource_scheduling import ResourceUtilizationAnalysisBase
        u = ResourceUtilizationAnalysisBase(
            analysis_code="U001", analysis_name="利用率分析",
            analysis_period="2024-Q1", resource_id=1,
            resource_type="PERSON",
            period_start_date=date(2024, 1, 1),
            period_end_date=date(2024, 3, 31),
        )
        assert u.resource_type == "PERSON"

    def test_conflict_detection_request(self):
        from app.schemas.resource_scheduling import ConflictDetectionRequest
        r = ConflictDetectionRequest()
        assert r is not None

    def test_dashboard_summary(self):
        from app.schemas.resource_scheduling import DashboardSummary
        d = DashboardSummary(
            total_conflicts=5, critical_conflicts=2,
            unresolved_conflicts=3, total_suggestions=10,
            pending_suggestions=4, implemented_suggestions=6,
            idle_resources=2, overloaded_resources=1,
            avg_utilization=Decimal("75"),
            forecasts_count=3, critical_gaps=1, hiring_needed=2,
        )
        assert d.total_conflicts == 5

    def test_ai_scheduling_suggestion_request(self):
        from app.schemas.resource_scheduling import AISchedulingSuggestionRequest
        r = AISchedulingSuggestionRequest(conflict_id=1)
        assert r.conflict_id == 1

    def test_forecast_request(self):
        from app.schemas.resource_scheduling import ForecastRequest
        r = ForecastRequest(forecast_period="2024-Q1")
        assert r.forecast_period == "2024-Q1"


# ==================== staff_matching ====================
class TestStaffMatching:
    def test_tag_dict_base(self):
        from app.schemas.staff_matching import TagDictBase
        t = TagDictBase(tag_code="SKILL001", tag_name="Python", tag_type="SKILL")
        assert t.weight == 1.0

    def test_tag_dict_create(self):
        from app.schemas.staff_matching import TagDictCreate
        t = TagDictCreate(tag_code="S001", tag_name="PLC", tag_type="SKILL")
        assert t.is_required is False

    def test_tag_dict_update(self):
        from app.schemas.staff_matching import TagDictUpdate
        t = TagDictUpdate()
        assert t.tag_name is None

    def test_employee_tag_evaluation_create(self):
        from app.schemas.staff_matching import EmployeeTagEvaluationCreate
        e = EmployeeTagEvaluationCreate(
            employee_id=1, tag_id=1, score=4,
            evaluate_date=date(2024, 6, 1),
        )
        assert e.score == 4

    def test_employee_profile_update(self):
        from app.schemas.staff_matching import EmployeeProfileUpdate
        p = EmployeeProfileUpdate()
        assert p is not None

    def test_project_performance_create(self):
        from app.schemas.staff_matching import ProjectPerformanceCreate
        p = ProjectPerformanceCreate(
            employee_id=1, project_id=1,
            role_code="ENGINEER",
        )
        assert p.role_code == "ENGINEER"

    def test_staffing_need_create(self):
        from app.schemas.staff_matching import StaffingNeedCreate, SkillRequirement
        s = StaffingNeedCreate(
            project_id=1, role_code="ENGINEER",
            required_skills=[SkillRequirement(tag_id=1)],
        )
        assert s.project_id == 1

    def test_matching_request(self):
        from app.schemas.staff_matching import MatchingRequest
        m = MatchingRequest(staffing_need_id=1)
        assert m.staffing_need_id == 1

    def test_matching_accept_request(self):
        from app.schemas.staff_matching import MatchingAcceptRequest
        m = MatchingAcceptRequest(matching_log_id=1, staffing_need_id=1, employee_id=1)
        assert m.employee_id == 1

    def test_staffing_dashboard(self):
        from app.schemas.staff_matching import StaffingDashboard, MatchingStatistics
        d = StaffingDashboard(
            open_needs=10, matching_needs=5,
            filled_needs=3, total_headcount_needed=20,
            total_headcount_filled=8,
            needs_by_priority={"HIGH": 5},
            matching_stats=MatchingStatistics(
                total_requests=20, total_candidates_matched=50,
                accepted_count=15, rejected_count=5, pending_count=0,
            ),
            recent_matches=[],
        )
        assert d.open_needs == 10

    def test_tag_statistics(self):
        from app.schemas.staff_matching import TagStatistics
        s = TagStatistics(
            tag_type="SKILL", total_count=100,
            active_count=80, used_count=50,
        )
        assert s.total_count == 100

    def test_staffing_need_update(self):
        from app.schemas.staff_matching import StaffingNeedUpdate
        u = StaffingNeedUpdate()
        assert u is not None


# ==================== pmo ====================
class TestPmo:
    def test_initiation_create(self):
        from app.schemas.pmo import InitiationCreate
        i = InitiationCreate(
            project_name="项目A", project_type="STANDARD",
            customer_name="客户A", estimated_amount=Decimal("100000"),
        )
        assert i.project_name == "项目A"

    def test_initiation_update(self):
        from app.schemas.pmo import InitiationUpdate
        i = InitiationUpdate()
        assert i is not None

    def test_risk_create(self):
        from app.schemas.pmo import RiskCreate
        r = RiskCreate(
            risk_category="TECHNICAL", risk_name="技术风险",
        )
        assert r.risk_category == "TECHNICAL"

    def test_closure_create(self):
        from app.schemas.pmo import ClosureCreate
        c = ClosureCreate()
        assert c.acceptance_date is None

    def test_meeting_create(self):
        from app.schemas.pmo import MeetingCreate
        m = MeetingCreate(
            meeting_type="KICKOFF", meeting_name="启动会",
            meeting_date=date(2024, 6, 1),
        )
        assert m.meeting_type == "KICKOFF"

    def test_dashboard_summary(self):
        from app.schemas.pmo import DashboardSummary
        d = DashboardSummary(
            total_projects=10, active_projects=8,
            risk_projects=2, delayed_projects=1,
        )
        assert d.total_projects == 10

    def test_initiation_approve_request(self):
        from app.schemas.pmo import InitiationApproveRequest
        r = InitiationApproveRequest(review_result="APPROVED")
        assert r.review_result == "APPROVED"

    def test_risk_response_request(self):
        from app.schemas.pmo import RiskResponseRequest
        r = RiskResponseRequest(response_strategy="MITIGATE", response_plan="制定应急预案")
        assert r.response_strategy == "MITIGATE"


# ==================== rd_project ====================
class TestRdProject:
    def test_category_create(self):
        from app.schemas.rd_project import RdProjectCategoryCreate
        c = RdProjectCategoryCreate(category_code="RD001", category_name="新产品研发", category_type="PRODUCT")
        assert c.category_code == "RD001"

    def test_project_create(self):
        from app.schemas.rd_project import RdProjectCreate
        p = RdProjectCreate(
            project_name="新产品A", category_type="PRODUCT",
            initiation_date=date(2024, 1, 1),
        )
        assert p.project_name == "新产品A"

    def test_project_update(self):
        from app.schemas.rd_project import RdProjectUpdate
        p = RdProjectUpdate()
        assert p is not None

    def test_cost_create(self):
        from app.schemas.rd_project import RdCostCreate
        c = RdCostCreate(
            rd_project_id=1, cost_type_id=1,
            cost_amount=Decimal("5000"), cost_date=date(2024, 6, 1),
        )
        assert c.cost_amount == Decimal("5000")

    def test_cost_update(self):
        from app.schemas.rd_project import RdCostUpdate
        c = RdCostUpdate()
        assert c is not None

    def test_category_update(self):
        from app.schemas.rd_project import RdProjectCategoryUpdate
        u = RdProjectCategoryUpdate()
        assert u is not None

    def test_cost_type_create(self):
        from app.schemas.rd_project import RdCostTypeCreate
        c = RdCostTypeCreate(type_code="RDC001", type_name="人工成本", category="LABOR")
        assert c.type_code == "RDC001"

    def test_approve_request(self):
        from app.schemas.rd_project import RdProjectApproveRequest
        r = RdProjectApproveRequest(approved=True)
        assert r.approved is True


# ==================== purchase_intelligence ====================
class TestPurchaseIntelligence:
    def test_suggestion_create(self):
        from app.schemas.purchase_intelligence import PurchaseSuggestionCreate
        s = PurchaseSuggestionCreate(
            material_id=1,
            suggested_qty=Decimal("100"),
            source_type="SAFETY_STOCK",
        )
        assert s.suggested_qty == Decimal("100")

    def test_suggestion_update(self):
        from app.schemas.purchase_intelligence import PurchaseSuggestionUpdate
        s = PurchaseSuggestionUpdate()
        assert s is not None

    def test_suggestion_approve(self):
        from app.schemas.purchase_intelligence import PurchaseSuggestionApprove
        a = PurchaseSuggestionApprove(approved=True)
        assert a.approved is True

    def test_quotation_create(self):
        from app.schemas.purchase_intelligence import SupplierQuotationCreate
        q = SupplierQuotationCreate(
            material_id=1, supplier_id=1,
            unit_price=Decimal("5.5"),
            valid_from=date(2024, 1, 1),
            valid_to=date(2024, 12, 31),
        )
        assert q.unit_price == Decimal("5.5")

    def test_quotation_compare_request(self):
        from app.schemas.purchase_intelligence import QuotationCompareRequest
        r = QuotationCompareRequest(material_id=1)
        assert r.material_id == 1

    def test_supplier_performance_calculate(self):
        from app.schemas.purchase_intelligence import SupplierPerformanceCalculate
        p = SupplierPerformanceCalculate(supplier_id=1, evaluation_period="2024-Q1")
        assert p.supplier_id == 1

    def test_order_tracking_create(self):
        from app.schemas.purchase_intelligence import PurchaseOrderTrackingCreate
        t = PurchaseOrderTrackingCreate(
            order_id=1, event_type="CREATED",
        )
        assert t.order_id == 1

    def test_quotation_update(self):
        from app.schemas.purchase_intelligence import SupplierQuotationUpdate
        u = SupplierQuotationUpdate()
        assert u is not None

    def test_create_order_from_suggestion(self):
        from app.schemas.purchase_intelligence import CreateOrderFromSuggestionRequest
        r = CreateOrderFromSuggestionRequest(supplier_id=1)
        assert r.supplier_id == 1


# ==================== shortage_smart ====================
class TestShortageSmart:
    def test_shortage_alert_base(self):
        from app.schemas.shortage_smart import ShortageAlertBase
        a = ShortageAlertBase(
            project_id=1, material_id=1,
            required_qty=Decimal("100"),
            required_date=date(2024, 6, 1),
        )
        assert a.required_qty == Decimal("100")

    def test_shortage_alert_create(self):
        from app.schemas.shortage_smart import ShortageAlertCreate
        a = ShortageAlertCreate(
            project_id=1, material_id=1,
            required_qty=Decimal("100"),
            required_date=date(2024, 6, 1),
        )
        assert a is not None

    def test_scan_shortage_request(self):
        from app.schemas.shortage_smart import ScanShortageRequest
        r = ScanShortageRequest()
        assert r is not None

    def test_resolve_alert_request(self):
        from app.schemas.shortage_smart import ResolveAlertRequest
        r = ResolveAlertRequest(resolution_type="PURCHASE")
        assert r.resolution_type == "PURCHASE"

    def test_handling_plan_base(self):
        from app.schemas.shortage_smart import HandlingPlanBase
        p = HandlingPlanBase(
            alert_id=1, solution_type="PURCHASE", solution_name="紧急采购",
        )
        assert p.solution_name == "紧急采购"

    def test_demand_forecast_request(self):
        from app.schemas.shortage_smart import DemandForecastRequest
        r = DemandForecastRequest(material_id=1)
        assert r.material_id == 1

    def test_notification_subscribe_request(self):
        from app.schemas.shortage_smart import NotificationSubscribeRequest
        r = NotificationSubscribeRequest(alert_levels=["HIGH", "CRITICAL"])
        assert len(r.alert_levels) == 2

    def test_validate_forecast_request(self):
        from app.schemas.shortage_smart import ValidateForecastRequest
        r = ValidateForecastRequest(actual_demand=Decimal("100"))
        assert r.actual_demand == Decimal("100")


# ==================== sales_target ====================
class TestSalesTarget:
    def test_target_base(self):
        from app.schemas.sales_target import SalesTargetV2Base
        t = SalesTargetV2Base(
            target_period="year",
            target_year=2024,
            target_type="company",
        )
        assert t.sales_target == 0

    def test_target_update(self):
        from app.schemas.sales_target import SalesTargetV2Update
        t = SalesTargetV2Update()
        assert t is not None

    def test_target_breakdown_request(self):
        from app.schemas.sales_target import TargetBreakdownRequest
        r = TargetBreakdownRequest(breakdown_items=[])
        assert r.breakdown_items == []

    def test_auto_breakdown_request(self):
        from app.schemas.sales_target import AutoBreakdownRequest
        r = AutoBreakdownRequest(breakdown_method="EQUAL", target_ids=[1, 2])
        assert r.breakdown_method == "EQUAL"

    def test_target_response(self):
        from app.schemas.sales_target import SalesTargetV2Response
        now = datetime.now()
        r = SalesTargetV2Response(
            id=1, target_period="year", target_year=2024,
            target_type="company",
            actual_sales=Decimal("0"), actual_payment=Decimal("0"),
            actual_new_customers=0, actual_leads=0,
            actual_opportunities=0, actual_deals=0,
            completion_rate=Decimal("0"),
            parent_target_id=None, created_by=None,
            created_at=now, updated_at=now,
        )
        assert r.id == 1

    def test_target_breakdown_item(self):
        from app.schemas.sales_target import TargetBreakdownItem
        i = TargetBreakdownItem(
            target_type="team", team_id=1,
            sales_target=Decimal("500000"),
        )
        assert i.target_type == "team"


# ==================== standard_cost ====================
class TestStandardCost:
    def test_create(self):
        from app.schemas.standard_cost import StandardCostCreate
        c = StandardCostCreate(
            cost_code="SC001", cost_name="工时成本",
            cost_category="LABOR", unit="小时",
            standard_cost=Decimal("150"),
            cost_source="MANUAL",
            effective_date=date(2024, 1, 1),
        )
        assert c.standard_cost == Decimal("150")

    def test_update(self):
        from app.schemas.standard_cost import StandardCostUpdate
        u = StandardCostUpdate()
        assert u is not None

    def test_search_request(self):
        from app.schemas.standard_cost import StandardCostSearchRequest
        s = StandardCostSearchRequest()
        assert s is not None

    def test_apply_request(self):
        from app.schemas.standard_cost import ApplyStandardCostRequest
        a = ApplyStandardCostRequest(
            project_id=1,
            cost_items=[{"cost_id": 1, "quantity": 10}],
            budget_name="预算",
        )
        assert a.project_id == 1

    def test_import_row(self):
        from app.schemas.standard_cost import StandardCostImportRow
        r = StandardCostImportRow(
            cost_code="SC001", cost_name="T",
            cost_category="LABOR", unit="小时",
            standard_cost=Decimal("100"),
            cost_source="MANUAL",
            effective_date="2024-01-01",
        )
        assert r.cost_code == "SC001"

    def test_comparison_request(self):
        from app.schemas.standard_cost import ProjectCostComparisonRequest
        r = ProjectCostComparisonRequest(project_id=1)
        assert r.project_id == 1


# ==================== task_center ====================
class TestTaskCenter:
    def test_task_overview(self):
        from app.schemas.task_center import TaskOverviewResponse
        t = TaskOverviewResponse(
            total_tasks=10, pending_tasks=3,
            in_progress_tasks=5, overdue_tasks=2,
            this_week_tasks=4, urgent_tasks=1,
        )
        assert t.total_tasks == 10

    def test_task_unified_create(self):
        from app.schemas.task_center import TaskUnifiedCreate
        t = TaskUnifiedCreate(title="新任务", task_type="GENERAL")
        assert t.title == "新任务"

    def test_task_unified_update(self):
        from app.schemas.task_center import TaskUnifiedUpdate
        t = TaskUnifiedUpdate()
        assert t is not None

    def test_batch_task_operation(self):
        from app.schemas.task_center import BatchTaskOperation
        b = BatchTaskOperation(task_ids=[1, 2], operation="COMPLETE")
        assert len(b.task_ids) == 2

    def test_task_progress_update(self):
        from app.schemas.task_center import TaskProgressUpdate
        t = TaskProgressUpdate(progress=80)
        assert t.progress == 80

    def test_task_transfer_request(self):
        from app.schemas.task_center import TaskTransferRequest
        r = TaskTransferRequest(target_user_id=2, transfer_reason="休假")
        assert r.target_user_id == 2

    def test_task_comment_create(self):
        from app.schemas.task_center import TaskCommentCreate
        c = TaskCommentCreate(content="进度正常")
        assert c.content == "进度正常"


# ==================== timesheet ====================
class TestTimesheet:
    def test_create(self):
        from app.schemas.timesheet import TimesheetCreate
        t = TimesheetCreate(
            project_id=1, work_date=date(2024, 6, 1),
            work_hours=Decimal("8"), description="开发",
        )
        assert t.work_hours == Decimal("8")

    def test_update(self):
        from app.schemas.timesheet import TimesheetUpdate
        t = TimesheetUpdate()
        assert t is not None

    def test_batch_create(self):
        from app.schemas.timesheet import TimesheetBatchCreate
        b = TimesheetBatchCreate(timesheets=[])
        assert b.timesheets == []

    def test_response(self):
        from app.schemas.timesheet import TimesheetResponse
        r = TimesheetResponse(
            id=1, user_id=1, work_date=date(2024, 6, 1),
            work_hours=Decimal("8"), work_type="NORMAL",
            status="SUBMITTED",
        )
        assert r.id == 1


# ==================== session ====================
class TestSession:
    def test_session_response(self):
        from app.schemas.session import SessionResponse
        now = datetime.now()
        s = SessionResponse(
            id=1, user_id=1,
            access_token_jti="abc", refresh_token_jti="def",
            is_active=True, login_at=now,
            last_activity_at=now, expires_at=now,
            is_suspicious=False, risk_score=0,
        )
        assert s.user_id == 1

    def test_device_info(self):
        from app.schemas.session import DeviceInfo
        d = DeviceInfo()
        assert d is not None

    def test_refresh_token_request(self):
        from app.schemas.session import RefreshTokenRequest
        r = RefreshTokenRequest(refresh_token="abc123")
        assert r.refresh_token == "abc123"

    def test_logout_request(self):
        from app.schemas.session import LogoutRequest
        r = LogoutRequest()
        assert r is not None

    def test_session_list_response(self):
        from app.schemas.session import SessionListResponse
        r = SessionListResponse(sessions=[], total=0, active_count=0)
        assert r.total == 0

    def test_revoke_session_request(self):
        from app.schemas.session import RevokeSessionRequest
        r = RevokeSessionRequest(session_id=1)
        assert r.session_id == 1

    def test_refresh_token_response(self):
        from app.schemas.session import RefreshTokenResponse
        r = RefreshTokenResponse(access_token="tok", token_type="bearer", expires_in=3600)
        assert r.access_token == "tok"


# ==================== work_log ====================
class TestWorkLog:
    def test_create(self):
        from app.schemas.work_log import WorkLogCreate
        w = WorkLogCreate(work_date=date(2024, 6, 1), content="今日完成设计")
        assert w.content == "今日完成设计"

    def test_update(self):
        from app.schemas.work_log import WorkLogUpdate
        w = WorkLogUpdate()
        assert w is not None

    def test_config_create(self):
        from app.schemas.work_log import WorkLogConfigCreate
        c = WorkLogConfigCreate()
        assert c is not None

    def test_config_update(self):
        from app.schemas.work_log import WorkLogConfigUpdate
        u = WorkLogConfigUpdate()
        assert u is not None

    def test_mention_response(self):
        from app.schemas.work_log import MentionResponse
        m = MentionResponse(id=1, mention_type="PROJECT", mention_id=1, mention_name="P1")
        assert m.mention_type == "PROJECT"

    def test_mention_options_response(self):
        from app.schemas.work_log import MentionOptionsResponse
        r = MentionOptionsResponse(projects=[], machines=[], users=[])
        assert r.projects == []


# ==================== workload ====================
class TestWorkload:
    def test_user_workload_summary(self):
        from app.schemas.workload import UserWorkloadSummary
        w = UserWorkloadSummary(
            total_assigned_hours=160.0,
            standard_hours=160.0,
            allocation_rate=100.0,
            actual_hours=140.0,
            efficiency=87.5,
        )
        assert w.allocation_rate == 100.0

    def test_team_workload_item(self):
        from app.schemas.workload import TeamWorkloadItem
        t = TeamWorkloadItem(
            user_id=1, user_name="张三",
            assigned_hours=Decimal("120"),
            standard_hours=Decimal("160"),
            allocation_rate=Decimal("75"),
            task_count=5,
        )
        assert t.user_name == "张三"

    def test_project_workload_item(self):
        from app.schemas.workload import ProjectWorkloadItem
        p = ProjectWorkloadItem(
            project_id=1, assigned_hours=Decimal("80"),
            actual_hours=Decimal("60"), task_count=3,
        )
        assert p.project_id == 1

    def test_daily_workload_item(self):
        from app.schemas.workload import DailyWorkloadItem
        d = DailyWorkloadItem(
            date=date(2024, 6, 1),
            assigned=Decimal("8"), actual=Decimal("7"),
        )
        assert d.assigned == Decimal("8")

    def test_dashboard_summary(self):
        from app.schemas.workload import WorkloadDashboardSummary
        d = WorkloadDashboardSummary(
            total_users=50, overloaded_users=5,
            normal_users=40, underloaded_users=5,
            total_assigned_hours=Decimal("8000"),
            total_actual_hours=Decimal("7000"),
            average_allocation_rate=Decimal("87.5"),
        )
        assert d.total_users == 50


# ==================== sla ====================
class TestSla:
    def test_sla_policy_create(self):
        from app.schemas.sla import SLAPolicyCreate
        s = SLAPolicyCreate(
            policy_name="标准SLA", policy_code="SLA001",
            response_time_hours=4, resolve_time_hours=24,
        )
        assert s.response_time_hours == 4

    def test_sla_policy_update(self):
        from app.schemas.sla import SLAPolicyUpdate
        s = SLAPolicyUpdate()
        assert s is not None

    def test_sla_statistics(self):
        from app.schemas.sla import SLAStatisticsResponse
        s = SLAStatisticsResponse(
            total_tickets=100, monitored_tickets=80,
            response_on_time=70, response_overdue=10,
            response_warning=5, resolve_on_time=60,
            resolve_overdue=15, resolve_warning=5,
            response_rate=Decimal("87.5"), resolve_rate=Decimal("75"),
        )
        assert s.total_tickets == 100


# ==================== scheduler_config ====================
class TestSchedulerConfig:
    def test_create_base(self):
        from app.schemas.scheduler_config import SchedulerTaskConfigBase
        c = SchedulerTaskConfigBase(
            task_id="task1", task_name="daily_report",
            module="reports", callable_name="generate",
            cron_config={"hour": 9, "minute": 0},
        )
        assert c.task_name == "daily_report"

    def test_update(self):
        from app.schemas.scheduler_config import SchedulerTaskConfigUpdate
        u = SchedulerTaskConfigUpdate()
        assert u is not None

    def test_sync_request(self):
        from app.schemas.scheduler_config import SchedulerTaskConfigSyncRequest
        r = SchedulerTaskConfigSyncRequest()
        assert r is not None


# ==================== timesheet_reminder ====================
class TestTimesheetReminder:
    def test_reminder_config_create(self):
        from app.schemas.timesheet_reminder import ReminderConfigCreate
        c = ReminderConfigCreate(
            rule_code="R001", rule_name="日报提醒",
            reminder_type="DAILY",
            rule_parameters={"time": "18:00"},
        )
        assert c.reminder_type == "DAILY"

    def test_reminder_config_update(self):
        from app.schemas.timesheet_reminder import ReminderConfigUpdate
        u = ReminderConfigUpdate()
        assert u is not None

    def test_reminder_dismiss_request(self):
        from app.schemas.timesheet_reminder import ReminderDismissRequest
        r = ReminderDismissRequest()
        assert r is not None

    def test_anomaly_resolve_request(self):
        from app.schemas.timesheet_reminder import AnomalyResolveRequest
        r = AnomalyResolveRequest(resolution_note="已补填")
        assert r.resolution_note == "已补填"

    def test_reminder_statistics(self):
        from app.schemas.timesheet_reminder import ReminderStatistics
        s = ReminderStatistics(
            total_reminders=100, pending_reminders=20,
            sent_reminders=70, dismissed_reminders=10,
            resolved_reminders=5,
            by_type={"DAILY": 80}, by_priority={"HIGH": 20},
            recent_reminders=[],
        )
        assert s.total_reminders == 100

    def test_anomaly_statistics(self):
        from app.schemas.timesheet_reminder import AnomalyStatistics
        s = AnomalyStatistics(
            total_anomalies=50, unresolved_anomalies=10,
            resolved_anomalies=40,
            by_type={"MISSING": 30}, by_severity={"HIGH": 10},
            recent_anomalies=[],
        )
        assert s.total_anomalies == 50


# ==================== shortage ====================
class TestShortage:
    def test_shortage_report_create(self):
        from app.schemas.shortage import ShortageReportCreate
        r = ShortageReportCreate(
            project_id=1, material_id=1,
            required_qty=Decimal("100"),
            shortage_qty=Decimal("50"),
        )
        assert r.shortage_qty == Decimal("50")

    def test_material_arrival_create(self):
        from app.schemas.shortage import MaterialArrivalCreate
        a = MaterialArrivalCreate(
            shortage_report_id=1, material_id=1,
            expected_qty=Decimal("50"),
            expected_date=date(2024, 7, 1),
        )
        assert a.expected_qty == Decimal("50")

    def test_material_substitution_create(self):
        from app.schemas.shortage import MaterialSubstitutionCreate
        s = MaterialSubstitutionCreate(
            shortage_report_id=1, project_id=1,
            original_material_id=1, substitute_material_id=2,
            original_qty=Decimal("100"), substitute_qty=Decimal("100"),
            substitution_reason="紧急替换",
        )
        assert s.substitution_reason == "紧急替换"

    def test_material_transfer_create(self):
        from app.schemas.shortage import MaterialTransferCreate
        t = MaterialTransferCreate(
            shortage_report_id=1, to_project_id=2,
            material_id=1, transfer_qty=Decimal("30"),
            transfer_reason="项目间调拨",
        )
        assert t.transfer_qty == Decimal("30")

    def test_arrival_followup_create(self):
        from app.schemas.shortage import ArrivalFollowUpCreate
        f = ArrivalFollowUpCreate(
            follow_up_type="PHONE", follow_up_note="已联系供应商",
        )
        assert f.follow_up_type == "PHONE"


# ==================== timesheet_analytics ====================
class TestTimesheetAnalytics:
    def test_query(self):
        from app.schemas.timesheet_analytics import TimesheetAnalyticsQuery
        q = TimesheetAnalyticsQuery(
            period_type="MONTHLY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert q.start_date == date(2024, 1, 1)

    def test_project_forecast_request(self):
        from app.schemas.timesheet_analytics import ProjectForecastRequest
        r = ProjectForecastRequest(project_id=1, project_name="P1")
        assert r.project_id == 1

    def test_completion_forecast_query(self):
        from app.schemas.timesheet_analytics import CompletionForecastQuery
        q = CompletionForecastQuery(project_id=1)
        assert q.project_id == 1

    def test_workload_alert_query(self):
        from app.schemas.timesheet_analytics import WorkloadAlertQuery
        q = WorkloadAlertQuery()
        assert q is not None

    def test_trend_chart_data(self):
        from app.schemas.timesheet_analytics import TrendChartData
        t = TrendChartData(labels=["Jan", "Feb"], datasets=[])
        assert len(t.labels) == 2

    def test_pie_chart_data(self):
        from app.schemas.timesheet_analytics import PieChartData
        p = PieChartData(labels=["A", "B"], values=[60, 40])
        assert sum(p.values) == 100

    def test_heatmap_data(self):
        from app.schemas.timesheet_analytics import HeatmapData
        h = HeatmapData(rows=["R1"], columns=["C1"], data=[[1]])
        assert h.data == [[1]]
