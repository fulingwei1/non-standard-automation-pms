# -*- coding: utf-8 -*-
"""
operation_log_service 单元测试

测试销售操作日志服务的核心功能。
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.sales.operation_log import (
    SalesEntityType,
    SalesOperationLog,
    SalesOperationType,
)
from app.services.sales.operation_log_service import (
    SalesOperationLogService,
    _get_entity_name,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def mock_operator():
    """模拟操作人"""
    user = MagicMock()
    user.id = 1
    user.username = "zhangsan"
    user.real_name = "张三"
    user.department = MagicMock()
    user.department.name = "销售部"
    return user


@pytest.fixture
def mock_operator_no_dept():
    """模拟无部门操作人"""
    user = MagicMock()
    user.id = 2
    user.username = "lisi"
    user.real_name = None
    user.department = None
    return user


# ========== log_operation 测试 ==========

class TestLogOperation:
    """log_operation 测试"""

    def test_log_basic_operation(self, mock_db, mock_operator):
        """记录基础操作"""
        result = SalesOperationLogService.log_operation(
            mock_db,
            entity_type=SalesEntityType.LEAD,
            entity_id=100,
            operation_type=SalesOperationType.CREATE,
            operator=mock_operator,
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        
        # 验证添加的日志对象
        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.entity_type == SalesEntityType.LEAD
        assert log_entry.entity_id == 100
        assert log_entry.operation_type == SalesOperationType.CREATE
        assert log_entry.operator_id == 1
        assert log_entry.operator_name == "张三"
        assert log_entry.operator_dept == "销售部"

    def test_log_operation_with_all_fields(self, mock_db, mock_operator):
        """记录完整字段的操作"""
        old_value = {"status": "draft"}
        new_value = {"status": "submitted"}
        
        result = SalesOperationLogService.log_operation(
            mock_db,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=200,
            operation_type=SalesOperationType.STATUS_CHANGE,
            operator=mock_operator,
            entity_code="HT-20260312-001",
            operation_desc="合同状态变更",
            old_value=old_value,
            new_value=new_value,
            changed_fields=["status"],
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            request_id="req-12345",
            remark="审批后状态变更",
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.entity_code == "HT-20260312-001"
        assert log_entry.operation_desc == "合同状态变更"
        assert log_entry.old_value == old_value
        assert log_entry.new_value == new_value
        assert log_entry.changed_fields == ["status"]
        assert log_entry.ip_address == "192.168.1.100"
        assert log_entry.request_id == "req-12345"

    def test_log_operation_no_department(self, mock_db, mock_operator_no_dept):
        """操作人无部门"""
        result = SalesOperationLogService.log_operation(
            mock_db,
            entity_type=SalesEntityType.LEAD,
            entity_id=100,
            operation_type=SalesOperationType.CREATE,
            operator=mock_operator_no_dept,
        )

        log_entry = mock_db.add.call_args[0][0]
        # 无 real_name 时使用 username
        assert log_entry.operator_name == "lisi"
        assert log_entry.operator_dept is None


# ========== log_create 测试 ==========

class TestLogCreate:
    """log_create 测试"""

    def test_log_create(self, mock_db, mock_operator):
        """记录创建操作"""
        new_value = {"name": "新线索", "source": "电话"}
        
        result = SalesOperationLogService.log_create(
            mock_db,
            entity_type=SalesEntityType.LEAD,
            entity_id=100,
            operator=mock_operator,
            entity_code="XS-001",
            new_value=new_value,
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.operation_type == SalesOperationType.CREATE
        assert log_entry.new_value == new_value
        assert "创建线索" in log_entry.operation_desc


# ========== log_update 测试 ==========

class TestLogUpdate:
    """log_update 测试"""

    def test_log_update_with_changes(self, mock_db, mock_operator):
        """记录更新操作（有变更）"""
        old_value = {"name": "旧名称", "phone": "123456"}
        new_value = {"name": "新名称", "phone": "123456"}
        
        result = SalesOperationLogService.log_update(
            mock_db,
            entity_type=SalesEntityType.OPPORTUNITY,
            entity_id=200,
            operator=mock_operator,
            old_value=old_value,
            new_value=new_value,
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.operation_type == SalesOperationType.UPDATE
        assert log_entry.changed_fields == ["name"]
        assert "更新商机" in log_entry.operation_desc

    def test_log_update_multiple_changes(self, mock_db, mock_operator):
        """记录更新操作（多字段变更）"""
        old_value = {"name": "旧名称", "phone": "111", "email": "old@test.com"}
        new_value = {"name": "新名称", "phone": "222", "email": "old@test.com"}
        
        result = SalesOperationLogService.log_update(
            mock_db,
            entity_type=SalesEntityType.CUSTOMER,
            entity_id=300,
            operator=mock_operator,
            old_value=old_value,
            new_value=new_value,
        )

        log_entry = mock_db.add.call_args[0][0]
        assert set(log_entry.changed_fields) == {"name", "phone"}


# ========== log_status_change 测试 ==========

class TestLogStatusChange:
    """log_status_change 测试"""

    def test_log_status_change(self, mock_db, mock_operator):
        """记录状态变更"""
        result = SalesOperationLogService.log_status_change(
            mock_db,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=100,
            operator=mock_operator,
            old_status="draft",
            new_status="submitted",
            entity_code="HT-001",
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.operation_type == SalesOperationType.STATUS_CHANGE
        assert log_entry.old_value == {"status": "draft"}
        assert log_entry.new_value == {"status": "submitted"}
        assert log_entry.changed_fields == ["status"]
        assert "draft → submitted" in log_entry.operation_desc


# ========== log_approval 测试 ==========

class TestLogApproval:
    """log_approval 测试"""

    def test_log_approve(self, mock_db, mock_operator):
        """记录审批通过"""
        result = SalesOperationLogService.log_approval(
            mock_db,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=100,
            operator=mock_operator,
            action="approve",
            entity_code="HT-001",
            comment="同意",
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.operation_type == SalesOperationType.APPROVE
        assert "审批通过" in log_entry.operation_desc
        assert log_entry.remark == "同意"

    def test_log_reject(self, mock_db, mock_operator):
        """记录审批驳回"""
        result = SalesOperationLogService.log_approval(
            mock_db,
            entity_type=SalesEntityType.QUOTE,
            entity_id=200,
            operator=mock_operator,
            action="reject",
            comment="价格不合理",
        )

        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.operation_type == SalesOperationType.REJECT
        assert "审批驳回" in log_entry.operation_desc


# ========== get_entity_logs 测试 ==========

class TestGetEntityLogs:
    """get_entity_logs 测试"""

    def test_get_logs(self, mock_db):
        """获取实体日志列表"""
        mock_logs = [MagicMock(spec=SalesOperationLog) for _ in range(3)]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_logs

        logs, total = SalesOperationLogService.get_entity_logs(
            mock_db,
            entity_type=SalesEntityType.CONTRACT,
            entity_id=100,
            skip=0,
            limit=50,
        )

        assert len(logs) == 3
        assert total == 10

    def test_get_logs_with_pagination(self, mock_db):
        """获取日志（分页）"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        logs, total = SalesOperationLogService.get_entity_logs(
            mock_db,
            entity_type=SalesEntityType.LEAD,
            entity_id=50,
            skip=10,
            limit=20,
        )

        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(20)


