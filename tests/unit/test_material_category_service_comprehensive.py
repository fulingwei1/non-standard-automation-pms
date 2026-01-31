# -*- coding: utf-8 -*-
"""
MaterialCategoryService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换响应对象
- get_tree: 获取分类树
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestMaterialCategoryServiceInit:
    """测试 MaterialCategoryService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()

        service = MaterialCategoryService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "物料分类"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.material_category_service import MaterialCategoryService
        from app.models.material import MaterialCategory

        mock_db = MagicMock()

        service = MaterialCategoryService(mock_db)

        assert service.model == MaterialCategory


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_category_to_response(self):
        """测试转换分类为响应对象"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        mock_category = MagicMock()
        mock_category.id = 1
        mock_category.category_code = "ELEC"
        mock_category.category_name = "电子元器件"
        mock_category.parent_id = None
        mock_category.sort_order = 1
        mock_category.created_at = datetime(2024, 1, 1)
        mock_category.updated_at = datetime(2024, 1, 1)

        with patch('app.schemas.material.MaterialCategoryResponse.model_validate') as mock_validate:
            mock_response = MagicMock()
            mock_validate.return_value = mock_response

            result = service._to_response(mock_category)

            mock_validate.assert_called_once_with(mock_category)
            assert result == mock_response


class TestGetTree:
    """测试 get_tree 方法"""

    def test_returns_root_categories(self):
        """测试返回根分类"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.category_name = "电子元器件"

        mock_cat2 = MagicMock()
        mock_cat2.id = 2
        mock_cat2.category_name = "机械零件"

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_cat1, mock_cat2]
        mock_db.query.return_value = mock_query

        with patch.object(service, '_to_response') as mock_to_response:
            mock_resp1 = MagicMock()
            mock_resp1.children = []
            mock_resp2 = MagicMock()
            mock_resp2.children = []
            mock_to_response.side_effect = [mock_resp1, mock_resp2]

            # 需要模拟子分类查询返回空列表
            def query_side_effect(*args, **kwargs):
                return mock_query

            mock_db.query.side_effect = query_side_effect
            mock_query.filter.return_value.order_by.return_value.all.side_effect = [
                [mock_cat1, mock_cat2],  # 根分类
                [],  # cat1 的子分类
                [],  # cat2 的子分类
            ]

            result = service.get_tree(parent_id=None)

            assert len(result) == 2

    def test_returns_empty_list_for_no_categories(self):
        """测试没有分类时返回空列表"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_tree(parent_id=None)

        assert result == []

    def test_returns_child_categories(self):
        """测试返回子分类"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        mock_child = MagicMock()
        mock_child.id = 3
        mock_child.category_name = "电容"

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.side_effect = [
            [mock_child],  # parent_id=1 的子分类
            [],  # mock_child 的子分类
        ]
        mock_db.query.return_value = mock_query

        with patch.object(service, '_to_response') as mock_to_response:
            mock_resp = MagicMock()
            mock_resp.children = []
            mock_to_response.return_value = mock_resp

            result = service.get_tree(parent_id=1)

            assert len(result) == 1

    def test_orders_by_sort_order(self):
        """测试按排序顺序排序"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_tree(parent_id=None)

        mock_filter.order_by.assert_called_once()

    def test_builds_recursive_tree(self):
        """测试构建递归树结构"""
        from app.services.material_category_service import MaterialCategoryService

        mock_db = MagicMock()
        service = MaterialCategoryService(mock_db)

        # 根分类
        mock_root = MagicMock()
        mock_root.id = 1
        mock_root.category_name = "电子元器件"

        # 子分类
        mock_child = MagicMock()
        mock_child.id = 2
        mock_child.category_name = "电容"

        # 孙分类
        mock_grandchild = MagicMock()
        mock_grandchild.id = 3
        mock_grandchild.category_name = "贴片电容"

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.side_effect = [
            [mock_root],        # 根分类
            [mock_child],       # root 的子分类
            [mock_grandchild],  # child 的子分类
            [],                 # grandchild 的子分类
        ]
        mock_db.query.return_value = mock_query

        with patch.object(service, '_to_response') as mock_to_response:
            mock_resp_root = MagicMock()
            mock_resp_child = MagicMock()
            mock_resp_grandchild = MagicMock()
            mock_resp_grandchild.children = []
            mock_resp_child.children = [mock_resp_grandchild]
            mock_resp_root.children = [mock_resp_child]

            mock_to_response.side_effect = [
                mock_resp_root,
                mock_resp_child,
                mock_resp_grandchild,
            ]

            result = service.get_tree(parent_id=None)

            assert len(result) == 1
            assert result[0].children == [mock_resp_child]
