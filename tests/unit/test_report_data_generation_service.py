# -*- coding: utf-8 -*-
"""
Tests for report_data_generation_service
Covers: app/services/report_data_generation_service.py
注意：此服务使用静态方法，不需要实例化
"""

from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.services.report_data_generation_service import ReportDataGenerationService


class TestReportDataGenerationService:
    """Test suite for ReportDataGenerationService (静态方法服务)."""

    def test_role_report_matrix_structure(self):
        """验证角色-报表权限矩阵结构。"""
        matrix = ReportDataGenerationService.ROLE_REPORT_MATRIX

        # 验证必要的角色存在
        assert "PROJECT_MANAGER" in matrix
        assert "DEPARTMENT_MANAGER" in matrix
        assert "FINANCE_MANAGER" in matrix
        assert "HR_MANAGER" in matrix
        assert "SALES_MANAGER" in matrix

        # 验证每个角色都有报表权限列表
        for role, reports in matrix.items():
            assert isinstance(reports, list)
            assert len(reports) > 0

    def test_project_manager_permissions(self):
        """验证项目经理的报表权限。"""
        pm_reports = ReportDataGenerationService.ROLE_REPORT_MATRIX["PROJECT_MANAGER"]

        assert "PROJECT_WEEKLY" in pm_reports
        assert "PROJECT_MONTHLY" in pm_reports
        assert "COST_ANALYSIS" in pm_reports
        assert "RISK_REPORT" in pm_reports

    def test_finance_manager_permissions(self):
        """验证财务经理的报表权限。"""
        fm_reports = ReportDataGenerationService.ROLE_REPORT_MATRIX["FINANCE_MANAGER"]

        assert "COST_ANALYSIS" in fm_reports
        assert "COMPANY_MONTHLY" in fm_reports

    def test_check_permission_superuser(self, db_session: Session):
        """超级管理员应有所有权限。"""
        mock_user = MagicMock()
        mock_user.is_superuser = True

        result = ReportDataGenerationService.check_permission(
            db=db_session,
            user=mock_user,
            report_type="ANY_REPORT"
        )

        assert result is True

    def test_check_permission_no_roles(self, db_session: Session):
        """没有角色的用户应无权限。"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_user_result = MagicMock()
        mock_user_result.user_roles = []

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_user_result

            result = ReportDataGenerationService.check_permission(
                db=db_session,
                user=mock_user,
                report_type="PROJECT_WEEKLY"
            )

            assert result is False

    def test_check_permission_with_valid_role(self, db_session: Session):
        """有正确角色的用户应有对应权限。"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_role = MagicMock()
        mock_role.role_code = "PROJECT_MANAGER"
        mock_role.is_active = True

        mock_user_role = MagicMock()
        mock_user_role.role = mock_role

        mock_user_result = MagicMock()
        mock_user_result.user_roles = [mock_user_role]

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_user_result

            result = ReportDataGenerationService.check_permission(
                db=db_session,
                user=mock_user,
                report_type="PROJECT_WEEKLY"
            )

            assert result is True

    def test_custom_role_only_custom_reports(self):
        """CUSTOM 角色只能访问自定义报表。"""
        custom_reports = ReportDataGenerationService.ROLE_REPORT_MATRIX.get("CUSTOM", [])

        assert "CUSTOM" in custom_reports
        assert len(custom_reports) == 1  # 只有 CUSTOM
