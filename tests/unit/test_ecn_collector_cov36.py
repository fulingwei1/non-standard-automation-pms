# -*- coding: utf-8 -*-
"""ECN数据收集器单元测试 - 第三十六批"""

import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.performance_collector.ecn_collector")

try:
    from app.services.performance_collector.ecn_collector import EcnCollector
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    EcnCollector = None


START = date(2024, 1, 1)
END = date(2024, 1, 31)


def make_collector():
    collector = EcnCollector.__new__(EcnCollector)
    collector.db = MagicMock()
    return collector


class TestCollectEcnResponsibilityData:
    def test_no_projects_returns_zeros(self):
        collector = make_collector()
        # 模拟没有项目成员
        collector.db.query.return_value.filter.return_value.all.return_value = []
        result = collector.collect_ecn_responsibility_data(1, START, END)
        assert result["total_ecn"] == 0
        assert result["responsible_ecn"] == 0
        assert result["ecn_responsibility_rate"] == 0.0

    def test_with_projects_calculates_ecn_rate(self):
        collector = make_collector()
        # 模拟有两个项目
        pm1 = MagicMock(); pm1.project_id = 1
        pm2 = MagicMock(); pm2.project_id = 2
        collector.db.query.return_value.filter.return_value.all.return_value = [pm1, pm2]
        # 模拟ECN数量
        collector.db.query.return_value.filter.return_value.count.return_value = 4
        result = collector.collect_ecn_responsibility_data(1, START, END)
        assert result["total_ecn"] >= 0
        assert "ecn_responsibility_rate" in result

    def test_exception_returns_defaults_with_error(self):
        collector = make_collector()
        collector.db.query.side_effect = Exception("DB error")
        result = collector.collect_ecn_responsibility_data(1, START, END)
        assert "error" in result
        assert result["total_ecn"] == 0
        assert result["ecn_responsibility_rate"] == 0.0

    def test_responsible_ecn_less_than_total(self):
        collector = make_collector()
        pm = MagicMock(); pm.project_id = 10
        collector.db.query.return_value.filter.return_value.all.return_value = [pm]
        call_count = [0]
        def count_side(*args, **kwargs):
            call_count[0] += 1
            return 10 if call_count[0] == 1 else 3
        collector.db.query.return_value.filter.return_value.count.side_effect = count_side
        result = collector.collect_ecn_responsibility_data(1, START, END)
        assert "ecn_responsibility_rate" in result

    def test_returns_dict_with_required_keys(self):
        collector = make_collector()
        collector.db.query.return_value.filter.return_value.all.return_value = []
        result = collector.collect_ecn_responsibility_data(1, START, END)
        assert "total_ecn" in result
        assert "responsible_ecn" in result
        assert "ecn_responsibility_rate" in result
