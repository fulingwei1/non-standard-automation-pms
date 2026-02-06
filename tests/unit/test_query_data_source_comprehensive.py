# -*- coding: utf-8 -*-
"""
QueryDataSource 综合单元测试

测试覆盖:
- __init__: 初始化查询数据源
- validate_config: 验证配置
- fetch: 执行SQL查询
- get_required_params: 获取需要的参数名
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime
from decimal import Decimal

import pytest


class TestQueryDataSourceInit:
    """测试 QueryDataSource 初始化"""

    def test_initializes_with_valid_config(self):
        """测试使用有效配置初始化"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "SELECT * FROM projects WHERE id = :project_id"

        source = QueryDataSource(mock_db, mock_config)

        assert source.db == mock_db
        assert source.config == mock_config

    def test_raises_for_missing_sql(self):
        """测试缺少SQL时抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = None

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "SQL query is required" in str(exc_info.value)

    def test_raises_for_empty_sql(self):
        """测试空SQL时抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = ""

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "SQL query is required" in str(exc_info.value)


class TestValidateConfig:
    """测试 validate_config 方法"""

    def test_validates_select_query(self):
        """测试验证SELECT查询"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "SELECT id, name FROM users"

        # Should not raise
        source = QueryDataSource(mock_db, mock_config)

    def test_raises_for_drop_keyword(self):
        """测试DROP关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "DROP TABLE users"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_raises_for_delete_keyword(self):
        """测试DELETE关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "DELETE FROM users WHERE id = 1"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_raises_for_update_keyword(self):
        """测试UPDATE关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "UPDATE users SET name = 'test'"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_raises_for_insert_keyword(self):
        """测试INSERT关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "INSERT INTO users VALUES (1, 'test')"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_raises_for_alter_keyword(self):
        """测试ALTER关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "ALTER TABLE users ADD COLUMN email"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_raises_for_truncate_keyword(self):
        """测试TRUNCATE关键词抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "TRUNCATE TABLE users"

        with pytest.raises(DataSourceError) as exc_info:
            QueryDataSource(mock_db, mock_config)

        assert "Dangerous SQL keyword" in str(exc_info.value)

    def test_allows_delete_in_column_name(self):
        """测试允许DELETE作为列名的一部分"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "SELECT deleted_at, is_deleted FROM users"

        # Should not raise because 'deleted' is not 'DELETE'
        source = QueryDataSource(mock_db, mock_config)


class TestFetch:
    """测试 fetch 方法"""

    def test_fetches_data_successfully(self):
        """测试成功获取数据"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_result = MagicMock()
        mock_result.keys.return_value = ['id', 'name']
        mock_result.fetchall.return_value = [(1, '项目A'), (2, '项目B')]
        mock_db.execute.return_value = mock_result

        mock_config = MagicMock()
        mock_config.sql = "SELECT id, name FROM projects WHERE status = :status"

        source = QueryDataSource(mock_db, mock_config)

        result = source.fetch({"status": "ACTIVE"})

        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['name'] == '项目A'
        assert result[1]['id'] == 2
        assert result[1]['name'] == '项目B'

    def test_fetches_empty_result(self):
        """测试获取空结果"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_result = MagicMock()
        mock_result.keys.return_value = ['id', 'name']
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        mock_config = MagicMock()
        mock_config.sql = "SELECT id, name FROM projects WHERE id = :id"

        source = QueryDataSource(mock_db, mock_config)

        result = source.fetch({"id": 999})

        assert result == []

    def test_raises_for_execution_error(self):
        """测试执行错误时抛出异常"""
        from app.services.report_framework.data_sources.query import QueryDataSource
        from app.services.report_framework.data_sources.base import DataSourceError

        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database error")

        mock_config = MagicMock()
        mock_config.sql = "SELECT * FROM projects"

        source = QueryDataSource(mock_db, mock_config)

        with pytest.raises(DataSourceError) as exc_info:
            source.fetch({})

        assert "SQL query execution failed" in str(exc_info.value)


class TestGetRequiredParams:
    """测试 get_required_params 方法"""

    def test_extracts_single_param(self):
        """测试提取单个参数"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "SELECT * FROM projects WHERE id = :project_id"

        source = QueryDataSource(mock_db, mock_config)

        result = source.get_required_params()

        assert 'project_id' in result

    def test_extracts_multiple_params(self):
        """测试提取多个参数"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = """
            SELECT * FROM projects
            WHERE status = :status
            AND created_at >= :start_date
            AND created_at <= :end_date
        """

        source = QueryDataSource(mock_db, mock_config)

        result = source.get_required_params()

        assert 'status' in result
        assert 'start_date' in result
        assert 'end_date' in result

    def test_deduplicates_params(self):
        """测试参数去重"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = """
            SELECT * FROM projects
            WHERE id = :project_id
            OR parent_id = :project_id
        """

        source = QueryDataSource(mock_db, mock_config)

        result = source.get_required_params()

        assert result.count('project_id') == 1

    def test_returns_empty_for_no_params(self):
        """测试无参数时返回空列表"""
        from app.services.report_framework.data_sources.query import QueryDataSource

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.sql = "SELECT * FROM projects"

        source = QueryDataSource(mock_db, mock_config)

        result = source.get_required_params()

        assert result == []
