# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/data_sources/query.py"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.data_sources.query import QueryDataSource
    from app.services.report_framework.data_sources.base import DataSourceError
    from app.services.report_framework.models import DataSourceConfig, DataSourceType
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_config(sql=None):
    return DataSourceConfig(type=DataSourceType.QUERY, sql=sql)


def _make_db():
    return MagicMock()


def test_validate_config_no_sql():
    config = _make_config(sql=None)
    with pytest.raises(DataSourceError, match="SQL query is required"):
        QueryDataSource(_make_db(), config)


def test_validate_config_dangerous_drop():
    config = _make_config(sql="DROP TABLE projects")
    with pytest.raises(DataSourceError, match="Dangerous SQL keyword"):
        QueryDataSource(_make_db(), config)


def test_validate_config_dangerous_delete():
    config = _make_config(sql="DELETE FROM users WHERE id=1")
    with pytest.raises(DataSourceError, match="Dangerous SQL keyword"):
        QueryDataSource(_make_db(), config)


def test_validate_config_safe_select():
    config = _make_config(sql="SELECT id, name FROM projects WHERE id = :project_id")
    ds = QueryDataSource(_make_db(), config)
    assert ds is not None


def test_fetch_returns_dict_list():
    config = _make_config(sql="SELECT id, name FROM projects")
    db = _make_db()
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name"]
    mock_result.fetchall.return_value = [(1, "P1"), (2, "P2")]
    db.execute.return_value = mock_result

    ds = QueryDataSource(db, config)
    result = ds.fetch({})
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["name"] == "P2"


def test_fetch_raises_data_source_error_on_exception():
    config = _make_config(sql="SELECT * FROM projects")
    db = _make_db()
    db.execute.side_effect = Exception("connection error")
    ds = QueryDataSource(db, config)
    with pytest.raises(DataSourceError, match="SQL query execution failed"):
        ds.fetch({})


def test_get_required_params():
    config = _make_config(sql="SELECT * FROM t WHERE a = :start_date AND b = :end_date")
    ds = QueryDataSource(_make_db(), config)
    params = ds.get_required_params()
    assert "start_date" in params
    assert "end_date" in params
