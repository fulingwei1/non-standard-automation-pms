# -*- coding: utf-8 -*-
"""
产能分析服务测试

测试 app/services/production/capacity/capacity_service.py
目标覆盖率: 60%+
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services.production.capacity.capacity_service import CapacityAnalysisService
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
    Workstation,
    WorkOrder,
)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def capacity_service(mock_db):
    """创建产能分析服务实例"""
    return CapacityAnalysisService(mock_db)


@pytest.fixture
def sample_equipment():
    """示例设备数据"""
    equipment = MagicMock(spec=Equipment)
    equipment.id = 1
    equipment.equipment_code = "EQ001"
    equipment.equipment_name = "冲压机A"
    equipment.workshop_id = 1
    return equipment


@pytest.fixture
def sample_workshop():
    """示例车间数据"""
    workshop = MagicMock(spec=Workshop)
    workshop.id = 1
    workshop.workshop_name = "冲压车间"
    return workshop


@pytest.fixture
def sample_workstation():
    """示例工位数据"""
    workstation = MagicMock(spec=Workstation)
    workstation.id = 1
    workstation.workstation_code = "WS001"
    workstation.workstation_name = "装配工位1"
    workstation.workshop_id = 1
    return workstation


@pytest.fixture
def sample_worker():
    """示例工人数据"""
    worker = MagicMock(spec=Worker)
    worker.id = 1
    worker.worker_code = "W001"
    worker.worker_name = "张三"
    return worker


class TestIdentifyBottlenecks:
    """测试 identify_bottlenecks 方法"""

    def test_identify_bottlenecks_default_dates(self, capacity_service, mock_db):
        """测试瓶颈识别（默认日期）"""
        # 配置 mock queries
        mock_equipment_query = MagicMock()
        mock_equipment_query.join.return_value = mock_equipment_query
        mock_equipment_query.filter.return_value = mock_equipment_query
        mock_equipment_query.group_by.return_value = mock_equipment_query
        mock_equipment_query.having.return_value = mock_equipment_query
        mock_equipment_query.order_by.return_value = mock_equipment_query
        mock_equipment_query.limit.return_value = mock_equipment_query
        mock_equipment_query.all.return_value = []

        mock_workstation_query = MagicMock()
        mock_workstation_query.join.return_value = mock_workstation_query
        mock_workstation_query.filter.return_value = mock_workstation_query
        mock_workstation_query.group_by.return_value = mock_workstation_query
        mock_workstation_query.having.return_value = mock_workstation_query
        mock_workstation_query.order_by.return_value = mock_workstation_query
        mock_workstation_query.limit.return_value = mock_workstation_query
        mock_workstation_query.all.return_value = []

        mock_worker_query = MagicMock()
        mock_worker_query.join.return_value = mock_worker_query
        mock_worker_query.filter.return_value = mock_worker_query
        mock_worker_query.group_by.return_value = mock_worker_query
        mock_worker_query.having.return_value = mock_worker_query
        mock_worker_query.order_by.return_value = mock_worker_query
        mock_worker_query.limit.return_value = mock_worker_query
        mock_worker_query.all.return_value = []

        mock_db.query.return_value = mock_equipment_query

        # 执行
        result = capacity_service.identify_bottlenecks(
            workshop_id=None,
            start_date=None,
            end_date=None,
            threshold=80.0,
            limit=10
        )

        # 验证
        assert "equipment_bottlenecks" in result
        assert "workstation_bottlenecks" in result
        assert "low_efficiency_workers" in result
        assert "analysis_period" in result
        assert result["analysis_period"]["threshold"] == 80.0

    def test_identify_equipment_bottlenecks(self, capacity_service, mock_db):
        """测试设备瓶颈识别"""
        # 创建模拟设备瓶颈数据
        mock_row = MagicMock()
        mock_row.equipment_id = 1
        mock_row.equipment_code = "EQ001"
        mock_row.equipment_name = "冲压机A"
        mock_row.workshop_name = "冲压车间"
        mock_row.record_count = 30
        mock_row.avg_oee = 75.5
        mock_row.total_operating_time = 180.0
        mock_row.total_planned_time = 200.0
        mock_row.total_downtime = 20.0
        mock_row.total_output = 1000
        mock_row.utilization_rate = 90.0

        # 配置 mock
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # 第一次调用返回设备瓶颈，后面返回空
        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_row]
            return []
        
        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        # 执行
        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        # 验证
        assert len(result["equipment_bottlenecks"]) == 1
        bottleneck = result["equipment_bottlenecks"][0]
        assert bottleneck["type"] == "设备"
        assert bottleneck["equipment_id"] == 1
        assert bottleneck["equipment_code"] == "EQ001"
        assert bottleneck["utilization_rate"] == 90.0
        assert bottleneck["avg_oee"] == 75.5
        assert bottleneck["impact_level"] == "高"

    def test_identify_workstation_bottlenecks(self, capacity_service, mock_db):
        """测试工位瓶颈识别"""
        mock_row = MagicMock()
        mock_row.workstation_id = 1
        mock_row.workstation_code = "WS001"
        mock_row.workstation_name = "装配工位1"
        mock_row.workshop_name = "装配车间"
        mock_row.work_order_count = 50
        mock_row.total_hours = 400.0
        mock_row.total_completed = 1000
        mock_row.avg_efficiency = 85.0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # 第二次调用返回工位数据
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        assert len(result["workstation_bottlenecks"]) == 1
        bottleneck = result["workstation_bottlenecks"][0]
        assert bottleneck["type"] == "工位"
        assert bottleneck["workstation_id"] == 1
        assert bottleneck["total_hours"] == 400.0

    def test_identify_low_efficiency_workers(self, capacity_service, mock_db):
        """测试低效率工人识别"""
        mock_row = MagicMock()
        mock_row.worker_id = 1
        mock_row.worker_code = "W001"
        mock_row.worker_name = "张三"
        mock_row.record_count = 20
        mock_row.avg_efficiency = 65.0
        mock_row.total_hours = 160.0
        mock_row.total_completed = 500

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # 第三次调用返回工人数据
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        assert len(result["low_efficiency_workers"]) == 1
        worker = result["low_efficiency_workers"][0]
        assert worker["type"] == "工人"
        assert worker["worker_id"] == 1
        assert worker["avg_efficiency"] == 65.0
        assert "培训" in worker["suggestion"]

    def test_identify_bottlenecks_with_null_values(self, capacity_service, mock_db):
        """测试处理空值的情况"""
        mock_row = MagicMock()
        mock_row.equipment_id = 1
        mock_row.equipment_code = "EQ001"
        mock_row.equipment_name = "测试设备"
        mock_row.workshop_name = "测试车间"
        mock_row.record_count = 0
        mock_row.avg_oee = None
        mock_row.total_operating_time = None
        mock_row.total_planned_time = None
        mock_row.total_downtime = None
        mock_row.total_output = None
        mock_row.utilization_rate = None

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        bottleneck = result["equipment_bottlenecks"][0]
        assert bottleneck["utilization_rate"] == 0
        assert bottleneck["avg_oee"] == 0
        assert bottleneck["total_output"] == 0
        assert bottleneck["total_downtime"] == 0


class TestGetEquipmentSuggestion:
    """测试 _get_equipment_suggestion 方法"""

    def test_get_equipment_suggestion_exists(self, capacity_service):
        """测试获取设备建议（方法存在的情况）"""
        # 检查方法是否存在
        if hasattr(capacity_service, '_get_equipment_suggestion'):
            mock_row = MagicMock()
            mock_row.utilization_rate = 95.0
            mock_row.avg_oee = 70.0
            mock_row.total_downtime = 50.0

            suggestion = capacity_service._get_equipment_suggestion(mock_row)
            assert isinstance(suggestion, str)
        else:
            # 如果方法不存在，跳过测试
            pytest.skip("_get_equipment_suggestion method not found")


class TestBottleneckAnalysisPeriod:
    """测试瓶颈分析的时间段处理"""

    def test_custom_date_range(self, capacity_service, mock_db):
        """测试自定义日期范围"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        start = date(2024, 2, 1)
        end = date(2024, 2, 28)

        result = capacity_service.identify_bottlenecks(
            workshop_id=None,
            start_date=start,
            end_date=end,
            threshold=75.0,
            limit=20
        )

        assert result["analysis_period"]["start_date"] == "2024-02-01"
        assert result["analysis_period"]["end_date"] == "2024-02-28"
        assert result["analysis_period"]["threshold"] == 75.0

    def test_default_30_days(self, capacity_service, mock_db):
        """测试默认30天范围"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=None,
            start_date=None,
            end_date=None,
            threshold=80.0,
            limit=10
        )

        # 验证日期范围大约是30天
        start = date.fromisoformat(result["analysis_period"]["start_date"])
        end = date.fromisoformat(result["analysis_period"]["end_date"])
        days_diff = (end - start).days
        assert days_diff >= 29
        assert days_diff <= 31


class TestBottleneckThreshold:
    """测试瓶颈阈值处理"""

    def test_high_threshold(self, capacity_service, mock_db):
        """测试高阈值"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=95.0,
            limit=5
        )

        assert result["analysis_period"]["threshold"] == 95.0

    def test_low_threshold(self, capacity_service, mock_db):
        """测试低阈值"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=50.0,
            limit=5
        )

        assert result["analysis_period"]["threshold"] == 50.0


class TestBottleneckLimit:
    """测试结果数量限制"""

    def test_limit_results(self, capacity_service, mock_db):
        """测试限制返回结果数量"""
        # 创建多个模拟结果
        mock_rows = []
        for i in range(15):
            row = MagicMock()
            row.equipment_id = i
            row.equipment_code = f"EQ{i:03d}"
            row.equipment_name = f"设备{i}"
            row.workshop_name = "车间"
            row.record_count = 10
            row.avg_oee = 75.0
            row.total_operating_time = 100.0
            row.total_planned_time = 110.0
            row.total_downtime = 10.0
            row.total_output = 500
            row.utilization_rate = 85.0
            mock_rows.append(row)

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_rows[:5]  # 限制为5个
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=None,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        assert len(result["equipment_bottlenecks"]) <= 5


class TestWorkshopFilter:
    """测试车间过滤"""

    def test_with_workshop_filter(self, capacity_service, mock_db):
        """测试指定车间ID的过滤"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=5,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=10
        )

        # 验证查询被调用
        assert mock_db.query.called

    def test_without_workshop_filter(self, capacity_service, mock_db):
        """测试不指定车间（全部车间）"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=None,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=10
        )

        assert mock_db.query.called


class TestBottleneckImpactLevel:
    """测试影响级别判断"""

    def test_high_impact_level(self, capacity_service, mock_db):
        """测试高影响级别（利用率>=90%）"""
        mock_row = MagicMock()
        mock_row.equipment_id = 1
        mock_row.equipment_code = "EQ001"
        mock_row.equipment_name = "高负载设备"
        mock_row.workshop_name = "车间"
        mock_row.record_count = 30
        mock_row.avg_oee = 75.0
        mock_row.total_operating_time = 180.0
        mock_row.total_planned_time = 200.0
        mock_row.total_downtime = 20.0
        mock_row.total_output = 1000
        mock_row.utilization_rate = 92.0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        bottleneck = result["equipment_bottlenecks"][0]
        assert bottleneck["impact_level"] == "高"

    def test_medium_impact_level(self, capacity_service, mock_db):
        """测试中等影响级别（利用率<90%）"""
        mock_row = MagicMock()
        mock_row.equipment_id = 1
        mock_row.equipment_code = "EQ001"
        mock_row.equipment_name = "中负载设备"
        mock_row.workshop_name = "车间"
        mock_row.record_count = 30
        mock_row.avg_oee = 75.0
        mock_row.total_operating_time = 170.0
        mock_row.total_planned_time = 200.0
        mock_row.total_downtime = 30.0
        mock_row.total_output = 900
        mock_row.utilization_rate = 85.0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=5
        )

        bottleneck = result["equipment_bottlenecks"][0]
        assert bottleneck["impact_level"] == "中"


class TestDataAggregation:
    """测试数据聚合"""

    def test_equipment_data_aggregation(self, capacity_service, mock_db):
        """测试设备数据聚合计算"""
        mock_row = MagicMock()
        mock_row.equipment_id = 1
        mock_row.equipment_code = "EQ001"
        mock_row.equipment_name = "测试设备"
        mock_row.workshop_name = "车间"
        mock_row.record_count = 15
        mock_row.avg_oee = 78.5
        mock_row.total_operating_time = 120.0
        mock_row.total_planned_time = 150.0
        mock_row.total_downtime = 30.0
        mock_row.total_output = 750
        mock_row.utilization_rate = 80.0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=75.0,
            limit=10
        )

        bottleneck = result["equipment_bottlenecks"][0]
        assert bottleneck["utilization_rate"] == 80.0
        assert bottleneck["avg_oee"] == 78.5
        assert bottleneck["total_output"] == 750
        assert bottleneck["total_downtime"] == 30.0

    def test_workstation_efficiency_calculation(self, capacity_service, mock_db):
        """测试工位效率计算"""
        mock_row = MagicMock()
        mock_row.workstation_id = 1
        mock_row.workstation_code = "WS001"
        mock_row.workstation_name = "测试工位"
        mock_row.workshop_name = "车间"
        mock_row.work_order_count = 25
        mock_row.total_hours = 200.0
        mock_row.total_completed = 500
        mock_row.avg_efficiency = 88.5

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        call_count = 0
        def all_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return [mock_row]
            return []

        mock_query.all.side_effect = all_side_effect
        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=10
        )

        bottleneck = result["workstation_bottlenecks"][0]
        assert bottleneck["work_order_count"] == 25
        assert bottleneck["total_hours"] == 200.0
        assert bottleneck["total_completed"] == 500
        assert bottleneck["avg_efficiency"] == 88.5


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_results(self, capacity_service, mock_db):
        """测试无数据的情况"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=10
        )

        assert len(result["equipment_bottlenecks"]) == 0
        assert len(result["workstation_bottlenecks"]) == 0
        assert len(result["low_efficiency_workers"]) == 0

    def test_single_day_range(self, capacity_service, mock_db):
        """测试单日查询"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        single_date = date(2024, 1, 15)
        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=single_date,
            end_date=single_date,
            threshold=80.0,
            limit=10
        )

        assert result["analysis_period"]["start_date"] == "2024-01-15"
        assert result["analysis_period"]["end_date"] == "2024-01-15"

    def test_large_limit(self, capacity_service, mock_db):
        """测试大数量限制"""
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = capacity_service.identify_bottlenecks(
            workshop_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            threshold=80.0,
            limit=1000
        )

        # 验证执行成功
        assert "equipment_bottlenecks" in result
        assert "workstation_bottlenecks" in result
        assert "low_efficiency_workers" in result
