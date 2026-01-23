# -*- coding: utf-8 -*-
"""
Tests for bonus_allocation_parser
"""

import pytest
from unittest.mock import MagicMock

from app.services.bonus_allocation_parser import parse_bonus_allocation


class TestParseBonusAllocation:
    """Test suite for parse_bonus_allocation function."""

    def test_parse_empty_string(self):
        """Test parsing empty allocation string."""
        from app.services.bonus_allocation_parser import parse_bonus_allocation

        result = parse_bonus_allocation("")

        assert result is not None
        assert result['total_amount'] == 0

    def test_parse_basic_allocation(self):
        """Test parsing basic bonus allocation string."""
        from app.services.bonus_allocation_parser import parse_bonus_allocation

        allocation_str = "团队奖金：总金额100000，甲50000，乙50000"
        result = parse_bonus_allocation(allocation_str)

        assert result is not None
        assert result['total_amount'] == 100000

    def test_parse_allocation_with_ratios(self):
        """Test parsing allocation with team ratios."""
        from app.services.bonus_allocation_parser import parse_bonus_allocation

        allocation_str = "团队奖金：总金额100000，甲60%，乙40%"
        result = parse_bonus_allocation(allocation_str)

        assert result is not None
        assert result['total_amount'] == 100000
        assert result['allocations'][0]['amount'] == 60000
        assert result['allocations'][1]['amount'] == 40000

    def test_parse_invalid_format(self):
        """Test parsing invalid allocation format."""
        from app.services.bonus_allocation_parser import parse_bonus_allocation

        result = parse_bonus_allocation("无效格式")

        assert result is None
