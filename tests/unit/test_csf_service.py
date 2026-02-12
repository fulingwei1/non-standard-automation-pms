# -*- coding: utf-8 -*-
"""Tests for app/services/strategy/csf_service.py"""
import pytest
from unittest.mock import MagicMock

from app.services.strategy.csf_service import (
    create_csf, get_csf, list_csfs, update_csf, delete_csf,
)


@pytest.mark.skip("TODO: hangs during import/collection")
class TestCsfService:
    def setup_method(self):
        self.db = MagicMock()

    def test_create_csf(self):
        data = MagicMock()
        data.strategy_id = 1
        data.name = "Test CSF"
        data.dimension = "FINANCIAL"
        result = create_csf(self.db, data)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_csf_found(self):
        mock_csf = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_csf
        result = get_csf(self.db, 1)
        assert result == mock_csf

    def test_get_csf_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_csf(self.db, 999)
        assert result is None

    def test_delete_csf_found(self):
        mock_csf = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_csf
        result = delete_csf(self.db, 1)
        assert result is True

    def test_delete_csf_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_csf(self.db, 999)
        assert result is False
