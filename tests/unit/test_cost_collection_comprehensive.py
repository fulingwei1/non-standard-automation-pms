# -*- coding: utf-8 -*-
"""CostCollectionService 综合测试"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.cost_collection_service import CostCollectionService


class TestInit:
    def test_class_exists(self):
        assert CostCollectionService is not None

    def test_has_methods(self):
        assert hasattr(CostCollectionService, 'collect_from_purchase_order')
        assert hasattr(CostCollectionService, 'collect_from_outsourcing_order')
        assert hasattr(CostCollectionService, 'collect_from_ecn')
        assert hasattr(CostCollectionService, 'remove_cost_from_source')
        assert hasattr(CostCollectionService, 'collect_from_bom')
