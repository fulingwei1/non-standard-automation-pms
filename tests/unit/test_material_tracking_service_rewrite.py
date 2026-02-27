# -*- coding: utf-8 -*-
"""
物料跟踪服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 让业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.production.material_tracking.material_tracking_service import (
    MaterialTrackingService,
)


class TestMaterialTrackingServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init(self):
        """测试服务初始化"""
        db_mock = MagicMock()
        service = MaterialTrackingService(db_mock)
        self.assertEqual(service.db, db_mock)


class TestGetRealtimeStock(unittest.TestCase):
    """测试实时库存查询"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_get_realtime_stock_basic(self):
        """测试基本库存查询"""
        # 准备mock数据
        material1 = MagicMock()
        material1.id = 1
        material1.material_code = "MAT001"
        material1.material_name = "铝板"
        material1.specification = "5mm"
        material1.unit = "张"
        material1.current_stock = Decimal("100")
        material1.safety_stock = Decimal("20")
        material1.is_active = True

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        # Mock the slice operation that apply_pagination uses
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [material1]

        self.db_mock.query.return_value = query_mock

        # 批次查询mock
        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.all.return_value = []

        # 每次db.query调用返回不同mock
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Material查询
                return query_mock
            else:  # MaterialBatch查询
                return batch_query_mock

        self.db_mock.query.side_effect = query_side_effect

        # 调用方法
        result = self.service.get_realtime_stock(page=1, page_size=20)

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["page"], 1)
        self.assertEqual(len(result["items"]), 1)

        item = result["items"][0]
        self.assertEqual(item["material_id"], 1)
        self.assertEqual(item["material_code"], "MAT001")
        self.assertEqual(item["material_name"], "铝板")
        self.assertEqual(item["current_stock"], 100)
        self.assertEqual(item["safety_stock"], 20)
        self.assertEqual(item["available_stock"], 100)
        self.assertEqual(item["reserved_stock"], 0)
        self.assertFalse(item["is_low_stock"])  # 100 >= 20, not low stock
        self.assertEqual(item["batch_count"], 0)

    def test_get_realtime_stock_with_batches(self):
        """测试带批次的库存查询"""
        # 准备物料mock
        material1 = MagicMock()
        material1.id = 1
        material1.material_code = "MAT001"
        material1.material_name = "铝板"
        material1.specification = "5mm"
        material1.unit = "张"
        material1.current_stock = Decimal("100")
        material1.safety_stock = Decimal("20")

        # 准备批次mock
        batch1 = MagicMock()
        batch1.batch_no = "BATCH001"
        batch1.current_qty = Decimal("60")
        batch1.reserved_qty = Decimal("10")
        batch1.warehouse_location = "A区01架"
        batch1.production_date = date(2024, 1, 1)
        batch1.expire_date = date(2025, 1, 1)
        batch1.quality_status = "QUALIFIED"

        batch2 = MagicMock()
        batch2.batch_no = "BATCH002"
        batch2.current_qty = Decimal("40")
        batch2.reserved_qty = Decimal("5")
        batch2.warehouse_location = "A区02架"
        batch2.production_date = date(2024, 2, 1)
        batch2.expire_date = date(2025, 2, 1)
        batch2.quality_status = "QUALIFIED"

        # Mock Material查询
        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.count.return_value = 1
        material_query_mock.offset.return_value = material_query_mock
        material_query_mock.limit.return_value = material_query_mock
        material_query_mock.all.return_value = [material1]

        # Mock MaterialBatch查询
        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.all.return_value = [batch1, batch2]

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return material_query_mock
            else:
                return batch_query_mock

        self.db_mock.query.side_effect = query_side_effect

        # 调用方法
        result = self.service.get_realtime_stock(page=1, page_size=20)

        # 验证
        item = result["items"][0]
        self.assertEqual(item["batch_count"], 2)
        self.assertEqual(item["reserved_stock"], 15)  # 10 + 5
        self.assertEqual(item["available_stock"], 85)  # 100 - 15
        self.assertEqual(len(item["batches"]), 2)

        batch = item["batches"][0]
        self.assertEqual(batch["batch_no"], "BATCH001")
        self.assertEqual(batch["current_qty"], 60)
        self.assertEqual(batch["reserved_qty"], 10)
        self.assertEqual(batch["available_qty"], 50)

    def test_get_realtime_stock_with_filters(self):
        """测试带筛选条件的库存查询"""
        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.count.return_value = 0
        material_query_mock.all.return_value = []

        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.all.return_value = []

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return material_query_mock
            else:
                return batch_query_mock

        self.db_mock.query.side_effect = query_side_effect

        # 带各种筛选条件
        result = self.service.get_realtime_stock(
            material_id=1,
            material_code="MAT001",
            category_id=2,
            warehouse_location="A区",
            status="ACTIVE",
            low_stock_only=True,
            page=1,
            page_size=10
        )

        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["items"]), 0)


