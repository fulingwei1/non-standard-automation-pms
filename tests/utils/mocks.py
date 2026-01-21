# -*- coding: utf-8 -*-
"""
Mock 工具库

提供常用的 Mock 对象和辅助函数，简化测试编写。
"""

from unittest.mock import MagicMock, Mock
from datetime import datetime, date, timedelta


def mock_db_session():
    """
    创建 Mock 数据库会话

    Returns:
        Mock: 模拟的数据库会话对象
    """
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


def mock_project(**overrides):
    """
    创建 Mock 项目对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的项目对象
    """
    defaults = {
        "id": 1,
        "project_code": "PJ-TEST001",
        "project_name": "测试项目",
        "customer_id": 1,
        "customer_name": "测试客户",
        "stage": "S3",
        "status": "ST05",
        "health": "H1",
        "pm_id": 1,
        "pm_name": "测试PM",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_machine(**overrides):
    """
    创建 Mock 设备对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的设备对象
    """
    defaults = {
        "id": 1,
        "project_id": 1,
        "machine_code": "M-001",
        "machine_name": "测试设备",
        "machine_type": "ICT",
        "status": "DESIGN",
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_task(**overrides):
    """
    创建 Mock 任务对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的任务对象
    """
    defaults = {
        "id": 1,
        "task_code": "TASK-001",
        "title": "测试任务",
        "status": "IN_PROGRESS",
        "progress": 50,
        "assignee_id": 1,
        "assignee_name": "测试工程师",
        "project_id": 1,
        "plan_start_date": date.today(),
        "plan_end_date": date.today() + timedelta(days=7),
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_issue(**overrides):
    """
    创建 Mock 问题对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的问题对象
    """
    defaults = {
        "id": 1,
        "issue_code": "ISSUE-001",
        "title": "测试问题",
        "status": "OPEN",
        "priority": "HIGH",
        "issue_type": "DESIGN",
        "project_id": 1,
        "assignee_id": 1,
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_milestone(**overrides):
    """
    创建 Mock 里程碑对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的里程碑对象
    """
    defaults = {
        "id": 1,
        "milestone_code": "MS-001",
        "milestone_name": "设计评审",
        "status": "PENDING",
        "planned_date": date.today() + timedelta(days=14),
        "actual_date": None,
        "project_id": 1,
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_alert(**overrides):
    """
    创建 Mock 预警对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的预警对象
    """
    defaults = {
        "id": 1,
        "event_no": "ALERT-001",
        "level": "WARNING",
        "status": "OPEN",
        "alert_type": "DELAY",
        "project_id": 1,
        "description": "测试预警",
        "created_at": datetime.now(),
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def mock_shortage(**overrides):
    """
    创建 Mock 缺料对象

    Args:
        **overrides: 覆盖默认属性

    Returns:
        Mock: 模拟的缺料对象
    """
    defaults = {
        "id": 1,
        "report_no": "SH-001",
        "material_code": "MAT-001",
        "material_name": "测试物料",
        "shortage_quantity": 10,
        "required_date": date.today(),
        "status": "OPEN",
        "project_id": 1,
    }
    defaults.update(overrides)

    mock_obj = Mock()
    for key, value in defaults.items():
        setattr(mock_obj, key, value)

    return mock_obj


def create_mock_query_result(count=0, items=None):
    """
    创建 Mock 查询结果

    Args:
        count: 返回的 count() 方法结果
        items: 返回的 all() 方法结果列表

    Returns:
        Mock: 模拟的查询对象
    """
    if items is None:
        items = []

    query_mock = MagicMock()
    query_mock.count.return_value = count
    query_mock.all.return_value = items
    query_mock.first.return_value = items[0] if items else None

    # 支持链式调用
    filter_mock = MagicMock()
    filter_mock.count.return_value = count
    filter_mock.all.return_value = items
    filter_mock.first.return_value = items[0] if items else None
    query_mock.filter.return_value = filter_mock

    return query_mock


class MockServiceResponse:
    """
    Mock 服务响应包装器

    用于包装测试中常用的服务响应
    """

    @staticmethod
    def success(data=None, message="操作成功"):
        """成功的响应"""
        return {"success": True, "message": message, "data": data}

    @staticmethod
    def error(message="操作失败", code=400):
        """失败的响应"""
        return {"success": False, "message": message, "code": code}


class MockExternalAPI:
    """
    Mock 外部 API 调用

    用于模拟外部服务（如邮件、短信等）的调用
    """

    def __init__(self):
        self.calls = []

    def send_email(self, to: str, subject: str, body: str):
        """Mock 发送邮件"""
        self.calls.append({"type": "email", "to": to, "subject": subject, "body": body})
        return True

    def send_sms(self, phone: str, content: str):
        """Mock 发送短信"""
        self.calls.append({"type": "sms", "phone": phone, "content": content})
        return True

    def reset(self):
        """重置调用记录"""
        self.calls = []
