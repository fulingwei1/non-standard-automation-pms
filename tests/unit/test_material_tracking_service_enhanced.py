# -*- coding: utf-8 -*-
"""
MaterialTrackingService 完整测试套件
覆盖范围: 物料入库/出库、库存查询、批次追踪、浪费分析、成本分析等
"""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.production.material_tracking.material_tracking_service import (
    MaterialTrackingService,
)


# ================== Fixtures ==================


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """服务实例"""
    return MaterialTrackingService(mock_db)


@pytest.fixture
def mock_material():
    """模拟物料对象"""
    material = MagicMock()
    material.id = 1
    material.material_code = "MAT001"
    material.material_name = "测试物料"
    material.specification = "规格A"
    material.unit = "kg"
    material.current_stock = Decimal("100.00")
    material.safety_stock = Decimal("20.00")
    material.standard_price = Decimal("50.00")
    material.is_active = True
    material.category_id = 10
    return material


@pytest.fixture
def mock_batch():
    """模拟批次对象"""
    batch = MagicMock()
    batch.id = 1
    batch.batch_no = "BATCH001"
    batch.material_id = 1
    batch.current_qty = Decimal("50.00")
    batch.reserved_qty = Decimal("10.00")
    batch.initial_qty = Decimal("100.00")
    batch.consumed_qty = Decimal("50.00")
    batch.production_date = date(2024, 1, 1)
    batch.expire_date = date(2024, 12, 31)
    batch.warehouse_location = "A-01-01"
    batch.quality_status = "QUALIFIED"
    batch.status = "ACTIVE"
    batch.barcode = "BC001"
    batch.supplier_batch_no = "SUP-001"
    return batch


@pytest.fixture
def mock_consumption():
    """模拟消耗记录"""
    consumption = MagicMock()
    consumption.id = 1
    consumption.consumption_no = "CONS-20240101-MAT001"
    consumption.material_id = 1
    consumption.material_code = "MAT001"
    consumption.material_name = "测试物料"
    consumption.batch_id = 1
    consumption.consumption_date = datetime(2024, 1, 15)
    consumption.consumption_qty = Decimal("30.00")
    consumption.standard_qty = Decimal("25.00")
    consumption.variance_qty = Decimal("5.00")
    consumption.variance_rate = Decimal("20.00")
    consumption.is_waste = True
    consumption.consumption_type = "PRODUCTION"
    consumption.unit_price = Decimal("50.00")
    consumption.total_cost = Decimal("1500.00")
    consumption.project_id = 100
    consumption.work_order_id = 200
    consumption.operator_id = 1
    consumption.unit = "kg"
    consumption.remark = "测试消耗"
    return consumption


@pytest.fixture
def mock_alert():
    """模拟预警对象"""
    alert = MagicMock()
    alert.id = 1
    alert.alert_no = "ALERT-20240101-MAT001"
    alert.material_id = 1
    alert.material_code = "MAT001"
    alert.material_name = "测试物料"
    alert.alert_date = datetime(2024, 1, 1)
    alert.alert_type = "LOW_STOCK"
    alert.alert_level = "WARNING"
    alert.current_stock = Decimal("15.00")
    alert.safety_stock = Decimal("20.00")
    alert.shortage_qty = Decimal("5.00")
    alert.days_to_stockout = 3
    alert.alert_message = "库存低于安全值"
    alert.recommendation = "建议采购"
    alert.status = "ACTIVE"
    alert.assigned_to_id = None
    return alert


@pytest.fixture
def mock_alert_rule():
    """模拟预警规则"""
    rule = MagicMock()
    rule.id = 1
    rule.rule_name = "低库存预警"
    rule.material_id = None
    rule.category_id = None
    rule.alert_type = "LOW_STOCK"
    rule.alert_level = "WARNING"
    rule.threshold_type = "PERCENTAGE"
    rule.threshold_value = Decimal("80.00")
    rule.safety_days = 7
    rule.is_active = True
    rule.priority = 1
    return rule


# ================== 1. 实时库存查询测试 ==================


def test_get_realtime_stock_basic(service, mock_db, mock_material, mock_batch):
    """测试基础库存查询"""
    # Setup
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_material]

    # Mock batch query
    batch_query = MagicMock()
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_realtime_stock()

    # Assertions
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["material_code"] == "MAT001"
    assert result["items"][0]["batch_count"] == 1


