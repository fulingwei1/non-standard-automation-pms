# -*- coding: utf-8 -*-
"""
DataScope 测试配置
提供通用的 fixtures 用于过滤服务测试
"""
from unittest.mock import Mock, MagicMock
from datetime import datetime

import pytest


class MockUser:
    """模拟用户"""
    def __init__(self, id=1, username="test_user", department=None, 
                 is_superuser=False, is_active=True):
        self.id = id
        self.username = username
        self.department = department
        self.is_superuser = is_superuser
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockIssue:
    """模拟问题"""
    def __init__(self, id=1, project_id=1, reporter_id=1, assignee_id=2,
                 responsible_engineer_id=3, resolved_by=4, verified_by=5):
        self.id = id
        self.project_id = project_id
        self.reporter_id = reporter_id
        self.assignee_id = assignee_id
        self.responsible_engineer_id = responsible_engineer_id
        self.resolved_by = resolved_by
        self.verified_by = verified_by
        self.status = "open"
        self.created_at = datetime.now()


class MockProject:
    """模拟项目"""
    def __init__(self, id=1, dept_id=1, pm_id=1, created_by=1, 
                 is_active=True, customer_id=None):
        self.id = id
        self.dept_id = dept_id
        self.pm_id = pm_id
        self.created_by = created_by
        self.is_active = is_active
        self.customer_id = customer_id
        self.name = f"Project {id}"
        self.created_at = datetime.now()


class MockDepartment:
    """模拟部门"""
    def __init__(self, id=1, dept_name="研发部"):
        self.id = id
        self.dept_name = dept_name
        self.created_at = datetime.now()


class MockProjectMember:
    """模拟项目成员"""
    def __init__(self, id=1, project_id=1, user_id=1, is_active=True):
        self.id = id
        self.project_id = project_id
        self.user_id = user_id
        self.is_active = is_active


class MockQuery:
    """模拟查询对象"""
    def __init__(self):
        self._filters = []
        self._filter_result = MockQuery()
        
    def filter(self, *conditions):
        self._filters.extend(conditions)
        return self
        
    def filter_by(self, **kwargs):
        self._filters.append(kwargs)
        return self
        
    def all(self):
        return []
        
    def first(self):
        return None
        
    def count(self):
        return 0
        
    def in_(self, values):
        return MockCondition(f"IN {values}")
        
    def __eq__(self, other):
        return MockCondition(f"== {other}")
        
    def __ne__(self, other):
        return MockCondition(f"!= {other}")
        
    def __lt__(self, other):
        return MockCondition(f"< {other}")
        
    def __gt__(self, other):
        return MockCondition(f"> {other}")


class MockCondition:
    """模拟查询条件"""
    def __init__(self, description=""):
        self.description = description
        
    def __or__(self, other):
        return MockCondition(f"({self.description} OR {other.description})")
        
    def __and__(self, other):
        return MockCondition(f"({self.description} AND {other.description})")


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    db = Mock()
    db.query = Mock(return_value=MockQuery())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_user():
    """创建普通用户"""
    return MockUser(id=1, username="test_user", department="研发部")


@pytest.fixture
def mock_superuser():
    """创建超级管理员用户"""
    return MockUser(id=1, username="admin", is_superuser=True)


@pytest.fixture
def mock_user_no_dept():
    """创建没有部门的用户"""
    return MockUser(id=2, username="user_no_dept", department=None)


@pytest.fixture
def mock_issue():
    """创建模拟问题"""
    return MockIssue(
        id=1, 
        project_id=1, 
        reporter_id=1, 
        assignee_id=2,
        responsible_engineer_id=3,
        resolved_by=4,
        verified_by=5
    )


@pytest.fixture
def mock_project():
    """创建模拟项目"""
    return MockProject(id=1, dept_id=1, pm_id=1, created_by=1)


@pytest.fixture
def mock_department():
    """创建模拟部门"""
    return MockDepartment(id=1, dept_name="研发部")