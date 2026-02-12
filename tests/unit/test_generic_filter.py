# -*- coding: utf-8 -*-
"""Tests for data_scope/generic_filter.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestGenericFilterService:
    def test_import(self):
        from app.services.data_scope.generic_filter import GenericFilterService
        assert GenericFilterService is not None

    def test_filter_by_scope_callable(self):
        from app.services.data_scope.generic_filter import GenericFilterService
        assert callable(GenericFilterService.filter_by_scope)
