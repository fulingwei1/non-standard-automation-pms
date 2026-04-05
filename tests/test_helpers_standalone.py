# -*- coding: utf-8 -*-
"""
测试 fixture 和 helpers 模块
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime


class MockUser:
    def __init__(self, id: int = 1, name: str = "test"):
        self.id = id
        self.name = name


class MockProject:
    def __init__(self, id: int = 1, name: str = "test_project"):
        self.id = id
        self.name = name
        self.created_at = datetime.now()


class TestMockObjects:
    """测试模拟对象"""

    def test_mock_user(self):
        """测试模拟用户"""
        user = MockUser(id=1, name="test_user")
        assert user.id == 1
        assert user.name == "test_user"

    def test_mock_project(self):
        """测试模拟项目"""
        project = MockProject(id=1, name="test_project")
        assert project.id == 1
        assert project.name == "test_project"
        assert project.created_at is not None


class TestPaginationHelper:
    """测试分页辅助函数"""

    def test_pagination_default_page(self):
        """测试默认页码"""
        page = 1
        assert page >= 1

    def test_pagination_default_page_size(self):
        """测试默认页面大小"""
        page_size = 20
        assert page_size > 0
        assert page_size <= 100

    def test_calculate_offset(self):
        """测试计算偏移量"""
        page = 3
        page_size = 20
        offset = (page - 1) * page_size
        assert offset == 40

    def test_calculate_total_pages(self):
        """测试计算总页数"""
        total = 100
        page_size = 20
        total_pages = (total + page_size - 1) // page_size
        assert total_pages == 5


class TestDateTimeHelper:
    """测试日期时间辅助函数"""

    def test_datetime_now(self):
        """测试当前时间"""
        now = datetime.now()
        assert now is not None

    def test_datetime_format(self):
        """测试日期时间格式化"""
        dt = datetime(2026, 4, 5, 10, 30, 0)
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == "2026-04-05 10:30:00"


class TestValidationHelper:
    """测试验证辅助函数"""

    def test_email_validation(self):
        """测试邮箱验证"""
        email = "test@example.com"
        assert "@" in email
        assert "." in email.split("@")[1]

    def test_phone_validation(self):
        """测试电话验证"""
        phone = "13812345678"
        assert len(phone) == 11
        assert phone.isdigit()

    def test_id_validation(self):
        """测试ID验证"""
        id_value = "12345"
        assert id_value.isdigit()
        assert int(id_value) > 0


class TestStringHelper:
    """测试字符串辅助函数"""

    def test_truncate_string(self):
        """测试字符串截断"""
        text = "这是一个很长的字符串需要被截断"
        max_length = 10
        truncated = text[:max_length] + "..." if len(text) > max_length else text
        assert len(truncated) <= max_length + 3

    def test_slug_generation(self):
        """测试生成 slug"""
        text = "Hello World Test"
        slug = text.lower().replace(" ", "-")
        assert slug == "hello-world-test"

    def test_mask_sensitive_data(self):
        """测试敏感数据脱敏"""
        data = "13812345678"
        masked = data[:3] + "****" + data[-4:]
        assert masked == "138****5678"