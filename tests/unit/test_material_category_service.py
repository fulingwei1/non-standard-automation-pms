# -*- coding: utf-8 -*-
"""
Tests for material_category_service
物料分类服务测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.material import MaterialCategory


@pytest.mark.unit
class TestMaterialCategoryService:
    """物料分类服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建 MaterialCategoryService 实例"""
        from app.services.material_category_service import MaterialCategoryService
        return MaterialCategoryService(mock_db)

    def test_init(self, mock_db):
        """测试服务初始化"""
        from app.services.material_category_service import MaterialCategoryService
        service = MaterialCategoryService(mock_db)
        assert service.db == mock_db
        assert service.model == MaterialCategory
        assert service.resource_name == "物料分类"

    def test_to_response(self, service, mock_db):
        """测试响应转换"""
        mock_category = Mock(
            id=1,
            name="电子元件",
            code="EC",
            parent_id=None,
            level=1,
            full_path="/电子元件",
            sort_order=1,
            is_active=True
        )
        mock_category.model_dump = lambda: {
            "id": 1,
            "name": "电子元件",
            "code": "EC",
            "parent_id": None,
            "level": 1,
            "full_path": "/电子元件",
            "sort_order": 1,
            "is_active": True
        }

        # Patch model_validate
        with patch('app.schemas.material.MaterialCategoryResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response

            result = service._to_response(mock_category)

            mock_validate.assert_called_once_with(mock_category)
            assert result == mock_response

    def test_get_tree_empty(self, service, mock_db):
        """测试获取空分类树"""
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_tree()

        assert result == []

    def test_get_tree_single_level(self, service, mock_db):
        """测试获取单层分类树"""
        mock_cat1 = Mock(id=1, name="Cat1", parent_id=None, sort_order=1)
        mock_cat2 = Mock(id=2, name="Cat2", parent_id=None, sort_order=2)

        def mock_query_filter(condition):
            mock_result = Mock()
            # Check if filtering for root (parent_id == None) or children
            if "1" in str(condition) or "2" in str(condition):
                mock_result.all.return_value = []
            else:
                mock_result.all.return_value = [mock_cat1, mock_cat2]
            mock_result.order_by.return_value = mock_result
            return mock_result

        mock_query = Mock()
        mock_query.filter.side_effect = mock_query_filter
        mock_db.query.return_value = mock_query

        # Mock _to_response
        def mock_to_response(cat):
            resp = Mock()
            resp.children = []
            resp.id = cat.id
            resp.name = cat.name
            return resp

        with patch.object(service, '_to_response', side_effect=mock_to_response):
            result = service.get_tree(parent_id=None)

            assert len(result) == 2

    def test_get_tree_with_children(self, service, mock_db):
        """测试获取带子分类的树"""
        mock_parent = Mock(id=1, name="Parent", parent_id=None, sort_order=1)
        mock_child = Mock(id=2, name="Child", parent_id=1, sort_order=1)

        call_count = [0]

        def mock_filter(condition):
            mock_result = Mock()
            call_count[0] += 1
            if call_count[0] == 1:  # First call - root level
                mock_result.all.return_value = [mock_parent]
            elif call_count[0] == 2:  # Second call - children of parent
                mock_result.all.return_value = [mock_child]
            else:  # Subsequent calls - no more children
                mock_result.all.return_value = []
            mock_result.order_by.return_value = mock_result
            return mock_result

        mock_query = Mock()
        mock_query.filter.side_effect = mock_filter
        mock_db.query.return_value = mock_query

        def mock_to_response(cat):
            resp = Mock()
            resp.children = []
            resp.id = cat.id
            resp.name = cat.name
            return resp

        with patch.object(service, '_to_response', side_effect=mock_to_response):
            result = service.get_tree()

            assert len(result) == 1
            assert result[0].id == 1

    def test_get_tree_with_specific_parent(self, service, mock_db):
        """测试获取特定父级下的分类树"""
        mock_child1 = Mock(id=2, name="Child1", parent_id=1, sort_order=1)
        mock_child2 = Mock(id=3, name="Child2", parent_id=1, sort_order=2)

        call_count = [0]

        def mock_filter(condition):
            mock_result = Mock()
            call_count[0] += 1
            if call_count[0] == 1:  # First call - children of parent_id=1
                mock_result.all.return_value = [mock_child1, mock_child2]
            else:
                mock_result.all.return_value = []
            mock_result.order_by.return_value = mock_result
            return mock_result

        mock_query = Mock()
        mock_query.filter.side_effect = mock_filter
        mock_db.query.return_value = mock_query

        def mock_to_response(cat):
            resp = Mock()
            resp.children = []
            resp.id = cat.id
            resp.name = cat.name
            return resp

        with patch.object(service, '_to_response', side_effect=mock_to_response):
            result = service.get_tree(parent_id=1)

            assert len(result) == 2
            assert result[0].id == 2
            assert result[1].id == 3
