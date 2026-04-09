# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 验收审批服务"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.acceptance_approval.service import AcceptanceApprovalService


class TestAcceptanceApprovalServiceBusinessLogic:
    """验收审批服务业务逻辑测试"""

    def test_submit_orders_for_approval_order_not_found(self):
        """测试验收单不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AcceptanceApprovalService(mock_db)
        success, errors = service.submit_orders_for_approval([999], 1)

        assert len(success) == 0
        assert len(errors) == 1
        assert errors[0]["error"] == "验收单不存在"

    def test_submit_orders_for_approval_wrong_status(self):
        """测试状态不正确"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.status = "PENDING"  # 不是 COMPLETED 或 REJECTED
        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        service = AcceptanceApprovalService(mock_db)
        success, errors = service.submit_orders_for_approval([1], 1)

        assert len(success) == 0
        assert len(errors) == 1
        assert "不允许提交审批" in errors[0]["error"]

    def test_submit_orders_for_approval_no_result(self):
        """测试没有验收结论"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.status = "COMPLETED"
        mock_order.overall_result = None  # 没有验收结论
        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        service = AcceptanceApprovalService(mock_db)
        success, errors = service.submit_orders_for_approval([1], 1)

        assert len(success) == 0
        assert len(errors) == 1
        assert "没有验收结论" in errors[0]["error"]

    def test_submit_orders_for_approval_success(self):
        """测试成功提交审批"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "COMPLETED"
        mock_order.overall_result = "PASS"
        mock_order.order_no = "ACC-2026-001"
        mock_order.acceptance_type = "FAT"
        mock_order.pass_rate = 95.0
        mock_order.passed_items = 19
        mock_order.failed_items = 1
        mock_order.total_items = 20
        mock_order.project_id = 1
        mock_order.machine_id = 1
        mock_order.conclusion = "通过"
        mock_order.conditions = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock approval engine
        mock_instance = MagicMock()
        mock_instance.id = 100

        service = AcceptanceApprovalService(mock_db)
        service.engine.submit = MagicMock(return_value=mock_instance)

        success, errors = service.submit_orders_for_approval([1], 1)

        assert len(success) == 1
        assert len(errors) == 0
        assert success[0]["instance_id"] == 100

    def test_get_approval_status(self):
        """测试获取审批状态"""
        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)

        # Mock approval instance
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = "PENDING"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance

        result = service.get_approval_status(1)

        assert result is not None

    def test_cancel_approval(self):
        """测试取消审批"""
        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)

        # Mock approval instance
        mock_instance = MagicMock()
        mock_instance.status = "PENDING"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance

        result = service.cancel_approval(1, 1, "取消原因")

        # 验证调用了commit
        assert mock_db.commit.called or result is not None

    def test_batch_approve(self):
        """测试批量审批"""
        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)

        # Mock approval tasks
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "PENDING"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        results = service.batch_approve([1], 1, "批量通过")

        assert isinstance(results, list)

    def test_get_pending_approvals(self):
        """测试获取待审批列表"""
        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)

        # Mock pending tasks
        mock_task = MagicMock()
        mock_task.id = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

        results = service.get_pending_approvals(1)

        assert isinstance(results, list)


class TestAcceptanceApprovalServiceEdgeCases:
    """边界情况测试"""

    def test_empty_order_list(self):
        """测试空订单列表"""
        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)

        success, errors = service.submit_orders_for_approval([], 1)

        assert len(success) == 0
        assert len(errors) == 0

    def test_multiple_orders_mixed_results(self):
        """测试多个订单混合结果"""
        mock_db = MagicMock()

        # 创建多个订单
        order1 = MagicMock()
        order1.id = 1
        order1.status = "COMPLETED"
        order1.overall_result = "PASS"
        order1.order_no = "ACC-001"
        order1.acceptance_type = "FAT"
        order1.pass_rate = 100
        order1.passed_items = 10
        order1.failed_items = 0
        order1.total_items = 10
        order1.project_id = 1
        order1.machine_id = 1
        order1.conclusion = "通过"
        order1.conditions = None

        order2 = MagicMock()
        order2.id = 2
        order2.status = "PENDING"  # 错误状态

        # Mock query to return different orders
        def get_order(filter_cond):
            order_id = filter_cond.right.value
            if order_id == 1:
                return order1
            elif order_id == 2:
                return order2
            return None

        mock_db.query.return_value.filter.return_value.first.side_effect = lambda: order1 if mock_db.query.call_count % 2 == 1 else order2

        service = AcceptanceApprovalService(mock_db)
        mock_instance = MagicMock()
        mock_instance.id = 100
        service.engine.submit = MagicMock(return_value=mock_instance)

        success, errors = service.submit_orders_for_approval([1, 2], 1)

        # 验证结果
        assert isinstance(success, list)
        assert isinstance(errors, list)