# ========== search_logs 测试 ==========

class TestSearchLogs:
    """search_logs 测试"""

    def test_search_all(self, mock_db):
        """搜索所有日志"""
        mock_logs = [MagicMock(spec=SalesOperationLog) for _ in range(5)]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_logs

        logs, total = SalesOperationLogService.search_logs(mock_db)

        assert len(logs) == 5
        assert total == 50

    def test_search_by_entity_type(self, mock_db):
        """按实体类型搜索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        logs, total = SalesOperationLogService.search_logs(
            mock_db,
            entity_type=SalesEntityType.CONTRACT,
        )

        # 验证调用了 filter
        assert mock_query.filter.called

    def test_search_by_time_range(self, mock_db):
        """按时间范围搜索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        start = datetime.now() - timedelta(days=7)
        end = datetime.now()

        logs, total = SalesOperationLogService.search_logs(
            mock_db,
            start_time=start,
            end_time=end,
        )

        assert total == 5

    def test_search_by_operator(self, mock_db):
        """按操作人搜索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        logs, total = SalesOperationLogService.search_logs(
            mock_db,
            operator_id=1,
        )

        assert total == 3


# ========== _get_entity_name 测试 ==========

class TestGetEntityName:
    """_get_entity_name 辅助函数测试"""

    def test_get_known_entity_name(self):
        """获取已知实体名称"""
        assert _get_entity_name(SalesEntityType.LEAD) == "线索"
        assert _get_entity_name(SalesEntityType.OPPORTUNITY) == "商机"
        assert _get_entity_name(SalesEntityType.QUOTE) == "报价"
        assert _get_entity_name(SalesEntityType.CONTRACT) == "合同"
        assert _get_entity_name(SalesEntityType.INVOICE) == "发票"
        assert _get_entity_name(SalesEntityType.CUSTOMER) == "客户"

    def test_get_unknown_entity_name(self):
        """获取未知实体名称返回原值"""
        assert _get_entity_name("UNKNOWN") == "UNKNOWN"
        assert _get_entity_name("CUSTOM_TYPE") == "CUSTOM_TYPE"
