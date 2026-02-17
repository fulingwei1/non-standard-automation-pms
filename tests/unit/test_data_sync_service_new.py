# -*- coding: utf-8 -*-
"""
数据同步服务单元测试补充 (F组)

补充更多测试场景，提高 data_sync_service.py 覆盖率
"""
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


# ============================================================
# sync_contract_to_project - 更多场景
# ============================================================

class TestSyncContractToProjectExtended:

    def test_syncs_delivery_deadline(self, service, db):
        """测试同步 delivery_deadline"""
        from datetime import date
        contract = MagicMock(
            project_id=1,
            contract_amount=None,
            signed_date=None,
            delivery_deadline=date(2025, 6, 30),
            quote_version=None
        )
        project = MagicMock(
            contract_amount=None, contract_date=None,
            planned_end_date=date(2025, 5, 31)
        )
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.sync_contract_to_project(1)
        assert result["success"] is True
        assert "planned_end_date" in result.get("updated_fields", [])

    def test_syncs_contract_date(self, service, db):
        """测试同步合同签订日期"""
        from datetime import date
        contract = MagicMock(
            project_id=1,
            contract_amount=None,
            signed_date=date(2025, 1, 15),
            delivery_deadline=None,
            quote_version=None
        )
        project = MagicMock(
            contract_amount=None, contract_date=None,
            planned_end_date=None
        )
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.sync_contract_to_project(1)
        assert result["success"] is True
        assert "contract_date" in result.get("updated_fields", [])

    def test_syncs_from_quote_version(self, service, db):
        """测试从 quote_version 获取交期"""
        from datetime import date
        quote_version = MagicMock(delivery_date=date(2025, 7, 1))
        contract = MagicMock(
            project_id=1,
            contract_amount=None,
            signed_date=None,
            delivery_deadline=None,
            quote_version=quote_version
        )
        project = MagicMock(
            contract_amount=None, contract_date=None,
            planned_end_date=date(2025, 5, 1)
        )
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = service.sync_contract_to_project(1)
        assert result["success"] is True


# ============================================================
# sync_payment_plans_from_contract 测试
# ============================================================

class TestSyncPaymentPlansFromContract:

    def test_contract_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_payment_plans_from_contract(1)
        assert result["success"] is False

    def test_contract_no_project(self, service, db):
        contract = MagicMock(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = contract
        result = service.sync_payment_plans_from_contract(1)
        assert result["success"] is False

    def test_returns_plan_count(self, service, db):
        contract = MagicMock(project_id=1)
        plan1 = MagicMock()
        plan2 = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = contract
        db.query.return_value.filter.return_value.all.return_value = [plan1, plan2]
        result = service.sync_payment_plans_from_contract(1)
        assert result["success"] is True
        assert result["plan_count"] == 2


# ============================================================
# sync_project_to_contract - 更多场景
# ============================================================

class TestSyncProjectToContractExtended:

    def test_project_completed_updates_contract(self, service, db):
        """测试项目结项时更新合同状态"""
        project = MagicMock(id=1, stage="S9", status="ST30")
        contract = MagicMock(status="ACTIVE", id=1)
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [contract]
        result = service.sync_project_to_contract(1)
        assert result["success"] is True
        assert contract.status == "COMPLETED"

    def test_project_in_progress_no_update(self, service, db):
        """测试进行中的项目不更新合同"""
        project = MagicMock(id=1, stage="S5", status="ST15")
        contract = MagicMock(status="ACTIVE", id=1)
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [contract]
        result = service.sync_project_to_contract(1)
        assert result["success"] is True
        assert "无需同步" in result["message"]


# ============================================================
# sync_customer_to_projects - 更多场景
# ============================================================

class TestSyncCustomerToProjectsExtended:

    def test_syncs_name_contact_phone(self, service, db):
        """测试同步客户名称、联系人、电话"""
        customer = MagicMock(
            customer_name="新名称",
            contact_person="新联系人",
            contact_phone="13900000000"
        )
        project = MagicMock(
            customer_name="旧名称",
            customer_contact="旧联系人",
            customer_phone="13800000000"
        )
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = [project]
        result = service.sync_customer_to_projects(1)
        assert result["success"] is True
        assert result["updated_count"] == 1
        assert project.customer_name == "新名称"

    def test_no_update_when_data_same(self, service, db):
        """测试数据相同时不更新"""
        customer = MagicMock(
            customer_name="名称A",
            contact_person="联系人A",
            contact_phone="13900000000"
        )
        project = MagicMock(
            customer_name="名称A",
            customer_contact="联系人A",
            customer_phone="13900000000"
        )
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = [project]
        result = service.sync_customer_to_projects(1)
        assert result["updated_count"] == 0


# ============================================================
# sync_customer_to_contracts - 更多场景
# ============================================================

class TestSyncCustomerToContractsExtended:

    def test_syncs_contract_customer_name(self, service, db):
        """测试同步合同中客户名称字段"""
        customer = MagicMock(
            customer_name="新名称",
            contact_person="新联系人",
            contact_phone="13900000000"
        )
        contract = MagicMock(
            customer_name="旧名称",
            contact_person="旧联系人",
            contact_phone="13800000000"
        )
        # hasattr must return True for contract attributes
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = [contract]
        result = service.sync_customer_to_contracts(1)
        assert result["success"] is True

    def test_no_contracts_for_customer(self, service, db):
        customer = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.sync_customer_to_contracts(1)
        assert result["success"] is True
        assert result["updated_count"] == 0


# ============================================================
# get_sync_status - 更多场景
# ============================================================

class TestGetSyncStatusExtended:

    def test_contract_no_project_association(self, service, db):
        """测试合同未关联项目"""
        contract = MagicMock(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = contract
        result = service.get_sync_status(contract_id=1)
        assert result["success"] is True
        assert result["project_id"] is None
        assert result["synced"] is False

    def test_contract_project_not_found(self, service, db):
        """测试合同关联的项目不存在"""
        contract = MagicMock(project_id=99)
        db.query.return_value.filter.return_value.first.side_effect = [contract, None]
        result = service.get_sync_status(contract_id=1)
        assert result["success"] is False

    def test_project_with_amount_sync_check(self, service, db):
        """测试项目金额是否同步检查"""
        project = MagicMock(contract_amount=Decimal("100000"))
        c = MagicMock(
            id=1, contract_code="CT001",
            contract_amount=Decimal("100000")
        )
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [c]
        result = service.get_sync_status(project_id=1)
        assert result["success"] is True
        assert result["contracts"][0]["amount_synced"] is True

    def test_project_with_amount_not_synced(self, service, db):
        """测试项目金额不同步时的状态"""
        project = MagicMock(contract_amount=Decimal("100000"))
        c = MagicMock(
            id=1, contract_code="CT001",
            contract_amount=Decimal("90000")
        )
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [c]
        result = service.get_sync_status(project_id=1)
        assert result["contracts"][0]["amount_synced"] is False
