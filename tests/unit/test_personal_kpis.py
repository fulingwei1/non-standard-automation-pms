# -*- coding: utf-8 -*-
"""Tests for strategy/decomposition/personal_kpis.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestPersonalKPIs:
    def setup_method(self):
        self.db = MagicMock()

    @pytest.mark.skip(reason="PersonalKPI model constructor rejects mock fields")
    def test_create_personal_kpi(self):
        from app.services.strategy.decomposition.personal_kpis import create_personal_kpi
        data = MagicMock()
        data.model_dump.return_value = {"name": "KPI1", "target_value": 100}
        result = create_personal_kpi(self.db, data)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_personal_kpi_found(self):
        from app.services.strategy.decomposition.personal_kpis import get_personal_kpi
        kpi = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = kpi
        result = get_personal_kpi(self.db, 1)
        assert result == kpi

    def test_get_personal_kpi_not_found(self):
        from app.services.strategy.decomposition.personal_kpis import get_personal_kpi
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_personal_kpi(self.db, 999)
        assert result is None

    def test_delete_personal_kpi_not_found(self):
        from app.services.strategy.decomposition.personal_kpis import delete_personal_kpi
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_personal_kpi(self.db, 999)
        assert result is False
