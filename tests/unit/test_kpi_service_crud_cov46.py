# -*- coding: utf-8 -*-
"""第四十六批 - KPI服务CRUD单元测试"""
import pytest
import json

pytest.importorskip("app.services.strategy.kpi_service.crud",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.kpi_service.crud import (
    create_kpi,
    get_kpi,
    list_kpis,
    update_kpi,
    delete_kpi,
)


def _make_db():
    return MagicMock()


class TestCreateKpi:
    def test_adds_commits_refreshes(self):
        db = _make_db()
        data = MagicMock()
        data.csf_id = 1
        data.code = "K001"
        data.name = "KPI名称"
        data.description = None
        data.ipooc_type = "OUTPUT"
        data.unit = "%"
        data.direction = "UP"
        data.target_value = None
        data.baseline_value = None
        data.excellent_threshold = None
        data.good_threshold = None
        data.warning_threshold = None
        data.data_source_type = "MANUAL"
        data.data_source_config = None
        data.frequency = "MONTHLY"
        data.weight = None
        data.owner_user_id = None

        create_kpi(db, data)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_data_source_config_serialized_to_json(self):
        db = _make_db()
        data = MagicMock()
        data.csf_id = 1
        data.code = "K002"
        data.name = "KPI2"
        data.description = None
        data.ipooc_type = "INPUT"
        data.unit = "个"
        data.direction = "UP"
        data.target_value = None
        data.baseline_value = None
        data.excellent_threshold = None
        data.good_threshold = None
        data.warning_threshold = None
        data.data_source_type = "AUTO"
        data.data_source_config = {"module": "project", "metric": "count"}
        data.frequency = "WEEKLY"
        data.weight = None
        data.owner_user_id = None

        create_kpi(db, data)
        added = db.add.call_args[0][0]
        assert added.data_source_config == json.dumps({"module": "project", "metric": "count"})


class TestGetKpi:
    def test_returns_kpi_when_found(self):
        db = _make_db()
        kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi
        result = get_kpi(db, 1)
        assert result is kpi

    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_kpi(db, 99)
        assert result is None


class TestListKpis:
    def test_returns_items_and_total(self):
        db = _make_db()
        db.query.return_value.filter.return_value.count.return_value = 3

        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock(), MagicMock()]
            items, total = list_kpis(db)

        assert total == 3

    def test_applies_filters(self):
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            list_kpis(db, csf_id=5, ipooc_type="OUTPUT")


class TestUpdateKpi:
    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = update_kpi(db, 99, MagicMock())
        assert result is None

    def test_updates_fields_and_commits(self):
        db = _make_db()
        kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi
        data = MagicMock()
        data.model_dump.return_value = {"name": "新KPI名", "unit": "次"}

        update_kpi(db, 1, data)
        assert kpi.name == "新KPI名"
        db.commit.assert_called_once()


class TestDeleteKpi:
    def test_returns_false_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        assert delete_kpi(db, 99) is False

    def test_soft_deletes_and_returns_true(self):
        db = _make_db()
        kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi
        result = delete_kpi(db, 1)
        assert result is True
        assert kpi.is_active is False
        db.commit.assert_called_once()
