# -*- coding: utf-8 -*-
"""
物料跟踪服务增强测试
使用 unittest.mock 完全 Mock 数据库操作
目标覆盖率: 70%+
"""
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException

from app.services.production.material_tracking.material_tracking_service import (
    MaterialTrackingService,
)


class TestMaterialTrackingServiceEnhanced(unittest.TestCase):
    """物料跟踪服务增强测试类"""

    def setUp(self):
        """每个测试前的初始化"""
        self.db = MagicMock()
        self.service = MaterialTrackingService(self.db)
        self.current_user_id = 1

    def tearDown(self):
        """每个测试后的清理"""
        self.db.reset_mock()

    # ==================== 1. get_realtime_stock 测试 (8个) ====================

    def test_get_realtime_stock_basic(self):
        """测试基本库存查询"""
        # Mock 物料查询
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.specification = "规格A"
        mock_material.unit = "个"
        mock_material.current_stock = Decimal("100")
        mock_material.safety_stock = Decimal("20")

        # Mock 批次查询
        mock_batch = Mock()
        mock_batch.batch_no = "BATCH001"
        mock_batch.current_qty = Decimal("50")
        mock_batch.reserved_qty = Decimal("10")
        mock_batch.warehouse_location = "A01"
        mock_batch.production_date = date(2024, 1, 1)
        mock_batch.expire_date = date(2025, 1, 1)
        mock_batch.quality_status = "QUALIFIED"

        # 配置 Mock 查询链
        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.all.return_value = [mock_batch]

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_material]
            
            result = self.service.get_realtime_stock(page=1, page_size=20)

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["material_code"], "MAT001")

    def test_get_realtime_stock_with_material_id_filter(self):
        """测试按物料ID筛选"""
        mock_material = Mock()
        mock_material.id = 5
        mock_material.material_code = "MAT005"
        mock_material.current_stock = Decimal("200")
        mock_material.safety_stock = Decimal("50")

        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_material]
            
            result = self.service.get_realtime_stock(material_id=5)

        self.assertEqual(result["total"], 1)

    def test_get_realtime_stock_low_stock_only(self):
        """测试低库存筛选"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.current_stock = Decimal("10")
        mock_material.safety_stock = Decimal("50")

        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_material]
            
            result = self.service.get_realtime_stock(low_stock_only=True)

        self.assertEqual(result["total"], 1)

    def test_get_realtime_stock_with_material_code_filter(self):
        """测试按物料编码筛选"""
        with patch("app.common.query_filters.apply_keyword_filter") as mock_filter:
            with patch("app.common.query_filters.apply_pagination") as mock_pagination:
                mock_pagination.return_value.all.return_value = []
                self.db.query.return_value.filter.return_value.count.return_value = 0
                
                result = self.service.get_realtime_stock(material_code="MAT001")

        mock_filter.assert_called()
        self.assertEqual(result["total"], 0)

    def test_get_realtime_stock_with_category_filter(self):
        """测试按分类筛选"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []
            
            result = self.service.get_realtime_stock(category_id=3)

        self.assertEqual(result["total"], 0)

    def test_get_realtime_stock_pagination(self):
        """测试分页功能"""
        self.db.query.return_value.filter.return_value.count.return_value = 100
        self.db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []
            
            result = self.service.get_realtime_stock(page=3, page_size=10)

        self.assertEqual(result["page"], 3)
        self.assertEqual(result["page_size"], 10)

    def test_get_realtime_stock_with_warehouse_location(self):
        """测试按仓库位置筛选批次"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.current_stock = Decimal("100")
        mock_material.safety_stock = Decimal("20")

        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.common.query_filters.apply_keyword_filter"):
            with patch("app.common.query_filters.apply_pagination") as mock_pagination:
                mock_pagination.return_value.all.return_value = [mock_material]
                
                result = self.service.get_realtime_stock(warehouse_location="A01")

        self.assertEqual(result["total"], 1)

    def test_get_realtime_stock_batch_status_filter(self):
        """测试批次状态筛选"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.current_stock = Decimal("100")
        mock_material.safety_stock = Decimal("20")

        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_material]
            
            result = self.service.get_realtime_stock(status="ACTIVE")

        self.assertEqual(result["total"], 1)

    # ==================== 2. create_consumption 测试 (10个) ====================

    def test_create_consumption_basic(self):
        """测试基本消耗记录创建"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.unit = "个"
        mock_material.standard_price = Decimal("10.5")
        mock_material.current_stock = Decimal("100")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 50,
                "consumption_type": "PRODUCTION",
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertIn("consumption_no", result)
        self.assertEqual(result["material_code"], "MAT001")
        self.assertEqual(result["consumption_qty"], 50.0)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_consumption_missing_required_fields(self):
        """测试缺少必填字段"""
        consumption_data = {"material_id": 1}  # 缺少 consumption_qty

        with self.assertRaises(HTTPException) as context:
            self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertEqual(context.exception.status_code, 400)

    def test_create_consumption_with_barcode(self):
        """测试通过条码识别批次"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.unit = "个"
        mock_material.current_stock = Decimal("100")

        mock_batch = Mock()
        mock_batch.id = 10
        mock_batch.current_qty = Decimal("50")
        mock_batch.consumed_qty = Decimal("0")

        self.db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 10,
                "barcode": "BARCODE123",
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertIn("consumption_no", result)

    def test_create_consumption_with_variance(self):
        """测试消耗差异识别"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.unit = "个"
        mock_material.current_stock = Decimal("100")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 120,  # 实际消耗
                "standard_qty": 100,  # 标准消耗
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertTrue(result["is_waste"])  # 差异20%，应标记为浪费
        self.assertEqual(result["variance_rate"], 20.0)

    def test_create_consumption_waste_detection(self):
        """测试浪费检测（差异>10%）"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.current_stock = Decimal("100")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 115,
                "standard_qty": 100,
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertTrue(result["is_waste"])

    def test_create_consumption_no_waste(self):
        """测试正常消耗（差异<10%）"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.current_stock = Decimal("100")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 105,
                "standard_qty": 100,
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertFalse(result["is_waste"])

    def test_create_consumption_with_batch_update(self):
        """测试批次库存更新"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.current_stock = Decimal("100")

        mock_batch = Mock()
        mock_batch.id = 5
        mock_batch.current_qty = Decimal("50")
        mock_batch.consumed_qty = Decimal("0")

        self.db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 30,
                "batch_id": 5,
            }

            self.service.create_consumption(consumption_data, self.current_user_id)

        # 验证批次库存更新
        self.assertEqual(mock_batch.current_qty, 20)  # 50 - 30
        self.assertEqual(mock_batch.consumed_qty, 30)

    def test_create_consumption_batch_depleted(self):
        """测试批次耗尽状态更新"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.current_stock = Decimal("100")

        mock_batch = Mock()
        mock_batch.id = 5
        mock_batch.current_qty = Decimal("10")
        mock_batch.consumed_qty = Decimal("0")
        mock_batch.status = "ACTIVE"

        self.db.query.return_value.filter.return_value.first.return_value = mock_batch

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 10,
                "batch_id": 5,
            }

            self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertEqual(mock_batch.status, "DEPLETED")

    def test_create_consumption_with_custom_unit_price(self):
        """测试自定义单价"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.current_stock = Decimal("100")
        mock_material.standard_price = Decimal("10")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            consumption_data = {
                "material_id": 1,
                "consumption_qty": 20,
                "unit_price": 15.5,  # 自定义单价
            }

            result = self.service.create_consumption(consumption_data, self.current_user_id)

        self.assertIn("consumption_no", result)

    def test_create_consumption_triggers_alert_check(self):
        """测试消耗后触发预警检查"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.current_stock = Decimal("100")

        with patch("app.utils.db_helpers.get_or_404", return_value=mock_material):
            with patch.object(self.service, "check_and_create_alerts") as mock_alert:
                consumption_data = {
                    "material_id": 1,
                    "consumption_qty": 50,
                }

                self.service.create_consumption(consumption_data, self.current_user_id)

                mock_alert.assert_called_once_with(mock_material)

    # ==================== 3. get_consumption_analysis 测试 (5个) ====================

    def test_get_consumption_analysis_basic(self):
        """测试基本消耗分析"""
        mock_consumption = Mock()
        mock_consumption.consumption_qty = Decimal("50")
        mock_consumption.total_cost = Decimal("500")
        mock_consumption.standard_qty = Decimal("45")
        mock_consumption.is_waste = False
        mock_consumption.consumption_date = datetime(2024, 1, 15)

        self.db.query.return_value.all.return_value = [mock_consumption]

        result = self.service.get_consumption_analysis()

        self.assertEqual(result["summary"]["total_records"], 1)
        self.assertEqual(result["summary"]["total_consumption"], 50.0)
        self.assertEqual(result["summary"]["total_cost"], 500.0)

    def test_get_consumption_analysis_with_filters(self):
        """测试带筛选条件的消耗分析"""
        self.db.query.return_value.all.return_value = []

        result = self.service.get_consumption_analysis(
            material_id=1,
            project_id=10,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        self.assertEqual(result["summary"]["total_records"], 0)

    def test_get_consumption_analysis_group_by_material(self):
        """测试按物料分组分析"""
        mock_c1 = Mock()
        mock_c1.material_code = "MAT001"
        mock_c1.material_name = "物料A"
        mock_c1.consumption_qty = Decimal("100")
        mock_c1.total_cost = Decimal("1000")
        mock_c1.is_waste = True

        mock_c2 = Mock()
        mock_c2.material_code = "MAT001"
        mock_c2.material_name = "物料A"
        mock_c2.consumption_qty = Decimal("50")
        mock_c2.total_cost = Decimal("500")
        mock_c2.is_waste = False

        self.db.query.return_value.all.return_value = [mock_c1, mock_c2]

        result = self.service.get_consumption_analysis(group_by="material")

        self.assertEqual(len(result["grouped_data"]), 1)
        self.assertEqual(result["grouped_data"][0]["total_qty"], 150.0)

    def test_get_consumption_analysis_group_by_day(self):
        """测试按日期分组分析"""
        mock_c = Mock()
        mock_c.consumption_qty = Decimal("50")
        mock_c.total_cost = Decimal("500")
        mock_c.consumption_date = datetime(2024, 1, 15)
        mock_c.standard_qty = None
        mock_c.is_waste = False

        self.db.query.return_value.all.return_value = [mock_c]

        result = self.service.get_consumption_analysis(group_by="day")

        self.assertEqual(len(result["grouped_data"]), 1)
        self.assertIn("2024-01-15", result["grouped_data"][0]["period"])

    def test_get_consumption_analysis_waste_rate(self):
        """测试浪费率计算"""
        mock_c1 = Mock()
        mock_c1.consumption_qty = Decimal("100")
        mock_c1.total_cost = Decimal("1000")
        mock_c1.standard_qty = Decimal("100")
        mock_c1.is_waste = True

        mock_c2 = Mock()
        mock_c2.consumption_qty = Decimal("50")
        mock_c2.total_cost = Decimal("500")
        mock_c2.standard_qty = Decimal("50")
        mock_c2.is_waste = False

        self.db.query.return_value.all.return_value = [mock_c1, mock_c2]

        result = self.service.get_consumption_analysis()

        self.assertEqual(result["summary"]["waste_count"], 1)
        self.assertEqual(result["summary"]["waste_rate"], 50.0)

    # ==================== 4. list_alerts 测试 (4个) ====================

    def test_list_alerts_basic(self):
        """测试基本预警列表查询"""
        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.alert_no = "ALERT-001"
        mock_alert.material_code = "MAT001"
        mock_alert.material_name = "测试物料"
        mock_alert.alert_type = "LOW_STOCK"
        mock_alert.alert_level = "WARNING"
        mock_alert.alert_date = datetime(2024, 1, 1)
        mock_alert.current_stock = Decimal("10")
        mock_alert.safety_stock = Decimal("50")
        mock_alert.shortage_qty = Decimal("40")
        mock_alert.days_to_stockout = 5
        mock_alert.alert_message = "库存不足"
        mock_alert.recommendation = "建议采购"
        mock_alert.status = "ACTIVE"
        mock_alert.assigned_to_id = None

        self.db.query.return_value.order_by.return_value.count.return_value = 1

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_alert]

            result = self.service.list_alerts()

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["alert_no"], "ALERT-001")

    def test_list_alerts_with_filters(self):
        """测试带筛选条件的预警列表"""
        self.db.query.return_value.order_by.return_value.count.return_value = 0

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []

            result = self.service.list_alerts(
                alert_type="SHORTAGE",
                alert_level="CRITICAL",
                material_id=5,
            )

        self.assertEqual(result["total"], 0)

    def test_list_alerts_pagination(self):
        """测试预警列表分页"""
        self.db.query.return_value.order_by.return_value.count.return_value = 50

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []

            result = self.service.list_alerts(page=2, page_size=10)

        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_size"], 10)

    def test_list_alerts_order_by_date(self):
        """测试预警列表按日期排序"""
        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []
            self.db.query.return_value.order_by.return_value.count.return_value = 0

            result = self.service.list_alerts()

        # 验证调用了 order_by
        self.db.query.return_value.order_by.assert_called()

    # ==================== 5. create_alert_rule 测试 (3个) ====================

    def test_create_alert_rule_basic(self):
        """测试基本预警规则创建"""
        rule_data = {
            "rule_name": "低库存预警",
            "alert_type": "LOW_STOCK",
            "threshold_value": 20,
        }

        with patch("app.utils.db_helpers.save_obj") as mock_save:
            mock_save.return_value = None

            result = self.service.create_alert_rule(rule_data, self.current_user_id)

        self.assertIn("rule_name", result)
        mock_save.assert_called_once()

    def test_create_alert_rule_with_material(self):
        """测试针对特定物料的预警规则"""
        rule_data = {
            "rule_name": "物料A低库存预警",
            "material_id": 5,
            "alert_type": "LOW_STOCK",
            "threshold_value": 30,
        }

        with patch("app.utils.db_helpers.save_obj"):
            result = self.service.create_alert_rule(rule_data, self.current_user_id)

        self.assertIn("rule_name", result)

    def test_create_alert_rule_with_category(self):
        """测试针对分类的预警规则"""
        rule_data = {
            "rule_name": "原材料分类预警",
            "category_id": 3,
            "alert_type": "SHORTAGE",
            "threshold_value": 10,
        }

        with patch("app.utils.db_helpers.save_obj"):
            result = self.service.create_alert_rule(rule_data, self.current_user_id)

        self.assertIn("rule_name", result)

    # ==================== 6. get_waste_records 测试 (4个) ====================

    def test_get_waste_records_basic(self):
        """测试基本浪费记录查询"""
        mock_waste = Mock()
        mock_waste.id = 1
        mock_waste.consumption_no = "CONS-001"
        mock_waste.material_code = "MAT001"
        mock_waste.material_name = "测试物料"
        mock_waste.consumption_date = datetime(2024, 1, 15)
        mock_waste.consumption_qty = Decimal("120")
        mock_waste.standard_qty = Decimal("100")
        mock_waste.variance_qty = Decimal("20")
        mock_waste.variance_rate = Decimal("20")
        mock_waste.consumption_type = "PRODUCTION"
        mock_waste.project_id = None
        mock_waste.work_order_id = None
        mock_waste.total_cost = Decimal("2000")
        mock_waste.remark = "测试浪费"
        mock_waste.unit_price = Decimal("10")

        self.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_waste]

            result = self.service.get_waste_records()

        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertIn("summary", result)

    def test_get_waste_records_with_filters(self):
        """测试带筛选条件的浪费记录"""
        self.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 0

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = []

            result = self.service.get_waste_records(
                material_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                min_variance_rate=15,
            )

        self.assertEqual(result["total"], 0)

    def test_get_waste_records_with_project_info(self):
        """测试浪费记录包含项目信息"""
        mock_waste = Mock()
        mock_waste.id = 1
        mock_waste.consumption_no = "CONS-001"
        mock_waste.material_code = "MAT001"
        mock_waste.material_name = "测试物料"
        mock_waste.consumption_date = datetime(2024, 1, 15)
        mock_waste.consumption_qty = Decimal("120")
        mock_waste.standard_qty = Decimal("100")
        mock_waste.variance_qty = Decimal("20")
        mock_waste.variance_rate = Decimal("20")
        mock_waste.consumption_type = "PRODUCTION"
        mock_waste.project_id = 10
        mock_waste.work_order_id = None
        mock_waste.total_cost = Decimal("2000")
        mock_waste.remark = None
        mock_waste.unit_price = Decimal("10")

        mock_project = Mock()
        mock_project.id = 10
        mock_project.project_name = "测试项目"

        self.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_waste]

            result = self.service.get_waste_records()

        self.assertEqual(result["items"][0]["project_name"], "测试项目")

    def test_get_waste_records_summary(self):
        """测试浪费记录汇总统计"""
        mock_waste = Mock()
        mock_waste.variance_qty = Decimal("20")
        mock_waste.unit_price = Decimal("10")
        mock_waste.consumption_date = datetime(2024, 1, 15)
        mock_waste.consumption_qty = Decimal("120")
        mock_waste.standard_qty = Decimal("100")
        mock_waste.variance_rate = Decimal("20")
        mock_waste.consumption_type = "PRODUCTION"
        mock_waste.project_id = None
        mock_waste.work_order_id = None
        mock_waste.total_cost = Decimal("2000")

        self.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1

        with patch("app.common.query_filters.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [mock_waste]

            result = self.service.get_waste_records()

        self.assertEqual(result["summary"]["total_waste_qty"], 20.0)
        self.assertEqual(result["summary"]["total_waste_cost"], 200.0)

    # ==================== 7. trace_batch 测试 (5个) ====================

    def test_trace_batch_by_id(self):
        """测试通过批次ID追溯"""
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.batch_no = "BATCH001"
        mock_batch.material_id = 5
        mock_batch.initial_qty = Decimal("100")
        mock_batch.current_qty = Decimal("50")
        mock_batch.consumed_qty = Decimal("50")
        mock_batch.production_date = date(2024, 1, 1)
        mock_batch.expire_date = date(2025, 1, 1)
        mock_batch.supplier_batch_no = "SUP001"
        mock_batch.quality_status = "QUALIFIED"
        mock_batch.warehouse_location = "A01"
        mock_batch.status = "ACTIVE"

        mock_material = Mock()
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_batch,  # 批次查询
            mock_material,  # 物料查询
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = self.service.trace_batch(batch_id=1)

        self.assertEqual(result["batch_info"]["batch_no"], "BATCH001")
        self.assertIn("consumption_trail", result)

    def test_trace_batch_by_batch_no(self):
        """测试通过批次号追溯"""
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.batch_no = "BATCH002"
        mock_batch.material_id = 5
        mock_batch.initial_qty = Decimal("100")
        mock_batch.current_qty = Decimal("50")
        mock_batch.consumed_qty = Decimal("50")
        mock_batch.production_date = None
        mock_batch.expire_date = None
        mock_batch.supplier_batch_no = None
        mock_batch.quality_status = None
        mock_batch.warehouse_location = None
        mock_batch.status = "ACTIVE"

        mock_material = Mock()
        mock_material.material_code = "MAT002"
        mock_material.material_name = "物料B"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_batch,
            mock_material,
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = self.service.trace_batch(batch_no="BATCH002")

        self.assertEqual(result["batch_info"]["batch_no"], "BATCH002")

    def test_trace_batch_by_barcode(self):
        """测试通过条码追溯"""
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.batch_no = "BATCH003"
        mock_batch.material_id = 5
        mock_batch.initial_qty = Decimal("200")
        mock_batch.current_qty = Decimal("100")
        mock_batch.consumed_qty = Decimal("100")
        mock_batch.production_date = None
        mock_batch.expire_date = None
        mock_batch.supplier_batch_no = None
        mock_batch.quality_status = None
        mock_batch.warehouse_location = None
        mock_batch.status = "ACTIVE"

        mock_material = Mock()
        mock_material.material_code = "MAT003"
        mock_material.material_name = "物料C"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            mock_batch,
            mock_material,
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = self.service.trace_batch(barcode="BARCODE123")

        self.assertEqual(result["batch_info"]["batch_no"], "BATCH003")

    def test_trace_batch_not_found(self):
        """测试批次不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.service.trace_batch(batch_id=999)

        self.assertEqual(context.exception.status_code, 404)

    def test_trace_batch_with_consumption_trail(self):
        """测试批次消耗追溯链"""
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.batch_no = "BATCH001"
        mock_batch.material_id = 5
        mock_batch.initial_qty = Decimal("100")
        mock_batch.current_qty = Decimal("20")
        mock_batch.consumed_qty = Decimal("80")
        mock_batch.production_date = None
        mock_batch.expire_date = None
        mock_batch.supplier_batch_no = None
        mock_batch.quality_status = None
        mock_batch.warehouse_location = None
        mock_batch.status = "ACTIVE"

        mock_material = Mock()
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"

        mock_consumption = Mock()
        mock_consumption.consumption_no = "CONS-001"
        mock_consumption.consumption_date = datetime(2024, 1, 15)
        mock_consumption.consumption_qty = Decimal("50")
        mock_consumption.consumption_type = "PRODUCTION"
        mock_consumption.project_id = 10
        mock_consumption.work_order_id = 20
        mock_consumption.operator_id = 1

        mock_project = Mock()
        mock_project.id = 10
        mock_project.project_no = "PROJ001"
        mock_project.project_name = "测试项目"

        mock_wo = Mock()
        mock_wo.id = 20
        mock_wo.work_order_no = "WO001"

        # 配置复杂的 Mock 返回序列
        first_call_results = [mock_batch, mock_material, mock_project, mock_wo]
        self.db.query.return_value.filter.return_value.first.side_effect = first_call_results
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_consumption
        ]

        result = self.service.trace_batch(batch_id=1)

        self.assertEqual(len(result["consumption_trail"]), 1)
        self.assertEqual(result["summary"]["total_consumptions"], 1)

    # ==================== 8. get_cost_analysis 测试 (3个) ====================

    def test_get_cost_analysis_basic(self):
        """测试基本成本分析"""
        mock_c = Mock()
        mock_c.material_id = 1
        mock_c.material_code = "MAT001"
        mock_c.material_name = "测试物料"
        mock_c.consumption_qty = Decimal("100")
        mock_c.total_cost = Decimal("1000")

        self.db.query.return_value.all.return_value = [mock_c]

        result = self.service.get_cost_analysis()

        self.assertEqual(result["total_cost"], 1000.0)
        self.assertEqual(result["material_count"], 1)

    def test_get_cost_analysis_with_filters(self):
        """测试带筛选条件的成本分析"""
        self.db.query.return_value.all.return_value = []

        result = self.service.get_cost_analysis(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            project_id=10,
        )

        self.assertEqual(result["total_cost"], 0)

    def test_get_cost_analysis_top_n(self):
        """测试Top N成本排序"""
        mock_materials = []
        for i in range(15):
            mock_c = Mock()
            mock_c.material_id = i + 1
            mock_c.material_code = f"MAT{i+1:03d}"
            mock_c.material_name = f"物料{i+1}"
            mock_c.consumption_qty = Decimal("100")
            mock_c.total_cost = Decimal(str((15 - i) * 100))
            mock_materials.append(mock_c)

        self.db.query.return_value.all.return_value = mock_materials

        result = self.service.get_cost_analysis(top_n=5)

        self.assertEqual(len(result["top_materials"]), 5)
        # 验证排序（最高成本在前）
        self.assertEqual(result["top_materials"][0]["material_code"], "MAT001")

    # ==================== 9. get_turnover_analysis 测试 (3个) ====================

    def test_get_turnover_analysis_basic(self):
        """测试基本库存周转率分析"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.current_stock = Decimal("100")

        mock_consumption = Mock()
        mock_consumption.consumption_qty = Decimal("300")

        self.db.query.return_value.filter.return_value.all.side_effect = [
            [mock_material],
            [mock_consumption],
        ]

        result = self.service.get_turnover_analysis(days=30)

        self.assertEqual(result["period_days"], 30)
        self.assertEqual(len(result["materials"]), 1)
        self.assertEqual(result["materials"][0]["turnover_rate"], 3.0)  # 300/100

    def test_get_turnover_analysis_zero_stock(self):
        """测试零库存周转率"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.current_stock = Decimal("0")

        self.db.query.return_value.filter.return_value.all.side_effect = [
            [mock_material],
            [],
        ]

        result = self.service.get_turnover_analysis()

        self.assertEqual(result["materials"][0]["turnover_rate"], 0)

    def test_get_turnover_analysis_with_filters(self):
        """测试带筛选条件的周转率分析"""
        self.db.query.return_value.filter.return_value.all.side_effect = [[], []]

        result = self.service.get_turnover_analysis(material_id=5, category_id=3)

        self.assertEqual(len(result["materials"]), 0)

    # ==================== 10. check_and_create_alerts 测试 (4个) ====================

    def test_check_and_create_alerts_low_stock_percentage(self):
        """测试低库存预警（百分比阈值）"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.current_stock = Decimal("15")
        mock_material.safety_stock = Decimal("50")

        mock_rule = Mock()
        mock_rule.alert_type = "LOW_STOCK"
        mock_rule.threshold_type = "PERCENTAGE"
        mock_rule.threshold_value = Decimal("50")
        mock_rule.alert_level = "WARNING"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        self.db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(
            self.service, "calculate_avg_daily_consumption", return_value=5.0
        ):
            self.service.check_and_create_alerts(mock_material)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_check_and_create_alerts_low_stock_fixed(self):
        """测试低库存预警（固定阈值）"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.current_stock = Decimal("5")
        mock_material.safety_stock = Decimal("50")

        mock_rule = Mock()
        mock_rule.alert_type = "LOW_STOCK"
        mock_rule.threshold_type = "FIXED"
        mock_rule.threshold_value = Decimal("10")
        mock_rule.alert_level = "CRITICAL"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        self.db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(
            self.service, "calculate_avg_daily_consumption", return_value=2.0
        ):
            self.service.check_and_create_alerts(mock_material)

        self.db.add.assert_called_once()

    def test_check_and_create_alerts_shortage(self):
        """测试缺料预警"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"
        mock_material.current_stock = Decimal("0")
        mock_material.safety_stock = Decimal("50")

        mock_rule = Mock()
        mock_rule.alert_type = "SHORTAGE"
        mock_rule.threshold_type = "FIXED"
        mock_rule.threshold_value = Decimal("0")
        mock_rule.alert_level = "CRITICAL"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        self.db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(
            self.service, "calculate_avg_daily_consumption", return_value=10.0
        ):
            self.service.check_and_create_alerts(mock_material)

        self.db.add.assert_called_once()

    def test_check_and_create_alerts_existing_alert(self):
        """测试已存在活动预警时不重复创建"""
        mock_material = Mock()
        mock_material.id = 1
        mock_material.current_stock = Decimal("5")
        mock_material.safety_stock = Decimal("50")

        mock_rule = Mock()
        mock_rule.alert_type = "LOW_STOCK"
        mock_rule.threshold_type = "FIXED"
        mock_rule.threshold_value = Decimal("10")

        mock_existing_alert = Mock()

        self.db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        self.db.query.return_value.filter.return_value.first.return_value = (
            mock_existing_alert
        )

        self.service.check_and_create_alerts(mock_material)

        # 不应该创建新预警
        self.db.add.assert_not_called()

    # ==================== 11. calculate_avg_daily_consumption 测试 (2个) ====================

    def test_calculate_avg_daily_consumption_basic(self):
        """测试计算平均日消耗"""
        mock_c1 = Mock()
        mock_c1.consumption_qty = Decimal("100")
        mock_c2 = Mock()
        mock_c2.consumption_qty = Decimal("200")

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_c1,
            mock_c2,
        ]

        result = self.service.calculate_avg_daily_consumption(material_id=1, days=30)

        self.assertEqual(result, 10.0)  # (100+200)/30

    def test_calculate_avg_daily_consumption_no_data(self):
        """测试无消耗数据时返回0"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.calculate_avg_daily_consumption(material_id=1, days=30)

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
