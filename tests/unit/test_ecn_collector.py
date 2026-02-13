# -*- coding: utf-8 -*-
"""ECN数据收集器单元测试"""
import pytest
from unittest.mock import MagicMock
from datetime import date
from app.services.performance_collector.ecn_collector import EcnCollector


class TestEcnCollector:
    def setup_method(self):
        self.db = MagicMock()
        self.collector = EcnCollector(self.db)

    def test_no_projects(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.collector.collect_ecn_responsibility_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_ecn'] == 0

    def test_with_ecn_data(self):
        pm = MagicMock()
        pm.project_id = 1
        self.db.query.return_value.filter.return_value.all.return_value = [pm]
        self.db.query.return_value.filter.return_value.count.return_value = 5
        result = self.collector.collect_ecn_responsibility_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_ecn'] == 5

    def test_error_handling(self):
        self.db.query.side_effect = Exception("DB error")
        result = self.collector.collect_ecn_responsibility_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_ecn'] == 0
        assert 'error' in result
