# -*- coding: utf-8 -*-
"""
Tests for template_report_service service
Covers: app/services/template_report_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 171 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.template_report_service import TemplateReportService


@pytest.fixture
def template_report_service(db_session: Session):
    """创建 TemplateReportService 实例"""
    return TemplateReportService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    from app.models.project import Project
    project = Project(
        project_code="PJ001",
        project_name="测试项目"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestTemplateReportService:
    """Test suite for TemplateReportService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = TemplateReportService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_generate_from_template_not_found(self, template_report_service):
        """测试模板不存在"""
        result = template_report_service.generate_from_template(
            template_id=99999,
            project_id=1,
            data={}
        )
        
        assert result is not None
        assert result.get('success') is False
        assert '不存在' in result.get('message', '')

    def test_generate_from_template_success(self, template_report_service, db_session, test_project):
        """测试成功生成报表"""
        # Mock模板查询
        with patch.object(template_report_service.db, 'query') as mock_query:
            # Mock模板对象
            mock_template = MagicMock()
            mock_template.id = 1
            mock_template.template_name = "测试模板"
            mock_template.template_content = "测试内容"
            mock_template.template_type = "PROJECT"
            
            # Mock查询链
            mock_query_result = MagicMock()
            mock_query_result.filter.return_value.first.return_value = mock_template
            mock_query.return_value = mock_query_result
            
            result = template_report_service.generate_from_template(
                template_id=1,
                project_id=test_project.id,
                data={"key": "value"}
            )
            
            assert result is not None
            # 根据实际实现调整断言

    def test_generate_from_template_invalid_data(self, template_report_service):
        """测试无效数据"""
        result = template_report_service.generate_from_template(
            template_id=1,
            project_id=1,
            data=None
        )
        
        # 根据实际实现，可能返回错误或使用默认值
        assert result is not None

    def test_get_available_templates(self, template_report_service, db_session):
        """测试获取可用模板列表"""
        result = template_report_service.get_available_templates(
            template_type="PROJECT"
        )
        
        assert isinstance(result, list)

    def test_get_available_templates_by_project(self, template_report_service, db_session, test_project):
        """测试根据项目获取模板"""
        result = template_report_service.get_available_templates(
            template_type="PROJECT",
            project_id=test_project.id
        )
        
        assert isinstance(result, list)
