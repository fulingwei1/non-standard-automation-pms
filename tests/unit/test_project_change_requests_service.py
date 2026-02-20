# -*- coding: utf-8 -*-
"""
项目变更请求服务层单元测试
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.models.enums import (
    ChangeStatusEnum,
    ChangeTypeEnum,
    ChangeSourceEnum,
    ApprovalDecisionEnum,
)
from app.schemas.change_request import (
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeApprovalRequest,
    ChangeStatusUpdateRequest,
    ChangeImplementationRequest,
    ChangeVerificationRequest,
    ChangeCloseRequest,
)
from app.services.project_change_requests import ProjectChangeRequestsService


class TestProjectChangeRequestsService(unittest.TestCase):
    """项目变更请求服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ProjectChangeRequestsService(self.db)
        self.current_user = MagicMock()
        self.current_user.id = 1
        self.current_user.real_name = "张三"
        self.current_user.username = "zhangsan"
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_generate_change_code(self, mock_get_or_404):
        """测试生成变更编号"""
        # 模拟项目
        mock_project = MagicMock()
        mock_project.project_code = "PRJ001"
        mock_get_or_404.return_value = mock_project
        
        # 模拟现有变更数量
        self.db.query.return_value.filter.return_value.scalar.return_value = 5
        
        # 执行
        code = self.service.generate_change_code(project_id=1)
        
        # 验证
        self.assertEqual(code, "CHG-PRJ001-006")
        mock_get_or_404.assert_called_once()
    
    def test_validate_status_transition_valid(self):
        """测试有效的状态转换"""
        # 从SUBMITTED到ASSESSING是合法的
        result = self.service.validate_status_transition(
            ChangeStatusEnum.SUBMITTED,
            ChangeStatusEnum.ASSESSING
        )
        self.assertTrue(result)
        
        # 从PENDING_APPROVAL到APPROVED是合法的
        result = self.service.validate_status_transition(
            ChangeStatusEnum.PENDING_APPROVAL,
            ChangeStatusEnum.APPROVED
        )
        self.assertTrue(result)
    
    def test_validate_status_transition_invalid(self):
        """测试无效的状态转换"""
        # 从CLOSED不能转换到其他状态
        result = self.service.validate_status_transition(
            ChangeStatusEnum.CLOSED,
            ChangeStatusEnum.IMPLEMENTING
        )
        self.assertFalse(result)
        
        # 从REJECTED不能转换到其他状态
        result = self.service.validate_status_transition(
            ChangeStatusEnum.REJECTED,
            ChangeStatusEnum.APPROVED
        )
        self.assertFalse(result)
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_create_change_request(self, mock_get_or_404, mock_save_obj):
        """测试创建变更请求"""
        # 模拟项目
        mock_project = MagicMock()
        mock_project.project_code = "PRJ001"
        mock_get_or_404.return_value = mock_project
        
        # 模拟变更数量
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        
        # 创建请求数据
        change_in = ChangeRequestCreate(
            project_id=1,
            title="测试变更",
            description="测试描述",
            change_type=ChangeTypeEnum.SCOPE,
            change_source=ChangeSourceEnum.CUSTOMER,
            notify_team=True,
        )
        
        # 执行
        change_request = self.service.create_change_request(change_in, self.current_user)
        
        # 验证
        self.assertEqual(change_request.change_code, "CHG-PRJ001-001")
        self.assertEqual(change_request.submitter_id, 1)
        self.assertEqual(change_request.submitter_name, "张三")
        self.assertEqual(change_request.status, ChangeStatusEnum.SUBMITTED)
        mock_save_obj.assert_called_once()
    
    def test_list_change_requests_with_filters(self):
        """测试带过滤条件的列表查询"""
        # 模拟查询链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        
        mock_changes = [MagicMock(), MagicMock()]
        mock_query.filter.return_value.filter.return_value.filter.return_value\
            .order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_changes
        
        # 执行
        with patch('app.services.project_change_requests.service.apply_pagination') as mock_paginate:
            mock_paginate.return_value.all.return_value = mock_changes
            
            changes = self.service.list_change_requests(
                offset=0,
                limit=10,
                project_id=1,
                status=ChangeStatusEnum.SUBMITTED,
            )
        
        # 验证
        self.assertEqual(len(changes), 2)
        self.db.query.assert_called_once()
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_get_change_request(self, mock_get_or_404):
        """测试获取变更请求详情"""
        # 模拟变更请求
        mock_change = MagicMock()
        mock_change.id = 1
        mock_get_or_404.return_value = mock_change
        
        # 执行
        change = self.service.get_change_request(change_id=1)
        
        # 验证
        self.assertEqual(change.id, 1)
        mock_get_or_404.assert_called_once()
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_update_change_request(self, mock_get_or_404, mock_save_obj):
        """测试更新变更请求"""
        # 模拟变更请求（SUBMITTED状态可以修改）
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.SUBMITTED
        mock_get_or_404.return_value = mock_change
        
        # 更新数据
        change_in = ChangeRequestUpdate(
            title="更新后的标题",
            description="更新后的描述",
        )
        
        # 执行
        change = self.service.update_change_request(change_id=1, change_in=change_in)
        
        # 验证
        self.assertEqual(change.title, "更新后的标题")
        mock_save_obj.assert_called_once()
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_update_change_request_invalid_status(self, mock_get_or_404):
        """测试更新已关闭的变更请求（应该失败）"""
        # 模拟已关闭的变更请求
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.CLOSED
        mock_get_or_404.return_value = mock_change
        
        # 更新数据
        change_in = ChangeRequestUpdate(title="不应该成功")
        
        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.update_change_request(change_id=1, change_in=change_in)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("不能修改", str(context.exception.detail))
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_approve_change_request(self, mock_get_or_404):
        """测试审批变更请求"""
        # 模拟待审批的变更请求
        mock_change = MagicMock()
        mock_change.id = 1
        mock_change.status = ChangeStatusEnum.PENDING_APPROVAL
        mock_get_or_404.return_value = mock_change
        
        # 审批数据
        approval_in = ChangeApprovalRequest(
            decision=ApprovalDecisionEnum.APPROVED,
            comments="同意变更",
        )
        
        # 执行
        change = self.service.approve_change_request(
            change_id=1,
            approval_in=approval_in,
            current_user=self.current_user
        )
        
        # 验证
        self.assertEqual(change.status, ChangeStatusEnum.APPROVED)
        self.assertEqual(change.approver_id, 1)
        self.assertEqual(change.approval_decision, ApprovalDecisionEnum.APPROVED)
        self.db.commit.assert_called_once()
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_approve_change_request_invalid_status(self, mock_get_or_404):
        """测试审批非待审批状态的变更（应该失败）"""
        # 模拟已提交的变更（不是待审批）
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.SUBMITTED
        mock_get_or_404.return_value = mock_change
        
        # 审批数据
        approval_in = ChangeApprovalRequest(
            decision=ApprovalDecisionEnum.APPROVED,
            comments="测试",
        )
        
        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.approve_change_request(
                change_id=1,
                approval_in=approval_in,
                current_user=self.current_user
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("待审批", str(context.exception.detail))
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_get_approval_records(self, mock_get_or_404):
        """测试获取审批记录"""
        # 模拟变更请求
        mock_change = MagicMock()
        mock_get_or_404.return_value = mock_change
        
        # 模拟审批记录
        mock_records = [MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_records
        
        # 执行
        records = self.service.get_approval_records(change_id=1)
        
        # 验证
        self.assertEqual(len(records), 2)
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_update_change_status(self, mock_get_or_404, mock_save_obj):
        """测试更新变更状态"""
        # 模拟变更请求
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.APPROVED
        mock_get_or_404.return_value = mock_change
        
        # 状态更新数据
        status_in = ChangeStatusUpdateRequest(
            new_status=ChangeStatusEnum.IMPLEMENTING,
        )
        
        # 执行
        change, old_status = self.service.update_change_status(
            change_id=1,
            status_in=status_in
        )
        
        # 验证
        self.assertEqual(change.status, ChangeStatusEnum.IMPLEMENTING)
        self.assertEqual(old_status, ChangeStatusEnum.APPROVED.value)
        mock_save_obj.assert_called_once()
    
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_update_change_status_invalid_transition(self, mock_get_or_404):
        """测试无效的状态转换（应该失败）"""
        # 模拟已关闭的变更
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.CLOSED
        mock_get_or_404.return_value = mock_change
        
        # 尝试转换到IMPLEMENTING（非法）
        status_in = ChangeStatusUpdateRequest(
            new_status=ChangeStatusEnum.IMPLEMENTING,
        )
        
        # 执行并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.update_change_status(change_id=1, status_in=status_in)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("不允许", str(context.exception.detail))
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_update_implementation_info(self, mock_get_or_404, mock_save_obj):
        """测试更新实施信息"""
        # 模拟已批准的变更
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.APPROVED
        mock_get_or_404.return_value = mock_change
        
        # 实施信息
        impl_in = ChangeImplementationRequest(
            implementation_start_date=datetime.utcnow(),
            implementation_plan="实施计划",
        )
        
        # 执行
        change = self.service.update_implementation_info(change_id=1, impl_in=impl_in)
        
        # 验证状态自动转换为IMPLEMENTING
        self.assertEqual(change.status, ChangeStatusEnum.IMPLEMENTING)
        mock_save_obj.assert_called_once()
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_verify_change_request(self, mock_get_or_404, mock_save_obj):
        """测试验证变更"""
        # 模拟验证中的变更
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.VERIFYING
        mock_get_or_404.return_value = mock_change
        
        # 验证数据
        verify_in = ChangeVerificationRequest(
            verification_notes="验证通过",
        )
        
        # 执行
        change = self.service.verify_change_request(
            change_id=1,
            verify_in=verify_in,
            current_user=self.current_user
        )
        
        # 验证
        self.assertEqual(change.status, ChangeStatusEnum.CLOSED)
        self.assertEqual(change.verified_by_id, 1)
        mock_save_obj.assert_called_once()
    
    @patch('app.services.project_change_requests.service.save_obj')
    @patch('app.services.project_change_requests.service.get_or_404')
    def test_close_change_request(self, mock_get_or_404, mock_save_obj):
        """测试关闭变更"""
        # 模拟变更请求
        mock_change = MagicMock()
        mock_change.status = ChangeStatusEnum.VERIFYING
        mock_get_or_404.return_value = mock_change
        
        # 关闭数据
        close_in = ChangeCloseRequest(
            close_notes="手动关闭",
        )
        
        # 执行
        change = self.service.close_change_request(change_id=1, close_in=close_in)
        
        # 验证
        self.assertEqual(change.status, ChangeStatusEnum.CLOSED)
        self.assertEqual(change.close_notes, "手动关闭")
        mock_save_obj.assert_called_once()
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 模拟变更数据
        mock_change1 = MagicMock()
        mock_change1.status = ChangeStatusEnum.SUBMITTED
        mock_change1.change_type = ChangeTypeEnum.SCOPE
        mock_change1.change_source = ChangeSourceEnum.CUSTOMER
        mock_change1.cost_impact = Decimal("1000.00")
        mock_change1.time_impact = 5
        
        mock_change2 = MagicMock()
        mock_change2.status = ChangeStatusEnum.APPROVED
        mock_change2.change_type = ChangeTypeEnum.DESIGN
        mock_change2.change_source = ChangeSourceEnum.INTERNAL
        mock_change2.cost_impact = Decimal("2000.00")
        mock_change2.time_impact = 10
        
        self.db.query.return_value.all.return_value = [mock_change1, mock_change2]
        
        # 执行
        stats = self.service.get_statistics()
        
        # 验证
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.total_cost_impact, Decimal("3000.00"))
        self.assertEqual(stats.total_time_impact, 15)
        self.assertEqual(stats.by_status[ChangeStatusEnum.SUBMITTED.value], 1)
        self.assertEqual(stats.by_status[ChangeStatusEnum.APPROVED.value], 1)


if __name__ == "__main__":
    unittest.main()
