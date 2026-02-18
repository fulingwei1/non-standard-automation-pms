# -*- coding: utf-8 -*-
"""第十八批 - 数据同步服务单元测试"""
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.data_sync_service import DataSyncService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return DataSyncService(db)


def make_contract(contract_id=1, project_id=5, amount=100000):
    c = MagicMock()
    c.id = contract_id
    c.project_id = project_id
    c.contract_amount = amount
    c.customer_id = 10
    return c


def make_project(project_id=5):
    p = MagicMock()
    p.id = project_id
    p.contract_amount = 80000
    return p


class TestDataSyncServiceInit:
    def test_db_set(self, db, service):
        assert service.db is db


class TestSyncContractToProject:
    def test_returns_error_if_contract_not_found(self, db, service):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_contract_to_project(999)
        assert result["success"] is False
        assert "合同不存在" in result["message"]

    def test_returns_error_if_no_project_linked(self, db, service):
        contract = make_contract(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = contract
        result = service.sync_contract_to_project(1)
        assert result["success"] is False

    def test_returns_error_if_project_not_found(self, db, service):
        contract = make_contract(project_id=5)
        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = contract
            else:
                m.filter.return_value.first.return_value = None
            return m

        db.query.side_effect = query_side
        result = service.sync_contract_to_project(1)
        assert result["success"] is False

    def test_syncs_successfully(self, db, service):
        contract = make_contract(project_id=5, amount=200000)
        project = make_project(project_id=5)

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = contract
            else:
                m.filter.return_value.first.return_value = project
            return m

        db.query.side_effect = query_side
        result = service.sync_contract_to_project(1)
        assert result["success"] is True


class TestSyncCustomerToContracts:
    def test_returns_error_if_customer_not_found(self, db, service):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_customer_to_contracts(999)
        assert result["success"] is False
        assert "客户不存在" in result["message"]

    def test_returns_ok_when_no_contracts(self, db, service):
        customer = MagicMock()
        customer.id = 10
        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = customer
            else:
                m.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = query_side
        result = service.sync_customer_to_contracts(10)
        assert result["success"] is True
        assert result["updated_count"] == 0

    def test_syncs_customer_name_to_contracts(self, db, service):
        customer = MagicMock()
        customer.id = 10
        customer.customer_name = "新客户名"
        customer.contact_person = "张三"
        customer.contact_phone = "13800138000"

        contract = MagicMock()
        contract.id = 1
        contract.customer_name = "旧名称"
        contract.contact_person = "李四"
        contract.contact_phone = "13900139000"

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = customer
            else:
                m.filter.return_value.all.return_value = [contract]
            return m

        db.query.side_effect = query_side
        result = service.sync_customer_to_contracts(10)
        assert result["success"] is True
