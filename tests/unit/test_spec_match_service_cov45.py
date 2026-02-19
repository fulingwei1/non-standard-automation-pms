# -*- coding: utf-8 -*-
"""
第四十五批覆盖：spec_match_service.py
"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.spec_match_service")

from app.services.spec_match_service import (
    get_project_requirements,
    check_po_item_match,
    check_bom_item_match,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_matcher():
    matcher = MagicMock()
    match_result = MagicMock()
    match_result.match_status = "MATCHED"
    match_result.match_score = 95.0
    match_result.differences = {}
    matcher.match_specification.return_value = match_result
    return matcher


def _make_requirement(req_id=1, material_code=None, material_name="物料A"):
    req = MagicMock()
    req.id = req_id
    req.material_code = material_code
    req.material_name = material_name
    return req


class TestGetProjectRequirements:
    def test_returns_requirements_for_project(self, mock_db):
        reqs = [_make_requirement(1), _make_requirement(2)]
        mock_db.query.return_value.filter.return_value.all.return_value = reqs

        result = get_project_requirements(mock_db, 1)
        assert result == reqs

    def test_returns_empty_for_project_with_no_reqs(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_project_requirements(mock_db, 999)
        assert result == []


class TestCheckPoItemMatch:
    def test_no_requirements_returns_empty(self, mock_db, mock_matcher):
        po_item = MagicMock(material_code="MAT001", specification="spec1")
        result = check_po_item_match(mock_db, po_item, [], 1, mock_matcher)
        assert result == []

    def test_material_code_filter_skips_non_matching(self, mock_db, mock_matcher):
        req = _make_requirement(material_code="MAT002")
        po_item = MagicMock(material_code="MAT001", specification="spec1")
        result = check_po_item_match(mock_db, po_item, [req], 1, mock_matcher)
        assert result == []

    def test_no_material_code_filter_processes_all(self, mock_db, mock_matcher):
        req = _make_requirement(material_code=None)
        po_item = MagicMock(specification="spec1")
        result = check_po_item_match(mock_db, po_item, [req], 1, mock_matcher)
        assert len(result) == 1
        assert result[0].match_status == "MATCHED"

    def test_adds_match_record_to_db(self, mock_db, mock_matcher):
        req = _make_requirement(material_code=None)
        po_item = MagicMock(specification="spec1", id=5)
        check_po_item_match(mock_db, po_item, [req], 1, mock_matcher)
        mock_db.add.assert_called_once()


class TestCheckBomItemMatch:
    def test_material_code_mismatch_skips(self, mock_db, mock_matcher):
        req = _make_requirement(material_code="MAT002")
        bom_item = MagicMock(specification="spec1")
        bom_item.material.material_code = "MAT001"
        result = check_bom_item_match(mock_db, bom_item, [req], 1, mock_matcher)
        assert result == []

    def test_matching_material_code_processes(self, mock_db, mock_matcher):
        req = _make_requirement(material_code="MAT001")
        bom_item = MagicMock(specification="spec1", id=10)
        bom_item.material.material_code = "MAT001"
        bom_item.material.brand = "BrandX"
        result = check_bom_item_match(mock_db, bom_item, [req], 1, mock_matcher)
        assert len(result) == 1

    def test_no_material_code_on_req(self, mock_db, mock_matcher):
        req = _make_requirement(material_code=None)
        bom_item = MagicMock(specification="spec1", id=10)
        bom_item.material.material_code = "ANYTHING"
        bom_item.material.brand = "BrandY"
        result = check_bom_item_match(mock_db, bom_item, [req], 1, mock_matcher)
        assert len(result) == 1
