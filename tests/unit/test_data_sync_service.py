# -*- coding: utf-8 -*-
"""
Tests for data_sync_service service
Covers: app/services/data_sync_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 138 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.data_sync_service import DataSyncService
from app.models.project import Project
from app.models.sales import Contract
from app.models.organization import Customer


@pytest.fixture
def data_sync_service(db_session: Session):
    """创建 DataSyncService 实例"""
    return DataSyncService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        contract_amount=Decimal("100000.00"),
        contract_date=date.today(),
        planned_end_date=date.today() + timedelta(days=90)
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_contract(db_session: Session, test_project):
    """创建测试合同"""
    contract = Contract(
        contract_no="CT001",
        project_id=test_project.id,
        contract_amount=Decimal("100000.00"),
        signed_date=date.today(),
        delivery_deadline=date.today() + timedelta(days=90)
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


class TestDataSyncService:
    """Test suite for DataSyncService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = DataSyncService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_sync_contract_to_project_not_found(self, data_sync_service):
        """测试同步合同到项目 - 合同不存在"""
        result = data_sync_service.sync_contract_to_project(99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_contract_to_project_no_project(self, data_sync_service, db_session):
        """测试同步合同到项目 - 合同未关联项目"""
        contract = Contract(
            contract_no="CT002",
            project_id=None,
            contract_amount=Decimal("50000.00")
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)
        
        result = data_sync_service.sync_contract_to_project(contract.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联项目' in result['message']

    def test_sync_contract_to_project_success(self, data_sync_service, test_contract, test_project):
        """测试同步合同到项目 - 成功场景"""
        # 修改合同金额
        test_contract.contract_amount = Decimal("150000.00")
        data_sync_service.db.add(test_contract)
        data_sync_service.db.commit()
        
        result = data_sync_service.sync_contract_to_project(test_contract.id)
        
        assert result is not None
        assert result['success'] is True
        assert 'contract_amount' in result.get('updated_fields', [])
        
        # 验证项目已更新
        data_sync_service.db.refresh(test_project)
        assert test_project.contract_amount == Decimal("150000.00")

    def test_sync_contract_to_project_no_changes(self, data_sync_service, test_contract, test_project):
        """测试同步合同到项目 - 无变化"""
        result = data_sync_service.sync_contract_to_project(test_contract.id)
        
        assert result is not None
        assert result['success'] is True
        assert '无需同步' in result['message']

    def test_sync_contract_to_project_sync_delivery_deadline(self, data_sync_service, test_contract, test_project):
        """测试同步合同到项目 - 同步交期"""
        new_deadline = date.today() + timedelta(days=120)
        test_contract.delivery_deadline = new_deadline
        data_sync_service.db.add(test_contract)
        data_sync_service.db.commit()
        
        result = data_sync_service.sync_contract_to_project(test_contract.id)
        
        assert result is not None
        assert result['success'] is True
        assert 'planned_end_date' in result.get('updated_fields', [])

    def test_sync_payment_plans_from_contract_not_found(self, data_sync_service):
        """测试同步收款计划 - 合同不存在"""
        result = data_sync_service.sync_payment_plans_from_contract(99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_payment_plans_from_contract_no_project(self, data_sync_service, db_session):
        """测试同步收款计划 - 合同未关联项目"""
        contract = Contract(
            contract_no="CT003",
            project_id=None
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)
        
        result = data_sync_service.sync_payment_plans_from_contract(contract.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联项目' in result['message']

    def test_sync_project_to_contract_not_found(self, data_sync_service):
        """测试同步项目到合同 - 项目不存在"""
        result = data_sync_service.sync_project_to_contract(99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_project_to_contract_no_contract(self, data_sync_service, test_project):
        """测试同步项目到合同 - 项目未关联合同"""
        test_project.contract_id = None
        data_sync_service.db.add(test_project)
        data_sync_service.db.commit()
        
        result = data_sync_service.sync_project_to_contract(test_project.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联合同' in result['message']

    def test_get_sync_status(self, data_sync_service, test_project, test_contract):
        """测试获取同步状态"""
        result = data_sync_service.get_sync_status(
            project_id=test_project.id,
            contract_id=test_contract.id
        )
        
        assert result is not None
        assert 'project_id' in result
        assert 'contract_id' in result
        assert 'is_synced' in result

    def test_sync_customer_to_projects_not_found(self, data_sync_service):
        """测试同步客户到项目 - 客户不存在"""
        result = data_sync_service.sync_customer_to_projects(99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_customer_to_projects_success(self, data_sync_service, db_session, test_project):
        """测试同步客户到项目 - 成功场景"""
        customer = Customer(
            customer_name="测试客户",
            customer_code="C001"
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        
        # 更新项目客户
        test_project.customer_id = customer.id
        db_session.add(test_project)
        db_session.commit()
        
        result = data_sync_service.sync_customer_to_projects(customer.id)
        
        assert result is not None
        assert result['success'] is True
