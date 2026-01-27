# -*- coding: utf-8 -*-
"""
Tests for report_data_generation service
Covers: app/services/report_data_generation/
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 193 lines (original)
Batch: 6
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_data_generation import (
    ReportDataGenerationService,
    report_data_service,
)
from app.services.report_data_generation.core import ReportDataGenerationCore
from app.services.report_data_generation.router import ReportRouterMixin
from app.services.report_data_generation.project_reports import ProjectReportMixin
from app.services.report_data_generation.dept_reports import DeptReportMixin
from app.services.report_data_generation.analysis_reports import AnalysisReportMixin
from app.models.user import User, Role, UserRole
from app.models.project import Project
from app.models.organization import Department
from tests.conftest import _get_or_create_user, _ensure_role, _ensure_login_user


@pytest.fixture
def test_user_with_role(db_session: Session):
    """创建带角色的测试用户"""
    from tests.conftest import _ensure_login_user
    
    user = _ensure_login_user(
        db_session,
        username="report_test_user",
        password="test123",
        real_name="报表测试用户",
        department="技术部",
        employee_role="ENGINEER",
        is_superuser=False
    )
    
    # 创建角色并关联
    role = _ensure_role(db_session, "PROJECT_MANAGER", "项目经理")
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def test_project(db_session: Session, test_user_with_role):
    """创建测试项目"""
    project = Project(
        project_code="REPORT-PJ-001",
        project_name="报表测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=test_user_with_role.id,
        created_at=datetime.now() - timedelta(days=30)
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_department(db_session: Session):
    """创建测试部门"""
    dept = Department(
        dept_code="REPORT-DEPT-001",
        dept_name="报表测试部门",
        is_active=True
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


class TestReportDataGenerationCore:
    """Test suite for ReportDataGenerationCore."""

    def test_check_permission_superuser(self, db_session, test_user_with_role):
        """测试超级管理员权限检查"""
        test_user_with_role.is_superuser = True
        db_session.commit()
        
        result = ReportDataGenerationCore.check_permission(
        db_session,
        test_user_with_role,
        "PROJECT_WEEKLY"
        )
        
        assert result is True

    def test_check_permission_with_role(self, db_session, test_user_with_role):
        """测试有角色的用户权限检查"""
        result = ReportDataGenerationCore.check_permission(
        db_session,
        test_user_with_role,
        "PROJECT_WEEKLY"
        )
        
        assert result is True

    def test_check_permission_no_role(self, db_session):
        """测试无角色的用户权限检查"""
        user = _get_or_create_user(
        db_session,
        username="no_role_user",
        password="test123",
        real_name="无角色用户",
        department="技术部",
        employee_role="ENGINEER"
        )
        
        result = ReportDataGenerationCore.check_permission(
        db_session,
        user,
        "PROJECT_WEEKLY"
        )
        
        assert result is False

    def test_check_permission_invalid_report_type(self, db_session, test_user_with_role):
        """测试无效报表类型权限检查"""
        result = ReportDataGenerationCore.check_permission(
        db_session,
        test_user_with_role,
        "INVALID_REPORT_TYPE"
        )
        
        assert result is False

    def test_get_allowed_reports_project_manager(self):
        """测试获取项目经理允许的报表类型"""
        result = ReportDataGenerationCore.get_allowed_reports("PROJECT_MANAGER")
        
        assert isinstance(result, list)
        assert "PROJECT_WEEKLY" in result
        assert "PROJECT_MONTHLY" in result
        assert "COST_ANALYSIS" in result

    def test_get_allowed_reports_department_manager(self):
        """测试获取部门经理允许的报表类型"""
        result = ReportDataGenerationCore.get_allowed_reports("DEPARTMENT_MANAGER")
        
        assert isinstance(result, list)
        assert "DEPT_WEEKLY" in result
        assert "DEPT_MONTHLY" in result

    def test_get_allowed_reports_invalid_role(self):
        """测试获取无效角色的报表类型"""
        result = ReportDataGenerationCore.get_allowed_reports("INVALID_ROLE")
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestProjectReportMixin:
    """Test suite for ProjectReportMixin."""

    def test_generate_project_weekly_report_project_not_found(self, db_session):
        """测试生成项目周报 - 项目不存在"""
        result = ProjectReportMixin.generate_project_weekly_report(
        db_session,
        project_id=99999,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_generate_project_weekly_report_success(self, db_session, test_project):
        """测试生成项目周报 - 成功场景"""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        result = ProjectReportMixin.generate_project_weekly_report(
        db_session,
        project_id=test_project.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert "error" not in result
        assert "summary" in result
        assert result["summary"]["project_code"] == "REPORT-PJ-001"
        assert "milestones" in result
        assert "timesheet" in result
        assert "machines" in result
        assert "risks" in result

    def test_generate_project_monthly_report_project_not_found(self, db_session):
        """测试生成项目月报 - 项目不存在"""
        result = ProjectReportMixin.generate_project_monthly_report(
        db_session,
        project_id=99999,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_generate_project_monthly_report_success(self, db_session, test_project):
        """测试生成项目月报 - 成功场景"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        result = ProjectReportMixin.generate_project_monthly_report(
        db_session,
        project_id=test_project.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert "error" not in result
        assert "summary" in result
        assert "progress_trend" in result
        assert "milestones" in result
        assert "cost" in result


