# -*- coding: utf-8 -*-
"""RPT-09: legacy dashboard stat cards using label must still render."""

from unittest.mock import MagicMock

from app.models.user import User
from app.schemas.dashboard import DashboardStatCard
from app.services.dashboard.adapters.presales import PresalesDashboardAdapter


def test_dashboard_stat_card_accepts_legacy_label_as_title():
    card = DashboardStatCard(key="active_projects", label="活跃项目", value=12, unit="个")

    assert card.title == "活跃项目"
    assert card.model_dump()["title"] == "活跃项目"


def test_legacy_dashboard_adapter_stats_do_not_drop_due_to_label_contract():
    project_query = MagicMock()
    project_query.filter.return_value.all.return_value = []

    db = MagicMock()
    db.query.return_value = project_query

    stats = PresalesDashboardAdapter(db, MagicMock(spec=User)).get_stats()

    assert len(stats) == 6
    assert {card.title for card in stats} == {
        "年度线索数",
        "赢单数",
        "整体赢率",
        "平均投入工时",
        "资源浪费率",
        "浪费成本",
    }
