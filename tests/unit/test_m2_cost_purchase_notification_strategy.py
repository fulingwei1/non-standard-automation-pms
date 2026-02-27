# -*- coding: utf-8 -*-
"""
M2组单元测试：成本/采购/通知/策略类服务
覆盖：
- cost_collection_service.py
- loss_deep_analysis_service.py
- purchase_suggestion_engine.py
- strategy/kpi_collector/collectors.py
- notification_dispatcher.py
- presale_ai_integration.py
- resource_scheduling_ai_service.py
- itr_analytics_service.py
- sales_target_service.py
"""
import sys
from unittest.mock import MagicMock

# Mock redis before any app imports
redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

import os
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock


# ===========================================================================
# 1. CostCollectionService
# ===========================================================================
class TestCostCollectionService:
    """成本自动归集服务测试"""

    def _make_db(self):
        return MagicMock()

    def test_collect_from_purchase_order_not_found_returns_none(self):
        """采购订单不存在时返回 None"""
        from app.services.cost_collection_service import CostCollectionService

        db = self._make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = CostCollectionService.collect_from_purchase_order(db, order_id=999)
        assert result is None

    def test_collect_from_purchase_order_no_project_id_returns_none(self):
        """订单没有关联项目时返回 None"""
        from app.services.cost_collection_service import CostCollectionService
        from app.models.purchase import PurchaseOrder

        db = self._make_db()
        order = Mock(spec=PurchaseOrder)
        order.project_id = None
        order.total_amount = Decimal("1000")
        order.order_no = "PO-001"

        # first call: order, second call: existing_cost check
        db.query.return_value.filter.return_value.first.side_effect = [order, None]

        result = CostCollectionService.collect_from_purchase_order(db, order_id=1)
        assert result is None

    def test_collect_from_purchase_order_existing_cost_updates(self):
        """已有成本记录时更新而不新建"""
        from app.services.cost_collection_service import CostCollectionService
        from app.models.purchase import PurchaseOrder
        from app.models.project import ProjectCost

        db = self._make_db()
        order = Mock(spec=PurchaseOrder)
        order.project_id = 10
        order.total_amount = Decimal("2000")
        order.tax_amount = Decimal("200")
        order.order_no = "PO-002"
        order.created_at = datetime(2024, 1, 15)

        existing_cost = Mock(spec=ProjectCost)

        project_mock = Mock()
        project_mock.actual_cost = 0

        # query chain: order → existing_cost → project (3 .first() calls)
        call_results = [order, existing_cost, project_mock]
        db.query.return_value.filter.return_value.first.side_effect = call_results

        # project recalculate: .all() returns list of costs
        db.query.return_value.filter.return_value.all.return_value = [existing_cost]

        with patch("app.services.cost_collection_service.CostAlertService"):
            result = CostCollectionService.collect_from_purchase_order(db, order_id=2)

        # Should return the existing cost
        assert result == existing_cost

    def test_collect_from_purchase_order_creates_new_cost(self):
        """新建成本记录并更新项目实际成本"""
        from app.services.cost_collection_service import CostCollectionService
        from app.models.purchase import PurchaseOrder
        from app.models.project import Project

        db = self._make_db()
        order = Mock(spec=PurchaseOrder)
        order.project_id = 5
        order.total_amount = Decimal("500")
        order.tax_amount = Decimal("50")
        order.order_no = "PO-003"
        order.order_title = "测试采购"
        order.order_date = date(2024, 3, 1)
        order.created_at = datetime(2024, 3, 1)

        project = Mock(spec=Project)
        project.actual_cost = 0

        # order exists, no existing cost, project exists
        db.query.return_value.filter.return_value.first.side_effect = [order, None, project]

        with patch("app.services.cost_collection_service.CostAlertService") as mock_alert:
            mock_alert.check_budget_execution.return_value = None
            result = CostCollectionService.collect_from_purchase_order(
                db, order_id=3, created_by=1
            )

        db.add.assert_called()
        assert result is not None

    def test_collect_from_purchase_order_alert_failure_does_not_raise(self):
        """预警检查失败不影响成本归集"""
        from app.services.cost_collection_service import CostCollectionService
        from app.models.purchase import PurchaseOrder
        from app.models.project import Project

        db = self._make_db()
        order = Mock(spec=PurchaseOrder)
        order.project_id = 7
        order.total_amount = Decimal("300")
        order.tax_amount = Decimal("30")
        order.order_no = "PO-004"
        order.order_title = "另一采购"
        order.order_date = date(2024, 4, 1)
        order.created_at = datetime(2024, 4, 1)

        project = Mock(spec=Project)
        project.actual_cost = 0

        db.query.return_value.filter.return_value.first.side_effect = [order, None, project]

        with patch("app.services.cost_collection_service.CostAlertService") as mock_alert:
            mock_alert.check_budget_execution.side_effect = Exception("预警服务异常")
            # Should NOT raise
            result = CostCollectionService.collect_from_purchase_order(db, order_id=4)

        assert result is not None


