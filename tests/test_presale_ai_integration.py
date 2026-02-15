"""
售前AI系统集成 - 单元测试
Team 10: 售前AI系统集成与前端UI
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.presale_ai import (
    PresaleAIUsageStats,
    PresaleAIFeedback,
    PresaleAIConfig,
    PresaleAIWorkflowLog,
    PresaleAIAuditLog,
    AIFunctionEnum,
    WorkflowStatusEnum,
)
from app.services.presale_ai_integration import PresaleAIIntegrationService

client = TestClient(app)


# ============ Fixtures ============

@pytest.fixture
def ai_service(db: Session):
    """创建AI服务实例"""
    return PresaleAIIntegrationService(db)


@pytest.fixture
def sample_usage_stat(db: Session, test_user):
    """创建示例使用统计"""
    stat = PresaleAIUsageStats(
        user_id=test_user.id,
        ai_function=AIFunctionEnum.REQUIREMENT,
        usage_count=10,
        success_count=8,
        avg_response_time=500,
        date=date.today(),
    )
    db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat


@pytest.fixture
def sample_feedback(db: Session, test_user):
    """创建示例反馈"""
    feedback = PresaleAIFeedback(
        user_id=test_user.id,
        ai_function="requirement",
        rating=4,
        feedback_text="很好用",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@pytest.fixture
def sample_config(db: Session):
    """创建示例配置"""
    config = PresaleAIConfig(
        ai_function="requirement",
        enabled=True,
        temperature=0.7,
        max_tokens=2000,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


# ============ Service Layer Tests ============

class TestPresaleAIService:
    """AI服务层测试"""

    def test_record_usage_new(self, ai_service, test_user):
        """测试记录新的使用统计"""
        stat = ai_service.record_usage(
            user_id=test_user.id,
            ai_function="requirement",
            success=True,
            response_time=300,
        )

        assert stat.user_id == test_user.id
        assert stat.ai_function == "requirement"
        assert stat.usage_count == 1
        assert stat.success_count == 1
        assert stat.avg_response_time == 300

    def test_record_usage_existing(self, ai_service, sample_usage_stat):
        """测试更新现有使用统计"""
        stat = ai_service.record_usage(
            user_id=sample_usage_stat.user_id,
            ai_function=sample_usage_stat.ai_function,
            success=True,
            response_time=600,
        )

        assert stat.usage_count == 11
        assert stat.success_count == 9
        # 平均响应时间应该更新
        assert stat.avg_response_time > 500

    def test_get_usage_stats(self, ai_service, sample_usage_stat):
        """测试获取使用统计"""
        stats = ai_service.get_usage_stats()
        assert len(stats) > 0
        assert any(s.id == sample_usage_stat.id for s in stats)

    def test_get_usage_stats_with_filters(self, ai_service, sample_usage_stat):
        """测试带过滤条件的使用统计"""
        stats = ai_service.get_usage_stats(
            ai_functions=["requirement"],
            start_date=date.today(),
        )
        assert len(stats) > 0
        assert all(s.ai_function == "requirement" for s in stats)

    def test_get_dashboard_stats(self, ai_service, sample_usage_stat):
        """测试获取仪表盘统计"""
        stats = ai_service.get_dashboard_stats(days=30)

        assert stats.total_usage >= 0
        assert stats.total_success >= 0
        assert 0 <= stats.success_rate <= 100
        assert stats.avg_response_time >= 0
        assert isinstance(stats.top_functions, list)
        assert isinstance(stats.usage_trend, list)

    def test_create_feedback(self, ai_service, test_user):
        """测试创建反馈"""
        from app.schemas.presale_ai import AIFeedbackCreate

        feedback_data = AIFeedbackCreate(
            ai_function="solution",
            rating=5,
            feedback_text="非常好用",
        )

        feedback = ai_service.create_feedback(
            user_id=test_user.id,
            feedback_data=feedback_data,
        )

        assert feedback.user_id == test_user.id
        assert feedback.ai_function == "solution"
        assert feedback.rating == 5

    def test_get_feedbacks(self, ai_service, sample_feedback):
        """测试获取反馈列表"""
        feedbacks = ai_service.get_feedbacks()
        assert len(feedbacks) > 0

    def test_get_feedbacks_with_filters(self, ai_service, sample_feedback):
        """测试带过滤条件的反馈列表"""
        feedbacks = ai_service.get_feedbacks(
            ai_function="requirement",
            min_rating=4,
        )
        assert all(f.rating >= 4 for f in feedbacks)

    def test_get_or_create_config(self, ai_service):
        """测试获取或创建配置"""
        config = ai_service.get_or_create_config("test_function")

        assert config.ai_function == "test_function"
        assert config.enabled is True

        # 再次调用应返回相同配置
        config2 = ai_service.get_or_create_config("test_function")
        assert config.id == config2.id

    def test_update_config(self, ai_service, sample_config):
        """测试更新配置"""
        from app.schemas.presale_ai import AIConfigUpdate

        update_data = AIConfigUpdate(
            enabled=False,
            temperature=0.5,
        )

        config = ai_service.update_config("requirement", update_data)

        assert config.enabled is False
        assert config.temperature == 0.5

    def test_start_workflow(self, ai_service):
        """测试启动工作流"""
        logs = ai_service.start_workflow(
            presale_ticket_id=123,
            initial_data={"test": "data"},
            auto_run=True,
        )

        assert len(logs) == 5  # 应该创建5个步骤
        assert logs[0].workflow_step == "requirement"
        assert logs[0].status == WorkflowStatusEnum.RUNNING

    def test_get_workflow_status(self, ai_service):
        """测试获取工作流状态"""
        # 先创建工作流
        ai_service.start_workflow(presale_ticket_id=456)

        status = ai_service.get_workflow_status(456)

        assert status is not None
        assert status.presale_ticket_id == 456
        assert len(status.steps) == 5
        assert 0 <= status.progress <= 100

    def test_update_workflow_step(self, ai_service):
        """测试更新工作流步骤"""
        logs = ai_service.start_workflow(presale_ticket_id=789)
        log_id = logs[0].id

        updated_log = ai_service.update_workflow_step(
            log_id=log_id,
            status=WorkflowStatusEnum.SUCCESS,
            output_data={"result": "success"},
        )

        assert updated_log.status == WorkflowStatusEnum.SUCCESS
        assert updated_log.output_data["result"] == "success"
        assert updated_log.completed_at is not None

    def test_create_audit_log(self, ai_service, test_user):
        """测试创建审计日志"""
        log = ai_service.create_audit_log(
            user_id=test_user.id,
            action="test_action",
            ai_function="requirement",
            details={"key": "value"},
        )

        assert log.user_id == test_user.id
        assert log.action == "test_action"
        assert log.details["key"] == "value"

    def test_get_audit_logs(self, ai_service, test_user):
        """测试获取审计日志"""
        # 创建一些日志
        ai_service.create_audit_log(
            user_id=test_user.id,
            action="test_action",
        )

        logs = ai_service.get_audit_logs(user_id=test_user.id)
        assert len(logs) > 0

    def test_health_check(self, ai_service):
        """测试健康检查"""
        health = ai_service.health_check()

        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert "database" in health.services
        assert "ai_functions" in health.services


# ============ API Endpoint Tests ============

class TestPresaleAIAPI:
    """AI API端点测试"""

    def test_get_dashboard_stats(self, auth_client):
        """测试获取仪表盘统计API"""
        response = auth_client.get("/api/v1/presale/ai/dashboard/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_usage" in data
        assert "success_rate" in data

    def test_get_usage_stats(self, auth_client):
        """测试获取使用统计API"""
        response = auth_client.get("/api/v1/presale/ai/usage-stats")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_submit_feedback(self, auth_client):
        """测试提交反馈API"""
        feedback_data = {
            "ai_function": "requirement",
            "rating": 5,
            "feedback_text": "很好",
        }

        response = auth_client.post("/api/v1/presale/ai/feedback", json=feedback_data)
        assert response.status_code == 200

        data = response.json()
        assert data["rating"] == 5

    def test_get_feedback_by_function(self, auth_client, sample_feedback):
        """测试获取指定功能的反馈API"""
        response = auth_client.get("/api/v1/presale/ai/feedback/requirement")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_start_workflow(self, auth_client):
        """测试启动工作流API"""
        workflow_data = {
            "presale_ticket_id": 123,
            "initial_data": {},
            "auto_run": True,
        }

        response = auth_client.post(
            "/api/v1/presale/ai/workflow/start",
            json=workflow_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_get_workflow_status(self, auth_client, ai_service):
        """测试获取工作流状态API"""
        # 先创建工作流
        ai_service.start_workflow(presale_ticket_id=999)

        response = auth_client.get("/api/v1/presale/ai/workflow/status/999")
        assert response.status_code == 200

        data = response.json()
        assert data["presale_ticket_id"] == 999

    def test_health_check(self, auth_client):
        """测试健康检查API"""
        response = auth_client.get("/api/v1/presale/ai/health-check")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "services" in data

    def test_update_config(self, auth_client):
        """测试更新配置API"""
        config_data = {
            "enabled": True,
            "temperature": 0.8,
        }

        response = auth_client.post(
            "/api/v1/presale/ai/config/update",
            json=config_data,
            params={"ai_function": "test_function"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["temperature"] == 0.8

    def test_get_all_configs(self, auth_client):
        """测试获取所有配置API"""
        response = auth_client.get("/api/v1/presale/ai/config")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_audit_logs(self, auth_client):
        """测试获取审计日志API"""
        response = auth_client.get("/api/v1/presale/ai/audit-log")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_export_report(self, auth_client):
        """测试导出报告API"""
        export_data = {
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today()),
            "format": "excel",
        }

        response = auth_client.post(
            "/api/v1/presale/ai/export-report",
            json=export_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert "file_url" in data
        assert "file_name" in data
