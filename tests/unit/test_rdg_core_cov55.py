# -*- coding: utf-8 -*-
"""
Tests for app/services/report_data_generation/core.py
"""
import sys
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_data_generation.core import ReportDataGenerationCore
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def db():
    return MagicMock()


def _make_user(is_superuser=False, user_id=1):
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    return user


def test_superuser_has_all_permissions(db):
    """超级管理员对所有报表类型有权限"""
    user = _make_user(is_superuser=True)
    result = ReportDataGenerationCore.check_permission(db, user, "ANY_REPORT_TYPE")
    assert result is True


def test_no_roles_returns_false(db):
    """无角色用户应无权限"""
    user = _make_user(is_superuser=False)
    # The function imports UserRole and Role inside; mock db.query to return []
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    result = ReportDataGenerationCore.check_permission(db, user, "PROJECT_WEEKLY")
    assert result is False


def test_role_matrix_project_manager():
    """PROJECT_MANAGER 角色应有 PROJECT_WEEKLY 权限"""
    allowed = ReportDataGenerationCore.get_allowed_reports("PROJECT_MANAGER")
    assert "PROJECT_WEEKLY" in allowed
    assert "PROJECT_MONTHLY" in allowed


def test_role_matrix_engineer():
    """ENGINEER 角色只有 PROJECT_WEEKLY 权限"""
    allowed = ReportDataGenerationCore.get_allowed_reports("ENGINEER")
    assert "PROJECT_WEEKLY" in allowed
    assert "COMPANY_MONTHLY" not in allowed


def test_role_matrix_unknown_role():
    """未知角色返回空列表"""
    allowed = ReportDataGenerationCore.get_allowed_reports("UNKNOWN_ROLE")
    assert allowed == []


def test_role_matrix_finance_manager():
    """FINANCE_MANAGER 有 COST_ANALYSIS 权限"""
    allowed = ReportDataGenerationCore.get_allowed_reports("FINANCE_MANAGER")
    assert "COST_ANALYSIS" in allowed
    assert "COMPANY_MONTHLY" in allowed


def test_check_permission_with_valid_role(db):
    """有合法角色的用户应获得权限"""
    user = _make_user(is_superuser=False)
    user_role = MagicMock()
    role = MagicMock()
    role.role_code = "PROJECT_MANAGER"
    role.is_active = True
    user_role.role = role
    # The function does db.query(UserRole).join(Role).filter(...).all()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [user_role]
    result = ReportDataGenerationCore.check_permission(db, user, "PROJECT_WEEKLY")
    assert result is True
