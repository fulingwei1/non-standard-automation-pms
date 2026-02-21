# -*- coding: utf-8 -*-
"""
PMO立项服务单元测试

测试策略:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+

参考: tests/unit/test_condition_parser_rewrite.py
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from sqlalchemy.orm import Session

from app.models.pmo.initiation_phase import PmoProjectInitiation
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.pmo import (
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationUpdate,
)
from app.services.pmo_initiation.service import PmoInitiationService


class TestPmoInitiationServiceGetInitiations(unittest.TestCase):
    """测试获取立项列表"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_get_initiations_without_filters(self):
        """测试获取立项列表 - 无过滤条件"""
        # 模拟查询链
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 5
        
        # 模拟返回的立项列表
        mock_initiations = [
            MagicMock(id=1, application_no="IN20260221001", project_name="项目A"),
            MagicMock(id=2, application_no="IN20260221002", project_name="项目B"),
        ]
        mock_query.all.return_value = mock_initiations
        
        self.db.query.return_value = mock_query

        # 调用服务
        initiations, total = self.service.get_initiations(offset=0, limit=10)

        # 验证结果
        self.assertEqual(total, 5)
        self.assertEqual(len(initiations), 2)
        self.assertEqual(initiations[0].project_name, "项目A")
        self.db.query.assert_called_once_with(PmoProjectInitiation)

    def test_get_initiations_with_keyword(self):
        """测试获取立项列表 - 关键词搜索"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 1
        
        mock_initiations = [MagicMock(id=1, project_name="测试项目")]
        mock_query.all.return_value = mock_initiations
        
        self.db.query.return_value = mock_query

        initiations, total = self.service.get_initiations(
            offset=0, limit=10, keyword="测试"
        )

        self.assertEqual(total, 1)
        self.assertEqual(len(initiations), 1)

    def test_get_initiations_with_status_filter(self):
        """测试获取立项列表 - 状态筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.all.return_value = [MagicMock(status="DRAFT")]
        
        self.db.query.return_value = mock_query

        initiations, total = self.service.get_initiations(
            offset=0, limit=10, status="DRAFT"
        )

        self.assertEqual(total, 3)

    def test_get_initiations_with_applicant_filter(self):
        """测试获取立项列表 - 申请人筛选"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.all.return_value = [MagicMock(applicant_id=1)]
        
        self.db.query.return_value = mock_query

        initiations, total = self.service.get_initiations(
            offset=0, limit=10, applicant_id=1
        )

        self.assertEqual(total, 2)

    def test_get_initiations_pagination(self):
        """测试分页"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.all.return_value = [MagicMock() for _ in range(10)]
        
        self.db.query.return_value = mock_query

        initiations, total = self.service.get_initiations(offset=20, limit=10)

        self.assertEqual(total, 100)
        self.assertEqual(len(initiations), 10)


class TestPmoInitiationServiceGetInitiation(unittest.TestCase):
    """测试获取立项详情"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_get_initiation_exists(self):
        """测试获取存在的立项详情"""
        mock_initiation = MagicMock(id=1, project_name="测试项目")
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        
        self.db.query.return_value = mock_query

        result = self.service.get_initiation(initiation_id=1)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.project_name, "测试项目")

    def test_get_initiation_not_exists(self):
        """测试获取不存在的立项"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.db.query.return_value = mock_query

        result = self.service.get_initiation(initiation_id=999)

        self.assertIsNone(result)