class TestCreateConsumption(unittest.TestCase):
    """测试物料消耗记录"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_create_consumption_basic(self):
        """测试基本消耗记录"""
        # 准备物料mock
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.unit = "张"
        material.standard_price = Decimal("100")
        material.current_stock = Decimal("100")

        # Mock get_or_404
        with patch('app.services.production.material_tracking.material_tracking_service.get_or_404') as mock_get_or_404:
            mock_get_or_404.return_value = material

            captured_consumption = None

            # Mock db.add to capture the consumption object
            def mock_add(obj):
                nonlocal captured_consumption
                captured_consumption = obj
                # Set id after add
                obj.id = 1

            self.db_mock.add.side_effect = mock_add

            # 准备消耗数据
            consumption_data = {
                "material_id": 1,
                "consumption_qty": Decimal("10"),
                "consumption_type": "PRODUCTION",
            }

            # 调用方法
            result = self.service.create_consumption(consumption_data, current_user_id=1)

            # 验证db操作
            self.db_mock.add.assert_called_once()
            self.db_mock.commit.assert_called_once()
            self.db_mock.refresh.assert_called_once()

            # 验证物料库存更新
            self.assertEqual(material.current_stock, Decimal("90"))  # 100 - 10

            # 验证返回值
            self.assertIn("CONS-", result.get("consumption_no", ""))
            self.assertEqual(result.get("material_code"), "MAT001")

    def test_create_consumption_with_barcode(self):
        """测试通过条码查找批次"""
        # 准备物料
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.unit = "张"
        material.standard_price = Decimal("100")
        material.current_stock = Decimal("100")

        # 准备批次
        batch = MagicMock()
        batch.id = 10
        batch.barcode = "BARCODE123"
        batch.material_id = 1
        batch.current_qty = Decimal("50")
        batch.consumed_qty = Decimal("0")

        # Mock查询
        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.first.return_value = batch

        self.db_mock.query.return_value = batch_query_mock

        with patch('app.services.production.material_tracking.material_tracking_service.get_or_404') as mock_get_or_404:
            mock_get_or_404.return_value = material

            consumption_data = {
                "material_id": 1,
                "consumption_qty": Decimal("10"),
                "barcode": "BARCODE123",
            }

            result = self.service.create_consumption(consumption_data, current_user_id=1)

            # 验证批次库存更新
            self.assertEqual(batch.current_qty, Decimal("40"))  # 50 - 10
            self.assertEqual(batch.consumed_qty, Decimal("10"))  # 0 + 10

    def test_create_consumption_with_variance(self):
        """测试带差异的消耗记录（浪费识别）"""
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.unit = "张"
        material.standard_price = Decimal("100")
        material.current_stock = Decimal("100")

        with patch('app.services.production.material_tracking.material_tracking_service.get_or_404') as mock_get_or_404:
            mock_get_or_404.return_value = material

            # 实际消耗15，标准10，差异50%，应标记为浪费
            consumption_data = {
                "material_id": 1,
                "consumption_qty": Decimal("15"),
                "standard_qty": Decimal("10"),
            }

            result = self.service.create_consumption(consumption_data, current_user_id=1)

            # 验证浪费标记
            self.assertTrue(result["is_waste"])  # 差异率50% > 10%
            self.assertEqual(result["variance_rate"], 50.0)

    def test_create_consumption_batch_depleted(self):
        """测试批次耗尽"""
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.unit = "张"
        material.standard_price = Decimal("100")
        material.current_stock = Decimal("100")

        batch = MagicMock()
        batch.id = 10
        batch.current_qty = Decimal("10")
        batch.consumed_qty = Decimal("0")
        batch.status = "ACTIVE"

        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.first.return_value = batch

        self.db_mock.query.return_value = batch_query_mock

        with patch('app.services.production.material_tracking.material_tracking_service.get_or_404') as mock_get_or_404:
            mock_get_or_404.return_value = material

            consumption_data = {
                "material_id": 1,
                "consumption_qty": Decimal("10"),
                "batch_id": 10,
            }

            self.service.create_consumption(consumption_data, current_user_id=1)

            # 验证批次状态更新为耗尽
            self.assertEqual(batch.status, "DEPLETED")
            self.assertEqual(batch.current_qty, Decimal("0"))

    def test_create_consumption_missing_required_fields(self):
        """测试缺少必填字段"""
        from fastapi import HTTPException

        consumption_data = {
            "material_id": 1,
            # 缺少 consumption_qty
        }

        with self.assertRaises(HTTPException) as context:
            self.service.create_consumption(consumption_data, current_user_id=1)

        self.assertEqual(context.exception.status_code, 400)


class TestGetConsumptionAnalysis(unittest.TestCase):
    """测试消耗分析"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_get_consumption_analysis_basic(self):
        """测试基本消耗分析"""
        # 准备消耗记录mock
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("10")
        consumption1.total_cost = Decimal("1000")
        consumption1.standard_qty = Decimal("9")
        consumption1.is_waste = False
        consumption1.material_code = "MAT001"
        consumption1.material_name = "铝板"
        consumption1.consumption_date = datetime(2024, 1, 1)

        consumption2 = MagicMock()
        consumption2.consumption_qty = Decimal("20")
        consumption2.total_cost = Decimal("2000")
        consumption2.standard_qty = Decimal("15")
        consumption2.is_waste = True
        consumption2.material_code = "MAT002"
        consumption2.material_name = "钢板"
        consumption2.consumption_date = datetime(2024, 1, 2)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1, consumption2]

        self.db_mock.query.return_value = query_mock

        # 调用方法
        result = self.service.get_consumption_analysis(group_by="day")

        # 验证汇总数据
        summary = result["summary"]
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["total_consumption"], 30)
        self.assertEqual(summary["total_cost"], 3000)
        self.assertEqual(summary["total_standard"], 24)
        self.assertEqual(summary["waste_count"], 1)
        self.assertEqual(summary["waste_rate"], 50.0)  # 1/2 * 100

    def test_get_consumption_analysis_group_by_material(self):
        """测试按物料分组"""
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("10")
        consumption1.total_cost = Decimal("1000")
        consumption1.standard_qty = Decimal("9")
        consumption1.is_waste = False
        consumption1.material_code = "MAT001"
        consumption1.material_name = "铝板"

        consumption2 = MagicMock()
        consumption2.consumption_qty = Decimal("5")
        consumption2.total_cost = Decimal("500")
        consumption2.standard_qty = Decimal("5")
        consumption2.is_waste = True
        consumption2.material_code = "MAT001"
        consumption2.material_name = "铝板"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1, consumption2]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_consumption_analysis(group_by="material")

        # 验证分组数据
        grouped = result["grouped_data"]
        self.assertEqual(len(grouped), 1)
        
        group = grouped[0]
        self.assertEqual(group["material_code"], "MAT001")
        self.assertEqual(group["total_qty"], 15)
        self.assertEqual(group["total_cost"], 1500)
        self.assertEqual(group["waste_qty"], 5)

    def test_get_consumption_analysis_group_by_week(self):
        """测试按周分组"""
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("10")
        consumption1.total_cost = Decimal("1000")
        consumption1.standard_qty = None
        consumption1.is_waste = False
        consumption1.consumption_date = datetime(2024, 1, 1)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_consumption_analysis(group_by="week")

        grouped = result["grouped_data"]
        self.assertEqual(len(grouped), 1)
        self.assertIn("2024-W", grouped[0]["period"])

    def test_get_consumption_analysis_group_by_month(self):
        """测试按月分组"""
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("10")
        consumption1.total_cost = Decimal("1000")
        consumption1.standard_qty = None
        consumption1.is_waste = False
        consumption1.consumption_date = datetime(2024, 1, 15)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_consumption_analysis(group_by="month")

        grouped = result["grouped_data"]
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["period"], "2024-01")


