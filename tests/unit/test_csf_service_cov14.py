# -*- coding: utf-8 -*-
"""
第十四批：CSF关键成功要素服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.strategy import csf_service
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_csf(**kwargs):
    csf = MagicMock()
    csf.id = kwargs.get("id", 1)
    csf.strategy_id = kwargs.get("strategy_id", 10)
    csf.dimension = kwargs.get("dimension", "FINANCIAL")
    csf.code = "CSF-001"
    csf.name = "收入增长"
    csf.description = "提升营收"
    csf.weight = 25.0
    csf.sort_order = 1
    csf.is_active = True
    csf.owner_user_id = None
    csf.owner_dept_id = None
    csf.created_at = None
    csf.updated_at = None
    return csf


class TestCsfService:
    def test_create_csf(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = make_csf()
        data = MagicMock()
        data.strategy_id = 10
        data.dimension = "FINANCIAL"
        data.code = "CSF-001"
        data.name = "收入增长"
        data.description = "提升营收"
        data.derivation_method = None
        data.weight = 25.0
        data.sort_order = 1
        data.owner_dept_id = None
        data.owner_user_id = None
        csf = csf_service.create_csf(db, data)
        db.add.assert_called_once()
        db.commit.assert_called()

    def test_get_csf_found(self):
        db = make_db()
        expected = make_csf()
        db.query.return_value.filter.return_value.first.return_value = expected
        result = csf_service.get_csf(db, 1)
        assert result is expected

    def test_get_csf_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = csf_service.get_csf(db, 999)
        assert result is None

    def test_update_csf_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        data = MagicMock()
        result = csf_service.update_csf(db, 999, data)
        assert result is None

    def test_update_csf_success(self):
        db = make_db()
        csf = make_csf()
        db.query.return_value.filter.return_value.first.return_value = csf
        data = MagicMock()
        data.model_dump.return_value = {"name": "新名称", "weight": 30.0}
        result = csf_service.update_csf(db, 1, data)
        assert csf.name == "新名称"
        db.commit.assert_called()

    def test_delete_csf_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = csf_service.delete_csf(db, 999)
        assert result is False

    def test_delete_csf_success(self):
        db = make_db()
        csf = make_csf()
        db.query.return_value.filter.return_value.first.return_value = csf
        result = csf_service.delete_csf(db, 1)
        assert result is True
        assert csf.is_active is False
        db.commit.assert_called()

    def test_list_csfs(self):
        db = make_db()
        mock_q = MagicMock()
        db.query.return_value.filter.return_value = mock_q
        mock_q.count.return_value = 2
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [make_csf(), make_csf(id=2)]
        with patch("app.services.strategy.csf_service.apply_pagination", return_value=mock_q):
            items, total = csf_service.list_csfs(db, strategy_id=10)
        assert total == 2
