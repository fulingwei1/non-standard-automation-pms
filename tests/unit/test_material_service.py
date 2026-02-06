# -*- coding: utf-8 -*-
"""
Tests for material_service
Covers: app/services/material_service.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.schemas.material import MaterialResponse


class TestMaterialServiceInit:
    """Test suite for service initialization."""

    def test_init_service(self):
        from app.services.material_service import MaterialService

        mock_session = Mock(spec=Session)
        service = MaterialService(mock_session)

        assert service.db == mock_session
        assert service.model == Material
        assert service.resource_name == "物料"


class TestToResponse:
    """Test suite for _to_response method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_to_response_with_category(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        mock_category = Mock()
        mock_category.category_name = "电气件"

        mock_material = Mock(spec=Material)
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "电阻"
        mock_material.category_id = 1
        mock_material.category = mock_category
        mock_material.material_type = "电气件"
        mock_material.specification = "10K"
        mock_material.unit = "个"
        mock_material.brand = "国产"
        mock_material.standard_price = 0.5
        mock_material.last_price = 0.45
        mock_material.safety_stock = 100
        mock_material.current_stock = 500
        mock_material.lead_time_days = 7
        mock_material.is_key_material = False
        mock_material.is_active = True
        mock_material.remark = None
        mock_material.created_at = None
        mock_material.updated_at = None

        with patch.object(MaterialResponse, 'model_validate') as mock_validate:
            mock_response = Mock(spec=MaterialResponse)
            mock_response.category_name = None
            mock_validate.return_value = mock_response

            result = service._to_response(mock_material)

            assert result.category_name == "电气件"
            assert result.standard_price == 0.5
            assert result.last_price == 0.45

    def test_to_response_without_category(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        mock_material = Mock(spec=Material)
        mock_material.id = 2
        mock_material.material_code = "MAT002"
        mock_material.material_name = "螺丝"
        mock_material.category_id = None
        mock_material.category = None  # No category
        mock_material.material_type = "标准件"
        mock_material.specification = "M4"
        mock_material.unit = "个"
        mock_material.brand = None
        mock_material.standard_price = 0.1
        mock_material.last_price = 0.08
        mock_material.safety_stock = 1000
        mock_material.current_stock = 5000
        mock_material.lead_time_days = 3
        mock_material.is_key_material = False
        mock_material.is_active = True
        mock_material.remark = None
        mock_material.created_at = None
        mock_material.updated_at = None

        with patch.object(MaterialResponse, 'model_validate') as mock_validate:
            mock_response = Mock(spec=MaterialResponse)
            mock_response.category_name = None
            mock_validate.return_value = mock_response

            result = service._to_response(mock_material)

            # category_name should remain None when no category
            mock_validate.assert_called_once_with(mock_material)

    def test_to_response_with_none_values(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        mock_material = Mock(spec=Material)
        mock_material.id = 3
        mock_material.material_code = "MAT003"
        mock_material.material_name = "测试物料"
        mock_material.category = None
        mock_material.standard_price = None
        mock_material.last_price = None
        mock_material.safety_stock = None
        mock_material.current_stock = None
        mock_material.lead_time_days = None

        with patch.object(MaterialResponse, 'model_validate') as mock_validate:
            mock_response = Mock(spec=MaterialResponse)
            mock_validate.return_value = mock_response

            result = service._to_response(mock_material)

            # None values should be converted to 0
            assert result.standard_price == 0
            assert result.last_price == 0
            assert result.safety_stock == 0
            assert result.current_stock == 0
            assert result.lead_time_days == 0


class TestListMaterials:
    """Test suite for list_materials method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_list_materials_default_params(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_materials()

            assert result["items"] == []
            assert result["total"] == 0
            assert result["page"] == 1
            assert result["page_size"] == 20
            assert result["pages"] == 0

    def test_list_materials_with_pagination(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = ["item1", "item2"]
            mock_result.total = 50
            mock_result.page = 2
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_materials(page=2, page_size=10)

            assert result["total"] == 50
            assert result["page"] == 2
            assert result["page_size"] == 10
            assert result["pages"] == 5  # 50/10 = 5 pages

    def test_list_materials_with_keyword(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            service.list_materials(keyword="电阻")

            # Verify list was called with search parameter
            call_args = mock_list.call_args[0][0]
            assert call_args.search == "电阻"
            assert "material_code" in call_args.search_fields
            assert "material_name" in call_args.search_fields

    def test_list_materials_with_filters(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            service.list_materials(
                category_id=5,
                material_type="电气件",
                is_key_material=True,
                is_active=True
            )

            # Verify filters were applied
            call_args = mock_list.call_args[0][0]
            assert call_args.filters["category_id"] == 5
            assert call_args.filters["material_type"] == "电气件"
            assert call_args.filters["is_key_material"] is True
            assert call_args.filters["is_active"] is True

    def test_list_materials_pages_calculation(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 25
            mock_result.page = 1
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_materials(page_size=10)

            # 25 items / 10 per page = 3 pages (rounded up)
            assert result["pages"] == 3


class TestGenerateCode:
    """Test suite for generate_code method."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_generate_code_without_category(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        with patch('app.utils.number_generator.generate_material_code') as mock_gen:
            mock_gen.return_value = "MAT20250130001"

            result = service.generate_code()

            mock_gen.assert_called_once_with(db_session, None)
            assert result == "MAT20250130001"

    def test_generate_code_with_category_id(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        mock_category = Mock(spec=MaterialCategory)
        mock_category.id = 1
        mock_category.category_code = "ELC"

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_category)
        db_session.query = Mock(return_value=mock_query)

        with patch('app.utils.number_generator.generate_material_code') as mock_gen:
            mock_gen.return_value = "ELC20250130001"

            result = service.generate_code(category_id=1)

            mock_gen.assert_called_once_with(db_session, "ELC")
            assert result == "ELC20250130001"

    def test_generate_code_with_nonexistent_category(self, db_session):
        from app.services.material_service import MaterialService

        service = MaterialService(db_session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)  # Category not found
        db_session.query = Mock(return_value=mock_query)

        with patch('app.utils.number_generator.generate_material_code') as mock_gen:
            mock_gen.return_value = "MAT20250130001"

            result = service.generate_code(category_id=999)

            # Should use None for category_code when category not found
            mock_gen.assert_called_once_with(db_session, None)
            assert result == "MAT20250130001"
