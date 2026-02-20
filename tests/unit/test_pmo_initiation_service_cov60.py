# -*- coding: utf-8 -*-
"""
PMO 立项管理服务层单元测试
覆盖率目标：60%+
"""
import unittest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.pmo_initiation import PmoInitiationService
from app.schemas.pmo import (
    InitiationCreate,
    InitiationUpdate,
    InitiationApproveRequest,
    InitiationRejectRequest,
)


class TestPmoInitiationService(unittest.TestCase):
    """PMO 立项管理服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = PmoInitiationService(self.db)
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.real_name = "测试用户"
        self.mock_user.username = "testuser"

    def test_get_initiations_success(self):
        """测试获取立项列表 - 成功"""
        # Mock query chain
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.all.return_value = []

        initiations, total = self.service.get_initiations(
            offset=0, limit=10, keyword="测试", status="DRAFT", applicant_id=1
        )

        self.assertEqual(total, 10)
        self.assertEqual(initiations, [])
        self.db.query.assert_called_once()

    def test_get_initiation_found(self):
        """测试获取立项详情 - 找到"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        result = self.service.get_initiation(1)

        self.assertEqual(result, mock_initiation)
        self.db.query.assert_called_once()

    def test_get_initiation_not_found(self):
        """测试获取立项详情 - 未找到"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.service.get_initiation(999)

        self.assertIsNone(result)

    @patch("app.services.pmo_initiation.service.pmo_codes")
    def test_create_initiation_success(self, mock_pmo_codes):
        """测试创建立项申请 - 成功"""
        mock_pmo_codes.generate_initiation_no.return_value = "LX20260220001"

        initiation_in = InitiationCreate(
            project_name="测试项目",
            project_type="T1",
            project_level="L1",
            customer_name="测试客户",
            contract_no="CT001",
            contract_amount=Decimal("100000"),
            required_start_date=date(2026, 3, 1),
            required_end_date=date(2026, 12, 31),
            requirement_summary="需求摘要",
        )

        result = self.service.create_initiation(initiation_in, self.mock_user)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_initiation_success(self):
        """测试更新立项申请 - 成功"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_initiation.status = "DRAFT"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        initiation_in = InitiationUpdate(project_name="更新后的项目名")

        result = self.service.update_initiation(1, initiation_in)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_initiation_not_draft(self):
        """测试更新立项申请 - 非草稿状态"""
        mock_initiation = MagicMock()
        mock_initiation.status = "SUBMITTED"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        initiation_in = InitiationUpdate(project_name="更新后的项目名")

        with self.assertRaises(ValueError) as ctx:
            self.service.update_initiation(1, initiation_in)

        self.assertIn("只有草稿状态", str(ctx.exception))

    def test_submit_initiation_success(self):
        """测试提交立项申请 - 成功"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_initiation.status = "DRAFT"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        result = self.service.submit_initiation(1)

        self.assertEqual(mock_initiation.status, "SUBMITTED")
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_approve_initiation_without_pm(self):
        """测试审批通过 - 不指定项目经理"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_initiation.status = "SUBMITTED"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        approve_request = InitiationApproveRequest(
            review_result="通过", approved_level="L1"
        )

        result = self.service.approve_initiation(1, approve_request, self.mock_user)

        self.assertEqual(mock_initiation.status, "APPROVED")
        self.assertEqual(mock_initiation.approved_by, 1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_approve_initiation_with_pm(self):
        """测试审批通过 - 指定项目经理（创建项目）"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_initiation.status = "SUBMITTED"
        mock_initiation.project_name = "测试项目"
        mock_initiation.customer_name = "测试客户"
        mock_initiation.contract_no = "CT001"
        mock_initiation.contract_amount = Decimal("100000")
        mock_initiation.required_start_date = date(2026, 3, 1)
        mock_initiation.required_end_date = date(2026, 12, 31)
        mock_initiation.project_type = "T1"

        # Mock project query
        mock_project_query = MagicMock()
        mock_customer_query = MagicMock()
        mock_pm_query = MagicMock()

        def query_side_effect(model):
            if "Project" in str(model):
                return mock_project_query
            elif "Customer" in str(model):
                return mock_customer_query
            elif "User" in str(model):
                return mock_pm_query
            else:
                mock_q = MagicMock()
                mock_q.filter.return_value = mock_q
                mock_q.first.return_value = mock_initiation
                return mock_q

        self.db.query.side_effect = query_side_effect

        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = None

        mock_customer_query.filter.return_value = mock_customer_query
        mock_customer_query.first.return_value = None

        mock_pm = MagicMock()
        mock_pm.id = 2
        mock_pm.real_name = "项目经理"
        mock_pm_query.filter.return_value = mock_pm_query
        mock_pm_query.first.return_value = mock_pm

        approve_request = InitiationApproveRequest(
            review_result="通过", approved_pm_id=2, approved_level="L1"
        )

        with patch("app.services.pmo_initiation.service.init_project_stages"):
            result = self.service.approve_initiation(
                1, approve_request, self.mock_user
            )

        self.assertEqual(mock_initiation.status, "APPROVED")
        self.db.flush.assert_called_once()
        self.db.commit.assert_called_once()

    def test_reject_initiation_success(self):
        """测试驳回立项申请 - 成功"""
        mock_initiation = MagicMock()
        mock_initiation.id = 1
        mock_initiation.status = "SUBMITTED"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        reject_request = InitiationRejectRequest(review_result="不符合要求")

        result = self.service.reject_initiation(1, reject_request, self.mock_user)

        self.assertEqual(mock_initiation.status, "REJECTED")
        self.assertEqual(mock_initiation.approved_by, 1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_reject_initiation_invalid_status(self):
        """测试驳回立项申请 - 状态不允许"""
        mock_initiation = MagicMock()
        mock_initiation.status = "APPROVED"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation

        reject_request = InitiationRejectRequest(review_result="不符合要求")

        with self.assertRaises(ValueError) as ctx:
            self.service.reject_initiation(1, reject_request, self.mock_user)

        self.assertIn("只有已提交或评审中", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