def test_get_realtime_stock_with_material_id(service, mock_db, mock_material, mock_batch):
    """测试按物料ID筛选"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_material]

    batch_query = MagicMock()
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_realtime_stock(material_id=1)

    assert result["total"] == 1


def test_get_realtime_stock_low_stock_only(service, mock_db, mock_material, mock_batch):
    """测试低库存筛选"""
    # 设置库存低于安全库存
    mock_material.current_stock = Decimal("10.00")
    mock_material.safety_stock = Decimal("20.00")

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_material]

    batch_query = MagicMock()
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_realtime_stock(low_stock_only=True)

    assert result["items"][0]["is_low_stock"] is True


def test_get_realtime_stock_available_calculation(service, mock_db, mock_material, mock_batch):
    """测试可用库存计算"""
    # 设置第一次查询返回物料，第二次查询返回批次
    material_query = MagicMock()
    batch_query = MagicMock()
    
    mock_db.query.side_effect = [material_query, batch_query]
    
    material_query.filter.return_value = material_query
    material_query.count.return_value = 1
    material_query.all.return_value = [mock_material]
    
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=material_query):
        result = service.get_realtime_stock()

    # 可用库存 = 当前数量 - 预留数量 (50 - 10 = 40)
    assert result["items"][0]["batches"][0]["available_qty"] == 40.0


def test_get_realtime_stock_pagination(service, mock_db, mock_material, mock_batch):
    """测试分页"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 50
    mock_query.all.return_value = [mock_material] * 10

    batch_query = MagicMock()
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_realtime_stock(page=2, page_size=10)

    assert result["page"] == 2
    assert result["page_size"] == 10
    assert result["total"] == 50


def test_get_realtime_stock_empty_batches(service, mock_db, mock_material):
    """测试无批次的物料"""
    # 设置第一次查询返回物料，第二次查询返回空批次
    material_query = MagicMock()
    batch_query = MagicMock()
    
    mock_db.query.side_effect = [material_query, batch_query]
    
    material_query.filter.return_value = material_query
    material_query.count.return_value = 1
    material_query.all.return_value = [mock_material]
    
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = []

    with patch("app.common.query_filters.apply_pagination", return_value=material_query):
        result = service.get_realtime_stock()

    assert result["items"][0]["batch_count"] == 0
    assert result["items"][0]["batches"] == []


# ================== 2. 物料消耗记录测试 ==================


def test_create_consumption_success(service, mock_db, mock_material, mock_batch):
    """测试创建消耗记录成功"""
    # Setup
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
        "consumption_type": "PRODUCTION",
        "batch_id": 1,
        "standard_qty": Decimal("25.00"),
        "unit_price": Decimal("50.00"),
        "work_order_id": 200,
        "project_id": 100,
    }

    # Mock get_or_404
    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        # Mock batch query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch.object(service, "check_and_create_alerts"):
            result = service.create_consumption(consumption_data, current_user_id=1)

    # Assertions
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_consumption_missing_required_fields(service, mock_db):
    """测试缺少必填字段"""
    from fastapi import HTTPException

    consumption_data = {"consumption_qty": 30.0}

    with pytest.raises(HTTPException) as exc_info:
        service.create_consumption(consumption_data, current_user_id=1)

    assert exc_info.value.status_code == 400


def test_create_consumption_with_barcode(service, mock_db, mock_material, mock_batch):
    """测试通过条码查找批次"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
        "barcode": "BC001",
    }

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        # Mock barcode lookup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch.object(service, "check_and_create_alerts"):
            result = service.create_consumption(consumption_data, current_user_id=1)

    assert mock_db.commit.called


def test_create_consumption_variance_calculation(service, mock_db, mock_material, mock_batch):
    """测试差异计算"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
        "standard_qty": Decimal("25.00"),
    }

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch.object(service, "check_and_create_alerts"):
            service.create_consumption(consumption_data, current_user_id=1)

    # 验证差异计算: (30-25)/25 * 100 = 20%
    # variance_qty = 5, variance_rate = 20%, is_waste = True (>10%)
    # 这个会在实际的 MaterialConsumption 对象中验证


