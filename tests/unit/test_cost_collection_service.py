# -*- coding: utf-8 -*-
"""
Tests for cost_collection_service service
Covers: app/services/cost_collection_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 180 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_collection_service import CostCollectionService
from app.models.project import Project, ProjectCost
from app.models.purchase import PurchaseOrder
from app.models.outsourcing import OutsourcingOrder
from app.models.ecn import Ecn


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        actual_cost=0.0
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_purchase_order(db_session: Session, test_project):
    """创建测试采购订单"""
    order = PurchaseOrder(
        order_no="PO001",
        order_title="测试采购订单",
        project_id=test_project.id,
        total_amount=Decimal("10000.00"),
        tax_amount=Decimal("1300.00"),
        order_date=date.today()
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


class TestCostCollectionService:
    """Test suite for CostCollectionService."""

    def test_collect_from_purchase_order_success(self, db_session, test_project, test_purchase_order):
        """测试从采购订单归集成本 - 成功场景"""
        result = CostCollectionService.collect_from_purchase_order(
            db_session,
            test_purchase_order.id
        )
        
        assert result is not None
        assert isinstance(result, ProjectCost)
        assert result.project_id == test_project.id
        assert result.amount == Decimal("10000.00")
        assert result.tax_amount == Decimal("1300.00")
        assert result.source_type == "PURCHASE_ORDER"
        assert result.source_id == test_purchase_order.id
        
        # 验证项目成本已更新
        db_session.refresh(test_project)
        assert test_project.actual_cost == 10000.0

    def test_collect_from_purchase_order_no_project(self, db_session):
        """测试从采购订单归集成本 - 订单无关联项目"""
        # 创建无项目的订单
        order = PurchaseOrder(
            order_no="PO002",
            order_title="无项目订单",
            project_id=None,
            total_amount=Decimal("5000.00"),
            order_date=date.today()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = CostCollectionService.collect_from_purchase_order(
            db_session,
            order.id
        )
        
        assert result is None

    def test_collect_from_purchase_order_not_found(self, db_session):
        """测试从采购订单归集成本 - 订单不存在"""
        result = CostCollectionService.collect_from_purchase_order(
            db_session,
            99999
        )
        
        assert result is None

    def test_collect_from_purchase_order_existing_cost(self, db_session, test_project, test_purchase_order):
        """测试从采购订单归集成本 - 已存在成本记录"""
        # 第一次归集
        result1 = CostCollectionService.collect_from_purchase_order(
            db_session,
            test_purchase_order.id
        )
        
        assert result1 is not None
        
        # 更新订单金额
        test_purchase_order.total_amount = Decimal("15000.00")
        db_session.add(test_purchase_order)
        db_session.commit()
        
        # 第二次归集（应该更新现有记录）
        result2 = CostCollectionService.collect_from_purchase_order(
            db_session,
            test_purchase_order.id
        )
        
        assert result2 is not None
        assert result2.id == result1.id  # 同一个记录
        assert result2.amount == Decimal("15000.00")  # 已更新

    def test_collect_from_purchase_order_with_custom_date(self, db_session, test_project, test_purchase_order):
        """测试从采购订单归集成本 - 自定义成本日期"""
        custom_date = date.today() - timedelta(days=10)
        result = CostCollectionService.collect_from_purchase_order(
            db_session,
            test_purchase_order.id,
            cost_date=custom_date
        )
        
        assert result is not None
        assert result.cost_date == custom_date

    def test_collect_from_outsourcing_order_success(self, db_session, test_project):
        """测试从外协订单归集成本 - 成功场景"""
        # 创建外协订单
        order = OutsourcingOrder(
            order_no="OO001",
            order_title="测试外协订单",
            project_id=test_project.id,
            total_amount=Decimal("8000.00"),
            order_date=date.today()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = CostCollectionService.collect_from_outsourcing_order(
            db_session,
            order.id
        )
        
        assert result is not None
        assert isinstance(result, ProjectCost)
        assert result.project_id == test_project.id
        assert result.amount == Decimal("8000.00")
        assert result.source_type == "OUTSOURCING_ORDER"

    def test_collect_from_outsourcing_order_no_project(self, db_session):
        """测试从外协订单归集成本 - 订单无关联项目"""
        order = OutsourcingOrder(
            order_no="OO002",
            order_title="无项目外协订单",
            project_id=None,
            total_amount=Decimal("3000.00"),
            order_date=date.today()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        result = CostCollectionService.collect_from_outsourcing_order(
            db_session,
            order.id
        )
        
        assert result is None

    def test_collect_from_ecn_success(self, db_session, test_project):
        """测试从ECN归集成本 - 成功场景"""
        # 创建ECN
        ecn = Ecn(
            ecn_no="ECN001",
            ecn_title="测试ECN",
            project_id=test_project.id,
            estimated_cost=Decimal("5000.00"),
            status="APPROVED"
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)
        
        result = CostCollectionService.collect_from_ecn(
            db_session,
            ecn.id
        )
        
        assert result is not None
        assert isinstance(result, ProjectCost)
        assert result.project_id == test_project.id
        assert result.amount == Decimal("5000.00")
        assert result.source_type == "ECN"

    def test_collect_from_ecn_no_project(self, db_session):
        """测试从ECN归集成本 - ECN无关联项目"""
        ecn = Ecn(
            ecn_no="ECN002",
            ecn_title="无项目ECN",
            project_id=None,
            estimated_cost=Decimal("2000.00"),
            status="APPROVED"
        )
        db_session.add(ecn)
        db_session.commit()
        db_session.refresh(ecn)
        
        result = CostCollectionService.collect_from_ecn(
            db_session,
            ecn.id
        )
        
        assert result is None

    def test_remove_cost_from_source_purchase(self, db_session, test_project, test_purchase_order):
        """测试移除成本 - 采购订单"""
        # 先创建成本记录
        cost = CostCollectionService.collect_from_purchase_order(
            db_session,
            test_purchase_order.id
        )
        assert cost is not None
        
        # 移除成本
        result = CostCollectionService.remove_cost_from_source(
            db_session,
            "PURCHASE",
            "PURCHASE_ORDER",
            test_purchase_order.id
        )
        
        assert result is True
        
        # 验证成本记录已删除
        deleted_cost = db_session.query(ProjectCost).filter_by(id=cost.id).first()
        assert deleted_cost is None
        
        # 验证项目成本已更新
        db_session.refresh(test_project)
        assert test_project.actual_cost == 0.0

    def test_remove_cost_from_source_not_found(self, db_session):
        """测试移除成本 - 成本记录不存在"""
        result = CostCollectionService.remove_cost_from_source(
            db_session,
            "PURCHASE",
            "PURCHASE_ORDER",
            99999
        )
        
        assert result is False
