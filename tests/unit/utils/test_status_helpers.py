# -*- coding: utf-8 -*-
"""
status_helpers 单元测试

测试所有状态工具函数的正确性和边界情况。
"""

import pytest
from enum import Enum
from unittest.mock import MagicMock, patch

from app.utils.status_helpers import (
    check_status_equals,
    assert_status_allows,
    assert_status_not,
    get_status_filter,
    count_by_status,
    validate_status_transition,
    assert_valid_transition,
    CommonStatus,
)


# 测试用枚举
class TestStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


# 测试用对象
class MockEntity:
    """模拟实体对象"""
    def __init__(self, status, approval_status=None):
        self.status = status
        if approval_status:
            self.approval_status = approval_status


class TestCheckStatusEquals:
    """check_status_equals 函数测试"""

    def test_string_status_match(self):
        """字符串状态匹配"""
        obj = MockEntity("draft")
        assert check_status_equals(obj, "draft") is True
        assert check_status_equals(obj, "approved") is False

    def test_enum_status_match(self):
        """枚举状态匹配"""
        obj = MockEntity(TestStatus.DRAFT)
        assert check_status_equals(obj, "draft") is True
        assert check_status_equals(obj, TestStatus.DRAFT) is True
        assert check_status_equals(obj, "approved") is False

    def test_list_status_match(self):
        """列表状态匹配"""
        obj = MockEntity("draft")
        assert check_status_equals(obj, ["draft", "approved"]) is True
        assert check_status_equals(obj, ["approved", "rejected"]) is False

    def test_custom_status_attr(self):
        """自定义状态属性"""
        obj = MockEntity("draft", approval_status="pending")
        assert check_status_equals(obj, "pending", status_attr="approval_status") is True
        assert check_status_equals(obj, "approved", status_attr="approval_status") is False

    def test_none_status_returns_false(self):
        """None 状态返回 False"""
        obj = MockEntity(None)
        assert check_status_equals(obj, "draft") is False

    def test_missing_attr_returns_false(self):
        """缺少属性返回 False"""
        obj = object()
        assert check_status_equals(obj, "draft") is False


class TestAssertStatusAllows:
    """assert_status_allows 函数测试"""

    def test_allowed_status_passes(self):
        """允许的状态不抛异常"""
        obj = MockEntity("draft")
        # 不应该抛出异常
        assert_status_allows(obj, "draft", "只能操作草稿状态")
        assert_status_allows(obj, ["draft", "approved"], "状态不允许")

    def test_not_allowed_raises(self):
        """不允许的状态抛出异常"""
        obj = MockEntity("completed")
        with pytest.raises(ValueError, match="只能操作草稿状态"):
            assert_status_allows(obj, "draft", "只能操作草稿状态")

    def test_custom_error_message(self):
        """自定义错误消息"""
        obj = MockEntity("completed")
        with pytest.raises(ValueError, match="自定义错误"):
            assert_status_allows(obj, "draft", "自定义错误")

    def test_custom_status_attr(self):
        """自定义状态属性"""
        obj = MockEntity("draft", approval_status="pending")
        assert_status_allows(obj, "pending", "错误", status_attr="approval_status")
        
        with pytest.raises(ValueError):
            assert_status_allows(obj, "approved", "错误", status_attr="approval_status")


class TestAssertStatusNot:
    """assert_status_not 函数测试"""

    def test_not_forbidden_passes(self):
        """不在禁止范围内不抛异常"""
        obj = MockEntity("draft")
        assert_status_not(obj, "completed", "已完成不能操作")
        assert_status_not(obj, ["completed", "voided"], "不能操作")

    def test_forbidden_raises(self):
        """在禁止范围内抛出异常"""
        obj = MockEntity("completed")
        with pytest.raises(ValueError, match="已完成不能操作"):
            assert_status_not(obj, "completed", "已完成不能操作")

    def test_list_forbidden_raises(self):
        """列表禁止范围"""
        obj = MockEntity("voided")
        with pytest.raises(ValueError, match="状态不允许"):
            assert_status_not(obj, ["completed", "voided"], "状态不允许")