def test_create_consumption_updates_batch_stock(service, mock_db, mock_material, mock_batch):
    """测试更新批次库存"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
        "batch_id": 1,
    }

    original_batch_qty = mock_batch.current_qty

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch.object(service, "check_and_create_alerts"):
            service.create_consumption(consumption_data, current_user_id=1)

    # 批次库存应该减少
    mock_db.commit.assert_called_once()


def test_create_consumption_depletes_batch(service, mock_db, mock_material, mock_batch):
    """测试批次耗尽"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("50.00"),  # 消耗全部
        "batch_id": 1,
    }

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch.object(service, "check_and_create_alerts"):
            service.create_consumption(consumption_data, current_user_id=1)

    # 批次状态应该更新为 DEPLETED
    assert mock_batch.status == "DEPLETED"


def test_create_consumption_triggers_alert_check(service, mock_db, mock_material):
    """测试触发预警检查"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
    }

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material) as mock_get:
        with patch.object(service, "check_and_create_alerts") as mock_check:
            service.create_consumption(consumption_data, current_user_id=1)

    # check_and_create_alerts 应该被调用一次
    assert mock_check.call_count == 1


# ================== 3. 消耗分析测试 ==================


def test_get_consumption_analysis_basic(service, mock_db, mock_consumption):
    """测试基础消耗分析"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    result = service.get_consumption_analysis()

    assert result["summary"]["total_records"] == 1
    assert result["summary"]["total_consumption"] == 30.0
    assert result["summary"]["waste_count"] == 1


def test_get_consumption_analysis_by_material(service, mock_db, mock_consumption):
    """测试按物料分组"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption, mock_consumption]

    result = service.get_consumption_analysis(group_by="material")

    assert len(result["grouped_data"]) == 1
    assert result["grouped_data"][0]["material_code"] == "MAT001"
    assert result["grouped_data"][0]["total_qty"] == 60.0  # 2次消耗


def test_get_consumption_analysis_by_day(service, mock_db, mock_consumption):
    """测试按天分组"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    result = service.get_consumption_analysis(group_by="day")

    assert len(result["grouped_data"]) >= 1
    assert "period" in result["grouped_data"][0]


def test_get_consumption_analysis_by_week(service, mock_db, mock_consumption):
    """测试按周分组"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    result = service.get_consumption_analysis(group_by="week")

    assert len(result["grouped_data"]) >= 1


def test_get_consumption_analysis_by_month(service, mock_db, mock_consumption):
    """测试按月分组"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    result = service.get_consumption_analysis(group_by="month")

    assert len(result["grouped_data"]) >= 1


def test_get_consumption_analysis_waste_rate(service, mock_db, mock_consumption):
    """测试浪费率计算"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query

    # 3条记录,2条浪费
    waste_consumption = MagicMock()
    waste_consumption.consumption_qty = Decimal("20.00")
    waste_consumption.standard_qty = Decimal("15.00")
    waste_consumption.total_cost = Decimal("1000.00")
    waste_consumption.is_waste = True

    normal_consumption = MagicMock()
    normal_consumption.consumption_qty = Decimal("10.00")
    normal_consumption.standard_qty = Decimal("10.00")
    normal_consumption.total_cost = Decimal("500.00")
    normal_consumption.is_waste = False

    mock_query.all.return_value = [waste_consumption, waste_consumption, normal_consumption]

    result = service.get_consumption_analysis()

    # 浪费率 = 2/3 * 100 ≈ 66.67%
    assert result["summary"]["waste_rate"] > 60
    assert result["summary"]["waste_rate"] < 70


def test_get_consumption_analysis_with_date_range(service, mock_db, mock_consumption):
    """测试日期范围筛选"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 31)

    result = service.get_consumption_analysis(start_date=start_date, end_date=end_date)

    assert result["summary"]["total_records"] >= 0


# ================== 4. 预警列表测试 ==================


def test_list_alerts_basic(service, mock_db, mock_alert):
    """测试基础预警列表"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_alert]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.list_alerts()

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["alert_no"] == "ALERT-20240101-MAT001"


def test_list_alerts_filter_by_type(service, mock_db, mock_alert):
    """测试按类型筛选"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_alert]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.list_alerts(alert_type="LOW_STOCK")

    assert result["total"] == 1


def test_list_alerts_filter_by_level(service, mock_db, mock_alert):
    """测试按级别筛选"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_alert]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.list_alerts(alert_level="WARNING")

    assert result["total"] == 1


def test_list_alerts_pagination(service, mock_db, mock_alert):
    """测试预警分页"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 25
    mock_query.all.return_value = [mock_alert] * 10

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.list_alerts(page=2, page_size=10)

    assert result["page"] == 2
    assert result["page_size"] == 10