class TestListAlerts(unittest.TestCase):
    """测试预警列表"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_list_alerts_basic(self):
        """测试基本预警列表查询"""
        alert1 = MagicMock()
        alert1.id = 1
        alert1.alert_no = "ALERT001"
        alert1.material_code = "MAT001"
        alert1.material_name = "铝板"
        alert1.alert_type = "LOW_STOCK"
        alert1.alert_level = "WARNING"
        alert1.alert_date = datetime(2024, 1, 1)
        alert1.current_stock = Decimal("5")
        alert1.safety_stock = Decimal("20")
        alert1.shortage_qty = Decimal("15")
        alert1.days_to_stockout = 3
        alert1.alert_message = "库存不足"
        alert1.recommendation = "建议采购"
        alert1.status = "ACTIVE"
        alert1.assigned_to_id = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [alert1]

        self.db_mock.query.return_value = query_mock

        result = self.service.list_alerts(page=1, page_size=20)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)

        item = result["items"][0]
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["alert_no"], "ALERT001")
        self.assertEqual(item["alert_type"], "LOW_STOCK")

    def test_list_alerts_with_filters(self):
        """测试带筛选条件的预警查询"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.all.return_value = []

        self.db_mock.query.return_value = query_mock

        result = self.service.list_alerts(
            alert_type="LOW_STOCK",
            alert_level="CRITICAL",
            status="ACTIVE",
            material_id=1
        )

        self.assertEqual(result["total"], 0)


