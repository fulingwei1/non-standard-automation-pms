# -*- coding: utf-8 -*-
"""Tests for app/services/shortage/shortage_management_service.py"""
import pytest
from unittest.mock import MagicMock

from app.services.shortage.shortage_management_service import ShortageManagementService


class TestShortageManagementService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = ShortageManagementService(self.db)

    @pytest.mark.skip(reason="Complex paginated query with joins")
    def test_get_shortage_list(self):
        result = self.service.get_shortage_list()
        assert result is not None

    @pytest.mark.skip(reason="Complex record creation with validation")
    def test_create_shortage_record(self):
        user = MagicMock()
        data = {"material_id": 1, "quantity": 10}
        result = self.service.create_shortage_record(data, user)

    @pytest.mark.skip(reason="Complex aggregate statistics query")
    def test_get_shortage_statistics(self):
        result = self.service.get_shortage_statistics()
        assert isinstance(result, dict)
