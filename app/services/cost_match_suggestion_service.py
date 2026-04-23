# -*- coding: utf-8 -*-
"""成本匹配建议兼容服务。"""

from decimal import Decimal
from typing import Any, Optional, Tuple

from app.common.query_filters import apply_keyword_filter


def find_matching_cost(db, item: Any, cost_query: Any) -> Tuple[Optional[Any], Optional[Decimal], Optional[int]]:
    item_name = getattr(item, "item_name", None)
    if not item_name:
        return None, None, None

    query = apply_keyword_filter(cost_query, type(item), item_name, "item_name")
    history = query.all()
    if not history:
        return None, None, 0

    costs = [Decimal(str(getattr(x, "unit_cost", 0) or 0)) for x in history]
    avg_cost = sum(costs) / len(costs) if costs else None
    return history[0], avg_cost, len(history)


def check_cost_anomalies(db, item: Any, cost_query: Any, current_cost: float):
    item_name = getattr(item, "item_name", None)
    if not item_name:
        return []

    query = apply_keyword_filter(cost_query, type(item), item_name, "item_name")
    history = query.all()
    if not history:
        return []

    costs = [float(getattr(x, "unit_cost", 0) or 0) for x in history]
    if not costs:
        return []

    avg_cost = sum(costs) / len(costs)
    messages = []
    if current_cost > avg_cost * 1.5:
        messages.append(f"当前成本偏高，当前 {current_cost:.2f}，历史均值 {avg_cost:.2f}")
    elif current_cost < avg_cost * 0.5:
        messages.append(f"当前成本偏低，当前 {current_cost:.2f}，历史均值 {avg_cost:.2f}")
    return messages
