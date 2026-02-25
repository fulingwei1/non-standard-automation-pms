# -*- coding: utf-8 -*-
"""Stock Count Service 测试 - Batch 2"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.services.stock_count_service import StockCountService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    return StockCountService(mock_db, tenant_id=1)


class TestInit:
    def test_init(self, mock_db):
        svc = StockCountService(mock_db, tenant_id=5)
        assert svc.tenant_id == 5
        assert svc.db == mock_db


class TestCreateCountTask:
    def test_create_basic_task(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="FULL",
            count_date=date(2024, 6, 1),
            created_by=1
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_task_with_location(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="SPOT",
            count_date=date(2024, 6, 1),
            location="仓库A"
        )
        mock_db.add.assert_called_once()

    def test_create_task_with_category(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="CATEGORY",
            count_date=date(2024, 6, 1),
            category_id=10
        )
        mock_db.add.assert_called_once()

    def test_create_task_with_material_ids(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="SELECTIVE",
            count_date=date(2024, 6, 1),
            material_ids=[1, 2, 3]
        )
        mock_db.add.assert_called_once()

    def test_create_task_with_assigned_to(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="FULL",
            count_date=date(2024, 6, 1),
            assigned_to=5,
            remark="测试盘点"
        )
        mock_db.add.assert_called_once()

    def test_task_has_pending_status(self, service, mock_db):
        stocks = []
        mock_db.query.return_value.filter.return_value.all.return_value = stocks
        result = service.create_count_task(
            count_type="FULL",
            count_date=date(2024, 6, 1)
        )
        assert result.status == 'PENDING'

    def test_task_no_generation(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.create_count_task(
            count_type="FULL",
            count_date=date(2024, 6, 1)
        )
        assert result.total_items == 0


class TestCreateCountDetails:
    def test_empty_stock(self, service, mock_db):
        task = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service._create_count_details(task, None, None, None)
        assert result == [] or len(result) == 0

    def test_with_location_filter(self, service, mock_db):
        task = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = service._create_count_details(task, "仓库A", None, None)
        assert isinstance(result, list)

    def test_with_stocks(self, service, mock_db):
        task = MagicMock()
        task.id = 1
        stock = MagicMock()
        stock.material_id = 1
        stock.material = MagicMock()
        stock.material.material_code = "M001"
        stock.material.material_name = "螺丝"
        stock.quantity = Decimal("100")
        stock.location = "A1"
        stock.batch_no = "B001"
        mock_db.query.return_value.filter.return_value.all.return_value = [stock]
        result = service._create_count_details(task, None, None, None)
        # The details are created and added to db
        assert isinstance(result, list)