class TestCreateAlertRule(unittest.TestCase,
        target_type="PROJECT"
    ):
    """测试创建预警规则"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_create_alert_rule_basic(self):
        """测试创建基本预警规则"""
        with patch('app.services.production.material_tracking.material_tracking_service.save_obj') as mock_save:
            # Mock save_obj to set the id on the object
            def side_effect_save_obj(db, obj):
                obj.id = 1

            mock_save.side_effect = side_effect_save_obj

            rule_data = {
                "rule_name": "低库存预警",
                "alert_type": "LOW_STOCK",
                "threshold_value": Decimal("80"),
            }

            result = self.service.create_alert_rule(rule_data, current_user_id=1)

            # 验证save_obj被调用
            mock_save.assert_called_once()

            # 验证返回值
            self.assertIsNotNone(result.get("id"))
            self.assertEqual(result.get("rule_name"), "低库存预警")


class TestGetWasteRecords(unittest.TestCase):
    """测试物料浪费追溯"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_get_waste_records_basic(self):
        """测试基本浪费记录查询"""
        waste1 = MagicMock()
        waste1.id = 1
        waste1.consumption_no = "CONS001"
        waste1.material_code = "MAT001"
        waste1.material_name = "铝板"
        waste1.consumption_date = datetime(2024, 1, 1)
        waste1.consumption_qty = Decimal("15")
        waste1.standard_qty = Decimal("10")
        waste1.variance_qty = Decimal("5")
        waste1.variance_rate = Decimal("50")
        waste1.consumption_type = "PRODUCTION"
        waste1.project_id = None
        waste1.work_order_id = None
        waste1.total_cost = Decimal("500")
        waste1.remark = "浪费原因"
        waste1.unit_price = Decimal("100")

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [waste1]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_waste_records(min_variance_rate=10)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)

        item = result["items"][0]
        self.assertEqual(item["variance_rate"], 50)
        
        # 验证汇总
        summary = result["summary"]
        self.assertEqual(summary["total_waste_qty"], 5)
        self.assertEqual(summary["total_waste_cost"], 500)

    def test_get_waste_records_with_project_info(self):
        """测试带项目信息的浪费记录"""
        waste1 = MagicMock()
        waste1.id = 1
        waste1.consumption_no = "CONS001"
        waste1.material_code = "MAT001"
        waste1.material_name = "铝板"
        waste1.consumption_date = datetime(2024, 1, 1)
        waste1.consumption_qty = Decimal("15")
        waste1.standard_qty = Decimal("10")
        waste1.variance_qty = Decimal("5")
        waste1.variance_rate = Decimal("50")
        waste1.consumption_type = "PRODUCTION"
        waste1.project_id = 1
        waste1.work_order_id = 2
        waste1.total_cost = Decimal("500")
        waste1.remark = None
        waste1.unit_price = Decimal("100")

        # Mock Project查询
        project = MagicMock()
        project.id = 1
        project.project_name = "测试项目"

        # Mock WorkOrder查询
        work_order = MagicMock()
        work_order.id = 2
        work_order.work_order_no = "WO001"

        # 设置多次db.query调用的返回值
        waste_query_mock = MagicMock()
        waste_query_mock.filter.return_value = waste_query_mock
        waste_query_mock.order_by.return_value = waste_query_mock
        waste_query_mock.count.return_value = 1
        waste_query_mock.offset.return_value = waste_query_mock
        waste_query_mock.limit.return_value = waste_query_mock
        waste_query_mock.all.return_value = [waste1]

        project_query_mock = MagicMock()
        project_query_mock.filter.return_value = project_query_mock
        project_query_mock.first.return_value = project

        wo_query_mock = MagicMock()
        wo_query_mock.filter.return_value = wo_query_mock
        wo_query_mock.first.return_value = work_order

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return waste_query_mock
            elif call_count == 2:
                return project_query_mock
            else:
                return wo_query_mock

        self.db_mock.query.side_effect = query_side_effect

        result = self.service.get_waste_records()

        item = result["items"][0]
        self.assertEqual(item["project_name"], "测试项目")
        self.assertEqual(item["work_order_no"], "WO001")