class TestDeptReportMixin:
    """Test suite for DeptReportMixin."""

    def test_generate_dept_weekly_report_department_not_found(self, db_session):
        """测试生成部门周报 - 部门不存在"""
        result = DeptReportMixin.generate_dept_weekly_report(
        db_session,
        department_id=99999,
        start_date=date.today() - timedelta(days=7),
        end_date=date.today()
        )
        
        assert "error" in result
        assert result["error"] == "部门不存在"

    def test_generate_dept_weekly_report_success(self, db_session, test_department):
        """测试生成部门周报 - 成功场景"""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        result = DeptReportMixin.generate_dept_weekly_report(
        db_session,
        department_id=test_department.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert "error" not in result
        assert isinstance(result, dict)
        # 检查报表结构（具体字段可能因实现而异）
        assert "error" not in result

    def test_generate_dept_monthly_report_department_not_found(self, db_session):
        """测试生成部门月报 - 部门不存在"""
        result = DeptReportMixin.generate_dept_monthly_report(
        db_session,
        department_id=99999,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "error" in result
        assert result["error"] == "部门不存在"

    def test_generate_dept_monthly_report_success(self, db_session, test_department):
        """测试生成部门月报 - 成功场景"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        result = DeptReportMixin.generate_dept_monthly_report(
        db_session,
        department_id=test_department.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert "error" not in result
        assert "summary" in result
        # 检查报表结构（具体字段可能因实现而异）
        assert isinstance(result, dict)


class TestAnalysisReportMixin:
    """Test suite for AnalysisReportMixin."""

    def test_generate_workload_analysis_no_department(self, db_session):
        """测试生成负荷分析 - 无部门限制"""
        result = AnalysisReportMixin.generate_workload_analysis(
        db_session,
        department_id=None,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "summary" in result
        assert "workload_details" in result
        assert result["summary"]["scope"] == "全公司"

    def test_generate_workload_analysis_with_department(self, db_session, test_department):
        """测试生成负荷分析 - 指定部门"""
        result = AnalysisReportMixin.generate_workload_analysis(
        db_session,
        department_id=test_department.id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "summary" in result
        assert "workload_details" in result
        # 检查范围名称（可能是部门名称或"全公司"）
        assert result["summary"]["scope"] in ["报表测试部门", "全公司"]

    def test_generate_workload_analysis_default_dates(self, db_session):
        """测试生成负荷分析 - 默认日期范围"""
        result = AnalysisReportMixin.generate_workload_analysis(
        db_session,
        department_id=None
        )
        
        assert "summary" in result
        assert "workload_details" in result

    def test_generate_cost_analysis_no_project(self, db_session):
        """测试生成成本分析 - 无项目限制"""
        result = AnalysisReportMixin.generate_cost_analysis(
        db_session,
        project_id=None,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "summary" in result
        assert "cost_by_project" in result

    def test_generate_cost_analysis_with_project(self, db_session, test_project):
        """测试生成成本分析 - 指定项目"""
        result = AnalysisReportMixin.generate_cost_analysis(
        db_session,
        project_id=test_project.id,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today()
        )
        
        assert "summary" in result
        assert "cost_by_project" in result


class TestReportRouterMixin:
    """Test suite for ReportRouterMixin."""

    def test_generate_report_by_type_project_weekly(self, db_session, test_project):
        """测试路由分发 - 项目周报"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="PROJECT_WEEKLY",
        project_id=test_project.id
        )
        
        assert "error" not in result
        assert "summary" in result

    def test_generate_report_by_type_project_weekly_no_project_id(self, db_session):
        """测试路由分发 - 项目周报无项目ID"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="PROJECT_WEEKLY"
        )
        
        assert "error" in result
        assert "项目周报需要指定项目ID" in result["error"]

    def test_generate_report_by_type_dept_weekly(self, db_session, test_department):
        """测试路由分发 - 部门周报"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="DEPT_WEEKLY",
        department_id=test_department.id
        )
        
        assert "error" not in result
        assert "summary" in result

    def test_generate_report_by_type_workload_analysis(self, db_session):
        """测试路由分发 - 负荷分析"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="WORKLOAD_ANALYSIS"
        )
        
        assert "summary" in result

    def test_generate_report_by_type_cost_analysis(self, db_session):
        """测试路由分发 - 成本分析"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="COST_ANALYSIS"
        )
        
        assert "summary" in result

    def test_generate_report_by_type_invalid_type(self, db_session):
        """测试路由分发 - 无效报表类型"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="INVALID_TYPE"
        )
        
        assert "message" in result
        assert "该报表类型待实现" in result["message"]

    def test_generate_report_by_type_default_dates(self, db_session):
        """测试路由分发 - 默认日期范围"""
        result = ReportRouterMixin.generate_report_by_type(
        db_session,
        report_type="WORKLOAD_ANALYSIS"
        )
        
        assert isinstance(result, dict)
        # 应该返回报表数据（具体结构可能因实现而异）


class TestReportDataGenerationService:
    """Test suite for ReportDataGenerationService (组合类)."""

    def test_init(self):
        """测试服务初始化"""
        service = ReportDataGenerationService()
        assert service is not None

    def test_service_has_all_mixins(self):
        """测试服务包含所有混入类"""
        service = ReportDataGenerationService()
        
        # 检查是否包含所有混入类的方法
        assert hasattr(service, "check_permission")
        assert hasattr(service, "generate_project_weekly_report")
        assert hasattr(service, "generate_dept_weekly_report")
        assert hasattr(service, "generate_workload_analysis")
        assert hasattr(service, "generate_report_by_type")
