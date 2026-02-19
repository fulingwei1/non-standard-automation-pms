# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 报表数据生成服务核心类"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_data_generation.core import ReportDataGenerationCore
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


def _make_user(is_superuser=False, roles=None):
    user = MagicMock()
    user.is_superuser = is_superuser
    user.id = 1
    return user


class TestReportDataGenerationCore:

    def test_role_report_matrix_exists(self):
        assert isinstance(ReportDataGenerationCore.ROLE_REPORT_MATRIX, dict)
        assert len(ReportDataGenerationCore.ROLE_REPORT_MATRIX) > 0

    def test_get_allowed_reports_project_manager(self):
        reports = ReportDataGenerationCore.get_allowed_reports("PROJECT_MANAGER")
        assert "PROJECT_WEEKLY" in reports
        assert "PROJECT_MONTHLY" in reports

    def test_get_allowed_reports_unknown_role(self):
        reports = ReportDataGenerationCore.get_allowed_reports("UNKNOWN_ROLE")
        assert reports == []

    def test_check_permission_superuser_always_true(self):
        db = MagicMock()
        user = _make_user(is_superuser=True)
        result = ReportDataGenerationCore.check_permission(db, user, "ANY_REPORT")
        assert result is True

    def test_check_permission_no_roles_returns_false(self):
        db = MagicMock()
        user = _make_user(is_superuser=False)
        with patch("app.models.user.UserRole"), \
             patch("app.models.user.Role"):
            db.query.return_value.join.return_value.filter.return_value.all.return_value = []
            result = ReportDataGenerationCore.check_permission(db, user, "PROJECT_WEEKLY")
        assert result is False

    def test_check_permission_with_matching_role(self):
        db = MagicMock()
        user = _make_user(is_superuser=False)
        mock_user_role = MagicMock()
        mock_user_role.role = MagicMock(role_code="PROJECT_MANAGER", is_active=True)
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_user_role]
        result = ReportDataGenerationCore.check_permission(db, user, "PROJECT_WEEKLY")
        assert result is True

    def test_check_permission_with_non_matching_role(self):
        db = MagicMock()
        user = _make_user(is_superuser=False)
        mock_user_role = MagicMock()
        mock_user_role.role = MagicMock(role_code="ENGINEER", is_active=True)
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_user_role]
        result = ReportDataGenerationCore.check_permission(db, user, "SALES_FUNNEL")
        assert result is False
