# -*- coding: utf-8 -*-
"""
状态工具函数测试
"""

from unittest.mock import MagicMock

import pytest

from app.utils.status_helpers import (
    assert_status_allows,
    assert_status_not,
    assert_valid_transition,
    check_status_equals,
    validate_status_transition,
)


class MockEntity:
    """测试用模拟实体"""

    def __init__(self, status: str):
        self.status = status


class TestCheckStatusEquals:
    """check_status_equals 函数测试"""

    def test_single_status_match(self):
        entity = MockEntity("active")
        assert check_status_equals(entity, "active") is True

    def test_single_status_no_match(self):
        entity = MockEntity("active")
        assert check_status_equals(entity, "inactive") is False

    def test_list_status_match(self):
        entity = MockEntity("pending")
        assert check_status_equals(entity, ["pending", "active"]) is True

    def test_list_status_no_match(self):
        entity = MockEntity("deleted")
        assert check_status_equals(entity, ["pending", "active"]) is False

    def test_custom_status_attr(self):
        entity = MagicMock()
        entity.state = "running"
        assert check_status_equals(entity, "running", status_attr="state") is True


class TestAssertStatusAllows:
    """assert_status_allows 函数测试"""

    def test_allowed_status_passes(self):
        entity = MockEntity("draft")
        # 不应抛出异常
        assert_status_allows(entity, "draft", "只允许草稿状态")

    def test_allowed_status_list_passes(self):
        entity = MockEntity("pending")
        assert_status_allows(entity, ["draft", "pending"], "只允许草稿或待审批状态")

    def test_disallowed_status_raises(self):
        entity = MockEntity("completed")
        with pytest.raises(ValueError, match="只允许草稿状态"):
            assert_status_allows(entity, "draft", "只允许草稿状态")


class TestAssertStatusNot:
    """assert_status_not 函数测试"""

    def test_not_forbidden_passes(self):
        entity = MockEntity("active")
        # 不应抛出异常
        assert_status_not(entity, "deleted", "已删除的不能操作")

    def test_not_forbidden_list_passes(self):
        entity = MockEntity("active")
        assert_status_not(entity, ["deleted", "archived"], "已归档的不能操作")

    def test_forbidden_status_raises(self):
        entity = MockEntity("completed")
        with pytest.raises(ValueError, match="已完成的不能操作"):
            assert_status_not(entity, "completed", "已完成的不能操作")


class TestValidateStatusTransition:
    """validate_status_transition 函数测试"""

    def test_valid_transition(self):
        transitions = {
            "draft": ["pending", "cancelled"],
            "pending": ["approved", "rejected"],
        }
        assert validate_status_transition("draft", "pending", transitions) is True

    def test_invalid_transition(self):
        transitions = {
            "draft": ["pending"],
            "pending": ["approved"],
        }
        assert validate_status_transition("draft", "approved", transitions) is False

    def test_unknown_current_status(self):
        transitions = {"draft": ["pending"]}
        assert validate_status_transition("unknown", "pending", transitions) is False


class TestAssertValidTransition:
    """assert_valid_transition 函数测试"""

    def test_valid_transition_passes(self):
        transitions = {"draft": ["pending", "cancelled"]}
        # 不应抛出异常
        assert_valid_transition("draft", "pending", transitions, "无效状态转换")

    def test_invalid_transition_raises(self):
        transitions = {"draft": ["pending"]}
        with pytest.raises(ValueError, match="无效状态转换"):
            assert_valid_transition("draft", "approved", transitions, "无效状态转换")