class TestGetStatusFilter:
    """get_status_filter 函数测试"""

    def test_single_status(self):
        """单个状态过滤"""
        # 创建模拟模型
        MockModel = MagicMock()
        MockModel.status = MagicMock()
        
        result = get_status_filter(MockModel, "draft")
        # 验证调用了 == 操作
        MockModel.status.__eq__.assert_called_with("draft")

    def test_list_status(self):
        """列表状态过滤"""
        MockModel = MagicMock()
        MockModel.status = MagicMock()
        
        result = get_status_filter(MockModel, ["draft", "approved"])
        # 验证调用了 in_ 操作
        MockModel.status.in_.assert_called_with(["draft", "approved"])

    def test_enum_status(self):
        """枚举状态过滤"""
        MockModel = MagicMock()
        MockModel.status = MagicMock()
        
        result = get_status_filter(MockModel, TestStatus.DRAFT)
        MockModel.status.__eq__.assert_called_with("draft")


class TestCountByStatus:
    """count_by_status 函数测试"""

    def test_count_all_statuses(self):
        """统计所有状态"""
        # 模拟数据库会话和查询结果
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            ("draft", 10),
            ("approved", 5),
            ("completed", 20),
        ]

        MockModel = MagicMock()
        MockModel.status = MagicMock()
        MockModel.id = MagicMock()

        result = count_by_status(mock_db, MockModel)
        
        assert result == {"draft": 10, "approved": 5, "completed": 20}

    def test_count_specific_statuses(self):
        """统计指定状态"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            ("draft", 10),
        ]

        MockModel = MagicMock()
        MockModel.status = MagicMock()
        MockModel.id = MagicMock()

        result = count_by_status(mock_db, MockModel, statuses=["draft", "approved"])
        
        # 应该包含所有指定状态，不存在的为 0
        assert result == {"draft": 10, "approved": 0}

    def test_empty_result(self):
        """无数据情况"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        MockModel = MagicMock()
        MockModel.status = MagicMock()
        MockModel.id = MagicMock()

        result = count_by_status(mock_db, MockModel, statuses=["draft", "approved"])
        
        assert result == {"draft": 0, "approved": 0}


class TestValidateStatusTransition:
    """validate_status_transition 函数测试"""

    def test_valid_transition(self):
        """有效转换"""
        transitions = {
            "draft": ["approving", "voided"],
            "approving": ["approved", "draft"],
            "approved": ["signed", "voided"],
        }
        
        assert validate_status_transition("draft", "approving", transitions) is True
        assert validate_status_transition("approving", "approved", transitions) is True

    def test_invalid_transition(self):
        """无效转换"""
        transitions = {
            "draft": ["approving", "voided"],
            "approving": ["approved", "draft"],
        }
        
        assert validate_status_transition("draft", "signed", transitions) is False
        assert validate_status_transition("draft", "approved", transitions) is False

    def test_unknown_current_status(self):
        """未知当前状态"""
        transitions = {"draft": ["approving"]}
        assert validate_status_transition("unknown", "approving", transitions) is False

    def test_enum_values(self):
        """枚举值转换"""
        transitions = {
            "draft": ["approved"],
        }
        
        assert validate_status_transition(TestStatus.DRAFT, "approved", transitions) is True
        assert validate_status_transition("draft", TestStatus.APPROVED, transitions) is True


class TestAssertValidTransition:
    """assert_valid_transition 函数测试"""

    def test_valid_transition_passes(self):
        """有效转换不抛异常"""
        transitions = {"draft": ["approving"]}
        # 不应该抛出异常
        assert_valid_transition("draft", "approving", transitions)

    def test_invalid_transition_raises(self):
        """无效转换抛出异常"""
        transitions = {"draft": ["approving"]}
        
        with pytest.raises(ValueError, match="无法从状态 draft 转换到 signed"):
            assert_valid_transition("draft", "signed", transitions)

    def test_custom_error_template(self):
        """自定义错误模板"""
        transitions = {"draft": ["approving"]}
        
        with pytest.raises(ValueError, match="不支持从 draft 到 signed"):
            assert_valid_transition(
                "draft", "signed", transitions,
                error_msg_template="不支持从 {current} 到 {target}"
            )


class TestCommonStatus:
    """CommonStatus 常量测试"""

    def test_status_values(self):
        """状态值正确"""
        assert CommonStatus.PENDING == "pending"
        assert CommonStatus.APPROVED == "approved"
        assert CommonStatus.REJECTED == "rejected"
        assert CommonStatus.DRAFT == "draft"
        assert CommonStatus.ACTIVE == "active"
        assert CommonStatus.INACTIVE == "inactive"
        assert CommonStatus.COMPLETED == "completed"
        assert CommonStatus.CANCELLED == "cancelled"
        assert CommonStatus.VOIDED == "voided"
