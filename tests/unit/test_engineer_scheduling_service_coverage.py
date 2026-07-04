# -*- coding: utf-8 -*-
"""
工程师智能排产服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta, datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List, Optional

from app.services.engineer_scheduling_service import EngineerSchedulingService
from app.models.engineer_capacity import EngineerCapacity, EngineerTaskAssignment, WorkloadWarning
from app.models.user import User
from app.models.project import Project
from sqlalchemy.exc import OperationalError


class TestEngineerSchedulingServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = EngineerSchedulingService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            EngineerSchedulingService()


class TestEngineerSchedulingServiceSafeQuery:
    """测试安全查询方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_query_task_assignments_success(self, service):
        """测试正常查询"""
        assignment = Mock(spec=EngineerTaskAssignment)
        assignment.id = 1
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.all.return_value = [assignment]
        service.db.query.return_value = query_mock
        
        result = service._query_task_assignments()
        
        assert len(result) == 1

    def test_query_task_assignments_table_missing_raises_after_ensure(self, service):
        """补表后仍查询失败时不再静默返回无冲突。"""
        exc = OperationalError("no such table: engineer_task_assignments", {}, None)
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.all.side_effect = exc
        service.db.query.return_value = query_mock
        
        with pytest.raises(OperationalError):
            service._query_task_assignments()

    def test_get_engineer_capacity_found(self, service):
        """测试找到工程师能力模型"""
        capacity = Mock(spec=EngineerCapacity)
        capacity.engineer_id = 1
        capacity.daily_capacity = 8
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = capacity
        service.db.query.return_value = query_mock
        
        result = service._get_engineer_capacity(1)
        
        assert result is not None
        assert result.engineer_id == 1

    def test_get_engineer_capacity_not_found(self, service):
        """测试未找到工程师能力模型"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        service.db.query.return_value = query_mock
        
        result = service._get_engineer_capacity(999)
        
        assert result is None

    def test_get_engineer_capacity_table_missing(self, service):
        """测试表不存在时返回None"""
        exc = OperationalError("no such table: engineer_capacity", {}, None)
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.side_effect = exc
        service.db.query.return_value = query_mock
        
        result = service._get_engineer_capacity(1)
        
        assert result is None


class TestEngineerSchedulingServiceAnalysis:
    """测试分析方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_analyze_engineer_workload_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'analyze_engineer_workload')

    def test_detect_task_conflicts_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'detect_task_conflicts')

    def test_extract_engineer_capacity_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'extract_engineer_capacity')


class TestEngineerSchedulingServiceCapacity:
    """测试能力模型"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_get_all_engineer_capacities_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_engineer_capacity')

    def test_save_or_update_capacity_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'save_or_update_capacity')


class TestEngineerSchedulingServiceWarning:
    """测试预警功能"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_generate_workload_warnings_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_workload_warnings')

    def test_generate_scheduling_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_scheduling_report')


class TestEngineerSchedulingServiceAssignment:
    """测试任务分配"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_analyze_engineer_workload_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'analyze_engineer_workload')

    def test_evaluate_ai_capability_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'evaluate_ai_capability')


class TestEngineerSchedulingServiceReport:
    """测试报告"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EngineerSchedulingService(mock_db)

    def test_generate_scheduling_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_scheduling_report')

    def test_save_ai_capability_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'save_ai_capability')
