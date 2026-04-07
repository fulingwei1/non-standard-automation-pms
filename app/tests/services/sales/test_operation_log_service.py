# -*- coding: utf-8 -*-
"""
销售操作日志服务测试
测试 SalesOperationLogService 的各项功能
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    db = Mock()
    db.add = Mock()
    db.flush = Mock()
    db.commit = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def mock_operator():
    """创建模拟操作人用户"""
    user = Mock()
    user.id = 1
    user.username = "test_operator"
    user.real_name = "测试操作员"
    user.department = Mock()
    user.department.name = "销售部"
    return user


class TestSalesOperationLogService:
    """销售操作日志服务测试类"""

    def test_log_operation_basic(self, mock_db_session, mock_operator):
        """测试基本的操作日志记录"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesOperationType, SalesEntityType
        
        SalesOperationLogService.log_operation(
            db=mock_db_session,
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=100,
            operation_type=SalesOperationType.CREATE,
            operator=mock_operator,
            entity_code="OPP-2024-001",
        )

        # 验证数据库添加操作
        mock_db_session.add.assert_called_once()
        
        # 验证日志对象字段
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.entity_type == "OPPORTUNITY"
        assert call_args.entity_id == 100
        assert call_args.operation_type == "CREATE"
        assert call_args.operator_id == 1
        assert call_args.operator_name == "测试操作员"
        assert call_args.entity_code == "OPP-2024-001"

    def test_log_operation_with_values(self, mock_db_session, mock_operator):
        """测试带变更值的操作日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        old_value = {"name": "旧名称", "amount": 10000}
        new_value = {"name": "新名称", "amount": 15000}
        
        SalesOperationLogService.log_operation(
            db=mock_db_session,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=200,
            operation_type=SalesOperationType.UPDATE,
            operator=mock_operator,
            old_value=old_value,
            new_value=new_value,
            changed_fields=["name", "amount"],
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.old_value == old_value
        assert call_args.new_value == new_value
        assert call_args.changed_fields == ["name", "amount"]

    def test_log_create(self, mock_db_session, mock_operator):
        """测试创建操作日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        new_value = {"name": "新线索", "source": "官网"}
        
        SalesOperationLogService.log_create(
            db=mock_db_session,
            entity_type=SalesEntityType.LEAD,
            entity_id=300,
            operator=mock_operator,
            entity_code="LEAD-001",
            new_value=new_value,
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.operation_type == SalesOperationType.CREATE
        assert call_args.operation_desc == "创建线索"
        assert call_args.new_value == new_value

    def test_log_update(self, mock_db_session, mock_operator):
        """测试更新操作日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        old_value = {"name": "旧商机", "stage": "跟进中"}
        new_value = {"name": "新商机", "stage": "已成交"}
        
        SalesOperationLogService.log_update(
            db=mock_db_session,
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=400,
            operator=mock_operator,
            old_value=old_value,
            new_value=new_value,
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.operation_type == SalesOperationType.UPDATE
        assert call_args.operation_desc == "更新商机"
        assert call_args.changed_fields == ["name", "stage"]

    def test_log_status_change(self, mock_db_session, mock_operator):
        """测试状态变更日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        SalesOperationLogService.log_status_change(
            db=mock_db_session,
            entity_type=SalesEntityType.QUOTE,
            entity_id=500,
            operator=mock_operator,
            old_status="draft",
            new_status="submitted",
            entity_code="QUOTE-001",
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.operation_type == SalesOperationType.STATUS_CHANGE
        assert call_args.operation_desc == "报价状态变更：draft → submitted"
        assert call_args.old_value == {"status": "draft"}
        assert call_args.new_value == {"status": "submitted"}
        assert call_args.changed_fields == ["status"]

    def test_log_approval_approve(self, mock_db_session, mock_operator):
        """测试审批通过日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        SalesOperationLogService.log_approval(
            db=mock_db_session,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=600,
            operator=mock_operator,
            action="approve",
            comment="同意该合同",
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.operation_type == SalesOperationType.APPROVE
        assert call_args.operation_desc == "合同审批通过"
        assert call_args.remark == "同意该合同"

    def test_log_approval_reject(self, mock_db_session, mock_operator):
        """测试审批驳回日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        SalesOperationLogService.log_approval(
            db=mock_db_session,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=600,
            operator=mock_operator,
            action="reject",
            comment="条款需要修改",
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.operation_type == SalesOperationType.REJECT
        assert call_args.operation_desc == "合同审批驳回"
        assert call_args.remark == "条款需要修改"

    def test_get_entity_logs(self, mock_db_session):
        """测试获取实体日志列表"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType
        
        # Mock 查询结果
        mock_log = Mock()
        mock_log.id = 1
        mock_log.entity_type = "OPPORTUNITY"
        mock_log.entity_id = 100
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=1)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_log])
        
        mock_db_session.query = Mock(return_value=mock_query)
        
        logs, total = SalesOperationLogService.get_entity_logs(
            db=mock_db_session,
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=100,
        )
        
        assert total == 1
        assert len(logs) == 1

    def test_search_logs_by_operator(self, mock_db_session):
        """测试按操作人搜索日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesOperationType
        
        mock_log = Mock()
        mock_log.id = 1
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=1)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_log])
        
        mock_db_session.query = Mock(return_value=mock_query)
        
        logs, total = SalesOperationLogService.search_logs(
            db=mock_db_session,
            operator_id=1,
            operation_type=SalesOperationType.CREATE,
        )
        
        assert total == 1

    def test_log_operation_with_ip_and_useragent(self, mock_db_session, mock_operator):
        """测试带IP和User-Agent的操作日志"""
        from app.services.sales.operation_log_service import SalesOperationLogService
        from app.models.sales.operation_log import SalesEntityType, SalesOperationType
        
        SalesOperationLogService.log_operation(
            db=mock_db_session,
            entity_type=SalesEntityType.CUSTOMER,
            entity_id=700,
            operation_type=SalesOperationType.CREATE,
            operator=mock_operator,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Macintosh)",
            request_id="req-123456",
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.ip_address == "192.168.1.100"
        assert call_args.user_agent == "Mozilla/5.0 (Macintosh)"
        assert call_args.request_id == "req-123456"