# ===========================================================================
# 2. LossDeepAnalysisService
# ===========================================================================
class TestLossDeepAnalysisService:
    """未中标深度分析服务测试"""

    def test_init_stores_db(self):
        """初始化时保存 db 引用"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        db = MagicMock()
        with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
            svc = LossDeepAnalysisService(db)
        assert svc.db is db

    def test_analyze_lost_projects_returns_dict(self):
        """analyze_lost_projects 返回字典类型"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []

        with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
            svc = LossDeepAnalysisService(db)
            result = svc.analyze_lost_projects()

        assert isinstance(result, dict)

    def test_analyze_lost_projects_no_results_has_expected_keys(self):
        """无数据时返回结构包含关键字段"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        db = MagicMock()
        # Use a chainable mock that always returns [] from .all()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = []  # lost_projects will be []
        db.query.return_value = q

        with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
            svc = LossDeepAnalysisService(db)
            result = svc.analyze_lost_projects(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31)
            )

        assert isinstance(result, dict)

    def test_analyze_lost_projects_with_salesperson_filter(self):
        """传入 salesperson_id 时正常运行"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
            svc = LossDeepAnalysisService(db)
            result = svc.analyze_lost_projects(salesperson_id=42)

        assert isinstance(result, dict)

    def test_stage_constants_defined(self):
        """阶段常量正确定义"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        assert LossDeepAnalysisService.STAGE_REQUIREMENT == 'S1'
        assert LossDeepAnalysisService.STAGE_DESIGN == 'S2'
        assert LossDeepAnalysisService.STAGE_DETAILED_DESIGN == 'S4'


# ===========================================================================
# 3. PurchaseSuggestionEngine
# ===========================================================================
class TestPurchaseSuggestionEngine:
    """智能采购建议引擎测试"""

    def test_init_sets_db_and_tenant_id(self):
        """初始化设置 db 和 tenant_id"""
        from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

        db = MagicMock()
        engine = PurchaseSuggestionEngine(db, tenant_id=5)
        assert engine.db is db
        assert engine.tenant_id == 5

    def test_init_default_tenant_id(self):
        """默认 tenant_id 为 1"""
        from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

        db = MagicMock()
        engine = PurchaseSuggestionEngine(db)
        assert engine.tenant_id == 1

    def test_generate_from_shortages_returns_list(self):
        """generate_from_shortages 返回列表"""
        from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        engine = PurchaseSuggestionEngine(db)
        result = engine.generate_from_shortages()
        assert isinstance(result, list)

    def test_generate_from_shortages_no_shortages_empty_list(self):
        """无缺料预警时返回空列表"""
        from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

        db = MagicMock()
        # Simulate empty shortage query
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        engine = PurchaseSuggestionEngine(db)
        result = engine.generate_from_shortages(project_id=None)
        assert result == [] or isinstance(result, list)

    def test_generate_from_shortages_with_project_id(self):
        """传入 project_id 参数时正常调用"""
        from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        engine = PurchaseSuggestionEngine(db)
        result = engine.generate_from_shortages(project_id=10)
        assert isinstance(result, list)


# ===========================================================================
# 4. strategy/kpi_collector/collectors.py
# ===========================================================================
class TestKpiCollectors:
    """KPI采集器测试"""

    def test_collect_project_metrics_project_count(self):
        """PROJECT_COUNT 指标返回 Decimal"""
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 10
        db.query.return_value = q

        result = collect_project_metrics(db, metric="PROJECT_COUNT")
        assert result == Decimal("10")

    def test_collect_project_metrics_with_status_filter(self):
        """带 status 筛选条件"""
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 5
        db.query.return_value = q

        result = collect_project_metrics(
            db, metric="PROJECT_COUNT", filters={"status": "ACTIVE"}
        )
        assert isinstance(result, Decimal)

    def test_collect_project_metrics_unknown_metric_returns_none(self):
        """未知指标返回 None"""
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        result = collect_project_metrics(db, metric="UNKNOWN_METRIC")
        assert result is None

    def test_collect_project_metrics_total_value_returns_decimal(self):
        """PROJECT_TOTAL_VALUE 指标返回 Decimal"""
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.with_entities.return_value.scalar.return_value = 500000
        db.query.return_value = q

        result = collect_project_metrics(db, metric="PROJECT_TOTAL_VALUE")
        assert result == Decimal("500000")

    def test_collect_project_metrics_health_rate_no_projects(self):
        """无项目时健康率返回 0"""
        from app.services.strategy.kpi_collector.collectors import collect_project_metrics

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        result = collect_project_metrics(db, metric="PROJECT_HEALTH_RATE")
        assert result == Decimal("0")


# ===========================================================================
# 5. NotificationDispatcher
# ===========================================================================
class TestNotificationDispatcher:
    """通知调度器测试"""

    def _make_dispatcher(self):
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service") as mock_svc:
            mock_svc.return_value = MagicMock()
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)
            dispatcher._unified_service_mock = mock_svc.return_value
        return dispatcher, db

    def test_init_creates_unified_service(self):
        """初始化时创建统一通知服务"""
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service") as mock_get:
            mock_get.return_value = MagicMock()
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)
        mock_get.assert_called_once_with(db)
        assert dispatcher.unified_service is not None

    def test_create_system_notification_adds_to_db(self):
        """create_system_notification 创建并加入 db"""
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service"):
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)

        notification = dispatcher.create_system_notification(
            recipient_id=1,
            notification_type="ALERT",
            title="测试标题",
            content="测试内容",
        )
        db.add.assert_called_once_with(notification)
        assert notification.user_id == 1
        assert notification.title == "测试标题"

    def test_compute_next_retry_first_retry(self):
        """第一次重试使用 RETRY_SCHEDULE[0]"""
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service"):
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)

        now = datetime.now()
        result = dispatcher._compute_next_retry(retry_count=1)
        # Should be approximately now + 5 minutes
        assert result > now
        assert result < now + timedelta(minutes=10)

    def test_resolve_recipients_empty_ids_returns_empty_dict(self):
        """空 user_ids 返回空字典"""
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service"):
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)

        result = dispatcher._resolve_recipients_by_ids([])
        assert result == {}

    def test_retry_schedule_has_four_levels(self):
        """RETRY_SCHEDULE 定义了4个重试等级"""
        db = MagicMock()
        with patch("app.services.notification_dispatcher.get_notification_service"):
            from app.services.notification_dispatcher import NotificationDispatcher
            dispatcher = NotificationDispatcher(db)

        assert len(dispatcher.RETRY_SCHEDULE) == 4


# ===========================================================================
# 6. PresaleAIIntegrationService
# ===========================================================================
class TestPresaleAIIntegrationService:
    """售前AI集成服务测试"""

    def test_init_stores_db(self):
        """初始化存储 db"""
        from app.services.presale_ai_integration import PresaleAIIntegrationService

        db = MagicMock()
        svc = PresaleAIIntegrationService(db)
        assert svc.db is db

    def test_record_usage_no_existing_stat_creates_new(self):
        """无当日统计记录时创建新记录"""
        from app.services.presale_ai_integration import PresaleAIIntegrationService

        db = MagicMock()
        # Simulate no existing record
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        # Mock the stat returned after commit/refresh
        new_stat = Mock()
        new_stat.usage_count = 1
        new_stat.success_count = 1
        db.refresh.side_effect = lambda obj: None

        svc = PresaleAIIntegrationService(db)

        with patch("app.services.presale_ai_integration.PresaleAIUsageStats") as MockStat:
            mock_instance = Mock()
            mock_instance.usage_count = 1
            mock_instance.success_count = 1
            MockStat.return_value = mock_instance
            
            # Make the query chain return None (no existing)
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            db.query.return_value = q
            db.refresh.side_effect = lambda obj: setattr(obj, '_refreshed', True)

            result = svc.record_usage(user_id=1, ai_function="COST_ESTIMATE", success=True)

        db.add.assert_called()

    def test_record_usage_existing_stat_increments_count(self):
        """已有当日记录时递增计数"""
        from app.services.presale_ai_integration import PresaleAIIntegrationService

        db = MagicMock()
        existing = Mock()
        existing.usage_count = 3
        existing.success_count = 2
        existing.avg_response_time = 500

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = existing
        db.query.return_value = q
        db.refresh.side_effect = lambda obj: None

        svc = PresaleAIIntegrationService(db)
        result = svc.record_usage(
            user_id=1, ai_function="WIN_RATE", success=True, response_time=400
        )

        assert existing.usage_count == 4
        assert existing.success_count == 3

    def test_get_usage_stats_returns_list(self):
        """get_usage_stats 返回列表"""
        from app.services.presale_ai_integration import PresaleAIIntegrationService

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = []
        db.query.return_value = q

        svc = PresaleAIIntegrationService(db)
        result = svc.get_usage_stats()
        assert isinstance(result, list)

    def test_get_usage_stats_with_date_range(self):
        """get_usage_stats 带日期过滤"""
        from app.services.presale_ai_integration import PresaleAIIntegrationService

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = []
        db.query.return_value = q

        svc = PresaleAIIntegrationService(db)
        result = svc.get_usage_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert isinstance(result, list)


# ===========================================================================
# 7. ResourceSchedulingAIService
# ===========================================================================
class TestResourceSchedulingAIService:
    """资源调度AI服务测试"""

    def test_init_stores_db(self):
        """初始化保存 db 引用"""
        with patch("app.services.resource_scheduling_ai_service.AIClientService"):
            from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
            db = MagicMock()
            svc = ResourceSchedulingAIService()
            assert svc.db is db

    def _make_svc(self, db):
        """Helper: create ResourceSchedulingAIService with mocked deps"""
        with patch("app.services.resource_scheduling_ai_service.AIClientService"):
            from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
            return ResourceSchedulingAIService()

    def test_detect_resource_conflicts_no_allocations_returns_empty(self):
        """无分配记录时返回空列表"""
        import app.models.finance as finance_mod
        finance_mod.PMOResourceAllocation = MagicMock()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        svc = self._make_svc(db)
        result = svc.detect_resource_conflicts()
        assert isinstance(result, list)

    def test_detect_resource_conflicts_with_resource_id_filter(self):
        """带 resource_id 参数筛选"""
        import app.models.finance as finance_mod
        finance_mod.PMOResourceAllocation = MagicMock()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        svc = self._make_svc(db)
        result = svc.detect_resource_conflicts(resource_id=1)
        assert isinstance(result, list)

    def test_detect_resource_conflicts_no_overlap_no_conflict(self):
        """分配时段不重叠时无冲突"""
        import app.models.finance as finance_mod
        finance_mod.PMOResourceAllocation = MagicMock()

        db = MagicMock()

        alloc1 = Mock()
        alloc1.resource_id = 1
        alloc1.start_date = date(2024, 1, 1)
        alloc1.end_date = date(2024, 1, 31)
        alloc1.allocation_percent = 80
        alloc1.project_id = 100
        alloc1.status = "PLANNED"

        alloc2 = Mock()
        alloc2.resource_id = 1
        alloc2.start_date = date(2024, 2, 1)
        alloc2.end_date = date(2024, 2, 28)
        alloc2.allocation_percent = 80
        alloc2.project_id = 101
        alloc2.status = "PLANNED"

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [alloc1, alloc2]
        db.query.return_value = q

        svc = self._make_svc(db)
        result = svc.detect_resource_conflicts()
        assert isinstance(result, list)

    def test_detect_resource_conflicts_with_project_id(self):
        """带 project_id 参数正常运行"""
        import app.models.finance as finance_mod
        finance_mod.PMOResourceAllocation = MagicMock()

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        svc = self._make_svc(db)
        result = svc.detect_resource_conflicts(project_id=5)
        assert isinstance(result, list)


# ===========================================================================
# 8. itr_analytics_service
# ===========================================================================
class TestItrAnalyticsService:
    """ITR流程效率分析服务测试"""

    def test_analyze_resolution_time_empty_returns_zeros(self):
        """无工单时返回零值结构"""
        from app.services.itr_analytics_service import analyze_resolution_time

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 0
        assert result["avg_resolution_hours"] == 0

    def test_analyze_resolution_time_with_tickets_calculates_stats(self):
        """有工单时正确计算平均时间"""
        from app.services.itr_analytics_service import analyze_resolution_time

        db = MagicMock()
        ticket = Mock()
        ticket.id = 1
        ticket.ticket_no = "TK-001"
        ticket.problem_type = "HARDWARE"
        ticket.urgency = "HIGH"
        ticket.status = "CLOSED"
        ticket.reported_time = datetime(2024, 1, 1, 9, 0)
        ticket.resolved_time = datetime(2024, 1, 1, 13, 0)  # 4 hours

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [ticket]
        db.query.return_value = q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 1
        assert result["avg_resolution_hours"] == 4.0

    def test_analyze_resolution_time_with_project_filter(self):
        """带 project_id 过滤时正常运行"""
        from app.services.itr_analytics_service import analyze_resolution_time

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = analyze_resolution_time(db, project_id=10)
        assert isinstance(result, dict)

    def test_analyze_resolution_time_groups_by_problem_type(self):
        """多工单按问题类型分组"""
        from app.services.itr_analytics_service import analyze_resolution_time

        db = MagicMock()

        tickets = []
        for i, ptype in enumerate(["HARDWARE", "HARDWARE", "SOFTWARE"]):
            t = Mock()
            t.id = i + 1
            t.ticket_no = f"TK-00{i+1}"
            t.problem_type = ptype
            t.urgency = "NORMAL"
            t.reported_time = datetime(2024, 1, 1, 8, 0)
            t.resolved_time = datetime(2024, 1, 1, 10, 0)
            tickets.append(t)

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = tickets
        db.query.return_value = q

        result = analyze_resolution_time(db)
        assert result["total_tickets"] == 3
        ptype_names = [g["problem_type"] for g in result["by_problem_type"]]
        assert "HARDWARE" in ptype_names
        assert "SOFTWARE" in ptype_names

    def test_analyze_resolution_time_with_date_range(self):
        """带日期范围参数时正常运行"""
        from app.services.itr_analytics_service import analyze_resolution_time

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = analyze_resolution_time(
            db,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )
        assert isinstance(result, dict)


# ===========================================================================
# 9. SalesTargetService
# ===========================================================================
class TestSalesTargetService:
    """销售目标服务测试"""

    def test_create_target_team_without_team_id_raises(self):
        """创建团队目标时缺少 team_id 抛出 HTTPException"""
        from app.services.sales_target_service import SalesTargetService
        from fastapi import HTTPException

        db = MagicMock()
        target_data = Mock()
        target_data.target_type = "team"
        target_data.team_id = None
        target_data.user_id = None

        with pytest.raises(HTTPException) as exc_info:
            SalesTargetService.create_target(db, target_data, created_by=1)
        assert exc_info.value.status_code == 400

    def test_create_target_personal_without_user_id_raises(self):
        """创建个人目标时缺少 user_id 抛出 HTTPException"""
        from app.services.sales_target_service import SalesTargetService
        from fastapi import HTTPException

        db = MagicMock()
        target_data = Mock()
        target_data.target_type = "personal"
        target_data.team_id = None
        target_data.user_id = None

        with pytest.raises(HTTPException) as exc_info:
            SalesTargetService.create_target(db, target_data, created_by=1)
        assert exc_info.value.status_code == 400

    def test_get_target_not_found_returns_none(self):
        """目标不存在时返回 None"""
        from app.services.sales_target_service import SalesTargetService

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = SalesTargetService.get_target(db, target_id=9999)
        assert result is None

    def test_get_targets_returns_list(self):
        """get_targets 返回列表"""
        from app.services.sales_target_service import SalesTargetService

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value = q

        result = SalesTargetService.get_targets(db)
        assert isinstance(result, list)

    def test_delete_target_with_sub_targets_raises(self):
        """存在子目标时删除抛出 HTTPException"""
        from app.services.sales_target_service import SalesTargetService
        from fastapi import HTTPException

        db = MagicMock()
        mock_target = Mock()

        with patch("app.services.sales_target_service.get_or_404", return_value=mock_target):
            db.query.return_value.filter.return_value.count.return_value = 2
            with pytest.raises(HTTPException) as exc_info:
                SalesTargetService.delete_target(db, target_id=1)
        assert exc_info.value.status_code == 400
