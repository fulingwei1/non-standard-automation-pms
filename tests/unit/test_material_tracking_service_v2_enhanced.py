# -*- coding: utf-8 -*-
"""
物料跟踪服务增强测试 v2 - 修复版
测试策略：Mock外部依赖，构造真实数据对象让业务逻辑执行
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException

from app.models.material import Material
from app.models.production.material_tracking import (
    MaterialAlert,
    MaterialAlertRule,
    MaterialBatch,
    MaterialConsumption,
)
from app.services.production.material_tracking.material_tracking_service import (
    MaterialTrackingService,
)


class TestMaterialTrackingService(unittest.TestCase):
    """物料跟踪服务测试"""

    def setUp(self):
        """初始化测试"""
        self.db = MagicMock()
        self.service = MaterialTrackingService(self.db)
        self.current_user_id = 1

    # ================== 1. 测试实时库存查询 ==================

    def test_get_realtime_stock_basic(self):
        """测试基本库存查询"""
        # 构造真实的物料对象
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            specification="100x200",
            unit="kg",
            current_stock=Decimal("100.5"),
            safety_stock=Decimal("20.0"),
            category_id=1,
            is_active=True,
        )

        batch = MaterialBatch(
            id=1,
            material_id=1,
            batch_no="BATCH001",
            current_qty=Decimal("50.0"),
            reserved_qty=Decimal("10.0"),
            warehouse_location="A1",
            production_date=date(2024, 1, 1),
            expire_date=date(2025, 1, 1),
            quality_status="QUALIFIED",
            status="ACTIVE",
        )

        # Mock数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [material]

        # Mock批次查询
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.all.return_value = [batch]

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query") as mock_db_query:
                # 第一次调用返回物料查询，第二次调用返回批次查询
                mock_db_query.side_effect = [mock_query, mock_batch_query]

                result = self.service.get_realtime_stock(page=1, page_size=20)

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["material_code"], "MAT001")
        self.assertEqual(item["current_stock"], 100.5)
        self.assertEqual(item["batch_count"], 1)
        self.assertEqual(item["available_stock"], 90.5)  # 100.5 - 10.0

    def test_get_realtime_stock_with_material_id(self):
        """测试按物料ID查询"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            unit="kg",
            current_stock=Decimal("100.0"),
            safety_stock=Decimal("20.0"),
            is_active=True,
        )

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [material]

        # Mock批次查询返回空
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.all.return_value = []

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query") as mock_db_query:
                mock_db_query.side_effect = [mock_query, mock_batch_query]
                result = self.service.get_realtime_stock(material_id=1, page=1, page_size=20)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["batch_count"], 0)

    def test_get_realtime_stock_low_stock_only(self):
        """测试低库存筛选"""
        material_low = Material(
            id=1,
            material_code="MAT001",
            material_name="低库存物料",
            unit="kg",
            current_stock=Decimal("10.0"),
            safety_stock=Decimal("20.0"),
            is_active=True,
        )

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [material_low]

        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.all.return_value = []

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query") as mock_db_query:
                mock_db_query.side_effect = [mock_query, mock_batch_query]
                result = self.service.get_realtime_stock(low_stock_only=True, page=1, page_size=20)

        self.assertEqual(result["items"][0]["is_low_stock"], True)

    def test_get_realtime_stock_pagination(self):
        """测试分页功能"""
        materials = [
            Material(
                id=i,
                material_code=f"MAT{i:03d}",
                material_name=f"物料{i}",
                unit="kg",
                current_stock=Decimal("100.0"),
                safety_stock=Decimal("20.0"),
                is_active=True,
            )
            for i in range(1, 6)
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.all.return_value = materials[:2]  # 第一页2条

        # Mock批次查询
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.all.return_value = []

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query") as mock_db_query:
                mock_db_query.side_effect = [mock_query] + [mock_batch_query] * 2
                result = self.service.get_realtime_stock(page=1, page_size=2)

        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 2)

    # ================== 2. 测试物料消耗记录 ==================

    def test_create_consumption_basic(self):
        """测试基本消耗记录"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            unit="kg",
            current_stock=Decimal("100.0"),
            safety_stock=Decimal("20.0"),
            standard_price=Decimal("50.0"),
        )

        consumption_data = {
            "material_id": 1,
            "consumption_qty": Decimal("10.0"),
            "consumption_type": "PRODUCTION",
        }

        # Mock预警检查（返回空规则列表）
        mock_alert_query = Mock()
        mock_alert_query.filter.return_value = mock_alert_query
        mock_alert_query.all.return_value = []

        with patch("app.services.production.material_tracking.material_tracking_service.get_or_404") as mock_get:
            mock_get.return_value = material
            with patch.object(self.db, "query", return_value=mock_alert_query):
                result = self.service.create_consumption(consumption_data, self.current_user_id)

        # 验证结果
        self.assertIn("id", result)
        self.assertIn("consumption_no", result)
        self.assertEqual(result["material_code"], "MAT001")
        self.assertEqual(result["consumption_qty"], 10.0)

        # 验证数据库操作
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_consumption_missing_required_fields(self):
        """测试缺少必填字段"""
        consumption_data = {
            "material_id": 1,
            # 缺少 consumption_qty
        }

        with self.assertRaises(HTTPException) as ctx:
            self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertEqual(ctx.exception.status_code, 400)

    def test_create_consumption_with_barcode(self):
        """测试条码扫描消耗"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            unit="kg",
            current_stock=Decimal("100.0"),
            safety_stock=Decimal("20.0"),
            standard_price=Decimal("50.0"),
        )

        batch = MaterialBatch(
            id=1,
            material_id=1,
            batch_no="BATCH001",
            barcode="BC123456",
            current_qty=Decimal("50.0"),
            consumed_qty=Decimal("0.0"),
            status="ACTIVE",
        )

        consumption_data = {
            "material_id": 1,
            "consumption_qty": Decimal("10.0"),
            "barcode": "BC123456",
        }

        # Mock批次查询 - 先通过条码查找
        mock_barcode_query = Mock()
        mock_barcode_query.filter.return_value = mock_barcode_query
        mock_barcode_query.first.return_value = batch

        # Mock批次更新查询 - 第二次通过ID查找
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.first.return_value = batch

        # Mock预警规则查询
        mock_alert_query = Mock()
        mock_alert_query.filter.return_value = mock_alert_query
        mock_alert_query.all.return_value = []

        with patch("app.services.production.material_tracking.material_tracking_service.get_or_404") as mock_get:
            mock_get.return_value = material
            with patch.object(self.db, "query") as mock_db_query:
                # 依次返回：条码查询、批次ID查询、预警规则查询
                mock_db_query.side_effect = [mock_barcode_query, mock_batch_query, mock_alert_query]
                result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertIn("consumption_no", result)
        # 验证批次更新
        self.assertEqual(batch.current_qty, Decimal("40.0"))
        self.assertEqual(batch.consumed_qty, Decimal("10.0"))

    def test_create_consumption_with_variance_waste(self):
        """测试带差异的浪费记录"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            unit="kg",
            current_stock=Decimal("100.0"),
            standard_price=Decimal("50.0"),
        )

        consumption_data = {
            "material_id": 1,
            "consumption_qty": Decimal("15.0"),
            "standard_qty": Decimal("10.0"),  # 标准用量
            "consumption_type": "PRODUCTION",
        }

        # Mock预警规则查询
        mock_alert_query = Mock()
        mock_alert_query.filter.return_value = mock_alert_query
        mock_alert_query.all.return_value = []

        with patch("app.services.production.material_tracking.material_tracking_service.get_or_404") as mock_get:
            mock_get.return_value = material
            with patch.object(self.db, "query", return_value=mock_alert_query):
                result = self.service.create_consumption(consumption_data, self.current_user_id)

        # 差异率 = (15-10)/10 * 100 = 50%
        # 超过10%视为浪费
        self.assertTrue(result["is_waste"])
        self.assertEqual(result["variance_rate"], 50.0)

    def test_create_consumption_batch_depleted(self):
        """测试批次耗尽"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="测试物料",
            unit="kg",
            current_stock=Decimal("10.0"),
            standard_price=Decimal("50.0"),
        )

        batch = MaterialBatch(
            id=1,
            material_id=1,
            batch_no="BATCH001",
            current_qty=Decimal("10.0"),
            consumed_qty=Decimal("0"),
            status="ACTIVE",
        )

        consumption_data = {
            "material_id": 1,
            "consumption_qty": Decimal("10.0"),
            "batch_id": 1,
        }

        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.first.return_value = batch

        # Mock预警规则查询
        mock_alert_query = Mock()
        mock_alert_query.filter.return_value = mock_alert_query
        mock_alert_query.all.return_value = []

        with patch("app.services.production.material_tracking.material_tracking_service.get_or_404") as mock_get:
            mock_get.return_value = material
            with patch.object(self.db, "query") as mock_db_query:
                mock_db_query.side_effect = [mock_batch_query, mock_alert_query]
                self.service.create_consumption(consumption_data, self.current_user_id)

        # 验证批次状态变为耗尽
        self.assertEqual(batch.status, "DEPLETED")
        self.assertEqual(batch.current_qty, Decimal("0"))

    # ================== 3. 测试消耗分析 ==================

    def test_get_consumption_analysis_summary(self):
        """测试消耗分析汇总"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal("500.0"),
                standard_qty=Decimal("9.0"),
                is_waste=False,
            ),
            MaterialConsumption(
                id=2,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 2),
                consumption_qty=Decimal("15.0"),
                total_cost=Decimal("750.0"),
                standard_qty=Decimal("10.0"),
                is_waste=True,
            ),
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_consumption_analysis(material_id=1, group_by="day")

        # 验证汇总数据
        self.assertEqual(result["summary"]["total_records"], 2)
        self.assertEqual(result["summary"]["total_consumption"], 25.0)
        self.assertEqual(result["summary"]["total_cost"], 1250.0)
        self.assertEqual(result["summary"]["waste_count"], 1)
        self.assertEqual(result["summary"]["waste_rate"], 50.0)

    def test_get_consumption_analysis_group_by_material(self):
        """测试按物料分组"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal("500.0"),
                is_waste=False,
            ),
            MaterialConsumption(
                id=2,
                material_id=2,
                material_code="MAT002",
                material_name="物料2",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("20.0"),
                total_cost=Decimal("1000.0"),
                is_waste=True,
            ),
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_consumption_analysis(group_by="material")

        # 验证分组数据
        self.assertEqual(len(result["grouped_data"]), 2)
        mat1 = next(g for g in result["grouped_data"] if g["material_code"] == "MAT001")
        self.assertEqual(mat1["total_qty"], 10.0)
        self.assertEqual(mat1["waste_qty"], 0)

        mat2 = next(g for g in result["grouped_data"] if g["material_code"] == "MAT002")
        self.assertEqual(mat2["total_qty"], 20.0)
        self.assertEqual(mat2["waste_qty"], 20.0)

    def test_get_consumption_analysis_group_by_day(self):
        """测试按天分组"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal("500.0"),
                is_waste=False,
            ),
            MaterialConsumption(
                id=2,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("5.0"),
                total_cost=Decimal("250.0"),
                is_waste=False,
            ),
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_consumption_analysis(group_by="day")

        # 同一天的数据应合并
        self.assertEqual(len(result["grouped_data"]), 1)
        day_data = result["grouped_data"][0]
        self.assertEqual(day_data["period"], "2024-01-01")
        self.assertEqual(day_data["total_qty"], 15.0)
        self.assertEqual(day_data["record_count"], 2)

    def test_get_consumption_analysis_with_date_filter(self):
        """测试日期筛选"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 15),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal("500.0"),
                is_waste=False,
            ),
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_consumption_analysis(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            group_by="day",
        )

        # 验证filter被调用
        self.assertTrue(mock_query.filter.called)
        self.assertEqual(result["summary"]["total_records"], 1)

    # ================== 4. 测试预警列表 ==================

    def test_list_alerts_basic(self):
        """测试基本预警列表"""
        alerts = [
            MaterialAlert(
                id=1,
                alert_no="ALERT001",
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                alert_type="LOW_STOCK",
                alert_level="WARNING",
                alert_date=datetime(2024, 1, 1),
                current_stock=Decimal("10.0"),
                safety_stock=Decimal("20.0"),
                shortage_qty=Decimal("10.0"),
                days_to_stockout=5,
                alert_message="库存不足",
                status="ACTIVE",
            ),
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = alerts

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query", return_value=mock_query):
                result = self.service.list_alerts(page=1, page_size=20)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["alert_no"], "ALERT001")

    def test_list_alerts_with_filters(self):
        """测试带筛选条件的预警列表"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            result = self.service.list_alerts(
                alert_type="LOW_STOCK",
                alert_level="CRITICAL",
                status="ACTIVE",
                material_id=1,
                page=1,
                page_size=20,
            )

        # 验证filter被多次调用
        self.assertTrue(mock_query.filter.called)
        self.assertEqual(result["total"], 0)

    # ================== 5. 测试预警规则创建 ==================

    def test_create_alert_rule_basic(self):
        """测试创建预警规则"""
        rule_data = {
            "rule_name": "低库存预警",
            "alert_type": "LOW_STOCK",
            "alert_level": "WARNING",
            "threshold_type": "PERCENTAGE",
            "threshold_value": 50,
            "safety_days": 7,
        }

        with patch("app.services.production.material_tracking.material_tracking_service.save_obj") as mock_save:
            result = self.service.create_alert_rule(rule_data, self.current_user_id)

        self.assertIn("rule_name", result)
        self.assertEqual(result["rule_name"], "低库存预警")
        mock_save.assert_called_once()

    def test_create_alert_rule_with_material(self):
        """测试创建特定物料的预警规则"""
        rule_data = {
            "rule_name": "物料1低库存预警",
            "material_id": 1,
            "alert_type": "LOW_STOCK",
            "threshold_value": 20,
        }

        with patch("app.services.production.material_tracking.material_tracking_service.save_obj") as mock_save:
            result = self.service.create_alert_rule(rule_data, self.current_user_id)

        self.assertIn("id", result)
        mock_save.assert_called_once()

    # ================== 6. 测试浪费追溯 ==================

    def test_get_waste_records_basic(self):
        """测试基本浪费记录查询"""
        waste_consumption = MaterialConsumption(
            id=1,
            consumption_no="CONS001",
            material_id=1,
            material_code="MAT001",
            material_name="物料1",
            consumption_date=datetime(2024, 1, 1),
            consumption_qty=Decimal("15.0"),
            standard_qty=Decimal("10.0"),
            variance_qty=Decimal("5.0"),
            variance_rate=Decimal("50.0"),
            is_waste=True,
            consumption_type="PRODUCTION",
            unit_price=Decimal("50.0"),
            total_cost=Decimal("750.0"),
            project_id=1,
            work_order_id=1,
        )

        # 使用Mock对象代替真实的Project和WorkOrder
        project = Mock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "项目1"

        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = "WO001"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [waste_consumption]

        # Mock关联查询
        mock_proj_query = Mock()
        mock_proj_query.filter.return_value = mock_proj_query
        mock_proj_query.first.return_value = project

        mock_wo_query = Mock()
        mock_wo_query.filter.return_value = mock_wo_query
        mock_wo_query.first.return_value = work_order

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            with patch.object(self.db, "query") as mock_db_query:
                mock_db_query.side_effect = [
                    mock_query,
                    mock_proj_query,
                    mock_wo_query,
                ]

                result = self.service.get_waste_records(page=1, page_size=20)

        # 验证结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        waste = result["items"][0]
        self.assertEqual(waste["variance_rate"], 50.0)
        self.assertEqual(waste["project_name"], "项目1")
        self.assertEqual(waste["work_order_no"], "WO001")

    def test_get_waste_records_with_filters(self):
        """测试带筛选条件的浪费记录"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        with patch('app.common.query_filters.apply_pagination') as mock_pagination:
            mock_pagination.return_value = mock_query
            
            result = self.service.get_waste_records(
                material_id=1,
                project_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                min_variance_rate=15.0,
                page=1,
                page_size=20,
            )

        # 验证filter被多次调用
        self.assertTrue(mock_query.filter.called)
        self.assertEqual(result["total"], 0)

    # ================== 7. 测试批次追溯 ==================

    def test_trace_batch_by_batch_no(self):
        """测试通过批次号追溯"""
        batch = MaterialBatch(
            id=1,
            material_id=1,
            batch_no="BATCH001",
            initial_qty=Decimal("100.0"),
            current_qty=Decimal("50.0"),
            consumed_qty=Decimal("50.0"),
            production_date=date(2024, 1, 1),
            expire_date=date(2025, 1, 1),
            supplier_batch_no="SUP-BATCH-001",
            quality_status="QUALIFIED",
            warehouse_location="A1",
            status="ACTIVE",
        )

        material = Material(
            id=1, material_code="MAT001", material_name="物料1"
        )

        consumption = MaterialConsumption(
            id=1,
            consumption_no="CONS001",
            batch_id=1,
            material_id=1,
            consumption_date=datetime(2024, 1, 15),
            consumption_qty=Decimal("10.0"),
            consumption_type="PRODUCTION",
            project_id=1,
            work_order_id=1,
        )

        # 使用Mock对象
        project = Mock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "项目1"

        work_order = Mock()
        work_order.id = 1
        work_order.work_order_no = "WO001"

        # Mock查询
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.first.return_value = batch

        mock_mat_query = Mock()
        mock_mat_query.filter.return_value = mock_mat_query
        mock_mat_query.first.return_value = material

        mock_cons_query = Mock()
        mock_cons_query.filter.return_value = mock_cons_query
        mock_cons_query.order_by.return_value = mock_cons_query
        mock_cons_query.all.return_value = [consumption]

        mock_proj_query = Mock()
        mock_proj_query.filter.return_value = mock_proj_query
        mock_proj_query.first.return_value = project

        mock_wo_query = Mock()
        mock_wo_query.filter.return_value = mock_wo_query
        mock_wo_query.first.return_value = work_order

        with patch.object(self.db, "query") as mock_db_query:
            mock_db_query.side_effect = [
                mock_batch_query,
                mock_mat_query,
                mock_cons_query,
                mock_proj_query,
                mock_wo_query,
            ]

            result = self.service.trace_batch(batch_no="BATCH001")

        # 验证结果
        self.assertEqual(result["batch_info"]["batch_no"], "BATCH001")
        self.assertEqual(result["batch_info"]["material_code"], "MAT001")
        self.assertEqual(len(result["consumption_trail"]), 1)
        self.assertEqual(result["summary"]["total_consumptions"], 1)

    def test_trace_batch_by_barcode(self):
        """测试通过条码追溯"""
        batch = MaterialBatch(
            id=1,
            material_id=1,
            batch_no="BATCH001",
            barcode="BC123456",
            initial_qty=Decimal("100.0"),
            current_qty=Decimal("100.0"),
            consumed_qty=Decimal("0"),
            status="ACTIVE",
        )

        material = Material(id=1, material_code="MAT001", material_name="物料1")

        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.first.return_value = batch

        mock_mat_query = Mock()
        mock_mat_query.filter.return_value = mock_mat_query
        mock_mat_query.first.return_value = material

        mock_cons_query = Mock()
        mock_cons_query.filter.return_value = mock_cons_query
        mock_cons_query.order_by.return_value = mock_cons_query
        mock_cons_query.all.return_value = []

        with patch.object(self.db, "query") as mock_db_query:
            mock_db_query.side_effect = [
                mock_batch_query,
                mock_mat_query,
                mock_cons_query,
            ]

            result = self.service.trace_batch(barcode="BC123456")

        self.assertEqual(result["batch_info"]["batch_no"], "BATCH001")
        self.assertEqual(len(result["consumption_trail"]), 0)

    def test_trace_batch_not_found(self):
        """测试批次不存在"""
        mock_batch_query = Mock()
        mock_batch_query.filter.return_value = mock_batch_query
        mock_batch_query.first.return_value = None

        with patch.object(self.db, "query", return_value=mock_batch_query):
            with self.assertRaises(HTTPException) as ctx:
                self.service.trace_batch(batch_no="NOTEXIST")

        self.assertEqual(ctx.exception.status_code, 404)

    # ================== 8. 测试成本分析 ==================

    def test_get_cost_analysis_basic(self):
        """测试基本成本分析"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                material_code="MAT001",
                material_name="物料1",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal("500.0"),
            ),
            MaterialConsumption(
                id=2,
                material_id=2,
                material_code="MAT002",
                material_name="物料2",
                consumption_date=datetime(2024, 1, 2),
                consumption_qty=Decimal("20.0"),
                total_cost=Decimal("1000.0"),
            ),
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_cost_analysis(top_n=10)

        # 验证汇总
        self.assertEqual(result["total_cost"], 1500.0)
        self.assertEqual(result["material_count"], 2)
        self.assertEqual(len(result["top_materials"]), 2)

        # 验证排序（按成本降序）
        self.assertEqual(result["top_materials"][0]["material_code"], "MAT002")
        self.assertEqual(result["top_materials"][0]["total_cost"], 1000.0)

    def test_get_cost_analysis_with_date_filter(self):
        """测试带日期筛选的成本分析"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.get_cost_analysis(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            top_n=5,
        )

        # 验证filter被调用
        self.assertTrue(mock_query.filter.called)
        self.assertEqual(result["total_cost"], 0)

    def test_get_cost_analysis_top_n(self):
        """测试Top N限制"""
        consumptions = [
            MaterialConsumption(
                id=i,
                material_id=i,
                material_code=f"MAT{i:03d}",
                material_name=f"物料{i}",
                consumption_date=datetime(2024, 1, 1),
                consumption_qty=Decimal("10.0"),
                total_cost=Decimal(str(100 * i)),
            )
            for i in range(1, 16)
        ]

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        result = self.service.get_cost_analysis(top_n=5)

        # 只返回Top 5
        self.assertEqual(len(result["top_materials"]), 5)
        # 验证是最高成本的5个
        self.assertEqual(result["top_materials"][0]["material_code"], "MAT015")

    # ================== 9. 测试库存周转率 ==================

    def test_get_turnover_analysis_basic(self):
        """测试基本周转率分析"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="物料1",
            current_stock=Decimal("100.0"),
            is_active=True,
        )

        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                consumption_date=datetime.now() - timedelta(days=10),
                consumption_qty=Decimal("30.0"),
            ),
        ]

        mock_mat_query = Mock()
        mock_mat_query.filter.return_value = mock_mat_query
        mock_mat_query.all.return_value = [material]

        mock_cons_query = Mock()
        mock_cons_query.filter.return_value = mock_cons_query
        mock_cons_query.all.return_value = consumptions

        with patch.object(self.db, "query") as mock_db_query:
            mock_db_query.side_effect = [mock_mat_query, mock_cons_query]

            result = self.service.get_turnover_analysis(days=30)

        # 验证结果
        self.assertEqual(result["period_days"], 30)
        self.assertEqual(len(result["materials"]), 1)
        mat = result["materials"][0]
        self.assertEqual(mat["material_code"], "MAT001")
        # 周转率 = 30 / 100 = 0.3
        self.assertEqual(mat["turnover_rate"], 0.3)
        # 周转天数 = 30 / 0.3 = 100
        self.assertEqual(mat["turnover_days"], 100.0)

    def test_get_turnover_analysis_zero_stock(self):
        """测试零库存的周转率"""
        material = Material(
            id=1,
            material_code="MAT001",
            material_name="物料1",
            current_stock=Decimal("0"),
            is_active=True,
        )

        mock_mat_query = Mock()
        mock_mat_query.filter.return_value = mock_mat_query
        mock_mat_query.all.return_value = [material]

        mock_cons_query = Mock()
        mock_cons_query.filter.return_value = mock_cons_query
        mock_cons_query.all.return_value = []

        with patch.object(self.db, "query") as mock_db_query:
            mock_db_query.side_effect = [mock_mat_query, mock_cons_query]

            result = self.service.get_turnover_analysis(days=30)

        mat = result["materials"][0]
        # 库存为0，周转率应为0
        self.assertEqual(mat["turnover_rate"], 0)
        self.assertEqual(mat["turnover_days"], 0)

    def test_get_turnover_analysis_sorting(self):
        """测试周转率排序"""
        materials = [
            Material(
                id=1,
                material_code="MAT001",
                material_name="快周转",
                current_stock=Decimal("10.0"),
                is_active=True,
            ),
            Material(
                id=2,
                material_code="MAT002",
                material_name="慢周转",
                current_stock=Decimal("100.0"),
                is_active=True,
            ),
        ]

        # MAT001消耗10，周转率1.0
        # MAT002消耗10，周转率0.1
        consumptions_1 = [
            MaterialConsumption(
                id=1,
                material_id=1,
                consumption_date=datetime.now(),
                consumption_qty=Decimal("10.0"),
            ),
        ]

        consumptions_2 = [
            MaterialConsumption(
                id=2,
                material_id=2,
                consumption_date=datetime.now(),
                consumption_qty=Decimal("10.0"),
            ),
        ]

        mock_mat_query = Mock()
        mock_mat_query.filter.return_value = mock_mat_query
        mock_mat_query.all.return_value = materials

        with patch.object(self.db, "query") as mock_db_query:
            # 为每个物料返回不同的消耗记录
            mock_cons_query_1 = Mock()
            mock_cons_query_1.filter.return_value = mock_cons_query_1
            mock_cons_query_1.all.return_value = consumptions_1

            mock_cons_query_2 = Mock()
            mock_cons_query_2.filter.return_value = mock_cons_query_2
            mock_cons_query_2.all.return_value = consumptions_2

            mock_db_query.side_effect = [
                mock_mat_query,
                mock_cons_query_1,
                mock_cons_query_2,
            ]

            result = self.service.get_turnover_analysis(days=30)

        # 验证按周转率降序排序
        self.assertEqual(result["materials"][0]["material_code"], "MAT001")
        self.assertTrue(result["materials"][0]["turnover_rate"] > result["materials"][1]["turnover_rate"])

    # ================== 10. 测试平均日消耗计算 ==================

    def test_calculate_avg_daily_consumption_basic(self):
        """测试基本平均日消耗计算"""
        consumptions = [
            MaterialConsumption(
                id=1,
                material_id=1,
                consumption_date=datetime.now() - timedelta(days=10),
                consumption_qty=Decimal("30.0"),
            ),
            MaterialConsumption(
                id=2,
                material_id=1,
                consumption_date=datetime.now() - timedelta(days=5),
                consumption_qty=Decimal("60.0"),
            ),
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = consumptions

        with patch.object(self.db, "query", return_value=mock_query):
            result = self.service.calculate_avg_daily_consumption(material_id=1, days=30)

        # 总消耗90 / 30天 = 3.0
        self.assertEqual(result, 3.0)

    def test_calculate_avg_daily_consumption_no_data(self):
        """测试无消耗数据"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(self.db, "query", return_value=mock_query):
            result = self.service.calculate_avg_daily_consumption(material_id=1, days=30)

        self.assertEqual(result, 0)

    def test_calculate_avg_daily_consumption_zero_days(self):
        """测试天数为0的边界情况"""
        result = self.service.calculate_avg_daily_consumption(material_id=1, days=0)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
