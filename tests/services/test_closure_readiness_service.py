# -*- coding: utf-8 -*-
"""项目结项准备度服务测试"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestClosureReadinessService:
    """ClosureReadinessService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import ClosureReadinessService

        return ClosureReadinessService(mock_db)

    def test_check_closure_readiness_project_not_found(self, service, mock_db):
        """测试项目不存在时返回未就绪 - 这个测试通过"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.check_readiness(project_id=999)

        assert result["ready"] is False
        assert result["score"] == 0
        assert "项目不存在" in result["missing_items"]

    def test_check_closure_readiness_returns_dict(self, service, mock_db):
        """测试返回是字典类型"""
        # 项目不存在返回基本结构
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.check_readiness(project_id=999)

        assert isinstance(result, dict)
        assert "ready" in result
        assert "score" in result
        assert "checks" in result
        assert "missing_items" in result

    def test_missing_items_list(self, service, mock_db):
        """测试 missing_items 是列表"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.check_readiness(project_id=999)

        assert isinstance(result["missing_items"], list)
        assert isinstance(result["recommendations"], list)

    def test_checks_is_list(self, service, mock_db):
        """测试 checks 是列表"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.check_readiness(project_id=999)

        assert isinstance(result["checks"], list)


class TestClosureNotificationService:
    """ClosureNotificationService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import ClosureNotificationService

        return ClosureNotificationService(mock_db)

    def test_notify_if_ready_ready(self, service, mock_db):
        """测试项目已就绪时发送通知"""
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 1,
        }

        project = MagicMock()
        project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = project

        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Should return list of notified user IDs
        assert isinstance(result, list)

    def test_notify_if_ready_not_ready(self, service, mock_db):
        """测试项目未就绪时不发送通知"""
        readiness = {
            "ready": False,
            "score": 50,
            "project_id": 1,
        }

        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Empty list when not ready
        assert result == []


class TestLessonsCollectionService:
    """LessonsCollectionService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import LessonsCollectionService

        return LessonsCollectionService(mock_db)

    def test_service_initialization(self, service, mock_db):
        """测试服务可以正常初始化"""
        assert service is not None
        assert service.db is mock_db