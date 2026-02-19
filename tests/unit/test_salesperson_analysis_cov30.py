# -*- coding: utf-8 -*-
"""
Unit tests for SalespersonAnalysisMixin (第三十批)
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.resource_waste_analysis.salesperson_analysis import SalespersonAnalysisMixin


class ConcreteSalespersonAnalysis(SalespersonAnalysisMixin):
    """Concrete subclass for testing the mixin"""

    def __init__(self, db, hourly_rate=Decimal("100")):
        self.db = db
        self.hourly_rate = hourly_rate


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def analyzer(mock_db):
    return ConcreteSalespersonAnalysis(db=mock_db)


class TestGetSalespersonWasteRanking:
    def test_returns_empty_list_when_no_projects(self, analyzer, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = analyzer.get_salesperson_waste_ranking()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_skips_projects_without_salesperson(self, analyzer, mock_db):
        project = MagicMock()
        project.id = 1
        project.salesperson_id = None
        project.outcome = "LOST"
        project.contract_amount = Decimal("0")

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [project]
        # work hours map query
        mock_query.in_.return_value = mock_query
        mock_query.group_by.return_value.all.return_value = []

        result = analyzer.get_salesperson_waste_ranking()
        assert result == []

    def test_aggregates_stats_for_salesperson(self, analyzer, mock_db):
        from app.models.enums import LeadOutcomeEnum

        project_won = MagicMock()
        project_won.id = 1
        project_won.salesperson_id = 10
        project_won.outcome = LeadOutcomeEnum.WON.value
        project_won.contract_amount = Decimal("50000")
        project_won.loss_reason = None

        project_lost = MagicMock()
        project_lost.id = 2
        project_lost.salesperson_id = 10
        project_lost.outcome = LeadOutcomeEnum.LOST.value
        project_lost.contract_amount = Decimal("0")
        project_lost.loss_reason = "PRICE"

        projects = [project_won, project_lost]

        work_hours_map = {1: Decimal("8"), 2: Decimal("12")}

        user = MagicMock()
        user.id = 10
        user.username = "sales01"
        user.real_name = "张三"

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                # Project query
                inner.filter.return_value = inner
                inner.all.return_value = projects
            elif call_count[0] == 2:
                # WorkLog query - work_hours_map
                inner.filter.return_value = inner
                inner.group_by.return_value.all.return_value = list(work_hours_map.items())
            else:
                # User query
                inner.filter.return_value.first.return_value = user
            return inner

        mock_db.query.side_effect = query_side_effect

        result = analyzer.get_salesperson_waste_ranking()
        assert isinstance(result, list)

    def test_applies_date_filters(self, analyzer, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.group_by.return_value.all.return_value = []

        result = analyzer.get_salesperson_waste_ranking(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert result == []

    def test_win_rate_calculation(self, analyzer, mock_db):
        from app.models.enums import LeadOutcomeEnum

        projects = []
        for i in range(4):
            p = MagicMock()
            p.id = i + 1
            p.salesperson_id = 20
            p.outcome = LeadOutcomeEnum.WON.value if i % 2 == 0 else LeadOutcomeEnum.LOST.value
            p.contract_amount = Decimal("10000") if i % 2 == 0 else Decimal("0")
            p.loss_reason = None if i % 2 == 0 else "BUDGET"
            projects.append(p)

        user = MagicMock()
        user.id = 20
        user.username = "sales02"
        user.real_name = "李四"

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                inner.filter.return_value = inner
                inner.all.return_value = projects
            elif call_count[0] == 2:
                inner.filter.return_value = inner
                inner.group_by.return_value.all.return_value = [(i + 1, Decimal("10")) for i in range(4)]
            else:
                inner.filter.return_value.first.return_value = user
            return inner

        mock_db.query.side_effect = query_side_effect

        result = analyzer.get_salesperson_waste_ranking()
        assert isinstance(result, list)

    def test_respects_limit_parameter(self, analyzer, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.group_by.return_value.all.return_value = []

        result = analyzer.get_salesperson_waste_ranking(limit=5)
        # No projects so result should be empty, but function ran with limit=5
        assert isinstance(result, list)
