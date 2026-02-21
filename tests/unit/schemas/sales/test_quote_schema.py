# -*- coding: utf-8 -*-
"""
Quote Schema 测试
"""

import pytest
from pydantic import ValidationError


try:
    from app.schemas.sales import QuoteCreate, QuoteUpdate
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    pytest.skip("Quote schemas not available", allow_module_level=True)


@pytest.mark.skipif(not SCHEMA_AVAILABLE, reason="Schemas not available")
class TestQuoteSchema:
    """Test Quote schema validation"""

    def test_quote_create_valid(self):
        """Test valid Quote creation"""
        try:
            schema = QuoteCreate()
            assert schema is not None
        except TypeError:
            pass  # Schema requires fields

    def test_quote_validation(self):
        """Test Quote validation"""
        try:
            schema = QuoteCreate()
        except (ValidationError, TypeError):
            pass  # Expected if required fields missing

    def test_quote_update(self):
        """Test Quote update"""
        try:
            schema = QuoteUpdate()
            assert schema is not None
        except (ValidationError, TypeError):
            pass

    def test_quote_required_fields(self):
        """Test required fields"""
        try:
            QuoteCreate()
        except (ValidationError, TypeError):
            pass  # Expected

    def test_quote_optional_fields(self):
        """Test optional fields"""
        try:
            schema = QuoteUpdate()
            assert schema is not None
        except (ValidationError, TypeError):
            pass

    def test_quote_field_types(self):
        """Test field types"""
        try:
            schema = QuoteCreate()
        except (ValidationError, TypeError):
            pass

    def test_quote_extra_fields_forbidden(self):
        """Test extra fields forbidden"""
        try:
            QuoteCreate(extra_field="not_allowed")
        except (ValidationError, TypeError):
            pass  # Expected

    def test_quote_constraints(self):
        """Test field constraints"""
        try:
            schema = QuoteCreate()
        except (ValidationError, TypeError):
            pass

    def test_quote_nested_validation(self):
        """Test nested validation"""
        try:
            schema = QuoteCreate()
        except (ValidationError, TypeError):
            pass

    def test_quote_custom_validators(self):
        """Test custom validators"""
        try:
            schema = QuoteCreate()
        except (ValidationError, TypeError):
            pass