class TestTraceBatch(unittest.TestCase):
    """测试批次追溯"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_trace_batch_by_id(self):
        """测试通过ID追溯批次"""
        # 准备批次mock
        batch = MagicMock()
        batch.id = 1
        batch.batch_no = "BATCH001"
        batch.material_id = 1
        batch.initial_qty = Decimal("100")
        batch.current_qty = Decimal("50")
        batch.consumed_qty = Decimal("50")
        batch.production_date = date(2024, 1, 1)
        batch.expire_date = date(2025, 1, 1)
        batch.supplier_batch_no = "SUP001"
        batch.quality_status = "QUALIFIED"
        batch.warehouse_location = "A区01架"
        batch.status = "ACTIVE"

        # 准备物料mock
        material = MagicMock()
        material.material_code = "MAT001"
        material.material_name = "铝板"

        # 准备消耗记录mock
        consumption1 = MagicMock()
        consumption1.consumption_no = "CONS001"
        consumption1.consumption_date = datetime(2024, 1, 15)
        consumption1.consumption_qty = Decimal("30")
        consumption1.consumption_type = "PRODUCTION"
        consumption1.project_id = None
        consumption1.work_order_id = None
        consumption1.operator_id = 1

        # Mock查询
        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.first.return_value = batch

        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.first.return_value = material

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.order_by.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = [consumption1]

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return batch_query_mock
            elif call_count == 2:
                return material_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        # 调用方法
        result = self.service.trace_batch(batch_id=1)

        # 验证批次信息
        batch_info = result["batch_info"]
        self.assertEqual(batch_info["batch_id"], 1)
        self.assertEqual(batch_info["batch_no"], "BATCH001")
        self.assertEqual(batch_info["material_code"], "MAT001")

        # 验证消耗轨迹
        trail = result["consumption_trail"]
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0]["consumption_no"], "CONS001")

        # 验证汇总
        summary = result["summary"]
        self.assertEqual(summary["total_consumptions"], 1)

    def test_trace_batch_not_found(self):
        """测试批次不存在"""
        from fastapi import HTTPException

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None

        self.db_mock.query.return_value = query_mock

        with self.assertRaises(HTTPException) as context:
            self.service.trace_batch(batch_id=999)

        self.assertEqual(context.exception.status_code, 404)

    def test_trace_batch_by_barcode(self):
        """测试通过条码追溯"""
        batch = MagicMock()
        batch.id = 1
        batch.batch_no = "BATCH001"
        batch.material_id = 1
        batch.initial_qty = Decimal("100")
        batch.current_qty = Decimal("50")
        batch.consumed_qty = Decimal("50")
        batch.production_date = None
        batch.expire_date = None
        batch.supplier_batch_no = None
        batch.quality_status = "QUALIFIED"
        batch.warehouse_location = "A区"
        batch.status = "ACTIVE"

        material = MagicMock()
        material.material_code = "MAT001"
        material.material_name = "铝板"

        batch_query_mock = MagicMock()
        batch_query_mock.filter.return_value = batch_query_mock
        batch_query_mock.first.return_value = batch

        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.first.return_value = material

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.order_by.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = []

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return batch_query_mock
            elif call_count == 2:
                return material_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        result = self.service.trace_batch(barcode="BARCODE123")

        self.assertEqual(result["batch_info"]["batch_no"], "BATCH001")


class TestGetCostAnalysis(unittest.TestCase):
    """测试成本分析"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_get_cost_analysis_basic(self):
        """测试基本成本分析"""
        consumption1 = MagicMock()
        consumption1.material_id = 1
        consumption1.material_code = "MAT001"
        consumption1.material_name = "铝板"
        consumption1.consumption_qty = Decimal("10")
        consumption1.total_cost = Decimal("1000")

        consumption2 = MagicMock()
        consumption2.material_id = 2
        consumption2.material_code = "MAT002"
        consumption2.material_name = "钢板"
        consumption2.consumption_qty = Decimal("20")
        consumption2.total_cost = Decimal("3000")

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1, consumption2]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_cost_analysis(top_n=10)

        self.assertEqual(result["total_cost"], 4000)
        self.assertEqual(result["material_count"], 2)
        self.assertEqual(len(result["top_materials"]), 2)

        # 验证排序（成本高的在前）
        top1 = result["top_materials"][0]
        self.assertEqual(top1["material_code"], "MAT002")
        self.assertEqual(top1["total_cost"], 3000)


