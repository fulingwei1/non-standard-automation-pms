# -*- coding: utf-8 -*-
"""第二十批 - material_category_service 单元测试"""
import pytest
pytest.importorskip("app.services.material_category_service")

from unittest.mock import MagicMock, patch
from app.services.material_category_service import MaterialCategoryService


def make_db():
    return MagicMock()


def make_category(id=1, parent_id=None, sort_order=0, name="分类A"):
    cat = MagicMock()
    cat.id = id
    cat.parent_id = parent_id
    cat.sort_order = sort_order
    cat.category_name = name
    return cat


class TestMaterialCategoryServiceInit:
    def test_init_sets_db(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        assert svc.db is db

    def test_init_sets_model(self):
        from app.models.material import MaterialCategory
        db = make_db()
        svc = MaterialCategoryService(db)
        assert svc.model is MaterialCategory


class TestGetTree:
    def test_get_tree_empty(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query
        result = svc.get_tree(parent_id=None)
        assert result == []

    def test_get_tree_single_level(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        cat = make_category(id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        # First call returns [cat], subsequent calls (for children) return []
        call_count = [0]
        def all_side():
            call_count[0] += 1
            if call_count[0] == 1:
                return [cat]
            return []
        mock_query.all.side_effect = all_side
        db.query.return_value = mock_query

        mock_resp = MagicMock()
        mock_resp.children = None

        with patch.object(svc, '_to_response', return_value=mock_resp):
            result = svc.get_tree(parent_id=None)
        assert len(result) == 1

    def test_get_tree_with_parent_id(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query
        result = svc.get_tree(parent_id=5)
        assert result == []


class TestToResponse:
    def test_to_response_calls_model_validate(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        cat = make_category()
        from app.schemas.material import MaterialCategoryResponse
        with patch.object(MaterialCategoryResponse, 'model_validate', return_value=MagicMock()) as mock_mv:
            svc._to_response(cat)
            mock_mv.assert_called_once_with(cat)

    def test_to_response_returns_schema(self):
        db = make_db()
        svc = MaterialCategoryService(db)
        cat = make_category()
        expected = MagicMock()
        from app.schemas.material import MaterialCategoryResponse
        with patch.object(MaterialCategoryResponse, 'model_validate', return_value=expected):
            result = svc._to_response(cat)
            assert result is expected
