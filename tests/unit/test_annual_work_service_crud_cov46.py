# -*- coding: utf-8 -*-
"""第四十六批 - 年度重点工作 CRUD 单元测试"""
import pytest

pytest.importorskip("app.services.strategy.annual_work_service.crud",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch, call
from app.services.strategy.annual_work_service.crud import (
    create_annual_work,
    get_annual_work,
    list_annual_works,
    update_annual_work,
    delete_annual_work,
)


def _make_db():
    db = MagicMock()
    return db


def _make_work(work_id=1):
    w = MagicMock()
    w.id = work_id
    w.is_active = True
    return w


class TestCreateAnnualWork:
    def test_create_adds_and_commits(self):
        db = _make_db()
        data = MagicMock()
        data.csf_id = 10
        data.code = "W001"
        data.name = "年度重点工作1"
        data.description = "描述"
        data.voc_source = None
        data.pain_point = None
        data.solution = None
        data.year = 2024
        data.priority = 1
        data.start_date = None
        data.end_date = None
        data.owner_dept_id = None
        data.owner_user_id = None

        result = create_annual_work(db, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_sets_fields_from_data(self):
        db = _make_db()
        data = MagicMock()
        data.csf_id = 5
        data.code = "W002"
        data.name = "测试工作"
        data.description = "desc"
        data.voc_source = "source"
        data.pain_point = "pain"
        data.solution = "sol"
        data.year = 2025
        data.priority = 2
        data.start_date = None
        data.end_date = None
        data.owner_dept_id = 1
        data.owner_user_id = 2

        create_annual_work(db, data)
        added_obj = db.add.call_args[0][0]
        assert added_obj.csf_id == 5
        assert added_obj.code == "W002"


class TestGetAnnualWork:
    def test_get_returns_first(self):
        db = _make_db()
        work = _make_work()
        db.query.return_value.filter.return_value.first.return_value = work

        result = get_annual_work(db, 1)
        assert result is work

    def test_get_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_annual_work(db, 99)
        assert result is None


class TestListAnnualWorks:
    def test_list_returns_items_and_total(self):
        db = _make_db()
        works = [_make_work(1), _make_work(2)]
        db.query.return_value.filter.return_value.count.return_value = 2

        with patch("app.services.strategy.annual_work_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = works
            items, total = list_annual_works(db)

        assert total == 2
        assert items is works

    def test_list_with_csf_id_filter(self):
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch("app.services.strategy.annual_work_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            items, total = list_annual_works(db, csf_id=3)
        # 不报错即可


class TestUpdateAnnualWork:
    def test_update_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        data = MagicMock()

        result = update_annual_work(db, 99, data)
        assert result is None

    def test_update_sets_attributes_and_commits(self):
        db = _make_db()
        work = _make_work()
        db.query.return_value.filter.return_value.first.return_value = work
        data = MagicMock()
        data.model_dump.return_value = {"name": "新名称", "year": 2025}

        result = update_annual_work(db, 1, data)
        assert work.name == "新名称"
        assert work.year == 2025
        db.commit.assert_called_once()


class TestDeleteAnnualWork:
    def test_delete_returns_false_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = delete_annual_work(db, 99)
        assert result is False

    def test_delete_soft_deletes_and_returns_true(self):
        db = _make_db()
        work = _make_work()
        db.query.return_value.filter.return_value.first.return_value = work

        result = delete_annual_work(db, 1)
        assert result is True
        assert work.is_active is False
        db.commit.assert_called_once()
