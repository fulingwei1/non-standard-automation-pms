# -*- coding: utf-8 -*-
"""
测试 QueryDataSource - SQL查询数据源

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.data_sources.query import QueryDataSource
from app.services.report_framework.data_sources.base import DataSourceError
from app.services.report_framework.models import DataSourceConfig


class TestQueryDataSourceInit:
    """测试QueryDataSource初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id"
        )
        ds = QueryDataSource(db, config)
        assert ds.db == db
        assert ds.config == config

    def test_init_missing_sql(self):
        """测试缺少SQL配置"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query"
        )
        with pytest.raises(DataSourceError, match="SQL query is required"):
            QueryDataSource(db, config)

    def test_init_with_empty_sql(self):
        """测试空SQL"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql=""
        )
        with pytest.raises(DataSourceError, match="SQL query is required"):
            QueryDataSource(db, config)


class TestValidateConfig:
    """测试配置验证"""

    @pytest.mark.parametrize("dangerous_keyword", [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE"
    ])
    def test_dangerous_keywords(self, dangerous_keyword):
        """测试危险SQL关键字检测"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql=f"{dangerous_keyword} FROM users"
        )
        with pytest.raises(DataSourceError, match=f"Dangerous SQL keyword detected: {dangerous_keyword}"):
            QueryDataSource(db, config)

    @pytest.mark.parametrize("dangerous_keyword", [
        "drop",
        "delete",
        "update",
        "insert",
        "alter",
        "truncate"
    ])
    def test_dangerous_keywords_lowercase(self, dangerous_keyword):
        """测试小写危险关键字检测"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql=f"{dangerous_keyword} from users"
        )
        with pytest.raises(DataSourceError):
            QueryDataSource(db, config)

    def test_safe_column_names_with_dangerous_substrings(self):
        """测试包含危险关键字子串的安全列名"""
        db = Mock(spec=Session)
        # "updated_at" 包含 "update" 但不是独立关键字
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT id, updated_at, inserted_at FROM users"
        )
        # 应该成功，因为是列名的一部分
        ds = QueryDataSource(db, config)
        assert ds.config.sql == config.sql

    def test_valid_select_query(self):
        """测试有效的SELECT查询"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT id, name FROM users WHERE status = :status"
        )
        ds = QueryDataSource(db, config)
        assert ds.config == config


class TestFetch:
    """测试数据获取"""

    def test_fetch_success(self):
        """测试成功获取数据"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT id, name FROM users WHERE status = :status"
        )

        # Mock执行结果
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [
            (1, "Alice"),
            (2, "Bob")
        ]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({"status": "active"})

        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Alice"}
        assert result[1] == {"id": 2, "name": "Bob"}

    def test_fetch_empty_result(self):
        """测试空结果"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id"
        )

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = []
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({"user_id": 999})

        assert result == []

    def test_fetch_with_multiple_columns(self):
        """测试多列查询"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT id, name, email, created_at FROM users"
        )

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name", "email", "created_at"]
        mock_result.fetchall.return_value = [
            (1, "Alice", "alice@test.com", "2024-01-01")
        ]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({})

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["email"] == "alice@test.com"
        assert result[0]["created_at"] == "2024-01-01"

    def test_fetch_with_none_values(self):
        """测试NULL值处理"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT id, name, email FROM users"
        )

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name", "email"]
        mock_result.fetchall.return_value = [
            (1, "Alice", None),
            (2, None, "bob@test.com")
        ]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({})

        assert result[0]["email"] is None
        assert result[1]["name"] is None

    def test_fetch_sql_error(self):
        """测试SQL执行错误"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM non_existent_table"
        )

        db.execute.side_effect = Exception("Table not found")

        ds = QueryDataSource(db, config)
        with pytest.raises(DataSourceError, match="SQL query execution failed"):
            ds.fetch({})

    def test_fetch_with_params(self):
        """测试参数化查询"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id AND status = :status"
        )

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "Alice")]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({"user_id": 1, "status": "active"})

        # 验证execute被正确调用
        assert db.execute.called
        assert len(result) == 1


class TestGetRequiredParams:
    """测试参数提取"""

    def test_get_single_param(self):
        """测试单参数提取"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id"
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert params == ["user_id"]

    def test_get_multiple_params(self):
        """测试多参数提取"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id AND status = :status AND dept = :dept_id"
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert set(params) == {"user_id", "status", "dept_id"}

    def test_get_duplicate_params(self):
        """测试重复参数去重"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users WHERE id = :user_id OR parent_id = :user_id"
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert params == ["user_id"]

    def test_get_no_params(self):
        """测试无参数SQL"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT COUNT(*) FROM users"
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert params == []

    def test_get_params_complex_query(self):
        """测试复杂查询参数提取"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="""
            SELECT u.id, u.name, d.name as dept_name
            FROM users u
            JOIN departments d ON u.dept_id = d.id
            WHERE u.status = :status
              AND u.created_at >= :start_date
              AND u.created_at <= :end_date
              AND d.id = :dept_id
            """
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert set(params) == {"status", "start_date", "end_date", "dept_id"}


class TestEdgeCases:
    """测试边界情况"""

    def test_sql_with_comments(self):
        """测试带注释的SQL"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="""
            -- 查询用户信息
            SELECT * FROM users
            WHERE status = :status  -- 状态过滤
            """
        )
        ds = QueryDataSource(db, config)
        assert ds.get_required_params() == ["status"]

    def test_sql_with_subquery(self):
        """测试子查询"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="""
            SELECT * FROM users
            WHERE dept_id IN (SELECT id FROM departments WHERE region = :region)
            """
        )
        ds = QueryDataSource(db, config)
        params = ds.get_required_params()
        assert "region" in params

    def test_large_result_set(self):
        """测试大结果集"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users"
        )

        # 模拟1000行数据
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(i, f"User{i}") for i in range(1000)]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({})

        assert len(result) == 1000
        assert result[0]["id"] == 0
        assert result[999]["id"] == 999

    def test_special_characters_in_data(self):
        """测试特殊字符数据"""
        db = Mock(spec=Session)
        config = DataSourceConfig(
            name="test_query",
            type="query",
            sql="SELECT * FROM users"
        )

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [
            (1, "User with 'quotes'"),
            (2, 'User with "double quotes"'),
            (3, "User with \n newline"),
            (4, "User with \t tab")
        ]
        db.execute.return_value = mock_result

        ds = QueryDataSource(db, config)
        result = ds.fetch({})

        assert len(result) == 4
        assert "'" in result[0]["name"]
        assert '"' in result[1]["name"]
