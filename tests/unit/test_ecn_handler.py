# -*- coding: utf-8 -*-
"""ECNStatusHandler 单元测试"""
from datetime import timedelta
from unittest.mock import MagicMock
import pytest

from app.services.status_handlers.ecn_handler import ECNStatusHandler


class TestECNStatusHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = ECNStatusHandler(db=self.db)

    def test_project_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.handler.handle_ecn_schedule_impact(999, 1, 5) is False

    def test_ecn_not_found(self):
        project = MagicMock()
        ecn_none = None
        self.db.query.return_value.filter.return_value.first.side_effect = [project, ecn_none]
        assert self.handler.handle_ecn_schedule_impact(1, 999, 5) is False

    def test_schedule_impact_small(self):
        from datetime import date
        project = MagicMock()
        project.planned_end_date = date(2024, 6, 30)
        project.health = "H1"
        project.stage = "S2"
        project.status = "ST02"
        project.description = ""
        ecn = MagicMock()
        ecn.ecn_no = "ECN001"
        self.db.query.return_value.filter.return_value.first.side_effect = [project, ecn]
        result = self.handler.handle_ecn_schedule_impact(1, 1, 3)
        assert result is True
        # Health should NOT change for <=7 days
        assert project.health == "H1"

    def test_schedule_impact_large(self):
        from datetime import date
        project = MagicMock()
        project.planned_end_date = date(2024, 6, 30)
        project.health = "H1"
        project.stage = "S2"
        project.status = "ST02"
        project.description = ""
        ecn = MagicMock()
        ecn.ecn_no = "ECN002"
        self.db.query.return_value.filter.return_value.first.side_effect = [project, ecn]
        result = self.handler.handle_ecn_schedule_impact(1, 1, 10)
        assert result is True
        assert project.health == "H2"

    def test_log_status_change_with_callback(self):
        callback = MagicMock()
        self.handler._log_status_change(1, log_status_change=callback, change_type="TEST")
        callback.assert_called_once()

    def test_log_status_change_without_callback(self):
        self.handler._log_status_change(1, change_type="TEST")
        self.db.add.assert_called_once()
