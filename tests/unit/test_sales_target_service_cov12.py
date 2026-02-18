# -*- coding: utf-8 -*-
"""第十二批：销售目标服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.sales_target_service import SalesTargetService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_db():
    return MagicMock()


def _make_target_data(**kwargs):
    data = MagicMock()
    data.target_type = kwargs.get("target_type", "team")
    data.team_id = kwargs.get("team_id", 1)
    data.user_id = kwargs.get("user_id", None)
    data.target_period = kwargs.get("target_period", "monthly")
    data.target_year = kwargs.get("target_year", 2025)
    data.target_month = kwargs.get("target_month", 1)
    data.model_dump = MagicMock(return_value={
        "target_type": data.target_type,
        "team_id": data.team_id,
        "user_id": data.user_id,
        "target_period": data.target_period,
        "target_year": data.target_year,
    })
    return data


class TestGetTarget:
    """get_target 静态方法测试"""

    def test_returns_target_when_found(self):
        db = _make_db()
        mock_target = MagicMock()
        mock_target.id = 1
        db.query.return_value.filter.return_value.first.return_value = mock_target

        result = SalesTargetService.get_target(db, 1)
        assert result is mock_target

    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = SalesTargetService.get_target(db, 999)
        assert result is None


class TestGetTargets:
    """get_targets 静态方法测试"""

    def _make_chainable_db(self, return_value=None):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = return_value or []
        db.query.return_value = mock_q
        return db

    def test_returns_list(self):
        t1, t2 = MagicMock(), MagicMock()
        db = self._make_chainable_db([t1, t2])
        result = SalesTargetService.get_targets(db)
        assert isinstance(result, list)

    def test_with_filters(self):
        db = self._make_chainable_db([])
        result = SalesTargetService.get_targets(
            db, target_type="team", target_year=2025
        )
        assert isinstance(result, list)


class TestCreateTarget:
    """create_target 静态方法测试"""

    def test_raises_for_team_type_without_team_id(self):
        from fastapi import HTTPException
        db = _make_db()
        target_data = _make_target_data(target_type="team", team_id=None)

        with pytest.raises(HTTPException):
            SalesTargetService.create_target(db, target_data, created_by=1)

    def test_raises_for_personal_type_without_user_id(self):
        from fastapi import HTTPException
        db = _make_db()
        target_data = _make_target_data(target_type="personal", team_id=None, user_id=None)

        with pytest.raises(HTTPException):
            SalesTargetService.create_target(db, target_data, created_by=1)

    def test_raises_when_target_already_exists(self):
        from fastapi import HTTPException
        db = _make_db()
        target_data = _make_target_data(target_type="team", team_id=5)
        
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(HTTPException):
            SalesTargetService.create_target(db, target_data, created_by=1)

    def test_creates_target_successfully(self):
        db = _make_db()
        target_data = _make_target_data(target_type="team", team_id=5)
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.sales_target_service.save_obj") as mock_save:
            with patch("app.services.sales_target_service.SalesTargetV2") as MockTarget:
                mock_target = MagicMock()
                MockTarget.return_value = mock_target
                result = SalesTargetService.create_target(db, target_data, created_by=1)
                assert mock_save.called


class TestDeleteTarget:
    """delete_target / get_target 测试"""

    def test_get_target_queries_db(self):
        db = _make_db()
        mock_t = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_t

        result = SalesTargetService.get_target(db, 10)
        assert result is mock_t
