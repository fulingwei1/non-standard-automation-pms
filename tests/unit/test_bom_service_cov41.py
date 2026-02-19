# -*- coding: utf-8 -*-
"""Unit tests for app/services/bom_service.py - batch 41"""
import pytest

pytest.importorskip("app.services.bom_service")

from unittest.mock import MagicMock, patch


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    with patch("app.services.bom_service.BaseService.__init__", return_value=None):
        from app.services.bom_service import BomService
        svc = BomService.__new__(BomService)
        svc.db = db
        svc.model = MagicMock()
        svc.response_schema = MagicMock()
        svc.resource_name = "BOM"
        return svc


def test_bom_service_instantiation(db):
    with patch("app.services.bom_service.BaseService.__init__", return_value=None):
        from app.services.bom_service import BomService
        svc = BomService.__new__(BomService)
        svc.db = db
        assert svc is not None


def test_list_boms_no_filters(service):
    mock_result = MagicMock()
    mock_result.items = []
    mock_result.total = 0
    mock_result.page = 1
    mock_result.page_size = 20
    service.list = MagicMock(return_value=mock_result)

    result = service.list_boms()
    assert result["total"] == 0
    assert result["items"] == []
    service.list.assert_called_once()


def test_list_boms_with_project_id(service):
    mock_result = MagicMock()
    mock_result.items = [MagicMock()]
    mock_result.total = 1
    mock_result.page = 1
    mock_result.page_size = 20
    service.list = MagicMock(return_value=mock_result)

    result = service.list_boms(project_id=5)
    assert result["total"] == 1
    call_args = service.list.call_args[0][0]
    assert call_args.filters.get("project_id") == 5


def test_list_boms_with_is_latest_filter(service):
    mock_result = MagicMock()
    mock_result.items = []
    mock_result.total = 0
    mock_result.page = 1
    mock_result.page_size = 10
    service.list = MagicMock(return_value=mock_result)

    service.list_boms(is_latest=True, page_size=10)
    call_args = service.list.call_args[0][0]
    assert call_args.filters.get("is_latest") is True


def test_list_boms_pages_calculation(service):
    mock_result = MagicMock()
    mock_result.items = []
    mock_result.total = 55
    mock_result.page = 1
    mock_result.page_size = 20
    service.list = MagicMock(return_value=mock_result)

    result = service.list_boms()
    # ceil(55 / 20) = 3
    assert result["pages"] == 3


def test_list_boms_machine_id_filter(service):
    mock_result = MagicMock()
    mock_result.items = []
    mock_result.total = 0
    mock_result.page = 1
    mock_result.page_size = 20
    service.list = MagicMock(return_value=mock_result)

    service.list_boms(machine_id=10)
    call_args = service.list.call_args[0][0]
    assert call_args.filters.get("machine_id") == 10


def test_to_response_calls_model_validate(service):
    from app.services.bom_service import BomService
    from unittest.mock import patch as mp
    bom_obj = MagicMock()
    with mp("app.services.bom_service.BomResponse") as MockResp:
        MockResp.model_validate.return_value = MagicMock()
        service._to_response(bom_obj)
        MockResp.model_validate.assert_called_once_with(bom_obj)
