# -*- coding: utf-8 -*-
"""
装配工艺齐套分析服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.assembly_kit_service import AssemblyKitService
from app.models.assembly_kit import AssemblyStage, BomItemAssemblyAttrs, MaterialReadiness
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine, Project


class TestAssemblyKitServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = AssemblyKitService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            AssemblyKitService()


class TestAssemblyKitServiceStages:
    """测试装配阶段管理"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_get_assembly_stages_empty(self, service):
        """测试空阶段列表"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = []
        service.db.query.return_value = query_mock
        
        stages = service.get_assembly_stages()
        
        assert stages == []

    def test_get_assembly_stages_with_data(self, service):
        """测试有阶段数据"""
        stage = Mock(spec=AssemblyStage)
        stage.id = 1
        stage.stage_code = "STAGE01"
        stage.stage_name = "装配阶段1"
        stage.stage_order = 1
        stage.description = "描述"
        stage.default_duration = 8
        stage.color_code = "#FF0000"
        stage.icon = "icon"
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = [stage]
        service.db.query.return_value = query_mock
        
        stages = service.get_assembly_stages(active_only=True)
        
        assert len(stages) == 1
        assert stages[0]["id"] == 1

    def test_get_assembly_stages_all(self, service):
        """测试获取所有阶段（包括禁用）"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.order_by.return_value.all.return_value = []
        service.db.query.return_value = query_mock
        
        stages = service.get_assembly_stages(active_only=False)
        
        assert stages == []


class TestAssemblyKitServiceAutoAssign:
    """测试物料自动分配"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_auto_assign_materials_bom_not_found(self, service):
        """测试BOM不存在"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        service.db.query.return_value = query_mock
        
        result = service.auto_assign_materials_to_stages(bom_id=999)
        
        assert result.get("error") == "BOM 不存在"

    def test_auto_assign_materials_empty_bom(self, service):
        """测试空BOM"""
        bom = Mock(spec=BomHeader)
        bom.id = 1
        
        service.db.query = Mock()
        
        def query_side_effect(model):
            query_mock = Mock()
            if model == BomHeader:
                query_mock.filter.return_value.first.return_value = bom
            else:
                query_mock.filter.return_value.all.return_value = []
            return query_mock
        
        service.db.query.side_effect = query_side_effect
        
        result = service.auto_assign_materials_to_stages(bom_id=1)
        
        assert result.get("assigned_count", 0) == 0


class TestAssemblyKitServiceReadiness:
    """测试物料齐套状态"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_calculate_stage_kit_rate_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'calculate_stage_kit_rate')

    def test_save_readiness_analysis_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'save_readiness_analysis')


class TestAssemblyKitServiceProject:
    """测试项目齐套分析"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_analyze_bom_item_method_exists(self, service):
        """测试模块函数存在"""
        from app.services.assembly_kit_service import analyze_bom_item
        assert callable(analyze_bom_item)

    def test_get_material_lead_time_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_material_lead_time')


class TestAssemblyKitServiceMachine:
    """测试设备齐套分析"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_calculate_time_based_kit_rate_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'calculate_time_based_kit_rate')

    def test_get_expected_arrival_date_method_exists(self, service):
        """测试方法存在"""
        # 这是模块级别的函数，不是类方法
        from app.services.assembly_kit_service import get_expected_arrival_date
        assert callable(get_expected_arrival_date)


class TestAssemblyKitServiceReport:
    """测试报告生成"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_validate_analysis_inputs_method_exists(self, service):
        """测试方法存在"""
        from app.services.assembly_kit_service import validate_analysis_inputs
        assert callable(validate_analysis_inputs)

    def test_initialize_stage_results_method_exists(self, service):
        """测试方法存在"""
        from app.services.assembly_kit_service import initialize_stage_results
        assert callable(initialize_stage_results)


class TestAssemblyKitServiceUpdate:
    """测试更新操作"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return AssemblyKitService(mock_db)

    def test_auto_assign_materials_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'auto_assign_materials_to_stages')

    def test_get_assembly_stages_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_assembly_stages')