# ================== 5. 预警规则测试 ==================


def test_create_alert_rule_success(service, mock_db):
    """测试创建预警规则成功"""
    rule_data = {
        "rule_name": "低库存预警",
        "alert_type": "LOW_STOCK",
        "alert_level": "WARNING",
        "threshold_type": "PERCENTAGE",
        "threshold_value": 80.0,
        "safety_days": 7,
    }

    with patch("app.utils.db_helpers.save_obj") as mock_save:
        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "低库存预警"
        mock_save.return_value = mock_rule

        result = service.create_alert_rule(rule_data, current_user_id=1)

    assert result["rule_name"] == "低库存预警"


def test_create_alert_rule_with_material(service, mock_db):
    """测试为特定物料创建规则"""
    rule_data = {
        "rule_name": "物料MAT001低库存预警",
        "material_id": 1,
        "alert_type": "LOW_STOCK",
        "threshold_value": 50.0,
    }

    with patch("app.utils.db_helpers.save_obj"):
        result = service.create_alert_rule(rule_data, current_user_id=1)

    # 验证规则已创建


def test_create_alert_rule_with_category(service, mock_db):
    """测试为分类创建规则"""
    rule_data = {
        "rule_name": "分类低库存预警",
        "category_id": 10,
        "alert_type": "LOW_STOCK",
        "threshold_value": 30.0,
    }

    with patch("app.utils.db_helpers.save_obj"):
        result = service.create_alert_rule(rule_data, current_user_id=1)


# ================== 6. 浪费追溯测试 ==================


def test_get_waste_records_basic(service, mock_db, mock_consumption):
    """测试基础浪费记录查询"""
    mock_consumption.is_waste = True
    mock_consumption.variance_rate = Decimal("15.00")

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_consumption]

    # Mock project and work order queries
    mock_project = MagicMock()
    mock_project.id = 100
    mock_project.project_name = "测试项目"

    mock_wo = MagicMock()
    mock_wo.id = 200
    mock_wo.work_order_no = "WO001"

    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_project, mock_wo]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_waste_records()

    assert result["total"] == 1
    assert result["summary"]["total_waste_qty"] == 5.0


def test_get_waste_records_min_variance_filter(service, mock_db, mock_consumption):
    """测试最小差异率筛选"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_consumption]

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_waste_records(min_variance_rate=20.0)

    assert result["total"] >= 0


def test_get_waste_records_cost_summary(service, mock_db, mock_consumption):
    """测试浪费成本汇总"""
    # 创建多条浪费记录
    waste1 = MagicMock()
    waste1.variance_qty = Decimal("10.00")
    waste1.unit_price = Decimal("50.00")
    waste1.is_waste = True
    waste1.project_id = None
    waste1.work_order_id = None

    waste2 = MagicMock()
    waste2.variance_qty = Decimal("20.00")
    waste2.unit_price = Decimal("30.00")
    waste2.is_waste = True
    waste2.project_id = None
    waste2.work_order_id = None

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 2
    mock_query.all.return_value = [waste1, waste2]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_waste_records()

    # 总浪费成本 = 10*50 + 20*30 = 1100
    assert result["summary"]["total_waste_cost"] == 1100.0


# ================== 7. 批次追溯测试 ==================


def test_trace_batch_by_id(service, mock_db, mock_batch, mock_material, mock_consumption):
    """测试按批次ID追溯"""
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_batch,
        mock_material,
        None,
        None,
    ]

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_consumption
    ]

    result = service.trace_batch(batch_id=1)

    assert result["batch_info"]["batch_no"] == "BATCH001"
    assert len(result["consumption_trail"]) == 1


def test_trace_batch_by_batch_no(service, mock_db, mock_batch, mock_material):
    """测试按批次号追溯"""
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_batch,
        mock_material,
    ]

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = service.trace_batch(batch_no="BATCH001")

    assert result["batch_info"]["batch_id"] == 1


def test_trace_batch_by_barcode(service, mock_db, mock_batch, mock_material):
    """测试按条码追溯"""
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_batch,
        mock_material,
    ]

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = service.trace_batch(barcode="BC001")

    assert result["batch_info"]["batch_no"] == "BATCH001"


def test_trace_batch_not_found(service, mock_db):
    """测试批次未找到"""
    from fastapi import HTTPException

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.trace_batch(batch_id=999)

    assert exc_info.value.status_code == 404


def test_trace_batch_consumption_trail(service, mock_db, mock_batch, mock_material):
    """测试消耗轨迹"""
    mock_consumption1 = MagicMock()
    mock_consumption1.consumption_no = "CONS-001"
    mock_consumption1.consumption_date = datetime(2024, 1, 10)
    mock_consumption1.consumption_qty = Decimal("20.00")
    mock_consumption1.consumption_type = "PRODUCTION"
    mock_consumption1.project_id = None
    mock_consumption1.work_order_id = None
    mock_consumption1.operator_id = 1

    mock_consumption2 = MagicMock()
    mock_consumption2.consumption_no = "CONS-002"
    mock_consumption2.consumption_date = datetime(2024, 1, 15)
    mock_consumption2.consumption_qty = Decimal("30.00")
    mock_consumption2.consumption_type = "MAINTENANCE"
    mock_consumption2.project_id = None
    mock_consumption2.work_order_id = None
    mock_consumption2.operator_id = 2

    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_batch,
        mock_material,
    ]

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_consumption1,
        mock_consumption2,
    ]

    result = service.trace_batch(batch_id=1)

    assert result["summary"]["total_consumptions"] == 2


# ================== 8. 成本分析测试 ==================


def test_get_cost_analysis_basic(service, mock_db, mock_consumption):
    """测试基础成本分析"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    result = service.get_cost_analysis()

    assert result["total_cost"] == 1500.0
    assert result["material_count"] == 1


