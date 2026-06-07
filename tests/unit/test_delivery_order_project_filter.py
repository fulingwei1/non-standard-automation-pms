from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_delivery_orders_accepts_project_filter():
    from app.api.v1.endpoints.business_support_orders.delivery_orders import crud

    db = MagicMock()
    query = MagicMock()
    filtered_query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = filtered_query
    filtered_query.count.return_value = 0
    filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    pagination = SimpleNamespace(
        offset=0,
        limit=20,
        page=1,
        page_size=20,
        pages_for_total=lambda total: 0,
    )

    with patch.object(crud, "apply_keyword_filter", side_effect=lambda q, *_args, **_kwargs: q):
        await crud.get_delivery_orders(
            pagination=pagination,
            project_id=42,
            order_id=None,
            customer_id=None,
            approval_status=None,
            delivery_status=None,
            search=None,
            db=db,
            current_user=MagicMock(),
        )

    query.filter.assert_called_once()
    assert "project_id" in str(query.filter.call_args.args[0])


@pytest.mark.asyncio
async def test_get_delivery_statistics_accepts_project_filter():
    from app.api.v1.endpoints.business_support_orders.delivery_orders import statistics

    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 0
    query.all.return_value = []

    await statistics.get_delivery_statistics(
        project_id=42,
        db=db,
        current_user=MagicMock(),
    )

    assert any("project_id" in str(call.args[0]) for call in query.filter.call_args_list)
