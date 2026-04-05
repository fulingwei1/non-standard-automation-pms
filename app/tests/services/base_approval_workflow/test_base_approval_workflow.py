# -*- coding: utf-8 -*-
"""
审批工作流基类服务测试

测试 BaseApprovalWorkflowService 的核心功能
仅测试不依赖外部导入的简单功能
"""

from unittest.mock import Mock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session


class TestBaseApprovalWorkflowService:
    """审批工作流基类服务测试类 - 简单功能测试"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟的数据库会话"""
        db = Mock(spec=Session)
        return db

    def test_get_entity_no_with_order_no(self):
        """测试获取实体编号 - 使用order_no字段"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        # 直接测试 _get_entity_no 方法
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        entity = Mock()
        entity.id = 1
        entity.order_no = "ORD001"
        
        result = service._get_entity_no(entity)
        assert result == "ORD001"

    def test_get_entity_no_with_contract_no(self):
        """测试获取实体编号 - 使用contract_no字段"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        entity = Mock()
        entity.id = 1
        entity.contract_no = "CON001"
        
        result = service._get_entity_no(entity)
        assert result == "CON001"

    def test_get_entity_no_with_quote_no(self):
        """测试获取实体编号 - 使用quote_no字段"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        entity = Mock()
        entity.id = 1
        entity.quote_no = "Q001"
        
        result = service._get_entity_no(entity)
        assert result == "Q001"

    def test_get_entity_no_fallback_to_id(self):
        """测试获取实体编号 - 找不到时使用id"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        entity = Mock()
        entity.id = 123
        
        result = service._get_entity_no(entity)
        assert result == "123"

    def test_on_approved_callback(self):
        """测试审批通过回调 - 默认无操作"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        # 默认实现不抛出异常
        service._on_approved(entity_id=1, approver_id=100)

    def test_on_rejected_callback(self):
        """测试审批驳回回调 - 默认无操作"""
        from app.services.base_approval_workflow import BaseApprovalWorkflowService
        
        service = BaseApprovalWorkflowService.__new__(BaseApprovalWorkflowService)
        service.db = Mock()
        
        # 默认实现不抛出异常
        service._on_rejected(entity_id=1, approver_id=100)