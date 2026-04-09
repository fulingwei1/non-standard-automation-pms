# -*- coding: utf-8 -*-
"""项目结项准备度服务测试 - ClosureReadinessService 专项测试

本测试文件聚焦于 ClosureReadinessService 类的核心功能测试
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def create_service(mock_db):
    """创建服务实例"""
    from app.services.project.closure_readiness_service import ClosureReadinessService
    return ClosureReadinessService(mock_db)


def test_check_closure_readiness_complete(mock_db):
    """测试结项就绪检查（完成状态）"""
    # Create project with real values inside patches
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        # Create project with real attributes - inside patch context
        project = MagicMock()
        # Set real values for properties that will be used in comparisons
        object.__setattr__(project, 'id', 1)
        object.__setattr__(project, 'project_code', "PRJ001")
        object.__setattr__(project, 'project_name', "测试项目")
        object.__setattr__(project, 'budget_amount', Decimal("100000"))
        object.__setattr__(project, 'actual_cost', Decimal("95000"))
        object.__setattr__(project, 'invoice_issued', True)
        object.__setattr__(project, 'final_payment_completed', True)
        
        # Also set via property to be safe
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        # Setup query results - sequence matters
        query_results = [
            (project, "first"),  # 1. Project query
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),  # 2. Stage instances
            ([], "all"),  # 3. Node instances (deliverables)
            ([MagicMock(doc_type="设计文档", doc_category="设计"),
              MagicMock(doc_type="测试报告", doc_category="测试"),
              MagicMock(doc_type="验收报告", doc_category="验收"),
              MagicMock(doc_type="用户手册", doc_category="培训")], "all"),  # 4. Documents
            (MagicMock(status="APPROVED"), "first"),  # 5. Approval
            ([MagicMock()], "all"),  # 6. Costs
            ([MagicMock(stage_code="S1", status="COMPLETED")], "all"),  # 7. Fallback to ProjectStage
            ([MagicMock()], "all"),  # 8. Cost count via func
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        # Mock func.count chain
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 10
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is True
    assert result["score"] == 100
    assert result["project_id"] == 1


def test_check_closure_readiness_incomplete(mock_db):
    """测试结项未就绪"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        # Project with issues - over budget, not invoiced, not paid
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("120000")  # Over!
        project.invoice_issued = False
        project.final_payment_completed = False
        
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code="S1", status="COMPLETED")], "all"),  # Only 1 stage
            ([], "all"),
            ([], "all"),  # No docs
            (None, "first"),  # No approval
            ([], "all"),  # No costs
            ([], "all"),  # Fallback stages
            ([], "all"),  # Cost count
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 0
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is False
    assert result["score"] < 100
    assert len(result["missing_items"]) > 0


def test_get_readiness_score(mock_db):
    """测试准备度评分"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),
            ([], "all"),
            ([MagicMock(doc_type="设计文档"), MagicMock(doc_type="测试报告"),
              MagicMock(doc_type="验收报告"), MagicMock(doc_type="用户手册")], "all"),
            (MagicMock(status="APPROVED"), "first"),
            ([MagicMock()], "all"),
            ([], "all"),
            ([], "all"),
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 5
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert "score" in result
    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert result["score"] == 100


def test_readiness_with_partial_deliverables(mock_db):
    """测试部分交付物边界情况"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        # Partial documents - only design doc
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),
            ([], "all"),
            ([MagicMock(doc_type="设计文档", doc_category="设计")], "all"),  # Only 1 doc
            (MagicMock(status="APPROVED"), "first"),
            ([MagicMock()], "all"),
            ([], "all"),
            ([], "all"),
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 5
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is False
    assert result["score"] < 100
    assert result["score"] > 0
    
    # Check deliverable check
    deliverable_check = next(
        (c for c in result["checks"] if c["key"] == "deliverable_upload"), None
    )
    assert deliverable_check is not None
    assert deliverable_check["passed"] is False


def test_project_not_found(mock_db):
    """测试项目不存在"""
    with patch("app.services.project.closure_readiness_service.Project"):
        with patch("app.services.project.closure_readiness_service.ProjectStageInstance"):
            with patch("app.services.project.closure_readiness_service.ProjectStage"):
                with patch("app.services.project.closure_readiness_service.ProjectNodeInstance"):
                    with patch("app.services.project.closure_readiness_service.ProjectDocument"):
                        with patch("app.services.project.closure_readiness_service.ProjectCost"):
                            with patch("app.services.project.closure_readiness_service.ApprovalInstance"):
                                with patch("app.services.project.closure_readiness_service.func"):
                                    mock_db.query.return_value.filter.return_value.first.return_value = None
                                    
                                    service = create_service(mock_db)
                                    result = service.check_readiness(project_id=999)

    assert result["ready"] is False
    assert result["score"] == 0
    assert "项目不存在" in result["missing_items"]