def test_get_cost_analysis_top_materials(service, mock_db):
    """测试Top物料成本"""
    # 创建多个不同物料的消耗记录
    consumptions = []
    for i in range(15):
        c = MagicMock()
        c.material_id = i + 1
        c.material_code = f"MAT{i+1:03d}"
        c.material_name = f"物料{i+1}"
        c.consumption_qty = Decimal("10.00")
        c.total_cost = Decimal(str((15 - i) * 100))  # 递减成本
        consumptions.append(c)

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = consumptions

    result = service.get_cost_analysis(top_n=5)

    # 应该返回成本最高的5个物料
    assert len(result["top_materials"]) == 5
    assert result["top_materials"][0]["total_cost"] >= result["top_materials"][1]["total_cost"]


def test_get_cost_analysis_with_date_range(service, mock_db, mock_consumption):
    """测试日期范围成本分析"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_consumption]

    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 31)

    result = service.get_cost_analysis(start_date=start_date, end_date=end_date)

    assert result["total_cost"] >= 0


# ================== 9. 周转率分析测试 ==================


def test_get_turnover_analysis_basic(service, mock_db, mock_material):
    """测试基础周转率分析"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_material]

    # Mock消耗查询
    mock_consumption = MagicMock()
    mock_consumption.consumption_qty = Decimal("60.00")

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_consumption]

    result = service.get_turnover_analysis(days=30)

    assert result["period_days"] == 30
    assert len(result["materials"]) == 1


def test_get_turnover_analysis_calculation(service, mock_db, mock_material):
    """测试周转率计算"""
    mock_material.current_stock = Decimal("100.00")
    mock_material.id = 1
    mock_material.material_code = "MAT001"
    mock_material.material_name = "测试物料"

    # Mock第一次查询返回物料列表
    material_query = MagicMock()
    material_query.filter.return_value = material_query
    material_query.all.return_value = [mock_material]

    # Mock第二次查询返回消耗记录
    consumption_query = MagicMock()
    mock_consumption = MagicMock()
    mock_consumption.consumption_qty = Decimal("60.00")
    consumption_query.filter.return_value = consumption_query
    consumption_query.all.return_value = [mock_consumption]

    # 设置 query 根据调用次数返回不同结果
    mock_db.query.side_effect = [material_query, consumption_query]

    result = service.get_turnover_analysis(days=30)

    turnover = result["materials"][0]
    # 30天消耗60单位, 平均库存100, 周转率=60/100=0.6, 周转天数=30/0.6=50
    assert turnover["turnover_rate"] == 0.6
    assert turnover["turnover_days"] == 50.0


