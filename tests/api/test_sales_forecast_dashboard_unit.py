# -*- coding: utf-8 -*-
"""
sales_forecast.py 端点单元测试
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


def _make_user(user_id: int = 1):
    return SimpleNamespace(id=user_id, username="sales-user")


class TestSalesForecastDashboardEndpoints:

    def test_get_team_forecast_uses_dashboard_service(self):
        from app.api.v1.endpoints.sales_forecast import get_team_forecast

        db = _make_db()
        current_user = _make_user()
        payload = {"period": "2026-Q1", "teams": []}

        with patch("app.api.v1.endpoints.sales_forecast.SalesForecastDashboardService") as MockService:
            MockService.return_value.get_team_breakdown.return_value = payload

            result = get_team_forecast(period="quarterly", db=db, current_user=current_user)

        MockService.assert_called_once_with(db)
        MockService.return_value.get_team_breakdown.assert_called_once_with(period="quarterly")
        assert result == payload

    def test_get_sales_rep_forecast_uses_dashboard_service(self):
        from app.api.v1.endpoints.sales_forecast import get_sales_rep_forecast

        db = _make_db()
        current_user = _make_user()
        payload = {"period": "2026-Q1", "sales_reps": []}

        with patch("app.api.v1.endpoints.sales_forecast.SalesForecastDashboardService") as MockService:
            MockService.return_value.get_sales_rep_breakdown.return_value = payload

            result = get_sales_rep_forecast(
                team_id=8,
                period="quarterly",
                db=db,
                current_user=current_user,
            )

        MockService.assert_called_once_with(db)
        MockService.return_value.get_sales_rep_breakdown.assert_called_once_with(
            team_id=8,
            period="quarterly",
        )
        assert result == payload

    def test_get_forecast_accuracy_uses_dashboard_service(self):
        from app.api.v1.endpoints.sales_forecast import get_forecast_accuracy

        db = _make_db()
        current_user = _make_user()
        payload = {"tracking_period": "最近4个月", "history": []}

        with patch("app.api.v1.endpoints.sales_forecast.SalesForecastDashboardService") as MockService:
            MockService.return_value.get_accuracy_tracking.return_value = payload

            result = get_forecast_accuracy(months=4, db=db, current_user=current_user)

        MockService.assert_called_once_with(db)
        MockService.return_value.get_accuracy_tracking.assert_called_once_with(months=4)
        assert result == payload

    def test_get_executive_dashboard_uses_dashboard_service(self):
        from app.api.v1.endpoints.sales_forecast import get_executive_dashboard

        db = _make_db()
        current_user = _make_user()
        payload = {"period": "2026-Q1", "kpi_summary": {}}

        with patch("app.api.v1.endpoints.sales_forecast.SalesForecastDashboardService") as MockService:
            MockService.return_value.get_executive_dashboard.return_value = payload

            result = get_executive_dashboard(db=db, current_user=current_user)

        MockService.assert_called_once_with(db)
        MockService.return_value.get_executive_dashboard.assert_called_once_with()
        assert result == payload
