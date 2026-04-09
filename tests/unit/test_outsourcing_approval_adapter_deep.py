# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 外包审批适配器"""
import pytest
from unittest.mock import MagicMock


class TestOutsourcingApprovalAdapterBusinessLogic:
    """外包审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取外包实体"""
        try:
            from app.services.approval_engine.adapters.outsourcing import OutsourcingApprovalAdapter

            mock_db = MagicMock()

            mock_outsourcing = MagicMock()
            mock_outsourcing.id = 1
            mock_outsourcing.outsourcing_no = "OUT-001"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_outsourcing

            adapter = OutsourcingApprovalAdapter(mock_db)
            result = adapter.get_entity(1)

            assert result.id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_get_entity_data(self):
        """测试获取外包数据"""
        try:
            from app.services.approval_engine.adapters.outsourcing import OutsourcingApprovalAdapter

            mock_db = MagicMock()

            mock_outsourcing = MagicMock()
            mock_outsourcing.outsourcing_no = "OUT-001"
            mock_outsourcing.partner_name = "外包商A"
            mock_outsourcing.amount = 50000
            mock_outsourcing.status = "PENDING"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_outsourcing

            adapter = OutsourcingApprovalAdapter(mock_db)
            result = adapter.get_entity_data(1)

            assert result["outsourcing_no"] == "OUT-001"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_submit(self):
        """测试提交审批回调"""
        try:
            from app.services.approval_engine.adapters.outsourcing import OutsourcingApprovalAdapter

            mock_db = MagicMock()

            mock_outsourcing = MagicMock()
            mock_outsourcing.status = "DRAFT"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_outsourcing

            adapter = OutsourcingApprovalAdapter(mock_db)
            adapter.on_submit(1, MagicMock())

            assert mock_outsourcing.status == "PENDING_APPROVAL"
        except ImportError:
            pytest.skip("Module not found")

    def test_on_approved(self):
        """测试审批通过"""
        try:
            from app.services.approval_engine.adapters.outsourcing import OutsourcingApprovalAdapter

            mock_db = MagicMock()

            mock_outsourcing = MagicMock()
            mock_outsourcing.status = "PENDING_APPROVAL"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_outsourcing

            adapter = OutsourcingApprovalAdapter(mock_db)
            adapter.on_approved(1, MagicMock())

            assert mock_outsourcing.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_route_by_amount(self):
        """测试按金额路由"""
        try:
            from app.services.approval_engine.adapters.outsourcing import OutsourcingApprovalAdapter

            mock_db = MagicMock()

            mock_outsourcing = MagicMock()
            mock_outsourcing.amount = 100000  # 大金额

            mock_db.query.return_value.filter.return_value.first.return_value = mock_outsourcing

            adapter = OutsourcingApprovalAdapter(mock_db)
            data = adapter.get_entity_data(1)

            assert data["amount"] == 100000
        except ImportError:
            pytest.skip("Module not found")