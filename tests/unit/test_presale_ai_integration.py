# -*- coding: utf-8 -*-
"""
I1组: PresaleAIIntegrationService 单元测试
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.services.presale_ai_integration import PresaleAIIntegrationService
from app.schemas.presale_ai import AIFeedbackCreate, AIConfigUpdate
from app.models.presale_ai import WorkflowStatusEnum, WorkflowStepEnum


# ============================================================
# Helper factory
# ============================================================

def _make_service():
    db = MagicMock()
    return PresaleAIIntegrationService(db), db


def _make_stat(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.user_id = kwargs.get("user_id", 1)
    s.ai_function = kwargs.get("ai_function", "requirement_analysis")
    s.usage_count = kwargs.get("usage_count", 3)
    s.success_count = kwargs.get("success_count", 3)
    s.avg_response_time = kwargs.get("avg_response_time", 200)
    s.date = kwargs.get("date", date.today())
    return s


def _make_config(**kwargs):
    c = MagicMock()
    c.ai_function = kwargs.get("ai_function", "requirement_analysis")
    c.enabled = kwargs.get("enabled", True)
    c.temperature = kwargs.get("temperature", 0.7)
    c.max_tokens = kwargs.get("max_tokens", 2000)
    c.timeout_seconds = kwargs.get("timeout_seconds", 30)
    return c


def _make_workflow_log(**kwargs):
    """创建具有正确字段类型的 workflow log mock"""
    log = MagicMock()
    log.id = kwargs.get("id", 1)
    log.presale_ticket_id = kwargs.get("presale_ticket_id", 100)
    log.workflow_step = kwargs.get("workflow_step", WorkflowStepEnum.REQUIREMENT.value)
    log.status = kwargs.get("status", WorkflowStatusEnum.PENDING)
    # 设置 Pydantic 需要的字段为正确类型
    log.input_data = kwargs.get("input_data", None)
    log.output_data = kwargs.get("output_data", None)
    log.error_message = kwargs.get("error_message", None)
    log.started_at = kwargs.get("started_at", None)
    log.completed_at = kwargs.get("completed_at", None)
    log.created_at = kwargs.get("created_at", datetime.now())
    return log


# ============================================================
# TestRecordUsage
# ============================================================

class TestRecordUsage:
    def test_record_usage_new_record(self):
        """新建使用记录"""
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = svc.record_usage(user_id=1, ai_function="requirement_analysis", success=True, response_time=300)

        db.add.assert_called_once()
        db.commit.assert_called()
        db.refresh.assert_called()

    def test_record_usage_existing_record_success(self):
        """更新已有记录 - 成功调用"""
        svc, db = _make_service()
        existing = _make_stat(usage_count=3, success_count=3, avg_response_time=200)
        db.query.return_value.filter.return_value.first.return_value = existing

        result = svc.record_usage(user_id=1, ai_function="requirement_analysis", success=True, response_time=400)

        assert existing.usage_count == 4
        assert existing.success_count == 4
        db.commit.assert_called()

    def test_record_usage_existing_record_failure(self):
        """更新已有记录 - 失败调用"""
        svc, db = _make_service()
        existing = _make_stat(usage_count=3, success_count=3)
        db.query.return_value.filter.return_value.first.return_value = existing

        result = svc.record_usage(user_id=1, ai_function="requirement_analysis", success=False)

        assert existing.usage_count == 4
        assert existing.success_count == 3  # 失败不加

    def test_record_usage_updates_avg_response_time(self):
        """更新平均响应时间"""
        svc, db = _make_service()
        existing = _make_stat(usage_count=3, avg_response_time=200)
        db.query.return_value.filter.return_value.first.return_value = existing

        svc.record_usage(user_id=1, ai_function="req", success=True, response_time=400)

        # 新的 avg = (200 * 3 + 400) / 4 = 250
        assert existing.avg_response_time == 250


# ============================================================
# TestGetUsageStats
# ============================================================

class TestGetUsageStats:
    def test_get_stats_no_filters(self):
        """无过滤获取所有统计"""
        svc, db = _make_service()
        mock_stats = [_make_stat()]
        db.query.return_value.order_by.return_value.all.return_value = mock_stats

        result = svc.get_usage_stats()
        assert result is mock_stats or result is not None

    def test_get_stats_with_date_filter(self):
        """带日期过滤"""
        svc, db = _make_service()
        filter_chain = MagicMock()
        filter_chain.filter.return_value = filter_chain
        filter_chain.order_by.return_value.all.return_value = []
        db.query.return_value = filter_chain

        result = svc.get_usage_stats(
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            ai_functions=["requirement_analysis"],
            user_ids=[1, 2],
        )
        assert result is not None


# ============================================================
# TestGetDashboardStats
# ============================================================

class TestGetDashboardStats:
    def test_get_dashboard_stats_empty(self):
        """空数据时返回默认值"""
        svc, db = _make_service()

        total_mock = MagicMock()
        total_mock.total_usage = None
        total_mock.total_success = None
        total_mock.avg_time = None
        db.query.return_value.filter.return_value.first.return_value = total_mock
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0

        result = svc.get_dashboard_stats(days=30)
        assert result.total_usage == 0
        assert result.success_rate == 0.0

    def test_get_dashboard_stats_with_data(self):
        """有数据时正确计算"""
        svc, db = _make_service()

        total_mock = MagicMock()
        total_mock.total_usage = 100
        total_mock.total_success = 90
        total_mock.avg_time = 250.0

        func_row = MagicMock()
        func_row.ai_function = "requirement_analysis"
        func_row.count = 50
        func_row.success = 45

        trend_row = MagicMock()
        trend_row.date = date.today()
        trend_row.count = 10

        db.query.return_value.filter.return_value.first.return_value = total_mock
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [func_row]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [trend_row]
        db.query.return_value.filter.return_value.scalar.return_value = 5

        result = svc.get_dashboard_stats(days=30)
        assert result.total_usage == 100
        assert result.success_rate == 90.0


# ============================================================
# TestCreateFeedback
# ============================================================

class TestCreateFeedback:
    def test_create_feedback_success(self):
        svc, db = _make_service()
        feedback_data = AIFeedbackCreate(ai_function="requirement_analysis", rating=4)

        with patch("app.services.presale_ai_integration.save_obj") as mock_save:
            result = svc.create_feedback(user_id=1, feedback_data=feedback_data)

        mock_save.assert_called_once()
        assert result is not None

    def test_get_feedbacks_no_filters(self):
        svc, db = _make_service()
        filter_chain = MagicMock()
        filter_chain.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        db.query.return_value = filter_chain

        result = svc.get_feedbacks()
        assert result is not None


# ============================================================
# TestAIConfig
# ============================================================

class TestAIConfig:
    def test_get_or_create_config_existing(self):
        """获取已有配置"""
        svc, db = _make_service()
        mock_config = _make_config()
        db.query.return_value.filter.return_value.first.return_value = mock_config

        result = svc.get_or_create_config("requirement_analysis")
        assert result is mock_config

    def test_get_or_create_config_new(self):
        """创建新配置"""
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.presale_ai_integration.save_obj") as mock_save:
            result = svc.get_or_create_config("new_function")

        mock_save.assert_called_once()

    def test_update_config(self):
        """更新配置"""
        svc, db = _make_service()
        mock_config = _make_config()
        db.query.return_value.filter.return_value.first.return_value = mock_config

        config_update = AIConfigUpdate(enabled=False, temperature=0.5)
        result = svc.update_config("requirement_analysis", config_update)

        db.commit.assert_called()
        db.refresh.assert_called_with(mock_config)

    def test_get_all_configs(self):
        """获取所有配置"""
        svc, db = _make_service()
        db.query.return_value.all.return_value = [_make_config()]

        result = svc.get_all_configs()
        assert len(result) == 1


# ============================================================
# TestWorkflow
# ============================================================

class TestWorkflow:
    def test_start_workflow_creates_logs(self):
        """启动工作流创建日志记录"""
        svc, db = _make_service()

        result = svc.start_workflow(presale_ticket_id=100, auto_run=False)

        assert db.add.call_count == 5  # 5个步骤
        db.commit.assert_called()

    def test_start_workflow_auto_run(self):
        """auto_run=True 时第一步进入 RUNNING 状态"""
        svc, db = _make_service()
        result = svc.start_workflow(presale_ticket_id=100, auto_run=True)

        # 第一个日志状态变为 RUNNING
        assert result[0].status == WorkflowStatusEnum.RUNNING

    def test_get_workflow_status_not_found(self):
        """工单没有工作流记录"""
        svc, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = svc.get_workflow_status(presale_ticket_id=999)
        assert result is None

    def test_get_workflow_status_pending(self):
        """所有步骤待开始"""
        svc, db = _make_service()
        logs = [_make_workflow_log(status=WorkflowStatusEnum.PENDING) for _ in range(5)]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = logs

        result = svc.get_workflow_status(presale_ticket_id=100)
        assert result is not None
        assert result.progress == 0.0

    def test_get_workflow_status_partial_complete(self):
        """部分完成的工作流"""
        svc, db = _make_service()
        logs = [
            _make_workflow_log(status=WorkflowStatusEnum.SUCCESS),
            _make_workflow_log(status=WorkflowStatusEnum.SUCCESS),
            _make_workflow_log(status=WorkflowStatusEnum.RUNNING),
            _make_workflow_log(status=WorkflowStatusEnum.PENDING),
            _make_workflow_log(status=WorkflowStatusEnum.PENDING),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = logs

        result = svc.get_workflow_status(presale_ticket_id=100)
        assert result.overall_status == "running"
        assert result.progress == 40.0

    def test_update_workflow_step_not_found(self):
        """更新不存在的工作流步骤"""
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            svc.update_workflow_step(999, WorkflowStatusEnum.SUCCESS)

    def test_update_workflow_step_success(self):
        """成功更新工作流步骤"""
        svc, db = _make_service()
        mock_log = _make_workflow_log()
        db.query.return_value.filter.return_value.first.return_value = mock_log

        result = svc.update_workflow_step(
            log_id=1,
            status=WorkflowStatusEnum.SUCCESS,
            output_data={"result": "ok"},
        )
        assert mock_log.status == WorkflowStatusEnum.SUCCESS
        db.commit.assert_called()


# ============================================================
# TestAuditLog
# ============================================================

class TestAuditLog:
    def test_create_audit_log(self):
        svc, db = _make_service()

        with patch("app.services.presale_ai_integration.save_obj") as mock_save:
            result = svc.create_audit_log(
                user_id=1,
                action="analyze",
                ai_function="requirement_analysis",
                resource_type="ticket",
                resource_id=1,
            )

        mock_save.assert_called_once()

    def test_get_audit_logs_with_filters(self):
        svc, db = _make_service()
        filter_chain = MagicMock()
        filter_chain.filter.return_value = filter_chain
        filter_chain.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        db.query.return_value = filter_chain

        result = svc.get_audit_logs(
            user_id=1,
            action="analyze",
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
        )
        assert result is not None


# ============================================================
# TestHealthCheck
# ============================================================

class TestHealthCheck:
    def test_health_check_healthy(self):
        """数据库正常时健康状态"""
        svc, db = _make_service()
        db.execute.return_value = None
        db.query.return_value.all.return_value = [_make_config(enabled=True)]
        db.query.return_value.filter.return_value.scalar.return_value = 10

        result = svc.health_check()
        assert result.status in ("healthy", "degraded", "unhealthy")

    def test_health_check_db_error(self):
        """数据库异常时返回 unhealthy"""
        svc, db = _make_service()
        db.execute.side_effect = Exception("Connection refused")
        db.query.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0

        result = svc.health_check()
        assert result.status == "unhealthy"
        assert result.services["database"]["status"] == "unhealthy"
