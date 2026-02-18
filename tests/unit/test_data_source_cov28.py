# -*- coding: utf-8 -*-
"""第二十八批 - data_source (KPI数据源) 单元测试"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.strategy.kpi_service.data_source")

from app.services.strategy.kpi_service.data_source import (
    create_kpi_data_source,
    get_kpi_data_sources,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_create_data(
    kpi_id=1,
    source_type="MANUAL",
    source_module="PROJECT",
    query_type="COUNT",
    metric="PROJECT_COUNT",
    filters=None,
    aggregation="SUM",
    formula=None,
    formula_params=None,
    is_primary=True,
):
    data = MagicMock()
    data.kpi_id = kpi_id
    data.source_type = source_type
    data.source_module = source_module
    data.query_type = query_type
    data.metric = metric
    data.filters = filters
    data.aggregation = aggregation
    data.formula = formula
    data.formula_params = formula_params
    data.is_primary = is_primary
    return data


def _make_db_source(
    source_id=1,
    kpi_id=1,
    source_type="MANUAL",
    source_module="PROJECT",
    query_type="COUNT",
    metric="PROJECT_COUNT",
    aggregation="SUM",
    formula=None,
    is_primary=True,
):
    s = MagicMock()
    s.id = source_id
    s.kpi_id = kpi_id
    s.source_type = source_type
    s.source_module = source_module
    s.query_type = query_type
    s.metric = metric
    s.aggregation = aggregation
    s.formula = formula
    s.is_primary = is_primary
    s.is_active = True
    s.last_executed_at = None
    s.last_result = None
    s.last_error = None
    s.created_at = datetime(2024, 1, 1)
    s.updated_at = datetime(2024, 1, 2)
    return s


# ─── create_kpi_data_source ──────────────────────────────────

class TestCreateKpiDataSource:

    def test_creates_and_returns_data_source(self):
        db = MagicMock()
        data = _make_create_data()

        # db.add / db.commit / db.refresh no-ops
        created_source = MagicMock()
        db.refresh.side_effect = lambda x: None

        result = create_kpi_data_source(db, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_filters_serialized_to_json(self):
        """filters 字典应序列化为 JSON 字符串"""
        db = MagicMock()
        filters_dict = {"year": 2024, "status": "ACTIVE"}
        data = _make_create_data(filters=filters_dict)

        import json
        from app.models.strategy import KPIDataSource

        with patch("app.services.strategy.kpi_service.data_source.KPIDataSource") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            db.refresh.side_effect = lambda x: None

            create_kpi_data_source(db, data)

            _, kwargs = mock_cls.call_args
            assert kwargs["filters"] == json.dumps(filters_dict)

    def test_none_filters_stored_as_none(self):
        """filters 为 None 时应存为 None"""
        db = MagicMock()
        data = _make_create_data(filters=None)

        with patch("app.services.strategy.kpi_service.data_source.KPIDataSource") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            db.refresh.side_effect = lambda x: None

            create_kpi_data_source(db, data)

            _, kwargs = mock_cls.call_args
            assert kwargs["filters"] is None

    def test_formula_params_serialized_to_json(self):
        """formula_params 字典应序列化为 JSON"""
        db = MagicMock()
        params = {"multiplier": 1.2}
        data = _make_create_data(formula_params=params)

        import json

        with patch("app.services.strategy.kpi_service.data_source.KPIDataSource") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            db.refresh.side_effect = lambda x: None

            create_kpi_data_source(db, data)

            _, kwargs = mock_cls.call_args
            assert kwargs["formula_params"] == json.dumps(params)

    def test_is_primary_passed_correctly(self):
        db = MagicMock()
        data = _make_create_data(is_primary=False)

        with patch("app.services.strategy.kpi_service.data_source.KPIDataSource") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            db.refresh.side_effect = lambda x: None

            create_kpi_data_source(db, data)

            _, kwargs = mock_cls.call_args
            assert kwargs["is_primary"] is False


# ─── get_kpi_data_sources ────────────────────────────────────

class TestGetKpiDataSources:

    def test_returns_empty_list_when_no_sources(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_kpi_data_sources(db, kpi_id=1)
        assert result == []

    def test_returns_response_objects(self):
        db = MagicMock()
        source = _make_db_source(source_id=1, kpi_id=1)
        db.query.return_value.filter.return_value.all.return_value = [source]

        result = get_kpi_data_sources(db, kpi_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].kpi_id == 1

    def test_returns_multiple_sources(self):
        db = MagicMock()
        sources = [_make_db_source(source_id=i, kpi_id=1) for i in range(1, 4)]
        db.query.return_value.filter.return_value.all.return_value = sources

        result = get_kpi_data_sources(db, kpi_id=1)
        assert len(result) == 3

    def test_response_fields_mapped_correctly(self):
        db = MagicMock()
        source = _make_db_source(
            source_id=5,
            kpi_id=10,
            source_type="AUTO",
            source_module="FINANCE",
            metric="CONTRACT_TOTAL_AMOUNT",
            aggregation="SUM",
            is_primary=True,
        )
        db.query.return_value.filter.return_value.all.return_value = [source]

        result = get_kpi_data_sources(db, kpi_id=10)
        r = result[0]
        assert r.source_type == "AUTO"
        assert r.source_module == "FINANCE"
        assert r.metric == "CONTRACT_TOTAL_AMOUNT"
        assert r.is_primary is True

    def test_last_executed_at_is_none_initially(self):
        db = MagicMock()
        source = _make_db_source(source_id=1)
        source.last_executed_at = None
        db.query.return_value.filter.return_value.all.return_value = [source]

        result = get_kpi_data_sources(db, kpi_id=1)
        assert result[0].last_executed_at is None
