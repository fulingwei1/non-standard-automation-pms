# -*- coding: utf-8 -*-
"""
审批引擎服务单元测试

测试 ApprovalEngineService 类（组合服务）
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.models.enums import ApprovalRecordStatusEnum, ApprovalActionEnum
from app.services.approval_engine.engine import ApprovalEngineService


@pytest.mark.unit
class TestApprovalEngineServiceCombined:
    """审批引擎组合服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return ApprovalEngineService(db_session)

    def test_service_init(self, service, db_session):
        """测试服务初始化"""
        assert service is not None
        assert service.db == db_session

    def test_service_has_submit(self, service):
        """测试服务有提交方法"""
        assert hasattr(service, 'submit') or hasattr(service, 'submit_approval')

    def test_service_has_approve(self, service):
        """测试服务有审批方法"""
        assert hasattr(service, 'approve') or hasattr(service, 'approve_task')

    def test_service_has_reject(self, service):
        """测试服务有驳回方法"""
        assert hasattr(service, 'reject') or hasattr(service, 'reject_task')

    def test_service_has_withdraw(self, service):
        """测试服务有撤回方法"""
        assert hasattr(service, 'withdraw') or hasattr(service, 'withdraw_approval')

    def test_service_has_terminate(self, service):
        """测试服务有终止方法"""
        assert hasattr(service, 'terminate') or hasattr(service, 'terminate_approval')

    def test_service_has_add_cc(self, service):
        """测试服务有抄送方法"""
        assert hasattr(service, 'add_cc') or hasattr(service, 'add_cc_users')

    def test_service_has_get_pending_tasks(self, service):
        """测试服务有待办任务查询方法"""
        assert hasattr(service, 'get_pending_tasks') or hasattr(service, 'get_pending_approvals')

    def test_service_has_get_initiated_instances(self, service):
        """测试服务有发起实例查询方法"""
        assert hasattr(service, 'get_initiated_instances') or hasattr(service, 'get_my_initiated')

    def test_service_inherits_all_mixins(self, service):
        """测试服务继承了所有混入类"""
        from app.services.approval_engine.engine.submit import ApprovalSubmitMixin
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        from app.services.approval_engine.engine.actions import ApprovalActionsMixin
        from app.services.approval_engine.engine.query import ApprovalQueryMixin
        from app.services.approval_engine.engine.core import ApprovalEngineCore

        assert isinstance(service, ApprovalEngineCore)
        assert isinstance(service, ApprovalSubmitMixin)
        assert isinstance(service, ApprovalProcessMixin)
        assert isinstance(service, ApprovalActionsMixin)
        assert isinstance(service, ApprovalQueryMixin)
