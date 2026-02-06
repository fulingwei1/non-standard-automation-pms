# -*- coding: utf-8 -*-
"""
Tests for data_sync_service
"""

import pytest
from datetime import date
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sales import Contract


class TestDataSyncService:
    """Test suite for DataSyncService class."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_init_service(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)

        assert service.db == db_session

    def test_sync_contract_to_project_contract_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
        return_value=Mock(
        filter=Mock(return_value=Mock(first=Mock(return_value=None)))
        )
        )

        result = service.sync_contract_to_project(999)

        assert result["success"] is False

    def test_sync_contract_to_project_not_linked_to_project(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = None

        mock_query = Mock()
        mock_query.filter = Mock(
        return_value=Mock(first=Mock(return_value=mock_contract))
        )
        db_session.query = Mock(return_value=mock_query)

        result = service.sync_contract_to_project(1)

        assert result["success"] is False
        assert "未关联项目" in result["message"]

    def test_sync_contract_to_project_project_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_contract))
                    )
                )
            else:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=None)))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_contract_to_project(1)

        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_sync_contract_to_project_sync_contract_amount(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = 150000.0

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_contract))
                    )
                )
            else:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_contract_to_project(1)

        assert result["success"] is True
        assert "已同步字段：contract_amount" in result["message"]
        assert mock_project.contract_amount == 150000.0

    def test_sync_contract_to_project_sync_contract_date(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = None
        mock_contract.signed_date = date(2025, 6, 15)

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0
        mock_project.contract_date = date(2025, 1, 1)

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_contract))
                    )
                )
            else:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_contract_to_project(1)

        assert result["success"] is True
        assert "已同步字段：contract_date" in result["message"]
        assert mock_project.contract_date == date(2025, 6, 15)

    def test_sync_contract_to_project_no_changes(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = 100000.0
        mock_contract.signed_date = date(2025, 6, 15)
        mock_contract.delivery_deadline = date(2025, 12, 31)

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0
        mock_project.contract_date = date(2025, 6, 15)
        mock_project.planned_end_date = date(2025, 12, 31)

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_contract))
                    )
                )
            else:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_contract_to_project(1)

        assert result["success"] is True
        # Message could be "数据已是最新，无需同步" or "没有需要同步的字段"
        assert "无需同步" in result.get("message", "") or "最新" in result.get("message", "")


class TestSyncPaymentPlansFromContract:
    """Test suite for sync_payment_plans_from_contract method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_contract_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.sync_payment_plans_from_contract(999)

        assert result["success"] is False
        assert "合同不存在" in result["message"]

    def test_contract_not_linked_to_project(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = None

        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
            )
        )

        result = service.sync_payment_plans_from_contract(1)

        assert result["success"] is False
        assert "未关联项目" in result["message"]

    def test_sync_payment_plans_success_with_plans(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import ProjectPaymentPlan

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100

        mock_plans = [Mock(), Mock(), Mock()]

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
                )
            elif model == ProjectPaymentPlan:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=mock_plans)))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_payment_plans_from_contract(1)

        assert result["success"] is True
        assert result["plan_count"] == 3
        assert "3 个收款计划" in result["message"]

    def test_sync_payment_plans_success_no_plans(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import ProjectPaymentPlan

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
                )
            elif model == ProjectPaymentPlan:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_payment_plans_from_contract(1)

        assert result["success"] is True
        assert result["plan_count"] == 0


class TestSyncProjectToContract:
    """Test suite for sync_project_to_contract method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_project_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.sync_project_to_contract(999)

        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_project_no_linked_contracts(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_project = Mock(spec=Project)
        mock_project.id = 100

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_project)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_project_to_contract(100)

        assert result["success"] is False
        assert "未关联合同" in result["message"]

    def test_sync_project_completed_updates_contract(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)

        class MockProject:
            id = 100
            stage = "S9"
            status = "ST30"

        class MockContract:
            id = 1
            project_id = 100
            status = "ACTIVE"

        mock_project = MockProject()
        mock_contract = MockContract()

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_project)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_contract])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_project_to_contract(100)

        assert result["success"] is True
        assert mock_contract.status == "COMPLETED"
        assert 1 in result["updated_contracts"]

    def test_sync_project_not_completed_no_update(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.stage = "S5"
        mock_project.status = "ST10"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.status = "ACTIVE"

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_project)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_contract])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_project_to_contract(100)

        assert result["success"] is True
        assert "无需同步" in result["message"] or "最新" in result["message"]


class TestGetSyncStatus:
    """Test suite for get_sync_status method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_no_params_provided(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)

        result = service.get_sync_status()

        assert result["success"] is False
        assert "请提供" in result["message"]

    def test_project_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.get_sync_status(project_id=999)

        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_get_status_by_project_id(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 150000.0

        mock_contract1 = Mock(spec=Contract)
        mock_contract1.id = 1
        mock_contract1.contract_code = "CT001"
        mock_contract1.contract_amount = 150000.0

        mock_contract2 = Mock(spec=Contract)
        mock_contract2.id = 2
        mock_contract2.contract_code = "CT002"
        mock_contract2.contract_amount = 100000.0

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_project)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_contract1, mock_contract2])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.get_sync_status(project_id=100)

        assert result["success"] is True
        assert result["project_id"] == 100
        assert result["contract_count"] == 2
        assert len(result["contracts"]) == 2
        assert result["contracts"][0]["amount_synced"] is True
        assert result["contracts"][1]["amount_synced"] is False

    def test_contract_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.get_sync_status(contract_id=999)

        assert result["success"] is False
        assert "合同不存在" in result["message"]

    def test_contract_not_linked(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = None

        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
            )
        )

        result = service.get_sync_status(contract_id=1)

        assert result["success"] is True
        assert result["contract_id"] == 1
        assert result["project_id"] is None
        assert result["synced"] is False

    def test_get_status_by_contract_id_synced(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = 150000.0
        mock_contract.signed_date = date(2025, 6, 15)

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 150000.0
        mock_project.contract_date = date(2025, 6, 15)

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_project)))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.get_sync_status(contract_id=1)

        assert result["success"] is True
        assert result["contract_id"] == 1
        assert result["project_id"] == 100
        assert result["synced"] is True
        assert result["amount_synced"] is True
        assert result["date_synced"] is True

    def test_get_status_linked_project_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_contract)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=None)))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.get_sync_status(contract_id=1)

        assert result["success"] is False
        assert "项目不存在" in result["message"]


