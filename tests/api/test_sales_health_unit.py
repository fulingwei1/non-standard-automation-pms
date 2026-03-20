# -*- coding: utf-8 -*-
"""
sales/health.py 端点单元测试
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")


def _make_user(user_id=1):
    return SimpleNamespace(id=user_id, username="sales-user")


def _make_query(items):
    query = MagicMock()
    ordered = MagicMock()
    limited = MagicMock()
    query.order_by.return_value = ordered
    ordered.limit.return_value = limited
    limited.all.return_value = items
    return query


class TestHealthWarnings:

    def test_collect_health_warnings_returns_sorted_actionable_items(self):
        from app.api.v1.endpoints.sales.health import _collect_health_warnings

        db = MagicMock()
        current_user = _make_user()

        lead = SimpleNamespace(id=1, lead_code="L001", customer_name="客户A")
        opportunity = SimpleNamespace(id=2, opp_code="O002", opp_name="商机B", customer=None)
        quote = SimpleNamespace(id=3, quote_code="Q003")
        contract = SimpleNamespace(id=4, contract_code="C004", contract_name="合同D")

        db.query.side_effect = [
            _make_query([lead]),
            _make_query([opportunity]),
            _make_query([quote]),
            _make_query([contract]),
        ]

        with (
            patch(
                "app.api.v1.endpoints.sales.health.security.filter_sales_data_by_scope",
                side_effect=lambda query, *_args, **_kwargs: query,
            ),
            patch("app.api.v1.endpoints.sales.health.PipelineHealthService") as MockService,
        ):
            MockService.return_value.calculate_lead_health.return_value = {
                "health_status": "H3",
                "health_score": 20,
                "risk_factors": ["已35天未跟进"],
                "lead_code": "L001",
            }
            MockService.return_value.calculate_opportunity_health.return_value = {
                "health_status": "H1",
                "health_score": 100,
                "risk_factors": [],
                "opp_code": "O002",
            }
            MockService.return_value.calculate_quote_health.return_value = {
                "health_status": "H2",
                "health_score": 50,
                "risk_factors": ["报价审批时间过长（40天）"],
                "quote_code": "Q003",
            }
            MockService.return_value.calculate_contract_health.return_value = {
                "health_status": "H3",
                "health_score": 10,
                "risk_factors": ["关联项目阻塞"],
                "contract_code": "C004",
            }

            warnings = _collect_health_warnings(
                db=db,
                current_user=current_user,
                level=None,
                entity_type=None,
                limit=10,
            )

        assert len(warnings) == 3
        assert [item["entityType"] for item in warnings] == ["CONTRACT", "LEAD", "QUOTE"]
        assert [item["healthStatus"] for item in warnings] == ["H3", "H3", "H2"]

    def test_get_health_warnings_returns_summary(self):
        from app.api.v1.endpoints.sales.health import get_health_warnings

        db = MagicMock()
        current_user = _make_user()
        warnings = [
            {"entityType": "QUOTE", "entityId": 1, "healthStatus": "H2", "healthScore": 50},
            {"entityType": "LEAD", "entityId": 2, "healthStatus": "H3", "healthScore": 20},
        ]

        with patch(
            "app.api.v1.endpoints.sales.health._collect_health_warnings",
            return_value=warnings,
        ) as mock_collect:
            result = get_health_warnings(
                level=None,
                entity_type=None,
                limit=50,
                db=db,
                current_user=current_user,
            )

        mock_collect.assert_called_once_with(
            db=db,
            current_user=current_user,
            level=None,
            entity_type=None,
            limit=50,
        )
        assert result.code == 200
        assert result.data["total"] == 2
        assert result.data["summary"] == {"H2": 1, "H3": 1}
