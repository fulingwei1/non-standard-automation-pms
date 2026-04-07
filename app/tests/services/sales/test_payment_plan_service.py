# -*- coding: utf-8 -*-
"""
收款计划服务测试
目标覆盖率: 60%+
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectPaymentPlan
from app.models.sales import Contract
from app.services.sales.payment_plan_service import PaymentPlanService


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.flush = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return PaymentPlanService(db=mock_db)


@pytest.fixture
def mock_contract():
    """模拟合同"""
    contract = Mock(spec=Contract)
    contract.id = 1
    contract.project_id = 100
    contract.contract_amount = Decimal("100000.00")
    contract.signing_date = date(2025, 1, 1)
    return contract


@pytest.fixture
def mock_project():
    """模拟项目"""
    project = Mock(spec=Project)
    project.id = 100
    project.planned_start_date = date(2025, 1, 1)
    project.planned_end_date = date(2025, 12, 31)
    return project


# ============================================================================
# 1. 验证合同测试 (4个测试)
# ============================================================================


def test_validate_contract_success(service, mock_contract, mock_project):
    """测试验证合同成功"""
    # 设置 mock - 需要模拟两次 query 调用
    # 第一次 query(Project).filter(...).first() 返回项目
    # 第二次 query(ProjectPaymentPlan).filter(...).count() 返回 0
    
    # 创建项目查询链
    project_query = Mock()
    project_query.filter.return_value.first.return_value = mock_project
    
    # 创建 payment_plans 计数查询链
    payment_query = Mock()
    payment_query.filter.return_value.count.return_value = 0
    
    # 创建 query 调用，根据 model 类型返回不同的 mock
    def query_side_effect(model):
        if model == Project:
            return project_query
        elif model == ProjectPaymentPlan:
            return payment_query
        return Mock()
    
    service.db.query = Mock(side_effect=query_side_effect)

    result = service._validate_contract(mock_contract)
    assert result is True


def test_validate_contract_no_project(service, mock_contract):
    """测试验证合同失败 - 项目不存在"""
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_db_query = Mock()
    mock_db_query.filter.return_value = mock_query
    service.db.query = Mock(return_value=mock_db_query)

    result = service._validate_contract(mock_contract)
    assert result is False


def test_validate_contract_invalid_amount(service, mock_contract):
    """测试验证合同失败 - 合同金额为0"""
    mock_contract.contract_amount = Decimal("0")
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = Mock()
    mock_db_query = Mock()
    mock_db_query.filter.return_value = mock_query
    service.db.query = Mock(return_value=mock_db_query)

    result = service._validate_contract(mock_contract)
    assert result is False


def test_validate_contract_existing_plans(service, mock_contract, mock_project):
    """测试验证合同失败 - 已有收款计划"""
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_project
    mock_query.filter.return_value.count.return_value = 5  # 已有5个收款计划
    mock_db_query = Mock()
    mock_db_query.filter.return_value = mock_query
    service.db.query = Mock(return_value=mock_db_query)

    result = service._validate_contract(mock_contract)
    assert result is False


# ============================================================================
# 2. 收款配置测试 (2个测试)
# ============================================================================


def test_get_payment_configurations(service):
    """测试获取收款计划配置"""
    configs = service._get_payment_configurations()
    
    assert len(configs) == 4
    
    # 验证预付款
    advance_config = configs[0]
    assert advance_config["payment_no"] == 1
    assert advance_config["payment_name"] == "预付款"
    assert advance_config["payment_type"] == "ADVANCE"
    assert advance_config["payment_ratio"] == 30.0
    
    # 验证发货款
    delivery_config = configs[1]
    assert delivery_config["payment_no"] == 2
    assert delivery_config["payment_ratio"] == 40.0
    
    # 验证验收款
    acceptance_config = configs[2]
    assert acceptance_config["payment_no"] == 3
    assert acceptance_config["payment_ratio"] == 25.0
    
    # 验证质保款
    warranty_config = configs[3]
    assert warranty_config["payment_no"] == 4
    assert warranty_config["payment_ratio"] == 5.0


def test_payment_configurations_total_ratio(service):
    """测试收款比例总和"""
    configs = service._get_payment_configurations()
    total_ratio = sum(c["payment_ratio"] for c in configs)
    assert total_ratio == 100.0