class TestSyncCustomerToProjects:
    """Test suite for sync_customer_to_projects method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_customer_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.sync_customer_to_projects(999)

        assert result["success"] is False
        assert "客户不存在" in result["message"]

    def test_customer_no_linked_projects(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)
        mock_customer = Mock(spec=Customer)
        mock_customer.id = 1

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_projects(1)

        assert result["success"] is True
        assert result["updated_count"] == 0
        assert "没有关联项目" in result["message"]

    def test_sync_customer_name_to_projects(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "新客户名称"
            contact_person = None
            contact_phone = None

        class MockProject:
            id = 100
            customer_id = 1
            customer_name = "旧客户名称"
            customer_contact = None
            customer_phone = None

        mock_customer = MockCustomer()
        mock_project = MockProject()

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_project])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_projects(1)

        assert result["success"] is True
        assert result["updated_count"] == 1
        assert mock_project.customer_name == "新客户名称"
        assert "customer_name" in result["updated_fields"]

    def test_sync_all_customer_fields_to_projects(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "新客户名"
            contact_person = "张三"
            contact_phone = "13800138000"

        class MockProject:
            id = 100
            customer_id = 1
            customer_name = "旧客户名"
            customer_contact = "李四"
            customer_phone = "13900139000"

        mock_customer = MockCustomer()
        mock_project = MockProject()

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_project])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_projects(1)

        assert result["success"] is True
        assert result["updated_count"] == 1
        assert mock_project.customer_name == "新客户名"
        assert mock_project.customer_contact == "张三"
        assert mock_project.customer_phone == "13800138000"

    def test_sync_no_changes_needed(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "同名客户"
            contact_person = "同名联系人"
            contact_phone = "13800138000"

        class MockProject:
            id = 100
            customer_id = 1
            customer_name = "同名客户"
            customer_contact = "同名联系人"
            customer_phone = "13800138000"

        mock_customer = MockCustomer()
        mock_project = MockProject()

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Project:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_project])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_projects(1)

        assert result["success"] is True
        assert result["updated_count"] == 0
        assert "已是最新" in result["message"]


class TestSyncCustomerToContracts:
    """Test suite for sync_customer_to_contracts method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_customer_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)
        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        result = service.sync_customer_to_contracts(999)

        assert result["success"] is False
        assert "客户不存在" in result["message"]

    def test_customer_no_linked_contracts(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)
        mock_customer = Mock(spec=Customer)
        mock_customer.id = 1

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_contracts(1)

        assert result["success"] is True
        assert result["updated_count"] == 0
        assert "没有关联合同" in result["message"]

    def test_sync_customer_to_contract_with_fields(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "新客户名称"
            contact_person = "新联系人"
            contact_phone = "13800138000"

        class MockContract:
            id = 1
            customer_id = 1
            customer_name = "旧客户名称"
            contact_person = "旧联系人"
            contact_phone = "13900139000"

        mock_customer = MockCustomer()
        mock_contract = MockContract()

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_contract])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_contracts(1)

        assert result["success"] is True
        assert result["updated_count"] == 1
        assert mock_contract.customer_name == "新客户名称"
        assert mock_contract.contact_person == "新联系人"
        assert mock_contract.contact_phone == "13800138000"

    def test_sync_contract_no_redundant_fields(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "客户名称"
            contact_person = "联系人"
            contact_phone = "13800138000"

        class MockContractNoFields:
            """Contract without redundant customer fields."""
            id = 1
            customer_id = 1

        mock_customer = MockCustomer()
        mock_contract = MockContractNoFields()

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=[mock_contract])))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_contracts(1)

        assert result["success"] is True
        assert result["updated_count"] == 0
        assert "无冗余字段" in result["message"] or "已是最新" in result["message"]

    def test_sync_multiple_contracts(self, db_session):
        from app.services.data_sync_service import DataSyncService
        from app.models.project import Customer

        service = DataSyncService(db_session)

        class MockCustomer:
            id = 1
            customer_name = "新客户名"
            contact_person = None
            contact_phone = None

        class MockContract1:
            id = 1
            customer_id = 1
            customer_name = "旧名1"

        class MockContract2:
            id = 2
            customer_id = 1
            customer_name = "旧名2"

        mock_customer = MockCustomer()
        mock_contracts = [MockContract1(), MockContract2()]

        def mock_query_side_effect(model):
            if model == Customer:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_customer)))
                )
            elif model == Contract:
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=mock_contracts)))
                )

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = service.sync_customer_to_contracts(1)

        assert result["success"] is True
        assert result["updated_count"] == 2
        assert 1 in result["updated_contracts"]
        assert 2 in result["updated_contracts"]
