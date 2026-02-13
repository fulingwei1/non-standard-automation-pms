# -*- coding: utf-8 -*-
"""知识贡献数据收集器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from app.services.performance_collector.knowledge_collector import KnowledgeCollector


class TestKnowledgeCollector:
    def setup_method(self):
        self.db = MagicMock()
        self.collector = KnowledgeCollector(self.db)

    def test_collect_knowledge_contribution_data_empty(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.count.return_value = 0
        result = self.collector.collect_knowledge_contribution_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_contributions'] == 0

    def test_collect_knowledge_contribution_data_with_data(self):
        contrib1 = MagicMock()
        contrib1.reuse_count = 5
        contrib1.contribution_type = 'document'
        contrib2 = MagicMock()
        contrib2.reuse_count = 3
        contrib2.contribution_type = 'template'
        self.db.query.return_value.filter.return_value.all.return_value = [contrib1, contrib2]
        self.db.query.return_value.filter.return_value.count.return_value = 2
        result = self.collector.collect_knowledge_contribution_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_contributions'] == 2
        assert result['total_reuse_count'] == 8

    def test_collect_knowledge_contribution_data_error(self):
        self.db.query.side_effect = Exception("DB error")
        result = self.collector.collect_knowledge_contribution_data(1, date(2024, 1, 1), date(2024, 12, 31))
        assert result['total_contributions'] == 0
        assert 'error' in result
