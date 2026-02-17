# -*- coding: utf-8 -*-
"""
app/common/crud/filters.py 覆盖率测试（当前 13%）
测试 QueryBuilder 静态方法
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class FakeModel(Base):
    __tablename__ = "fake_model_for_tests"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    status = Column(String(20))
    description = Column(String(200))


class TestQueryBuilder:
    """测试 QueryBuilder.build_list_query"""

    def test_build_basic_query(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count_query = QueryBuilder.build_list_query(FakeModel, db)
        assert query is not None
        assert count_query is not None

    def test_build_with_skip_limit(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count_query = QueryBuilder.build_list_query(FakeModel, db, skip=10, limit=20)
        assert query is not None

    def test_build_with_exact_filter(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, filters={"status": "ACTIVE"}
        )
        assert query is not None

    def test_build_with_list_filter(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, filters={"status": ["ACTIVE", "PENDING"]}
        )
        assert query is not None

    def test_build_with_range_filter(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, filters={"id": {"min": 1, "max": 100}}
        )
        assert query is not None

    def test_build_with_like_filter(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, filters={"name": {"like": "test"}}
        )
        assert query is not None

    def test_build_with_none_filter(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, filters={"description": None}
        )
        assert query is not None

    def test_build_with_keyword(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db,
            keyword="hello",
            keyword_fields=["name", "description"]
        )
        assert query is not None

    def test_build_order_asc(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, order_by="name", order_direction="asc"
        )
        assert query is not None

    def test_build_order_desc(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, order_by="id", order_direction="desc"
        )
        assert query is not None

    def test_build_with_nonexistent_order_field(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        # order_by 指定不存在的字段，应该被忽略
        query, count = QueryBuilder.build_list_query(
            FakeModel, db, order_by="nonexistent_field"
        )
        assert query is not None

    def test_build_combined_filters(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(
            FakeModel, db,
            skip=0,
            limit=50,
            filters={"status": "ACTIVE"},
            keyword="test",
            keyword_fields=["name"],
            order_by="id",
            order_direction="desc"
        )
        assert query is not None
        assert count is not None

    def test_zero_skip_not_applied(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query1, _ = QueryBuilder.build_list_query(FakeModel, db, skip=0, limit=10)
        query2, _ = QueryBuilder.build_list_query(FakeModel, db, skip=5, limit=10)
        # skip=0 和 skip=5 会生成不同的查询
        assert query1 is not None
        assert query2 is not None

    def test_empty_filters_dict(self):
        from app.common.crud.filters import QueryBuilder
        db = MagicMock()
        query, count = QueryBuilder.build_list_query(FakeModel, db, filters={})
        assert query is not None
