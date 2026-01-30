# -*- coding: utf-8 -*-
"""
MaterialService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换响应对象
- list_materials: 获取物料列表
- generate_code: 生成物料编码
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestMaterialServiceInit:
    """测试 MaterialService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()

        service = MaterialService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "物料"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.material_service import MaterialService
        from app.models.material import Material

        mock_db = MagicMock()

        service = MaterialService(mock_db)

        assert service.model == Material


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_material_with_category(self):
        """测试转换带分类的物料"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_category = MagicMock()
        mock_category.category_name = "电子元器件"

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.category = mock_category
        mock_material.standard_price = 100.5
        mock_material.last_price = 98.0
        mock_material.safety_stock = 50
        mock_material.current_stock = 100
        mock_material.lead_time_days = 7
        mock_material.created_at = datetime(2024, 1, 1)
        mock_material.updated_at = datetime(2024, 1, 1)

        with patch('app.schemas.material.MaterialResponse.model_validate') as mock_validate:
            mock_response = MagicMock()
            mock_response.category_name = None
            mock_validate.return_value = mock_response

            result = service._to_response(mock_material)

            assert result.category_name == "电子元器件"

    def test_handles_none_category(self):
        """测试处理无分类的物料"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT002"
        mock_material.material_name = "未分类物料"
        mock_material.category = None
        mock_material.standard_price = None
        mock_material.last_price = None
        mock_material.safety_stock = None
        mock_material.current_stock = None
        mock_material.lead_time_days = None
        mock_material.created_at = datetime(2024, 1, 1)
        mock_material.updated_at = datetime(2024, 1, 1)

        with patch('app.schemas.material.MaterialResponse.model_validate') as mock_validate:
            mock_response = MagicMock()
            mock_response.category_name = None
            mock_response.standard_price = None
            mock_response.last_price = None
            mock_response.safety_stock = None
            mock_response.current_stock = None
            mock_response.lead_time_days = None
            mock_validate.return_value = mock_response

            result = service._to_response(mock_material)

            assert result.standard_price == 0
            assert result.last_price == 0
            assert result.safety_stock == 0
            assert result.current_stock == 0
            assert result.lead_time_days == 0


class TestListMaterials:
    """测试 list_materials 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = [MagicMock(), MagicMock()]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_materials(page=1, page_size=20)

            assert result['items'] == mock_result.items
            assert result['total'] == 2
            assert result['page'] == 1
            assert result['page_size'] == 20

    def test_filters_by_category_id(self):
        """测试按分类ID过滤"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_materials(category_id=5)

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('category_id') == 5

    def test_filters_by_material_type(self):
        """测试按物料类型过滤"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_materials(material_type="STANDARD")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('material_type') == "STANDARD"

    def test_filters_by_is_key_material(self):
        """测试按关键物料过滤"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_materials(is_key_material=True)

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('is_key_material') is True

    def test_filters_by_is_active(self):
        """测试按激活状态过滤"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_materials(is_active=True)

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('is_active') is True

    def test_searches_by_keyword(self):
        """测试关键字搜索"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_materials(keyword="电阻")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "电阻"
            assert "material_code" in call_args.search_fields
            assert "material_name" in call_args.search_fields

    def test_calculates_pages(self):
        """测试计算总页数"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 100
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_materials()

            # (100 + 20 - 1) // 20 = 5
            assert result['pages'] == 5


class TestGenerateCode:
    """测试 generate_code 方法"""

    def test_generates_code_without_category(self):
        """测试不带分类生成编码"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        with patch('app.services.material_service.generate_material_code', return_value="MAT20260101001") as mock_gen:
            result = service.generate_code()

            mock_gen.assert_called_once_with(mock_db, None)
            assert result == "MAT20260101001"

    def test_generates_code_with_category(self):
        """测试带分类生成编码"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_category = MagicMock()
        mock_category.category_code = "ELEC"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_category

        with patch('app.services.material_service.generate_material_code', return_value="ELEC20260101001") as mock_gen:
            result = service.generate_code(category_id=1)

            mock_gen.assert_called_once_with(mock_db, "ELEC")
            assert result == "ELEC20260101001"

    def test_generates_code_with_nonexistent_category(self):
        """测试不存在的分类生成编码"""
        from app.services.material_service import MaterialService

        mock_db = MagicMock()
        service = MaterialService(mock_db)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.material_service.generate_material_code', return_value="MAT20260101001") as mock_gen:
            result = service.generate_code(category_id=999)

            mock_gen.assert_called_once_with(mock_db, None)
            assert result == "MAT20260101001"
