# -*- coding: utf-8 -*-
"""数据同步服务测试"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.data_sync_service import DataSyncService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return DataSyncService(db)


class TestSyncContractToProject:
    def test_contract_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_contract_to_project(1)
        assert result["success"] is False

    def test_no_project_id(self, service, db):
        contract = MagicMock(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = contract
        result = service.sync_contract_to_project(1)
        assert result["success"] is False

    def test_project_not_found(self, service, db):
        contract = MagicMock(project_id=1)
        db.query.return_value.filter.return_value.first.side_effect = [contract, None]
        result = service.sync_contract_to_project(1)
        assert result["success"] is False

    def test_amount_synced(self, service, db):
        contract = MagicMock(
            project_id=1, contract_amount=Decimal("100000"),
            signed_date=None, delivery_deadline=None, quote_version=None
        )
        project = MagicMock(contract_amount=Decimal("50000"), contract_date=None, planned_end_date=None)
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.sync_contract_to_project(1)
        assert result["success"] is True
        assert "contract_amount" in result.get("updated_fields", [])

    def test_no_changes(self, service, db):
        contract = MagicMock(
            project_id=1, contract_amount=Decimal("100000"),
            signed_date=None, delivery_deadline=None, quote_version=None
        )
        project = MagicMock(contract_amount=Decimal("100000"), contract_date=None, planned_end_date=None)
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.sync_contract_to_project(1)
        assert "无需同步" in result["message"]


class TestSyncProjectToContract:
    def test_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_project_to_contract(1)
        assert result["success"] is False

    def test_no_contracts(self, service, db):
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.sync_project_to_contract(1)
        assert result["success"] is False


class TestSyncCustomerToProjects:
    def test_customer_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_customer_to_projects(1)
        assert result["success"] is False

    def test_no_projects(self, service, db):
        customer = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.sync_customer_to_projects(1)
        assert result["success"] is True
        assert result["updated_count"] == 0


class TestGetSyncStatus:
    def test_no_params(self, service):
        result = service.get_sync_status()
        assert result["success"] is False

    def test_by_project(self, service, db):
        project = MagicMock(contract_amount=Decimal("100"))
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.get_sync_status(project_id=1)
        assert result["success"] is True

    def test_by_contract(self, service, db):
        contract = MagicMock(project_id=1, contract_amount=Decimal("100"), signed_date=None)
        project = MagicMock(contract_amount=Decimal("100"), contract_date=None)
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.get_sync_status(contract_id=1)
        assert result["success"] is True


class TestSyncCustomerToContracts:
    def test_customer_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_customer_to_contracts(1)
        assert result["success"] is False

    def test_no_contracts(self, service, db):
        customer = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.sync_customer_to_contracts(1)
        assert result["success"] is True
