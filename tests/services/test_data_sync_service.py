# -*- coding: utf-8 -*-
"""DataSyncService 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestDataSyncService:

    def _make_service(self):
        from app.services.data_sync_service import DataSyncService
        db = MagicMock()
        return DataSyncService(db), db

    # ---------- sync_contract_to_project ----------

    def test_sync_contract_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.sync_contract_to_project(999)
        assert result["success"] is False
        assert "合同不存在" in result["message"]

    def test_sync_contract_no_project_link(self):
        svc, db = self._make_service()
        contract = MagicMock(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = contract
        result = svc.sync_contract_to_project(1)
        assert result["success"] is False
        assert "未关联项目" in result["message"]

    def test_sync_contract_amount_updated(self):
        """合同金额变更时应同步到项目"""
        svc, db = self._make_service()
        contract = MagicMock(
            id=1, project_id=10,
            contract_amount=Decimal("500000"),
            signed_date=None,
            quote_version=None
        )
        project = MagicMock(
            id=10,
            contract_amount=Decimal("400000"),
            contract_date=None,
            planned_end_date=None
        )
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = svc.sync_contract_to_project(1)
        assert result["success"] is True
        assert "contract_amount" in result["updated_fields"]
        assert project.contract_amount == Decimal("500000")

    def test_sync_contract_no_change_needed(self):
        """数据已一致时返回无需同步"""
        svc, db = self._make_service()
        amount = Decimal("500000")
        contract = MagicMock(
            id=1, project_id=10,
            contract_amount=amount,
            signed_date=None,
            quote_version=None
        )
        project = MagicMock(
            id=10,
            contract_amount=amount,
            contract_date=None,
            planned_end_date=None
        )
        db.query.return_value.filter.return_value.first.side_effect = [contract, project]
        result = svc.sync_contract_to_project(1)
        assert result["success"] is True
        assert "无需同步" in result["message"]

    # ---------- sync_project_to_contract ----------

    def test_sync_project_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.sync_project_to_contract(999)
        assert result["success"] is False

    def test_sync_project_no_contract(self):
        svc, db = self._make_service()
        project = MagicMock(id=1, stage="S5", status="IN_PROGRESS")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.sync_project_to_contract(1)
        assert result["success"] is False
        assert "未关联合同" in result["message"]

    def test_sync_project_completed_updates_contract(self):
        """项目已结项（ST30）时更新合同状态为 COMPLETED"""
        svc, db = self._make_service()
        project = MagicMock(id=1, stage="S9", status="ST30")
        contract = MagicMock(id=10, status="ACTIVE")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [contract]
        result = svc.sync_project_to_contract(1)
        assert result["success"] is True
        assert contract.status == "COMPLETED"

    # ---------- get_sync_status ----------

    def test_get_sync_status_no_params(self):
        """两个参数都不传时返回错误提示"""
        svc, db = self._make_service()
        result = svc.get_sync_status()
        assert result["success"] is False
        assert "project_id" in result["message"]

    def test_get_sync_status_by_project(self):
        """按 project_id 查询返回合同列表"""
        svc, db = self._make_service()
        project = MagicMock(id=5, contract_amount=Decimal("100000"))
        contract = MagicMock(id=20, contract_code="C2025001", contract_amount=Decimal("100000"))
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = [contract]
        result = svc.get_sync_status(project_id=5)
        assert result["success"] is True
        assert result["project_id"] == 5
        assert len(result["contracts"]) == 1
        assert result["contracts"][0]["amount_synced"] is True

    # ---------- sync_customer_to_projects ----------

    def test_sync_customer_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.sync_customer_to_projects(999)
        assert result["success"] is False

    def test_sync_customer_no_projects(self):
        svc, db = self._make_service()
        customer = MagicMock(id=1, customer_name="客户A", contact_person="张三", contact_phone="138")
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.sync_customer_to_projects(1)
        assert result["success"] is True
        assert result["updated_count"] == 0

    def test_sync_customer_updates_project_name(self):
        """客户名称变更时项目中的 customer_name 应更新"""
        svc, db = self._make_service()
        customer = MagicMock(id=1, customer_name="新客户名", contact_person=None, contact_phone=None)
        project = MagicMock(id=100, customer_name="旧客户名", customer_contact=None, customer_phone=None)
        db.query.return_value.filter.return_value.first.return_value = customer
        db.query.return_value.filter.return_value.all.return_value = [project]
        result = svc.sync_customer_to_projects(1)
        assert result["success"] is True
        assert result["updated_count"] == 1
        assert project.customer_name == "新客户名"
