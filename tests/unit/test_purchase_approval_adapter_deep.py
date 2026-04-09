# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 采购审批适配器"""
import pytest
from unittest.mock import MagicMock


class TestPurchaseApprovalAdapterBusinessLogic:
    """采购审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取采购实体"""
        try:
            from app.services.approval_engine.adapters.purchase import PurchaseApprovalAdapter

            mock_db = MagicMock()

            mock_purchase = MagicMock()
            mock_purchase.id = 1
            mock_purchase.purchase_no = "PO-2026-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_purchase

            adapter = PurchaseApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取采购数据"""
        try:
            from app.services.approval_engine.adapters.purchase import PurchaseApprovalAdapter

            mock_db = MagicMock()

            mock_purchase = MagicMock()
            mock_purchase.purchase_no = "PO-001"
            mock_purchase.supplier_name = "供应商A"
            mock_purchase.amount = 10000
            mock_purchase.status = "PENDING"
            mock_purchase.purchase_type = "MATERIAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_purchase

            adapter = PurchaseApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["purchase_no"] == "PO-001"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批回调"""
        try:
            from app.services.approval_engine.adapters.purchase import PurchaseApprovalAdapter

            mock_db = MagicMock()

            mock_purchase = MagicMock()
            mock_purchase.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_purchase

            adapter = PurchaseApprovalAdapter(mock_db)
            adapter.on_submit(1, MagicMock())

            assert mock_purchase.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过回调"""
        try:
            from app.services.approval_engine.adapters.purchase import PurchaseApprovalAdapter

            mock_db = MagicMock()

            mock_purchase = MagicMock()
            mock_purchase.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_purchase

            adapter = PurchaseApprovalAdapter(mock_db)
            adapter.on_approved(1, MagicMock())

            assert mock_purchase.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_rejected(self):
        """测试审批拒绝回调"""
        try:
            from app.services.approval_engine.adapters.purchase import PurchaseApprovalAdapter

            mock_db = MagicMock()

            mock_purchase = MagicMock()
            mock_purchase.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_purchase

            adapter = PurchaseApprovalAdapter(mock_db)
            adapter.on_rejected(1, MagicMock(), "金额过高")

            assert mock_purchase.status == "REJECTED"
        except ImportError:
            pytest.skip("Module not found")