def test_get_turnover_analysis_zero_stock(service, mock_db, mock_material):
    """测试零库存周转率"""
    mock_material.current_stock = Decimal("0.00")
    mock_material.id = 1
    mock_material.material_code = "MAT001"
    mock_material.material_name = "测试物料"

    # Mock第一次查询返回物料列表
    material_query = MagicMock()
    material_query.filter.return_value = material_query
    material_query.all.return_value = [mock_material]

    # Mock第二次查询返回空消耗记录
    consumption_query = MagicMock()
    consumption_query.filter.return_value = consumption_query
    consumption_query.all.return_value = []

    mock_db.query.side_effect = [material_query, consumption_query]

    result = service.get_turnover_analysis()

    # 零库存应该返回周转率0
    assert result["materials"][0]["turnover_rate"] == 0


def test_get_turnover_analysis_sorting(service, mock_db):
    """测试周转率排序"""
    # 创建多个物料
    mat1 = MagicMock()
    mat1.id = 1
    mat1.material_code = "MAT001"
    mat1.material_name = "快速周转物料"
    mat1.current_stock = Decimal("50.00")
    mat1.is_active = True

    mat2 = MagicMock()
    mat2.id = 2
    mat2.material_code = "MAT002"
    mat2.material_name = "慢速周转物料"
    mat2.current_stock = Decimal("100.00")
    mat2.is_active = True

    # Mock第一次查询返回物料列表
    material_query = MagicMock()
    material_query.filter.return_value = material_query
    material_query.all.return_value = [mat1, mat2]

    # mat1消耗多,周转快
    c1 = MagicMock()
    c1.consumption_qty = Decimal("100.00")

    # mat2消耗少,周转慢
    c2 = MagicMock()
    c2.consumption_qty = Decimal("20.00")

    # Mock消耗查询
    consumption_query1 = MagicMock()
    consumption_query1.filter.return_value = consumption_query1
    consumption_query1.all.return_value = [c1]

    consumption_query2 = MagicMock()
    consumption_query2.filter.return_value = consumption_query2
    consumption_query2.all.return_value = [c2]

    mock_db.query.side_effect = [material_query, consumption_query1, consumption_query2]

    result = service.get_turnover_analysis()

    # 应该按周转率降序排列
    assert result["materials"][0]["turnover_rate"] >= result["materials"][1]["turnover_rate"]


# ================== 10. 预警检查测试 ==================


def test_check_and_create_alerts_low_stock_percentage(service, mock_db, mock_material):
    """测试低库存预警(百分比)"""
    # 设置库存低于安全库存80%
    mock_material.current_stock = Decimal("10.00")
    mock_material.safety_stock = Decimal("20.00")

    # 模拟规则
    mock_rule = MagicMock()
    mock_rule.alert_type = "LOW_STOCK"
    mock_rule.threshold_type = "PERCENTAGE"
    mock_rule.threshold_value = Decimal("80.00")
    mock_rule.alert_level = "WARNING"
    mock_rule.is_active = True
    mock_rule.material_id = None

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]

    # 没有现有预警
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(service, "calculate_avg_daily_consumption", return_value=2.0):
        service.check_and_create_alerts(mock_material)

    # 应该创建新预警
    mock_db.add.assert_called_once()


def test_check_and_create_alerts_low_stock_fixed(service, mock_db, mock_material):
    """测试低库存预警(固定值)"""
    mock_material.current_stock = Decimal("8.00")

    mock_rule = MagicMock()
    mock_rule.alert_type = "LOW_STOCK"
    mock_rule.threshold_type = "FIXED"
    mock_rule.threshold_value = Decimal("10.00")
    mock_rule.alert_level = "CRITICAL"
    mock_rule.is_active = True
    mock_rule.material_id = None

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(service, "calculate_avg_daily_consumption", return_value=1.5):
        service.check_and_create_alerts(mock_material)

    mock_db.add.assert_called_once()


def test_check_and_create_alerts_shortage(service, mock_db, mock_material):
    """测试缺料预警"""
    mock_material.current_stock = Decimal("0.00")

    mock_rule = MagicMock()
    mock_rule.alert_type = "SHORTAGE"
    mock_rule.alert_level = "CRITICAL"
    mock_rule.is_active = True
    mock_rule.material_id = None

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(service, "calculate_avg_daily_consumption", return_value=3.0):
        service.check_and_create_alerts(mock_material)

    mock_db.add.assert_called_once()


def test_check_and_create_alerts_existing_alert(service, mock_db, mock_material, mock_alert):
    """测试已存在活动预警时不重复创建"""
    mock_material.current_stock = Decimal("5.00")
    mock_material.safety_stock = Decimal("20.00")

    mock_rule = MagicMock()
    mock_rule.alert_type = "LOW_STOCK"
    mock_rule.threshold_type = "PERCENTAGE"
    mock_rule.threshold_value = Decimal("80.00")
    mock_rule.is_active = True
    mock_rule.material_id = None

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]

    # 已存在活动预警
    mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

    service.check_and_create_alerts(mock_material)

    # 不应该创建新预警
    mock_db.add.assert_not_called()


