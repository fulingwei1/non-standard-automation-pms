# -*- coding: utf-8 -*-
"""Tests for app/services/strategy/comparison_service.py"""
from unittest.mock import MagicMock, patch

from app.services.strategy.comparison_service import (
    create_strategy_comparison,
    get_strategy_comparison,
    list_strategy_comparisons,
    delete_strategy_comparison,
)


class TestComparisonService:
    def setup_method(self):
        self.db = MagicMock()

    def test_create_strategy_comparison(self):
        data = MagicMock()
        data.base_strategy_id = 1
        data.compare_strategy_id = 2
        data.comparison_type = "YOY"
        data.base_year = 2025
        data.compare_year = 2026
        data.summary = "test"
        result = create_strategy_comparison(self.db, data, created_by=1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_strategy_comparison_found(self):
        mock_comp = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_comp
        result = get_strategy_comparison(self.db, 1)
        assert result == mock_comp

    def test_get_strategy_comparison_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_strategy_comparison(self.db, 999)
        assert result is None

    def test_delete_strategy_comparison_found(self):
        mock_comp = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_comp
        result = delete_strategy_comparison(self.db, 1)
        assert result is True

    def test_delete_strategy_comparison_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_strategy_comparison(self.db, 999)
        assert result is False