class TestPmoInitiationServiceCreate(unittest.TestCase):
    """测试创建立项申请"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    @patch('app.services.pmo_initiation.service.pmo_codes')
    def test_create_initiation_success(self, mock_pmo_codes):
        """测试成功创建立项申请"""
        # Mock生成编号
        mock_pmo_codes.generate_initiation_no.return_value = "IN20260221001"
        
        # 准备输入数据
        initiation_in = InitiationCreate(
            project_name="新项目",
            project_type="NEW",
            project_level="A",
            customer_name="测试客户",
            contract_no="CT001",
            contract_amount=Decimal("100000.00"),
            required_start_date=date(2026, 3, 1),
            required_end_date=date(2026, 6, 30),
            requirement_summary="需求概述",
            technical_difficulty="MEDIUM",
            estimated_hours=500,
            resource_requirements="需要5人团队",
            risk_assessment="风险较低",
        )
        
        current_user = MagicMock(id=1, real_name="张三", username="zhangsan")
        
        # Mock数据库操作
        def side_effect_refresh(obj):
            obj.id = 1
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()
        
        self.db.refresh.side_effect = side_effect_refresh

        # 调用服务
        result = self.service.create_initiation(initiation_in, current_user)

        # 验证
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        
        # 验证传入add的对象
        added_obj = self.db.add.call_args[0][0]
        self.assertEqual(added_obj.application_no, "IN20260221001")
        self.assertEqual(added_obj.project_name, "新项目")
        self.assertEqual(added_obj.applicant_id, 1)
        self.assertEqual(added_obj.applicant_name, "张三")
        self.assertEqual(added_obj.status, "DRAFT")

    @patch('app.services.pmo_initiation.service.pmo_codes')
    def test_create_initiation_minimal_fields(self, mock_pmo_codes):
        """测试创建立项申请 - 最小必填字段"""
        mock_pmo_codes.generate_initiation_no.return_value = "IN20260221002"
        
        initiation_in = InitiationCreate(
            project_name="最小项目",
            customer_name="客户B",
        )
        
        current_user = MagicMock(id=2, real_name=None, username="user2")
        
        self.db.refresh.side_effect = lambda obj: setattr(obj, 'id', 2)

        result = self.service.create_initiation(initiation_in, current_user)

        added_obj = self.db.add.call_args[0][0]
        self.assertEqual(added_obj.project_name, "最小项目")
        self.assertEqual(added_obj.applicant_name, "user2")  # 使用username


class TestPmoInitiationServiceUpdate(unittest.TestCase):
    """测试更新立项申请"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_update_initiation_success(self):
        """测试成功更新立项"""
        # Mock现有立项（DRAFT状态）
        mock_initiation = MagicMock(
            id=1,
            status="DRAFT",
            project_name="原项目名",
            contract_amount=Decimal("50000"),
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        # 准备更新数据
        update_data = InitiationUpdate(
            project_name="新项目名",
            contract_amount=Decimal("80000"),
        )

        result = self.service.update_initiation(initiation_id=1, initiation_in=update_data)

        # 验证
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_initiation_not_found(self):
        """测试更新不存在的立项"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value = mock_query
        
        update_data = InitiationUpdate(project_name="新名称")

        with self.assertRaises(ValueError) as context:
            self.service.update_initiation(initiation_id=999, initiation_in=update_data)
        
        self.assertEqual(str(context.exception), "立项申请不存在")

    def test_update_initiation_wrong_status(self):
        """测试更新非草稿状态的立项"""
        mock_initiation = MagicMock(id=1, status="SUBMITTED")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        update_data = InitiationUpdate(project_name="新名称")

        with self.assertRaises(ValueError) as context:
            self.service.update_initiation(initiation_id=1, initiation_in=update_data)
        
        self.assertEqual(str(context.exception), "只有草稿状态的申请才能修改")


class TestPmoInitiationServiceSubmit(unittest.TestCase):
    """测试提交立项评审"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_submit_initiation_success(self):
        """测试成功提交立项"""
        mock_initiation = MagicMock(id=1, status="DRAFT")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query

        result = self.service.submit_initiation(initiation_id=1)

        # 验证状态已更新
        self.assertEqual(mock_initiation.status, "SUBMITTED")
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_submit_initiation_not_found(self):
        """测试提交不存在的立项"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.service.submit_initiation(initiation_id=999)
        
        self.assertEqual(str(context.exception), "立项申请不存在")

    def test_submit_initiation_wrong_status(self):
        """测试提交已提交的立项"""
        mock_initiation = MagicMock(id=1, status="SUBMITTED")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.service.submit_initiation(initiation_id=1)
        
        self.assertEqual(str(context.exception), "只有草稿状态的申请才能提交")


class TestPmoInitiationServiceApprove(unittest.TestCase):
    """测试立项审批通过"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_approve_initiation_without_pm(self):
        """测试审批通过 - 不指定项目经理"""
        mock_initiation = MagicMock(
            id=1,
            status="SUBMITTED",
            project_name="测试项目",
            customer_name="客户A",
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        approve_request = InitiationApproveRequest(
            review_result="评审通过",
            approved_level="A",
        )
        
        current_user = MagicMock(id=10, real_name="审批人")

        result = self.service.approve_initiation(1, approve_request, current_user)

        # 验证状态更新
        self.assertEqual(mock_initiation.status, "APPROVED")
        self.assertEqual(mock_initiation.review_result, "评审通过")
        self.assertEqual(mock_initiation.approved_level, "A")
        self.assertEqual(mock_initiation.approved_by, 10)
        self.assertIsNotNone(mock_initiation.approved_at)

    @patch.object(PmoInitiationService, '_create_project_from_initiation')
    def test_approve_initiation_with_pm(self, mock_create_project):
        """测试审批通过 - 指定项目经理并创建项目"""
        mock_initiation = MagicMock(
            id=1,
            status="SUBMITTED",
            project_name="测试项目",
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        mock_project = MagicMock(id=100, project_code="PJ260221001")
        mock_create_project.return_value = mock_project
        
        approve_request = InitiationApproveRequest(
            review_result="评审通过，指定PM",
            approved_pm_id=5,
            approved_level="B",
        )
        
        current_user = MagicMock(id=10)

        result = self.service.approve_initiation(1, approve_request, current_user)

        # 验证创建项目被调用
        mock_create_project.assert_called_once_with(mock_initiation, 5)
        self.assertEqual(mock_initiation.project_id, 100)

    def test_approve_initiation_reviewing_status(self):
        """测试审批评审中的立项"""
        mock_initiation = MagicMock(id=1, status="REVIEWING")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        approve_request = InitiationApproveRequest(review_result="通过")
        current_user = MagicMock(id=10)

        result = self.service.approve_initiation(1, approve_request, current_user)

        self.assertEqual(mock_initiation.status, "APPROVED")

    def test_approve_initiation_not_found(self):
        """测试审批不存在的立项"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value = mock_query
        
        approve_request = InitiationApproveRequest(review_result="通过")
        current_user = MagicMock(id=10)

        with self.assertRaises(ValueError) as context:
            self.service.approve_initiation(999, approve_request, current_user)
        
        self.assertEqual(str(context.exception), "立项申请不存在")

    def test_approve_initiation_wrong_status(self):
        """测试审批错误状态的立项"""
        mock_initiation = MagicMock(id=1, status="DRAFT")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        approve_request = InitiationApproveRequest(review_result="通过")
        current_user = MagicMock(id=10)

        with self.assertRaises(ValueError) as context:
            self.service.approve_initiation(1, approve_request, current_user)
        
        self.assertEqual(str(context.exception), "只有已提交或评审中的申请才能审批")


class TestPmoInitiationServiceReject(unittest.TestCase):
    """测试立项驳回"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_reject_initiation_success(self):
        """测试成功驳回立项"""
        mock_initiation = MagicMock(id=1, status="SUBMITTED")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        reject_request = InitiationRejectRequest(review_result="技术方案不可行")
        current_user = MagicMock(id=10)

        result = self.service.reject_initiation(1, reject_request, current_user)

        # 验证状态更新
        self.assertEqual(mock_initiation.status, "REJECTED")
        self.assertEqual(mock_initiation.review_result, "技术方案不可行")
        self.assertEqual(mock_initiation.approved_by, 10)
        self.assertIsNotNone(mock_initiation.approved_at)

    def test_reject_initiation_reviewing_status(self):
        """测试驳回评审中的立项"""
        mock_initiation = MagicMock(id=1, status="REVIEWING")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        reject_request = InitiationRejectRequest(review_result="需补充材料")
        current_user = MagicMock(id=10)

        result = self.service.reject_initiation(1, reject_request, current_user)

        self.assertEqual(mock_initiation.status, "REJECTED")

    def test_reject_initiation_not_found(self):
        """测试驳回不存在的立项"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value = mock_query
        
        reject_request = InitiationRejectRequest(review_result="驳回")
        current_user = MagicMock(id=10)

        with self.assertRaises(ValueError) as context:
            self.service.reject_initiation(999, reject_request, current_user)
        
        self.assertEqual(str(context.exception), "立项申请不存在")

    def test_reject_initiation_wrong_status(self):
        """测试驳回错误状态的立项"""
        mock_initiation = MagicMock(id=1, status="APPROVED")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        reject_request = InitiationRejectRequest(review_result="驳回")
        current_user = MagicMock(id=10)

        with self.assertRaises(ValueError) as context:
            self.service.reject_initiation(1, reject_request, current_user)
        
        self.assertEqual(str(context.exception), "只有已提交或评审中的申请才能驳回")


class TestPmoInitiationServiceCreateProject(unittest.TestCase):
    """测试从立项创建项目（私有方法）"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    @patch('app.utils.project_utils.init_project_stages')
    @patch('app.services.pmo_initiation.service.date')
    def test_create_project_from_initiation_new_customer(self, mock_date, mock_init_stages):
        """测试创建项目 - 新客户"""
        # Mock今天日期
        mock_date.today.return_value = date(2026, 2, 21)
        
        # Mock立项申请
        mock_initiation = MagicMock(
            id=5,
            project_name="新项目",
            customer_name="新客户",
            contract_no="CT001",
            contract_amount=Decimal("100000"),
            required_start_date=date(2026, 3, 1),
            required_end_date=date(2026, 6, 30),
            project_type="NEW",
        )
        
        # Mock客户查询（不存在）
        mock_customer_query = MagicMock()
        mock_customer_query.filter.return_value = mock_customer_query
        mock_customer_query.first.return_value = None
        
        # Mock PM查询
        mock_pm = MagicMock(id=3, real_name="项目经理", username="pm1")
        mock_pm_query = MagicMock()
        mock_pm_query.filter.return_value = mock_pm_query
        mock_pm_query.first.return_value = mock_pm
        
        # Mock项目编码查询（不存在重复）
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = None
        
        def query_side_effect(model):
            if model == Customer:
                return mock_customer_query
            elif model == User:
                return mock_pm_query
            elif model == Project:
                return mock_project_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        # Mock flush给项目设置ID
        def flush_side_effect():
            added_project = self.db.add.call_args_list[-1][0][0]
            added_project.id = 100
        
        self.db.flush.side_effect = flush_side_effect

        # 调用方法
        result = self.service._create_project_from_initiation(mock_initiation, pm_id=3)

        # 验证项目创建
        self.db.add.assert_called()
        self.db.flush.assert_called_once()
        
        # 验证初始化阶段被调用
        mock_init_stages.assert_called_once_with(self.db, 100)
        
        # 验证项目对象属性 - 获取最后一次 add 调用的对象
        added_project = self.db.add.call_args_list[-1][0][0]
        
        self.assertIsNotNone(added_project)
        self.assertEqual(added_project.project_code, "PJ260221005")
        self.assertEqual(added_project.project_name, "新项目")
        self.assertEqual(added_project.pm_id, 3)
        self.assertEqual(added_project.pm_name, "项目经理")

    @patch('app.utils.project_utils.init_project_stages')
    @patch('app.services.pmo_initiation.service.date')
    def test_create_project_from_initiation_existing_customer(self, mock_date, mock_init_stages):
        """测试创建项目 - 已有客户"""
        mock_date.today.return_value = date(2026, 2, 21)
        
        mock_initiation = MagicMock(
            id=3,
            project_name="项目B",
            customer_name="老客户",
            contract_no="CT002",
            contract_amount=None,  # 测试空金额
            required_start_date=date(2026, 4, 1),
            required_end_date=date(2026, 7, 31),
            project_type="UPGRADE",
        )
        
        # Mock客户查询（存在）
        mock_customer = MagicMock(id=20, customer_name="老客户")
        mock_customer_query = MagicMock()
        mock_customer_query.filter.return_value = mock_customer_query
        mock_customer_query.first.return_value = mock_customer
        
        mock_pm = MagicMock(id=5, real_name="经理B", username="pmb")
        mock_pm_query = MagicMock()
        mock_pm_query.filter.return_value = mock_pm_query
        mock_pm_query.first.return_value = mock_pm
        
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.return_value = None
        
        def query_side_effect(model):
            if model == Customer:
                return mock_customer_query
            elif model == User:
                return mock_pm_query
            elif model == Project:
                return mock_project_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        self.db.flush.side_effect = lambda: setattr(
            self.db.add.call_args_list[-1][0][0], 'id', 200
        )

        result = self.service._create_project_from_initiation(mock_initiation, pm_id=5)

        # 验证
        added_project = self.db.add.call_args_list[-1][0][0]
        self.assertEqual(added_project.customer_id, 20)
        self.assertEqual(added_project.contract_amount, Decimal("0"))

    @patch('app.utils.project_utils.init_project_stages')
    @patch('app.services.pmo_initiation.service.date')
    def test_create_project_duplicate_code(self, mock_date, mock_init_stages):
        """测试创建项目 - 项目编码重复"""
        mock_date.today.return_value = date(2026, 2, 21)
        
        mock_initiation = MagicMock(
            id=10,
            project_name="项目C",
            customer_name="客户C",
            contract_no="CT003",
            contract_amount=Decimal("200000"),
            required_start_date=date(2026, 5, 1),
            required_end_date=date(2026, 8, 31),
            project_type="NEW",
        )
        
        # Mock项目编码查询（第一次存在，第二次不存在）
        existing_project = MagicMock(project_code="PJ260221010")
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.first.side_effect = [existing_project, None]
        
        mock_customer_query = MagicMock()
        mock_customer_query.filter.return_value = mock_customer_query
        mock_customer_query.first.return_value = None
        
        mock_pm = MagicMock(id=7, real_name=None, username="pm7")
        mock_pm_query = MagicMock()
        mock_pm_query.filter.return_value = mock_pm_query
        mock_pm_query.first.return_value = mock_pm
        
        def query_side_effect(model):
            if model == Project:
                return mock_project_query
            elif model == Customer:
                return mock_customer_query
            elif model == User:
                return mock_pm_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        self.db.flush.side_effect = lambda: setattr(
            self.db.add.call_args_list[-1][0][0], 'id', 300
        )

        result = self.service._create_project_from_initiation(mock_initiation, pm_id=7)

        # 验证使用了备用编码（4位数）
        added_project = self.db.add.call_args_list[-1][0][0]
        self.assertEqual(added_project.project_code, "PJ2602210010")
        self.assertEqual(added_project.pm_name, "pm7")  # 使用username


class TestPmoInitiationServiceEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.service = PmoInitiationService(self.db)

    def test_get_initiations_empty_result(self):
        """测试查询空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query

        initiations, total = self.service.get_initiations(offset=0, limit=10)

        self.assertEqual(total, 0)
        self.assertEqual(len(initiations), 0)

    def test_update_with_empty_data(self):
        """测试使用空数据更新"""
        mock_initiation = MagicMock(id=1, status="DRAFT")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_initiation
        self.db.query.return_value = mock_query
        
        # 空更新（exclude_unset=True会返回空字典）
        update_data = InitiationUpdate()

        result = self.service.update_initiation(1, update_data)

        # 验证仍然调用了数据库操作
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
