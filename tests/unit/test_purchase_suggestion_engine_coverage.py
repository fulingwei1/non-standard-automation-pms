# -*- coding: utf-8 -*-
"""purchase_suggestion_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine

class TestPurchaseSuggestionEngineInit:
    def test_init(self):
        service = PurchaseSuggestionEngine(Mock())
        assert service is not None
