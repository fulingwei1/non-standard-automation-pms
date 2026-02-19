# -*- coding: utf-8 -*-
"""数据完整性检查单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

pytest.importorskip("app.services.data_integrity.check")

try:
    from app.services.data_integrity.check import DataCheckMixin
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    DataCheckMixin = None


def make_mixin(db=None):
    """创建带 db 属性的混入实例"""
    mixin = DataCheckMixin.__new__(DataCheckMixin)
    mixin.db = db or MagicMock()
    return mixin


class TestCheckDataCompleteness:
    def test_period_not_found_raises(self):
        db = MagicMock()
        # PerformancePeriod query returns None
        db.query.return_value.filter.return_value.first.return_value = None
        mixin = make_mixin(db)

        with pytest.raises(ValueError, match="考核周期不存在"):
            mixin.check_data_completeness(engineer_id=1, period_id=999)

    def test_no_profile_returns_zero_score(self):
        db = MagicMock()
        # Period exists
        period = MagicMock()
        period.start_date = date(2024, 1, 1)
        period.end_date = date(2024, 12, 31)

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            mock_q = MagicMock()
            if call_count[0] == 1:
                # First call: PerformancePeriod
                mock_q.filter.return_value.first.return_value = period
            else:
                # Second call: EngineerProfile
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        db.query.side_effect = query_side_effect
        mixin = make_mixin(db)
        result = mixin.check_data_completeness(engineer_id=1, period_id=1)
        assert result["completeness_score"] == 0.0
        assert "工程师档案不存在" in result["missing_items"]

    def test_result_has_required_keys(self):
        db = MagicMock()
        period = MagicMock()
        period.start_date = date(2024, 1, 1)
        period.end_date = date(2024, 12, 31)

        profile = MagicMock()
        profile.job_type = "software"

        query_count = [0]

        def query_side_effect(model):
            query_count[0] += 1
            mock_q = MagicMock()
            if query_count[0] == 1:
                mock_q.filter.return_value.first.return_value = period
            elif query_count[0] == 2:
                mock_q.filter.return_value.first.return_value = profile
            else:
                mock_q.filter.return_value.count.return_value = 0
                mock_q.filter.return_value.all.return_value = []
            return mock_q

        db.query.side_effect = query_side_effect
        mixin = make_mixin(db)
        result = mixin.check_data_completeness(engineer_id=1, period_id=1)

        for key in ["engineer_id", "period_id", "completeness_score", "missing_items", "warnings"]:
            assert key in result

    def test_engineer_id_in_result(self):
        db = MagicMock()
        period = MagicMock()
        period.start_date = date(2024, 1, 1)
        period.end_date = date(2024, 12, 31)

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            mock_q = MagicMock()
            if call_count[0] == 1:
                mock_q.filter.return_value.first.return_value = period
            else:
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        db.query.side_effect = query_side_effect
        mixin = make_mixin(db)
        result = mixin.check_data_completeness(engineer_id=42, period_id=1)
        assert result["engineer_id"] == 42

    def test_period_id_in_result(self):
        db = MagicMock()
        period = MagicMock()
        period.start_date = date(2024, 1, 1)
        period.end_date = date(2024, 12, 31)

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            mock_q = MagicMock()
            if call_count[0] == 1:
                mock_q.filter.return_value.first.return_value = period
            else:
                mock_q.filter.return_value.first.return_value = None
            return mock_q

        db.query.side_effect = query_side_effect
        mixin = make_mixin(db)
        result = mixin.check_data_completeness(engineer_id=1, period_id=77)
        assert result["period_id"] == 77
