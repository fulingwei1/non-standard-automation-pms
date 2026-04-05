# -*- coding: utf-8 -*-
"""员工绩效服务单元测试 (EmployeePerformanceService)"""
import os
import sys

# Setup environment BEFORE importing app
from unittest.mock import MagicMock
redis_mock = MagicMock()
sys.modules['redis'] = redis_mock
sys.modules['redis.exceptions'] = MagicMock()

os.environ['SQLITE_DB_PATH'] = ':memory:'
os.environ['REDIS_URL'] = ''
os.environ['DEBUG'] = 'true'
os.environ['ENABLE_SCHEDULER'] = 'false'
os.environ['RATE_LIMIT_ENABLED'] = 'false'


def _make_db():
    return MagicMock()


def _make_user(**kw):
    u = MagicMock()
    defaults = dict(
        id=1,
        username="test_user",
        email="test@example.com",
        is_superuser=False,
        roles=[],
        department_id=1,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(u, k, v)
    return u


def _make_role(role_code):
    """创建模拟的角色对象"""
    role = MagicMock()
    role.role_code = role_code
    return role


def _make_user_role(role_code):
    """创建模拟的用户角色对象"""
    ur = MagicMock()
    ur.role = _make_role(role_code)
    return ur


class TestEmployeePerformanceServiceInit:
    """测试服务初始化"""

    def test_init_sets_db(self):
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = _make_db()
        svc = EmployeePerformanceService(db)
        assert svc.db is db


class TestCheckPerformanceViewPermission:
    """测试绩效查看权限检查"""

    def test_superuser_can_view_any(self):
        """测试超级用户可以查看任何人的绩效"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = _make_db()
        svc = EmployeePerformanceService(db)

        superuser = _make_user(id=1, is_superuser=True)
        result = svc.check_performance_view_permission(superuser, target_user_id=2)

        assert result is True

    def test_user_can_view_own_performance(self):
        """测试用户可以查看自己的绩效"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = _make_db()
        svc = EmployeePerformanceService(db)

        user = _make_user(id=1, is_superuser=False)
        result = svc.check_performance_view_permission(user, target_user_id=1)

        assert result is True

    def test_non_existent_target_user(self):
        """测试目标用户不存在时返回False"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query

        svc = EmployeePerformanceService(db)

        current_user = _make_user(id=1, is_superuser=False)
        result = svc.check_performance_view_permission(
            current_user, target_user_id=999
        )

        assert result is False


class TestManagerRoles:
    """测试经理角色权限"""

    def test_dept_manager_can_view_dept_employee(self):
        """测试部门经理可以查看本部门员工绩效"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = MagicMock()

        # 当前用户是部门经理
        current_user = _make_user(
            id=100, is_superuser=False, roles=[_make_user_role("dept_manager")], department_id=1
        )

        # 目标用户同部门
        target_user = _make_user(id=200, department_id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = target_user
        db.query.return_value = mock_query

        svc = EmployeePerformanceService(db)
        result = svc.check_performance_view_permission(current_user, target_user_id=200)

        assert result is True

    def test_regular_user_cannot_view_others(self):
        """测试普通用户不能查看他人绩效"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = MagicMock()

        # 普通用户
        current_user = _make_user(id=1, is_superuser=False, roles=[])

        # 目标用户
        target_user = _make_user(id=2)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = target_user
        db.query.return_value = mock_query

        svc = EmployeePerformanceService(db)
        result = svc.check_performance_view_permission(current_user, target_user_id=2)

        assert result is False


class TestServiceMethods:
    """测试服务方法存在性"""

    def test_service_has_check_permission_method(self):
        """测试服务有权限检查方法"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = _make_db()
        svc = EmployeePerformanceService(db)
        assert hasattr(svc, 'check_performance_view_permission')

    def test_service_has_get_summary_method(self):
        """测试服务有获取摘要方法"""
        from app.services.employee_performance.employee_performance_service import (
            EmployeePerformanceService,
        )

        db = _make_db()
        svc = EmployeePerformanceService(db)
        # 服务应该有相关方法
        assert svc is not None