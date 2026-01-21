# -*- coding: utf-8 -*-
"""
Tests for invoice_auto_service service
Covers: app/services/invoice_auto_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 179 lines
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.invoice_auto_service import InvoiceAutoService
from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
from app.models.project import Project, ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice
from tests.factories import ProjectFactory, CustomerFactory


class TestInvoiceAutoService:
    """Test suite for InvoiceAutoService."""

    def test_check_and_create_invoice_request_acceptance_not_found(self, db_session):
        """测试检查并创建发票申请 - 验收单不存在"""
        service = InvoiceAutoService(db_session)
        result = service.check_and_create_invoice_request(99999)

        assert result["success"] is False
        assert "不存在" in result["message"]
        assert result["invoice_requests"] == []

    def test_check_and_create_invoice_request_not_passed(self, db_session):
        """测试检查并创建发票申请 - 验收未通过"""
        from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
        
        project = ProjectFactory()
        db_session.add(project)
        db_session.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST",
            template_name="测试模板",
            acceptance_type="FAT",
            is_system=True,
            is_active=True
        )
        db_session.add(template)
        db_session.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST",
            project_id=project.id,
            acceptance_type="FAT",
            template_id=template.id,
            overall_result="FAILED",
            status="COMPLETED",
            planned_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        service = InvoiceAutoService(db_session)
        result = service.check_and_create_invoice_request(order.id)

        assert result["success"] is True
        assert "无需开票" in result["message"]
        assert result["invoice_requests"] == []

    def test_check_and_create_invoice_request_unsupported_type(self, db_session):
        """测试检查并创建发票申请 - 不支持的验收类型"""
        from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
        
        project = ProjectFactory()
        db_session.add(project)
        db_session.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST2",
            template_name="测试模板2",
            acceptance_type="OTHER",
            is_system=True,
            is_active=True
        )
        db_session.add(template)
        db_session.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST2",
            project_id=project.id,
            acceptance_type="OTHER",
            template_id=template.id,
            overall_result="PASSED",
            status="COMPLETED",
            planned_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        service = InvoiceAutoService(db_session)
        result = service.check_and_create_invoice_request(order.id)

        assert result["success"] is True
        assert "不支持" in result["message"]
        assert result["invoice_requests"] == []

    def test_check_and_create_invoice_request_no_milestone(self, db_session):
        """测试检查并创建发票申请 - 未找到关联里程碑"""
        from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
        
        project = ProjectFactory()
        db_session.add(project)
        db_session.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST3",
            template_name="测试模板3",
            acceptance_type="FAT",
            is_system=True,
            is_active=True
        )
        db_session.add(template)
        db_session.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST3",
            project_id=project.id,
            acceptance_type="FAT",
            template_id=template.id,
            overall_result="PASSED",
            status="COMPLETED",
            planned_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        service = InvoiceAutoService(db_session)
        result = service.check_and_create_invoice_request(order.id)

        assert result["success"] is True
        assert "未找到关联的里程碑" in result["message"]
        assert result["invoice_requests"] == []

    def test_check_deliverables_complete_no_contract(self, db_session):
        """测试检查交付物是否齐全 - 无合同"""
        service = InvoiceAutoService(db_session)
        
        plan = ProjectPaymentPlan(
            project_id=1,
            payment_no=1,
            payment_name="首付款",
            payment_type="ADVANCE",
            planned_amount=Decimal("10000.00"),
            contract_id=None
        )

        result = service._check_deliverables_complete(plan)
        assert result is True  # 无合同时默认齐全

    def test_check_acceptance_issues_resolved_no_issues(self, db_session):
        """测试检查验收问题是否已解决 - 无问题"""
        from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
        
        project = ProjectFactory()
        db_session.add(project)
        db_session.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST4",
            template_name="测试模板4",
            acceptance_type="FAT",
            is_system=True,
            is_active=True
        )
        db_session.add(template)
        db_session.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST4",
            project_id=project.id,
            acceptance_type="FAT",
            template_id=template.id,
            overall_result="PASSED",
            status="COMPLETED",
            planned_date=date.today()
        )
        db_session.add(order)
        db_session.commit()

        service = InvoiceAutoService(db_session)
        result = service._check_acceptance_issues_resolved(order)

        # 无问题时应该返回True
        assert result is True

    def test_check_acceptance_issues_resolved_with_blocking_issues(self, db_session):
        """测试检查验收问题是否已解决 - 有阻塞问题"""
        from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate, AcceptanceIssue
        
        project = ProjectFactory()
        db_session.add(project)
        db_session.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST5",
            template_name="测试模板5",
            acceptance_type="FAT",
            is_system=True,
            is_active=True
        )
        db_session.add(template)
        db_session.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST5",
            project_id=project.id,
            acceptance_type="FAT",
            template_id=template.id,
            overall_result="PASSED",
            status="COMPLETED",
            planned_date=date.today()
        )
        db_session.add(order)
        db_session.flush()

        # 创建阻塞问题
        issue = AcceptanceIssue(
            issue_no="ISSUE-001",
            order_id=order.id,
            issue_type="DEFECT",
            severity="CRITICAL",
            title="阻塞问题",
            description="这是一个阻塞验收的问题",
            is_blocking=True,
            status="OPEN"
        )
        db_session.add(issue)
        db_session.commit()

        service = InvoiceAutoService(db_session)
        result = service._check_acceptance_issues_resolved(order)

        # 有阻塞问题时应该返回False
        assert result is False
