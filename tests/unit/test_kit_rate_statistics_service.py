# -*- coding: utf-8 -*-
"""
Tests for kit_rate_statistics_service
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, Mock
from sqlalchemy.orm import Session

from app.models.assembly_kit import BomItemAssemblyAttrs
from app.models.material import Material
from app.models.project import Project


class TestKitRateStatistics:
    """Test suite for kit_rate_statistics_service functions."""

    def test_calculate_basic_kit_rate(self):
        """Test calculating basic kit rate."""
        from app.services.kit_rate_statistics_service import calculate_kit_rate

        mock_attrs = Mock(spec=BomItemAssemblyAttrs)
        mock_attrs.unit_price = Decimal("10.00")
        mock_attrs.unit_qty = Decimal("100")
        mock_attrs.cost_price = Decimal("1000.00")
        mock_attrs.material_cost = Decimal("5000.00")
        mock_attrs.other_cost = Decimal("1000.00")

        mock_bom_item = Mock()
        mock_bom_item.assembly_attrs = mock_attrs

        result = calculate_kit_rate(mock_bom_item)

        assert result is not None
        assert result['unit_price'] == Decimal("10.00")
        assert result['unit_cost'] == Decimal("1000.00")
        assert result['material_cost'] == Decimal("5000.00")
        assert result['other_cost'] == Decimal("1000.00")
        assert result['total_cost'] == Decimal("7000.00")

    def test_calculate_kit_rate_with_bom_cost(self):
        """Test calculating kit rate with BOM cost."""
        from app.services.kit_rate_statistics_service import calculate_kit_rate

        mock_attrs = Mock(spec=BomItemAssemblyAttrs)
        mock_attrs.unit_price = Decimal("10.00")
        mock_attrs.unit_qty = Decimal("100")
        mock_attrs.cost_price = Decimal("1000.00")
        mock_attrs.material_cost = Decimal("5000.00")
        mock_attrs.other_cost = Decimal("1000.00")

        mock_bom_item = Mock()
        mock_bom_item.assembly_attrs = mock_attrs
        mock_bom_item.bom_cost = Decimal("50000.00")

        result = calculate_kit_rate(mock_bom_item)

        assert result is not None
        assert result['unit_price'] == Decimal("10.00")
        assert result['bom_cost'] == Decimal("50000.00")
        assert result['total_cost'] == Decimal("6000.00")
        assert result['material_cost'] == Decimal("5000.00")
        assert result['other_cost'] == Decimal("1000.00")
        assert result['total_cost'] == Decimal("6000.00")

    def test_calculate_kit_rate_without_material_cost(self):
        """Test when material cost is None."""
        from app.services.kit_rate_statistics_service import calculate_kit_rate

        mock_attrs = Mock(spec=BomItemAssemblyAttrs)
        mock_attrs.unit_price = Decimal("10.00")
        mock_attrs.unit_qty = Decimal("100")
        mock_attrs.cost_price = Decimal("1000.00")
        mock_attrs.material_cost = None
        mock_attrs.other_cost = Decimal("1000.00")

        mock_bom_item = Mock()
        mock_bom_item.assembly_attrs = mock_attrs

        result = calculate_kit_rate(mock_bom_item)

        assert result is not None
        assert result['unit_price'] == Decimal("10.00")
        assert result['bom_cost'] is None
        assert result['material_cost'] is None
        assert result['other_cost'] == Decimal("1000.00")
        assert result['total_cost'] == Decimal("2000.00")
