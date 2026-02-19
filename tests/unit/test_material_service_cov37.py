# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 物料管理服务
tests/unit/test_material_service_cov37.py
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.material_service")

from app.services.material_service import MaterialService


def _make_service():
    db = MagicMock()
    with patch(
        "app.services.material_service.BaseService.__init__",
        return_value=None,
    ):
        svc = MaterialService.__new__(MaterialService)
        svc.db = db
        return svc, db


class TestMaterialServiceToResponse:
    def test_to_response_without_category(self):
        svc, db = _make_service()
        obj = MagicMock()
        obj.category = None
        obj.standard_price = None
        obj.last_price = None
        obj.safety_stock = None
        obj.current_stock = None
        obj.lead_time_days = None

        mock_resp = MagicMock()
        mock_resp.category_name = None
        mock_resp.standard_price = None

        with patch(
            "app.services.material_service.MaterialResponse.model_validate",
            return_value=mock_resp,
        ):
            result = svc._to_response(obj)

        assert result.standard_price == 0
        assert result.last_price == 0

    def test_to_response_with_category(self):
        svc, db = _make_service()
        obj = MagicMock()
        obj.category = MagicMock()
        obj.category.category_name = "电子元件"
        obj.standard_price = 10
        obj.last_price = 9
        obj.safety_stock = 5
        obj.current_stock = 20
        obj.lead_time_days = 7

        mock_resp = MagicMock()

        with patch(
            "app.services.material_service.MaterialResponse.model_validate",
            return_value=mock_resp,
        ):
            result = svc._to_response(obj)

        assert result.category_name == "电子元件"


class TestMaterialServiceListMaterials:
    def _mock_list(self, svc, total=0, items=None, page_size=20):
        """Helper: patch both list() and QueryParams to return canned data"""
        mock_result = MagicMock()
        mock_result.items = items or []
        mock_result.total = total
        mock_result.page = 1
        mock_result.page_size = page_size
        return mock_result

    def test_list_materials_returns_dict(self):
        svc, db = _make_service()
        mock_result = self._mock_list(svc)
        with patch.object(svc, "list", return_value=mock_result), \
             patch("app.common.crud.types.QueryParams", MagicMock()):
            result = svc.list_materials()
        assert "items" in result
        assert "total" in result

    def test_list_materials_zero_total_gives_zero_pages(self):
        svc, db = _make_service()
        mock_result = self._mock_list(svc, total=0, page_size=20)
        with patch.object(svc, "list", return_value=mock_result), \
             patch("app.common.crud.types.QueryParams", MagicMock()):
            result = svc.list_materials()
        assert result["pages"] == 0

    def test_pages_calculated_correctly(self):
        svc, db = _make_service()
        mock_result = self._mock_list(svc, total=45, page_size=20)
        with patch.object(svc, "list", return_value=mock_result), \
             patch("app.common.crud.types.QueryParams", MagicMock()):
            result = svc.list_materials()
        assert result["pages"] == 3  # ceil(45/20)


class TestMaterialServiceGenerateCode:
    def test_generate_code_without_category(self):
        svc, db = _make_service()
        with patch(
            "app.utils.number_generator.generate_material_code",
            return_value="MAT-001",
        ):
            code = svc.generate_code()
        assert code == "MAT-001"
