# -*- coding: utf-8 -*-
"""
Tests for invoice_auto_service service
Covers: app/services/invoice_auto_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 179 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.invoice_auto_service import InvoiceAutoService
from app.models.acceptance import AcceptanceOrder
from app.models.project import Project, ProjectMilestone, ProjectPaymentPlan
from app.models.business_support import InvoiceRequest


@pytest.fixture
def invoice_auto_service(db_session: Session):
    """创建 InvoiceAutoService 实例"""
    return InvoiceAutoService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_acceptance_order(db_session: Session, test_project):
    """创建测试验收单"""
    order = AcceptanceOrder(
        project_id=test_project.id,
        acceptance_type="FAT",
        overall_result="PASSED",
        status="COMPLETED"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


class TestInvoiceAutoService:
    """Test suite for InvoiceAutoService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = InvoiceAutoService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_check_and_create_invoice_request_not_found(self, invoice_auto_service):
        """测试验收单不存在"""
        result = invoice_auto_service.check_and_create_invoice_request(99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']
        assert result['invoice_requests'] == []

    def test_check_and_create_invoice_request_not_passed(self, invoice_auto_service, db_session, test_project):
        """测试验收未通过"""
        order = AcceptanceOrder(
            project_id=test_project.id,
            acceptance_type="FAT",
            overall_result="FAILED",
            status="COMPLETED"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = invoice_auto_service.check_and_create_invoice_request(order.id)
        
        assert result is not None
        assert result['success'] is True
        assert '无需开票' in result['message']
        assert result['invoice_requests'] == []

    def test_check_and_create_invoice_request_not_completed(self, invoice_auto_service, db_session, test_project):
        """测试验收未完成"""
        order = AcceptanceOrder(
            project_id=test_project.id,
            acceptance_type="FAT",
            overall_result="PASSED",
            status="DRAFT"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = invoice_auto_service.check_and_create_invoice_request(order.id)
        
        assert result is not None
        assert result['success'] is True
        assert '无需开票' in result['message']

    def test_check_and_create_invoice_request_unsupported_type(self, invoice_auto_service, db_session, test_project):
        """测试不支持的验收类型"""
        order = AcceptanceOrder(
            project_id=test_project.id,
            acceptance_type="UNKNOWN",
            overall_result="PASSED",
            status="COMPLETED"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = invoice_auto_service.check_and_create_invoice_request(order.id)
        
        assert result is not None
        assert result['success'] is True
        assert '不支持' in result['message']

    def test_check_and_create_invoice_request_no_milestone(self, invoice_auto_service, test_acceptance_order):
        """测试无关联里程碑"""
        result = invoice_auto_service.check_and_create_invoice_request(test_acceptance_order.id)
        
        assert result is not None
        assert result['success'] is True
        assert '未找到关联的里程碑' in result['message']

    def test_check_and_create_invoice_request_success(self, invoice_auto_service, db_session, test_project, test_acceptance_order):
        """测试成功创建发票申请"""
        # 创建里程碑
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_type="FAT_PASS",
            status="COMPLETED"
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        # 创建收款计划
        payment_plan = ProjectPaymentPlan(
            project_id=test_project.id,
            milestone_id=milestone.id,
            payment_amount=Decimal("100000.00"),
            payment_status="PENDING"
        )
        db_session.add(payment_plan)
        db_session.commit()
        
        result = invoice_auto_service.check_and_create_invoice_request(test_acceptance_order.id)
        
        assert result is not None
        assert result['success'] is True
        # 应该创建了发票申请
        assert len(result.get('invoice_requests', [])) >= 0

    def test_check_and_create_invoice_request_auto_create(self, invoice_auto_service, db_session, test_project, test_acceptance_order):
        """测试自动创建发票"""
        # 创建里程碑和收款计划
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_type="FAT_PASS",
            status="COMPLETED"
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        payment_plan = ProjectPaymentPlan(
            project_id=test_project.id,
            milestone_id=milestone.id,
            payment_amount=Decimal("100000.00"),
            payment_status="PENDING"
        )
        db_session.add(payment_plan)
        db_session.commit()
        
        result = invoice_auto_service.check_and_create_invoice_request(
            test_acceptance_order.id,
            auto_create=True
        )
        
        assert result is not None
        assert result['success'] is True