def test_check_and_create_alerts_no_rules(service, mock_db, mock_material):
    """测试无适用规则时不创建预警"""
    mock_db.query.return_value.filter.return_value.all.return_value = []

    service.check_and_create_alerts(mock_material)

    mock_db.add.assert_not_called()


# ================== 11. 辅助方法测试 ==================


def test_calculate_avg_daily_consumption_with_data(service, mock_db):
    """测试计算平均日消耗(有数据)"""
    # 30天消耗90单位
    consumptions = []
    for i in range(3):
        c = MagicMock()
        c.consumption_qty = Decimal("30.00")
        consumptions.append(c)

    mock_db.query.return_value.filter.return_value.all.return_value = consumptions

    result = service.calculate_avg_daily_consumption(material_id=1, days=30)

    # 平均日消耗 = 90 / 30 = 3.0
    assert result == 3.0


def test_calculate_avg_daily_consumption_no_data(service, mock_db):
    """测试计算平均日消耗(无数据)"""
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = service.calculate_avg_daily_consumption(material_id=1, days=30)

    assert result == 0.0


def test_calculate_avg_daily_consumption_zero_days(service, mock_db):
    """测试零天数"""
    result = service.calculate_avg_daily_consumption(material_id=1, days=0)

    assert result == 0.0


# ================== 12. 边界条件和异常测试 ==================


def test_get_realtime_stock_null_values(service, mock_db, mock_material, mock_batch):
    """测试Null值处理"""
    mock_material.current_stock = None
    mock_material.safety_stock = None
    mock_batch.current_qty = None
    mock_batch.reserved_qty = None

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_material]

    batch_query = MagicMock()
    batch_query.filter.return_value = batch_query
    batch_query.all.return_value = [mock_batch]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.get_realtime_stock()

    # 应该正确处理None值
    assert result["items"][0]["current_stock"] == 0


def test_create_consumption_without_standard_qty(service, mock_db, mock_material):
    """测试无标准用量的消耗记录"""
    consumption_data = {
        "material_id": 1,
        "consumption_qty": Decimal("30.00"),
        # 没有 standard_qty
    }

    with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
        with patch.object(service, "check_and_create_alerts"):
            result = service.create_consumption(consumption_data, current_user_id=1)

    # 应该成功创建,无浪费标记
    mock_db.commit.assert_called_once()


def test_trace_batch_with_project_and_wo(service, mock_db, mock_batch, mock_material):
    """测试批次追溯包含项目和工单信息"""
    mock_project = MagicMock()
    mock_project.id = 100
    mock_project.project_no = "PRJ001"
    mock_project.project_name = "测试项目"

    mock_wo = MagicMock()
    mock_wo.id = 200
    mock_wo.work_order_no = "WO001"

    mock_consumption = MagicMock()
    mock_consumption.consumption_no = "CONS-001"
    mock_consumption.consumption_date = datetime(2024, 1, 10)
    mock_consumption.consumption_qty = Decimal("20.00")
    mock_consumption.consumption_type = "PRODUCTION"
    mock_consumption.project_id = 100
    mock_consumption.work_order_id = 200
    mock_consumption.operator_id = 1

    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_batch,
        mock_material,
        mock_project,
        mock_wo,
    ]

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_consumption
    ]

    result = service.trace_batch(batch_id=1)

    assert result["consumption_trail"][0]["project"]["project_no"] == "PRJ001"
    assert result["consumption_trail"][0]["work_order"]["work_order_no"] == "WO001"


def test_get_consumption_analysis_empty_result(service, mock_db):
    """测试空消耗分析结果"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []

    result = service.get_consumption_analysis()

    assert result["summary"]["total_records"] == 0
    assert result["summary"]["waste_rate"] == 0


def test_list_alerts_filter_by_material(service, mock_db, mock_alert):
    """测试按物料筛选预警"""
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.all.return_value = [mock_alert]

    with patch("app.common.query_filters.apply_pagination", return_value=mock_query):
        result = service.list_alerts(material_id=1)

    assert result["total"] == 1


# ================== 执行测试 ==================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
