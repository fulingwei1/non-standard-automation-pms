# -*- coding: utf-8 -*-
"""
DataSyncService 综合单元测试

测试覆盖:
- sync_contract_to_project: 同步合同数据到项目
- sync_payment_plans_from_contract: 同步收款计划
- sync_project_to_contract: 同步项目数据到合同
- get_sync_status: 获取同步状态
- sync_customer_to_projects: 同步客户信息到项目
- sync_customer_to_contracts: 同步客户信息到合同
"""

from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestSyncContractToProject:
    """测试 sync_contract_to_project 方法"""

    def test_returns_error_when_contract_not_found(self):
        """测试合同不存在时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DataSyncService(mock_db)
        result = service.sync_contract_to_project(999)

        assert result['success'] is False
        assert "合同不存在" in result['message']

    def test_returns_error_when_no_project_linked(self):
        """测试合同未关联项目时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.project_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        service = DataSyncService(mock_db)
        result = service.sync_contract_to_project(1)

        assert result['success'] is False
        assert "未关联项目" in result['message']

    def test_syncs_contract_amount(self):
        """测试同步合同金额"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.project_id = 10
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.signed_date = None
        mock_contract.quote_version = None

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.contract_amount = Decimal("50000")

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_contract
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_contract_to_project(1)

        assert result['success'] is True
        assert "contract_amount" in result['updated_fields']
        assert mock_project.contract_amount == Decimal("100000")

    def test_returns_no_sync_needed(self):
        """测试数据已是最新时"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.project_id = 10
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.signed_date = None
        mock_contract.quote_version = None

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.contract_amount = Decimal("100000")

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_contract
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_contract_to_project(1)

        assert result['success'] is True
        assert "无需同步" in result['message']


class TestSyncPaymentPlansFromContract:
    """测试 sync_payment_plans_from_contract 方法"""

    def test_returns_error_when_contract_not_found(self):
        """测试合同不存在时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DataSyncService(mock_db)
        result = service.sync_payment_plans_from_contract(999)

        assert result['success'] is False

    def test_returns_plan_count(self):
        """测试返回收款计划数量"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.project_id = 10

        mock_plans = [MagicMock(), MagicMock(), MagicMock()]

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_contract
            else:
                result.all.return_value = mock_plans
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_payment_plans_from_contract(1)

        assert result['success'] is True
        assert result['plan_count'] == 3


class TestSyncProjectToContract:
    """测试 sync_project_to_contract 方法"""

    def test_returns_error_when_project_not_found(self):
        """测试项目不存在时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DataSyncService(mock_db)
        result = service.sync_project_to_contract(999)

        assert result['success'] is False
        assert "项目不存在" in result['message']

    def test_returns_error_when_no_contracts(self):
        """测试项目无关联合同时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_project
            else:
                result.all.return_value = []
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_project_to_contract(1)

        assert result['success'] is False
        assert "未关联合同" in result['message']

    def test_updates_contract_status_on_project_completion(self):
        """测试项目完成时更新合同状态"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = "S9"
        mock_project.status = "ST30"

        mock_contract = MagicMock()
        mock_contract.id = 100
        mock_contract.status = "IN_PROGRESS"

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_project
            else:
                result.all.return_value = [mock_contract]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_project_to_contract(1)

        assert result['success'] is True
        assert mock_contract.status == "COMPLETED"
        assert 100 in result['updated_contracts']


class TestGetSyncStatus:
    """测试 get_sync_status 方法"""

    def test_returns_error_when_no_params(self):
        """测试无参数时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        service = DataSyncService(mock_db)

        result = service.get_sync_status()

        assert result['success'] is False
        assert "请提供" in result['message']

    def test_returns_project_sync_status(self):
        """测试返回项目同步状态"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")

        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.contract_code = "CT001"
        mock_contract.contract_amount = Decimal("100000")

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_project
            else:
                result.all.return_value = [mock_contract]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.get_sync_status(project_id=1)

        assert result['success'] is True
        assert result['project_id'] == 1
        assert result['contract_count'] == 1
        assert result['contracts'][0]['amount_synced'] is True

    def test_returns_contract_sync_status(self):
        """测试返回合同同步状态"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.project_id = 10
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.signed_date = date.today()

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.contract_amount = Decimal("100000")
        mock_project.contract_date = date.today()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_contract
            else:
                result.first.return_value = mock_project
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.get_sync_status(contract_id=1)

        assert result['success'] is True
        assert result['contract_id'] == 1
        assert result['project_id'] == 10
        assert result['amount_synced'] is True
        assert result['date_synced'] is True


class TestSyncCustomerToProjects:
    """测试 sync_customer_to_projects 方法"""

    def test_returns_error_when_customer_not_found(self):
        """测试客户不存在时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_projects(999)

        assert result['success'] is False
        assert "客户不存在" in result['message']

    def test_returns_zero_when_no_projects(self):
        """测试无关联项目时返回0"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = []
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_projects(1)

        assert result['success'] is True
        assert result['updated_count'] == 0

    def test_syncs_customer_name(self):
        """测试同步客户名称"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "新客户名称"
        mock_customer.contact_person = None
        mock_customer.contact_phone = None

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.customer_name = "旧客户名称"
        mock_project.customer_contact = None
        mock_project.customer_phone = None

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = [mock_project]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_projects(1)

        assert result['success'] is True
        assert result['updated_count'] == 1
        assert mock_project.customer_name == "新客户名称"

    def test_syncs_multiple_fields(self):
        """测试同步多个字段"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "新名称"
        mock_customer.contact_person = "新联系人"
        mock_customer.contact_phone = "13800138000"

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.customer_name = "旧名称"
        mock_project.customer_contact = "旧联系人"
        mock_project.customer_phone = "13900139000"

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = [mock_project]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_projects(1)

        assert result['success'] is True
        assert "customer_name" in result['updated_fields']
        assert "customer_contact" in result['updated_fields']
        assert "customer_phone" in result['updated_fields']


class TestSyncCustomerToContracts:
    """测试 sync_customer_to_contracts 方法"""

    def test_returns_error_when_customer_not_found(self):
        """测试客户不存在时返回错误"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_contracts(999)

        assert result['success'] is False
        assert "客户不存在" in result['message']

    def test_returns_zero_when_no_contracts(self):
        """测试无关联合同时返回0"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = []
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_contracts(1)

        assert result['success'] is True
        assert result['updated_count'] == 0

    def test_syncs_customer_name_to_contract(self):
        """测试同步客户名称到合同"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "新客户名称"
        mock_customer.contact_person = None
        mock_customer.contact_phone = None

        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.customer_name = "旧客户名称"

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = [mock_contract]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_contracts(1)

        assert result['success'] is True
        assert mock_contract.customer_name == "新客户名称"

    def test_skips_contracts_without_redundant_fields(self):
        """测试跳过没有冗余字段的合同"""
        from app.services.data_sync_service import DataSyncService

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "新名称"
        mock_customer.contact_person = None
        mock_customer.contact_phone = None

        # 创建没有 customer_name 属性的合同
        mock_contract = MagicMock(spec=['id'])
        mock_contract.id = 10

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_customer
            else:
                result.all.return_value = [mock_contract]
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = DataSyncService(mock_db)
        result = service.sync_customer_to_contracts(1)

        assert result['success'] is True
        assert result['updated_count'] == 0
