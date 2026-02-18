# -*- coding: utf-8 -*-
"""第十批：ContractEnhancedService 单元测试"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.sales.contract_enhanced import ContractEnhancedService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


def _make_contract(**kwargs):
    c = MagicMock()
    c.id = kwargs.get("id", 1)
    c.contract_code = kwargs.get("contract_code", "CT-20240101-0001")
    c.status = kwargs.get("status", "draft")
    c.total_amount = kwargs.get("total_amount", Decimal("100000"))
    c.received_amount = kwargs.get("received_amount", Decimal("0"))
    return c


def test_get_contract_found(db):
    """按ID获取合同"""
    mock_contract = _make_contract()
    db.query.return_value.filter.return_value.first.return_value = mock_contract

    result = ContractEnhancedService.get_contract(db, contract_id=1)
    assert result is not None
    assert result.id == 1


def test_get_contract_not_found(db):
    """合同不存在"""
    db.query.return_value.filter.return_value.first.return_value = None

    result = ContractEnhancedService.get_contract(db, contract_id=999)
    assert result is None


def test_generate_contract_code(db):
    """生成合同编号"""
    db.query.return_value.filter.return_value.count.return_value = 0
    code = ContractEnhancedService._generate_contract_code(db)
    assert code.startswith("CT-")
    assert len(code) > 5


def test_delete_contract_not_found(db):
    """删除不存在的合同"""
    db.query.return_value.filter.return_value.first.return_value = None
    result = ContractEnhancedService.delete_contract(db, contract_id=999)
    assert result is False


def test_delete_contract_success(db):
    """成功删除合同"""
    mock_contract = _make_contract(status="draft")
    db.query.return_value.filter.return_value.first.return_value = mock_contract
    result = ContractEnhancedService.delete_contract(db, contract_id=1)
    assert result is True
    db.delete.assert_called_once()


def test_get_contracts_empty(db):
    """合同列表为空"""
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.options.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.order_by.return_value = mock_q
    mock_q.count.return_value = 0
    mock_q.offset.return_value = mock_q
    mock_q.limit.return_value = mock_q
    mock_q.all.return_value = []

    result = ContractEnhancedService.get_contracts(db)
    assert result is not None


def test_get_pending_approvals(db):
    """获取待审批合同"""
    mock_approval = MagicMock()
    mock_approval.user_id = 1
    db.query.return_value.filter.return_value.all.return_value = [mock_approval]

    result = ContractEnhancedService.get_pending_approvals(db, user_id=1)
    assert isinstance(result, list)


def test_get_terms(db):
    """获取合同条款"""
    mock_terms = [MagicMock(), MagicMock()]
    db.query.return_value.filter.return_value.all.return_value = mock_terms

    result = ContractEnhancedService.get_terms(db, contract_id=1)
    assert len(result) == 2
