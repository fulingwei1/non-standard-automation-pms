# -*- coding: utf-8 -*-
"""Tests for sales/quotes_service.py"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date


class TestQuotesService:
    def _make_service(self):
        from app.services.sales.quotes_service import QuotesService
        db = MagicMock()
        return QuotesService(db), db

    def test_generate_quote_number(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.count.return_value = 0
        result = svc._generate_quote_number()
        today = date.today()
        assert result.startswith(f"QT{today.strftime('%Y%m%d')}")
        assert result.endswith("0001")

    def test_generate_quote_number_increment(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.count.return_value = 5
        result = svc._generate_quote_number()
        assert result.endswith("0006")

    def test_get_quotes_empty(self):
        svc, db = self._make_service()
        db.query.return_value.options.return_value = db.query.return_value
        db.query.return_value.filter.return_value = db.query.return_value
        db.query.return_value.count.return_value = 0
        db.query.return_value.order_by.return_value = db.query.return_value
        db.query.return_value.offset.return_value = db.query.return_value
        db.query.return_value.limit.return_value = db.query.return_value
        db.query.return_value.all.return_value = []
        result = svc.get_quotes()
        assert result.total == 0
