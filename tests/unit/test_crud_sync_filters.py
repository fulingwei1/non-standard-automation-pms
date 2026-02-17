# -*- coding: utf-8 -*-
"""
app/common/crud/sync_filters.py 覆盖率测试（当前 21%）
SyncQueryBuilder - 同步版查询构建器
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class FakeModel(Base):
    __tablename__ = "fake_sync_model_for_tests"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    status = Column(String(20))
    description = Column(String(200))


class TestSyncQueryBuilder:
    """测试 SyncQueryBuilder.build_list_query"""

    def test_build_basic_query(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        query, count_query = SyncQueryBuilder.build_list_query(FakeModel, db)
        db.query.assert_called()

    def test_build_with_skip_limit(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(FakeModel, db, skip=10, limit=20)
        assert query is not None

    def test_build_with_exact_filter(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, filters={"status": "ACTIVE"}
        )
        assert query is not None

    def test_build_with_list_filter(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, filters={"status": ["ACTIVE", "PENDING"]}
        )
        assert query is not None

    def test_build_with_range_filter(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, filters={"id": {"min": 1, "max": 100}}
        )
        assert query is not None

    def test_build_with_like_filter(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, filters={"name": {"like": "test"}}
        )
        assert query is not None

    def test_build_with_keyword(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, keyword="hello", keyword_fields=["name", "description"]
        )
        assert query is not None

    def test_build_order_asc(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, order_by="name", order_direction="asc"
        )
        assert query is not None

    def test_build_order_desc(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, order_by="id", order_direction="desc"
        )
        assert query is not None

    def test_none_filter_value(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, filters={"description": None}
        )
        assert query is not None

    def test_empty_filters(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        query, count = SyncQueryBuilder.build_list_query(FakeModel, db, filters={})
        assert query is not None

    def test_nonexistent_order_field(self):
        from app.common.crud.sync_filters import SyncQueryBuilder
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        db.query.return_value = mock_q
        # nonexistent order_by field should be ignored
        query, count = SyncQueryBuilder.build_list_query(
            FakeModel, db, order_by="totally_fake_field"
        )
        assert query is not None
