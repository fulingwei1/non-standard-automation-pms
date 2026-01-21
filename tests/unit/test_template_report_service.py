# -*- coding: utf-8 -*-
"""
Tests for template_report_service service
Covers: app/services/template_report/__init__.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 171 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.template_report import TemplateReportService
from app.models.report_center import ReportTemplate
from app.models.project import Project, Customer


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_code="C001",
        customer_name="测试客户",
        contact_person="联系人",
        contact_phone="13800000000",
        status="ACTIVE"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_project(db_session: Session, test_customer):
    """创建测试项目"""
    from tests.conftest import _ensure_login_user
    admin = _ensure_login_user(
        db_session,
        username="admin",
        password="admin123",
        real_name="系统管理员",
        department="系统",
        employee_role="ADMIN",
        is_superuser=True
    )
    
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        created_by=admin.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_template(db_session: Session):
    """创建测试报表模板"""
    template = ReportTemplate(
        template_code="TEMPLATE-001",
        template_name="测试模板",
        report_type="PROJECT_WEEKLY",
        is_active=True,
        sections={},
        metrics_config={}
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


class TestTemplateReportService:
    """Test suite for TemplateReportService."""

    def test_generate_from_template_project_weekly(self, db_session, test_template, test_project):
        """测试生成项目周报"""
        from app.services.template_report.core import TemplateReportCore
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {'project_name': '测试项目'},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id,
                start_date=date.today() - timedelta(days=7),
                end_date=date.today()
            )
            
            assert result is not None
            assert 'template_id' in result
            assert result['template_id'] == test_template.id
            assert 'period' in result
            mock_gen.assert_called_once()

    def test_generate_from_template_project_monthly(self, db_session, test_template, test_project):
        """测试生成项目月报"""
        from app.services.template_report.core import TemplateReportCore
        
        # 修改模板类型
        test_template.report_type = "PROJECT_MONTHLY"
        db_session.commit()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_monthly') as mock_gen:
            mock_gen.return_value = {
                'summary': {'project_name': '测试项目'},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            assert result['report_type'] == "PROJECT_MONTHLY"
            mock_gen.assert_called_once()

    def test_generate_from_template_dept_weekly(self, db_session, test_template):
        """测试生成部门周报"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "DEPT_WEEKLY"
        db_session.commit()
        
        with patch('app.services.template_report.dept_reports.DeptReportMixin._generate_dept_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {'department_name': '测试部门'},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                department_id=1
            )
            
            assert result is not None
            assert result['report_type'] == "DEPT_WEEKLY"
            mock_gen.assert_called_once()

    def test_generate_from_template_dept_monthly(self, db_session, test_template):
        """测试生成部门月报"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "DEPT_MONTHLY"
        db_session.commit()
        
        with patch('app.services.template_report.dept_reports.DeptReportMixin._generate_dept_monthly') as mock_gen:
            mock_gen.return_value = {
                'summary': {'department_name': '测试部门'},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                department_id=1
            )
            
            assert result is not None
            assert result['report_type'] == "DEPT_MONTHLY"
            mock_gen.assert_called_once()

    def test_generate_from_template_workload_analysis(self, db_session, test_template):
        """测试生成工作量分析报表"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "WORKLOAD_ANALYSIS"
        db_session.commit()
        
        with patch('app.services.template_report.analysis_reports.AnalysisReportMixin._generate_workload_analysis') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                department_id=1
            )
            
            assert result is not None
            assert result['report_type'] == "WORKLOAD_ANALYSIS"
            mock_gen.assert_called_once()

    def test_generate_from_template_cost_analysis(self, db_session, test_template, test_project):
        """测试生成成本分析报表"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "COST_ANALYSIS"
        db_session.commit()
        
        with patch('app.services.template_report.analysis_reports.AnalysisReportMixin._generate_cost_analysis') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            assert result['report_type'] == "COST_ANALYSIS"
            mock_gen.assert_called_once()

    def test_generate_from_template_company_monthly(self, db_session, test_template):
        """测试生成公司月报"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "COMPANY_MONTHLY"
        db_session.commit()
        
        with patch('app.services.template_report.company_reports.CompanyReportMixin._generate_company_monthly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template
            )
            
            assert result is not None
            assert result['report_type'] == "COMPANY_MONTHLY"
            mock_gen.assert_called_once()

    def test_generate_from_template_generic(self, db_session, test_template):
        """测试生成通用报表"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.report_type = "CUSTOM_TYPE"
        db_session.commit()
        
        with patch('app.services.template_report.generic_report.GenericReportMixin._generate_generic_report') as mock_gen:
            mock_gen.return_value = {
                'report_type': 'CUSTOM_TYPE',
                'sections': {},
                'metrics': {},
                'message': '该报表类型待扩展'
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template
            )
            
            assert result is not None
            assert result['report_type'] == "CUSTOM_TYPE"
            mock_gen.assert_called_once()

    def test_generate_from_template_default_dates(self, db_session, test_template, test_project):
        """测试生成报表 - 默认日期范围"""
        from app.services.template_report.core import TemplateReportCore
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            assert 'period' in result
            assert 'start_date' in result['period']
            assert 'end_date' in result['period']
            # 验证默认日期范围是30天
            start = date.fromisoformat(result['period']['start_date'])
            end = date.fromisoformat(result['period']['end_date'])
            assert (end - start).days == 30

    def test_generate_from_template_custom_dates(self, db_session, test_template, test_project):
        """测试生成报表 - 自定义日期范围"""
        from app.services.template_report.core import TemplateReportCore
        
        start_date = date.today() - timedelta(days=14)
        end_date = date.today()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result is not None
            assert result['period']['start_date'] == start_date.isoformat()
            assert result['period']['end_date'] == end_date.isoformat()

    def test_generate_from_template_with_filters(self, db_session, test_template, test_project):
        """测试生成报表 - 带过滤条件"""
        from app.services.template_report.core import TemplateReportCore
        
        filters = {'status': 'ACTIVE', 'priority': 'HIGH'}
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id,
                filters=filters
            )
            
            assert result is not None
            mock_gen.assert_called_once()

    def test_generate_from_template_with_sections_config(self, db_session, test_template, test_project):
        """测试生成报表 - 带sections配置"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.sections = {
            'summary': True,
            'milestones': True,
            'tasks': False
        }
        db_session.commit()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            mock_gen.assert_called_once()

    def test_generate_from_template_with_metrics_config(self, db_session, test_template, test_project):
        """测试生成报表 - 带metrics配置"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.metrics_config = {
            'progress': True,
            'cost': True,
            'quality': False
        }
        db_session.commit()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            mock_gen.assert_called_once()

    def test_generate_from_template_empty_sections(self, db_session, test_template, test_project):
        """测试生成报表 - 空sections配置"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.sections = None
        db_session.commit()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            assert 'sections' in result

    def test_generate_from_template_empty_metrics(self, db_session, test_template, test_project):
        """测试生成报表 - 空metrics配置"""
        from app.services.template_report.core import TemplateReportCore
        
        test_template.metrics_config = None
        db_session.commit()
        
        with patch('app.services.template_report.project_reports.ProjectReportMixin._generate_project_weekly') as mock_gen:
            mock_gen.return_value = {
                'summary': {},
                'sections': {},
                'metrics': {}
            }
            
            result = TemplateReportCore.generate_from_template(
                db=db_session,
                template=test_template,
                project_id=test_project.id
            )
            
            assert result is not None
            assert 'metrics' in result