class TestGetTurnoverAnalysis(unittest.TestCase):
    """测试库存周转率分析"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_get_turnover_analysis_basic(self):
        """测试基本周转率分析"""
        # 准备物料
        material1 = MagicMock()
        material1.id = 1
        material1.material_code = "MAT001"
        material1.material_name = "铝板"
        material1.current_stock = Decimal("100")
        material1.is_active = True

        # 准备消耗记录
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("30")

        consumption2 = MagicMock()
        consumption2.consumption_qty = Decimal("20")

        # Mock查询
        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.all.return_value = [material1]

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = [consumption1, consumption2]

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return material_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        result = self.service.get_turnover_analysis(days=30)

        self.assertEqual(result["period_days"], 30)
        self.assertEqual(len(result["materials"]), 1)

        item = result["materials"][0]
        self.assertEqual(item["material_code"], "MAT001")
        self.assertEqual(item["consumption_qty"], 50)  # 30 + 20
        self.assertEqual(item["turnover_rate"], 0.5)  # 50 / 100
        self.assertEqual(item["turnover_days"], 60)  # 30 / 0.5

    def test_get_turnover_analysis_zero_stock(self):
        """测试零库存的周转率"""
        material1 = MagicMock()
        material1.id = 1
        material1.material_code = "MAT001"
        material1.material_name = "铝板"
        material1.current_stock = Decimal("0")
        material1.is_active = True

        material_query_mock = MagicMock()
        material_query_mock.filter.return_value = material_query_mock
        material_query_mock.all.return_value = [material1]

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = []

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return material_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        result = self.service.get_turnover_analysis(days=30)

        item = result["materials"][0]
        self.assertEqual(item["turnover_rate"], 0)
        self.assertEqual(item["turnover_days"], 0)


class TestCheckAndCreateAlerts(unittest.TestCase):
    """测试预警检查和创建"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_check_and_create_alerts_low_stock_percentage(self):
        """测试低库存预警（百分比阈值）"""
        # 准备物料
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.current_stock = Decimal("15")
        material.safety_stock = Decimal("20")

        # 准备规则
        rule = MagicMock()
        rule.alert_type = "LOW_STOCK"
        rule.threshold_type = "PERCENTAGE"
        rule.threshold_value = Decimal("90")  # 90%
        rule.alert_level = "WARNING"

        # Mock查询
        rule_query_mock = MagicMock()
        rule_query_mock.filter.return_value = rule_query_mock
        rule_query_mock.all.return_value = [rule]

        alert_query_mock = MagicMock()
        alert_query_mock.filter.return_value = alert_query_mock
        alert_query_mock.first.return_value = None  # 无现有预警

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = []

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rule_query_mock
            elif call_count == 2:
                return alert_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        # 调用方法
        self.service.check_and_create_alerts(material)

        # 验证创建了预警
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called_once()

    def test_check_and_create_alerts_shortage(self):
        """测试缺料预警"""
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.current_stock = Decimal("0")
        material.safety_stock = Decimal("20")

        rule = MagicMock()
        rule.alert_type = "SHORTAGE"
        rule.threshold_type = "FIXED"
        rule.threshold_value = Decimal("0")
        rule.alert_level = "CRITICAL"

        rule_query_mock = MagicMock()
        rule_query_mock.filter.return_value = rule_query_mock
        rule_query_mock.all.return_value = [rule]

        alert_query_mock = MagicMock()
        alert_query_mock.filter.return_value = alert_query_mock
        alert_query_mock.first.return_value = None

        consumption_query_mock = MagicMock()
        consumption_query_mock.filter.return_value = consumption_query_mock
        consumption_query_mock.all.return_value = []

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rule_query_mock
            elif call_count == 2:
                return alert_query_mock
            else:
                return consumption_query_mock

        self.db_mock.query.side_effect = query_side_effect

        self.service.check_and_create_alerts(material)

        self.db_mock.add.assert_called_once()

    def test_check_and_create_alerts_existing_active_alert(self):
        """测试已存在活动预警时不重复创建"""
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "铝板"
        material.current_stock = Decimal("5")
        material.safety_stock = Decimal("20")

        rule = MagicMock()
        rule.alert_type = "LOW_STOCK"
        rule.threshold_type = "FIXED"
        rule.threshold_value = Decimal("10")
        rule.alert_level = "WARNING"

        existing_alert = MagicMock()
        existing_alert.id = 1

        rule_query_mock = MagicMock()
        rule_query_mock.filter.return_value = rule_query_mock
        rule_query_mock.all.return_value = [rule]

        alert_query_mock = MagicMock()
        alert_query_mock.filter.return_value = alert_query_mock
        alert_query_mock.first.return_value = existing_alert  # 已存在预警

        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rule_query_mock
            else:
                return alert_query_mock

        self.db_mock.query.side_effect = query_side_effect

        self.service.check_and_create_alerts(material)

        # 验证没有创建新预警
        self.db_mock.add.assert_not_called()


class TestCalculateAvgDailyConsumption(unittest.TestCase):
    """测试平均日消耗计算"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = MaterialTrackingService(self.db_mock)

    def test_calculate_avg_daily_consumption(self):
        """测试平均日消耗计算"""
        consumption1 = MagicMock()
        consumption1.consumption_qty = Decimal("30")

        consumption2 = MagicMock()
        consumption2.consumption_qty = Decimal("60")

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [consumption1, consumption2]

        self.db_mock.query.return_value = query_mock

        result = self.service.calculate_avg_daily_consumption(material_id=1, days=30)

        self.assertEqual(result, 3.0)  # (30 + 60) / 30

    def test_calculate_avg_daily_consumption_zero_days(self):
        """测试零天数"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        self.db_mock.query.return_value = query_mock

        result = self.service.calculate_avg_daily_consumption(material_id=1, days=0)

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
