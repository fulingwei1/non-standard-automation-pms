# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - SQL 查询数据源"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.data_sources.query import QueryDataSource
    from app.services.report_framework.data_sources.base import DataSourceError
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


def make_config(sql=None):
    config = MagicMock()
    config.sql = sql
    config.method = None
    return config


class TestQueryDataSource:

    def test_raises_when_no_sql(self):
        config = make_config(sql=None)
        with pytest.raises(DataSourceError, match="SQL query is required"):
            QueryDataSource(db=MagicMock(), config=config)

    def test_raises_on_dangerous_drop(self):
        config = make_config(sql="DROP TABLE projects")
        with pytest.raises(DataSourceError, match="Dangerous SQL keyword"):
            QueryDataSource(db=MagicMock(), config=config)

    def test_raises_on_dangerous_delete(self):
        config = make_config(sql="DELETE FROM users WHERE 1=1")
        with pytest.raises(DataSourceError, match="Dangerous SQL keyword"):
            QueryDataSource(db=MagicMock(), config=config)

    def test_safe_select_passes_validation(self):
        config = make_config(sql="SELECT id, name FROM projects WHERE id = :project_id")
        db = MagicMock()
        ds = QueryDataSource(db=db, config=config)
        assert ds is not None

    def test_fetch_returns_row_dicts(self):
        config = make_config(sql="SELECT id, name FROM projects")
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "Proj A"), (2, "Proj B")]
        db.execute.return_value = mock_result
        ds = QueryDataSource(db=db, config=config)
        with patch("app.services.report_framework.data_sources.query.text"):
            result = ds.fetch({"project_id": 1})
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["name"] == "Proj B"

    def test_fetch_raises_data_source_error_on_db_failure(self):
        config = make_config(sql="SELECT 1")
        db = MagicMock()
        db.execute.side_effect = Exception("DB error")
        ds = QueryDataSource(db=db, config=config)
        with patch("app.services.report_framework.data_sources.query.text"), \
             pytest.raises(DataSourceError):
            ds.fetch({})

    def test_inherits_datasource(self):
        from app.services.report_framework.data_sources.base import DataSource
        assert issubclass(QueryDataSource, DataSource)
