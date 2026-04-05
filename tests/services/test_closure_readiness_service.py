# -*- coding: utf-8 -*-
"""项目结项准备度服务测试"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# Mock the model classes before importing the service
with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
     patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
     patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInstance, \
     patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInstance, \
     patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDocument, \
     patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
     patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
     patch("app.services.project.closure_readiness_service.func") as MockFunc:
    
    # Configure mock project
    MockProject.id = 1
    MockProject.project_code = "PRJ001"
    MockProject.project_name = "测试项目"
    MockProject.budget_amount = Decimal("100000")
    MockProject.actual_cost = Decimal("95000")
    MockProject.invoice_issued = True
    MockProject.final_payment_completed = True


class TestClosureReadinessService:
    """ClosureReadinessService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import ClosureReadinessService

        return ClosureReadinessService(mock_db)

    def _create_mock_project(self, **kwargs):
        """创建模拟项目对象"""
        project = MagicMock()
        project.id = kwargs.get("id", 1)
        project.project_code = kwargs.get("project_code", "PRJ001")
        project.project_name = kwargs.get("project_name", "测试项目")
        project.budget_amount = kwargs.get("budget_amount", Decimal("100000"))
        project.actual_cost = kwargs.get("actual_cost", Decimal("95000"))
        project.invoice_issued = kwargs.get("invoice_issued", True)
        project.final_payment_completed = kwargs.get("final_payment_completed", True)
        return project

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_check_closure_readiness_project_not_found(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试项目不存在时返回未就绪"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.check_readiness(project_id=999)

        assert result["ready"] is False
        assert result["score"] == 0
        assert "项目不存在" in result["missing_items"]

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_check_closure_readiness_with_default_rules(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试使用默认规则"""
        project = self._create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        assert "ready" in result
        assert "score" in result
        assert "checks" in result

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_check_closure_readiness_stage_not_complete(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试阶段未完成"""
        project = self._create_mock_project()
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        # Find stage completion check
        stage_check = next((c for c in result.get("checks", []) if c.get("key") == "stage_completion"), None)
        assert stage_check is not None
        assert stage_check["passed"] is False

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_validate_closure_documents(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试结项文档验证 - 文档不足"""
        project = self._create_mock_project(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        # Find document check result
        doc_check = next((c for c in result.get("checks", []) if c.get("key") == "document_completeness"), None)
        assert doc_check is not None

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_closure_with_missing_deliverables(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试缺少交付物边界情况"""
        project = self._create_mock_project(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        # Check deliverable check result
        deliverable_check = next((c for c in result.get("checks", []) if c.get("key") == "deliverable_upload"), None)
        assert deliverable_check is not None

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_full_closure_workflow(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试完整结项流程"""
        project = self._create_mock_project(
            id=1,
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("98000"),
            invoice_issued=True,
            final_payment_completed=True,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        assert "checks" in result
        # Should have 5 check types
        assert len(result["checks"]) == 5

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_closure_approval_chain(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试结项审批链"""
        project = self._create_mock_project(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        # Check customer acceptance result
        acceptance_check = next((c for c in result.get("checks", []) if c.get("key") == "customer_acceptance"), None)
        assert acceptance_check is not None

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.ProjectStage")
    @patch("app.services.project.closure_readiness_service.ProjectStageInstance")
    @patch("app.services.project.closure_readiness_service.ProjectNodeInstance")
    @patch("app.services.project.closure_readiness_service.ProjectDocument")
    @patch("app.services.project.closure_readiness_service.ProjectCost")
    @patch("app.services.project.closure_readiness_service.ApprovalInstance")
    def test_closure_cost_check(
        self, mock_approval, mock_cost, mock_doc, mock_node, mock_stage_inst, mock_stage, mock_project, service, mock_db
    ):
        """测试成本检查"""
        project = self._create_mock_project(
            id=1,
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("95000"),
            invoice_issued=True,
            final_payment_completed=True,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.check_readiness(project_id=1)

        # Find cost settlement check
        cost_check = next((c for c in result.get("checks", []) if c.get("key") == "cost_settlement"), None)
        assert cost_check is not None


class TestClosureNotificationService:
    """ClosureNotificationService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import ClosureNotificationService

        return ClosureNotificationService(mock_db)

    def test_notify_if_ready_ready(self, service, mock_db):
        """测试项目已就绪时发送通知"""
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 1,
        }

        project = MagicMock()
        project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Should return list of notified user IDs
        assert isinstance(result, list)

    def test_notify_if_ready_not_ready(self, service, mock_db):
        """测试项目未就绪时不发送通知"""
        readiness = {
            "ready": False,
            "score": 50,
            "project_id": 1,
        }

        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Empty list when not ready
        assert result == []


class TestLessonsCollectionService:
    """LessonsCollectionService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import LessonsCollectionService

        return LessonsCollectionService(mock_db)

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.Project")
    def test_auto_collect_creates_review(self, mock_project, mock_review_cls, service, mock_db):
        """测试自动收集创建回顾"""
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            project,  # project lookup
            None,  # no existing review
        ]

        mock_review = MagicMock()
        mock_review.id = 1
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        # Should call db.add and db.commit
        mock_db.add.assert_called()
        mock_db.commit.assert_called()