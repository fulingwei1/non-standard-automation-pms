# -*- coding: utf-8 -*-
"""
项目数据流通服务测试

测试 ProjectDataFlowService 的核心功能
"""

from unittest.mock import Mock, MagicMock

import pytest
from sqlalchemy.orm import Session


class TestProjectDataFlowService:
    """项目数据流通服务测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟的数据库会话"""
        db = Mock(spec=Session)
        db.query = Mock(return_value=Mock())
        db.add = Mock()
        db.commit = Mock()
        db.flush = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db_session):
        """创建项目数据流通服务实例"""
        from app.services.project_data_flow_service import ProjectDataFlowService
        return ProjectDataFlowService(mock_db_session)

    def test_create_work_orders_from_wbs_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_work_orders_from_wbs(project_id=999)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_transfer_to_after_sales_success(self, service, mock_db_session):
        """测试项目验收后成功转入售后服务"""
        # Mock 项目
        project = Mock()
        project.id = 1
        project.customer_id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = project
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.transfer_to_after_sales(project_id=1)

        # 验证结果
        assert result["project_id"] == 1
        assert result["maintenance_created"] == 4
        assert len(result["maintenance_records"]) == 4
        assert "1 个月保养" in result["maintenance_records"]
        assert "3 个月保养" in result["maintenance_records"]
        assert "6 个月保养" in result["maintenance_records"]
        assert "12 个月保养" in result["maintenance_records"]
        # 验证添加了4条保养记录
        assert mock_db_session.add.call_count == 4

    def test_transfer_to_after_sales_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.transfer_to_after_sales(project_id=999)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_create_purchase_requests_from_bom_no_bom(self, service, mock_db_session):
        """测试项目无BOM时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_purchase_requests_from_bom(project_id=1)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目无 BOM 数据"

    def test_create_delivery_schedule_project_not_found(self, service, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.create_delivery_schedule_from_project(project_id=999, initiator_id=100)

        # 验证结果
        assert "error" in result
        assert result["error"] == "项目不存在"