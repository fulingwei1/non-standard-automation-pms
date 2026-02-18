# -*- coding: utf-8 -*-
"""第二十三批：customer_service 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.customer_service")

from app.services.customer_service import CustomerService


def _make_db():
    return MagicMock()


class TestCustomerServiceListCustomers:
    def _make_service(self, db=None):
        if db is None:
            db = _make_db()
        with patch("app.services.customer_service.BaseService.__init__", return_value=None):
            svc = CustomerService.__new__(CustomerService)
            svc.db = db
            return svc

    def test_list_customers_returns_dict_keys(self):
        db = _make_db()
        svc = self._make_service(db)
        result_obj = MagicMock()
        result_obj.items = []
        result_obj.total = 0
        result_obj.page = 1
        result_obj.page_size = 20
        with patch.object(svc, "list", return_value=result_obj):
            result = svc.list_customers()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "pages" in result

    def test_list_customers_with_filters(self):
        db = _make_db()
        svc = self._make_service(db)
        result_obj = MagicMock()
        result_obj.items = [MagicMock()]
        result_obj.total = 1
        result_obj.page = 1
        result_obj.page_size = 10
        with patch.object(svc, "list", return_value=result_obj):
            result = svc.list_customers(
                page=1, page_size=10,
                customer_type="企业",
                industry="制造",
                status="ACTIVE"
            )
        assert result["total"] == 1

    def test_pages_calculation(self):
        db = _make_db()
        svc = self._make_service(db)
        result_obj = MagicMock()
        result_obj.items = []
        result_obj.total = 25
        result_obj.page = 1
        result_obj.page_size = 10
        with patch.object(svc, "list", return_value=result_obj):
            result = svc.list_customers(page_size=10)
        assert result["pages"] == 3

    def test_zero_total_pages(self):
        db = _make_db()
        svc = self._make_service(db)
        result_obj = MagicMock()
        result_obj.items = []
        result_obj.total = 0
        result_obj.page = 1
        result_obj.page_size = 20
        with patch.object(svc, "list", return_value=result_obj):
            result = svc.list_customers()
        assert result["pages"] == 0

    def test_keyword_passed_to_search(self):
        db = _make_db()
        svc = self._make_service(db)
        result_obj = MagicMock()
        result_obj.items = []
        result_obj.total = 0
        result_obj.page = 1
        result_obj.page_size = 20
        captured = {}
        def mock_list(params):
            captured["search"] = params.search
            return result_obj
        with patch.object(svc, "list", side_effect=mock_list):
            svc.list_customers(keyword="客户名")
        assert captured["search"] == "客户名"


class TestCustomerServiceBeforeDelete:
    def test_before_delete_raises_when_has_projects(self):
        db = _make_db()
        with patch("app.services.customer_service.BaseService.__init__", return_value=None):
            svc = CustomerService.__new__(CustomerService)
            svc.db = db

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = MagicMock()  # has project
        db.query.return_value = q

        with pytest.raises(Exception):
            svc._before_delete(1)

    def test_before_delete_passes_when_no_projects(self):
        db = _make_db()
        with patch("app.services.customer_service.BaseService.__init__", return_value=None):
            svc = CustomerService.__new__(CustomerService)
            svc.db = db

        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0  # count() returns int 0
        q.first.return_value = None
        db.query.return_value = q

        # Should not raise
        svc._before_delete(1)
