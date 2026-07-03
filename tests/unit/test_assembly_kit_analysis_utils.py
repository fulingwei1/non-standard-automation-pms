# -*- coding: utf-8 -*-
"""装配齐套分析工具测试"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.endpoints.assembly_kit.kit_analysis.utils import calculate_available_qty


@pytest.mark.unit
def test_calculate_available_qty_does_not_count_in_transit_as_current_available():
    db = MagicMock()
    material = SimpleNamespace(id=1, current_stock=Decimal("2"))

    call_count = [0]

    def query_side_effect(*args, **kwargs):
        query = MagicMock()
        if call_count[0] == 0:
            query.filter.return_value.first.return_value = material
        else:
            query.join.return_value.filter.return_value.scalar.return_value = Decimal("8")
        call_count[0] += 1
        return query

    db.query.side_effect = query_side_effect

    stock_qty, allocated_qty, in_transit_qty, available_qty = calculate_available_qty(
        db, 1, date.today()
    )

    assert stock_qty == Decimal("2")
    assert allocated_qty == Decimal("0")
    assert in_transit_qty == Decimal("8")
    assert available_qty == Decimal("2")
