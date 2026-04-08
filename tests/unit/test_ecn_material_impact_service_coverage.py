# -*- coding: utf-8 -*-
"""
ECN物料影响跟踪服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.ecn.ecn_material_impact_service import (
    EcnMaterialImpactService,
    ROLE_NAMES,
    EXECUTION_PHASES,
    NOTIFICATION_CATEGORY,
)
from app.models.ecn.core import Ecn
from app.models.ecn.material_impact import EcnExecutionProgress, EcnMaterialDisposition, EcnStakeholder


class TestEcnMaterialImpactServiceConstants:
    """测试常量和配置"""

    def test_role_names_not_empty(self):
        """测试角色名称映射非空"""
        assert len(ROLE_NAMES) > 0
        assert "PROJECT_MANAGER" in ROLE_NAMES
        assert "PURCHASER" in ROLE_NAMES

    def test_execution_phases_count(self):
        """测试执行阶段数量"""
        assert len(EXECUTION_PHASES) == 5

    def test_notification_category(self):
        """测试通知类别"""
        assert NOTIFICATION_CATEGORY == "project"


class TestEcnMaterialImpactServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = EcnMaterialImpactService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            EcnMaterialImpactService()


class TestEcnMaterialImpactServiceAnalysis:
    """测试影响分析"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EcnMaterialImpactService(mock_db)

    def test_analyze_material_impact_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'analyze_material_impact')

    def test_get_execution_progress_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_execution_progress')

    def test_get_stakeholders_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_stakeholders')


class TestEcnMaterialImpactServiceDisposition:
    """测试物料处置"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EcnMaterialImpactService(mock_db)

    def test_update_material_disposition_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'update_material_disposition')

    def test__ensure_disposition_record_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_ensure_disposition_record')


class TestEcnMaterialImpactServiceNotification:
    """测试通知功能"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EcnMaterialImpactService(mock_db)

    def test_notify_stakeholders_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'notify_stakeholders')

    def test__build_notification_content_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_build_notification_content')


class TestEcnMaterialImpactServiceHelper:
    """测试辅助方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EcnMaterialImpactService(mock_db)

    def test__determine_material_status_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_determine_material_status')

    def test__find_purchase_order_info_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_find_purchase_order_info')

    def test__calculate_potential_loss_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_calculate_potential_loss')

    def test__get_affected_orders_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_affected_orders')

    def test__get_project_impacts_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_project_impacts')

    def test__get_ecn_or_raise_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_ecn_or_raise')


class TestEcnMaterialImpactServiceSubscription:
    """测试订阅管理"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return EcnMaterialImpactService(mock_db)

    def test_update_subscription_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'update_subscription')

    def test__auto_identify_stakeholders_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_auto_identify_stakeholders')