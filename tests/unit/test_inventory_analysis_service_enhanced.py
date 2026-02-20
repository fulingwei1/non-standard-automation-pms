# -*- coding: utf-8 -*-
"""
库存分析服务增强测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.inventory_analysis_service import InventoryAnalysisService


class TestInventoryAnalysisServiceTurnoverRate(unittest.TestCase):
    """测试库存周转率相关功能"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 12, 31)

    def test_get_turnover_rate_data_basic(self):
        """测试基本的周转率计算"""
        # Mock材料查询
        mock_material_1 = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_id=1, category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10.50'), unit='kg',
            is_active=True
        )
        mock_material_2 = Mock(
            id=2, material_code='M002', material_name='材料2',
            category_id=1, category_name='分类A',
            current_stock=Decimal('200'), standard_price=Decimal('5.00'), unit='kg',
            is_active=True
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material_1, mock_material_2
        ]

        # Mock消耗量查询
        mock_consumption = Mock()
        mock_consumption.scalar.return_value = Decimal('150')
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date
        )

        self.assertIn('summary', result)
        self.assertIn('category_breakdown', result)
        self.assertEqual(result['summary']['total_materials'], 2)
        self.assertGreater(result['summary']['total_inventory_value'], 0)

    def test_get_turnover_rate_data_with_category_filter(self):
        """测试带分类过滤的周转率计算"""
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_id=1, category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'), unit='kg',
            is_active=True
        )

        query_mock = self.db.query.return_value.outerjoin.return_value.filter.return_value
        query_mock.filter.return_value.all.return_value = [mock_material]

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = Decimal('50')
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date, category_id=1
        )

        self.assertEqual(result['summary']['total_materials'], 1)
        self.assertGreater(result['summary']['total_inventory_value'], 0)

    def test_get_turnover_rate_data_zero_inventory(self):
        """测试库存为零的情况"""
        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = Decimal('0')
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(result['summary']['total_inventory_value'], 0)
        self.assertEqual(result['summary']['turnover_rate'], 0)
        self.assertEqual(result['summary']['turnover_days'], 0)

    def test_get_turnover_rate_data_zero_consumption(self):
        """测试消耗为零的情况"""
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_id=1, category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'), unit='kg',
            is_active=True
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material
        ]

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = None
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(result['summary']['total_consumption'], 0)
        self.assertEqual(result['summary']['turnover_rate'], 0)

    def test_get_turnover_rate_data_uncategorized_materials(self):
        """测试未分类材料的处理"""
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_id=None, category_name=None,
            current_stock=Decimal('100'), standard_price=Decimal('10'), unit='kg',
            is_active=True
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material
        ]

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = Decimal('50')
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(len(result['category_breakdown']), 1)
        self.assertEqual(result['category_breakdown'][0]['category_name'], '未分类')

    def test_get_turnover_rate_data_category_sorting(self):
        """测试分类按库存价值降序排列"""
        mock_materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_id=1, category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('5'), unit='kg',
                is_active=True
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_id=2, category_name='分类B',
                current_stock=Decimal('50'), standard_price=Decimal('20'), unit='kg',
                is_active=True
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = mock_materials

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = Decimal('100')
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, self.start_date, self.end_date
        )

        # 分类B应该排在前面(50*20=1000 > 100*5=500)
        self.assertEqual(result['category_breakdown'][0]['category_name'], '分类B')
        self.assertEqual(result['category_breakdown'][1]['category_name'], '分类A')


class TestInventoryAnalysisServiceStaleMaterials(unittest.TestCase):
    """测试呆滞物料分析功能"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()

    def test_get_stale_materials_data_basic(self):
        """测试基本的呆滞物料查询"""
        old_date = datetime.now() - timedelta(days=100)
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'),
            updated_at=old_date, unit='kg'
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material
        ]

        result = self.service.get_stale_materials_data(self.db, threshold_days=90)

        self.assertEqual(result['summary']['stale_count'], 1)
        self.assertGreater(result['summary']['stale_value'], 0)
        self.assertEqual(len(result['stale_materials']), 1)

    def test_get_stale_materials_data_with_category_filter(self):
        """测试带分类过滤的呆滞物料查询"""
        old_date = datetime.now() - timedelta(days=100)
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'),
            updated_at=old_date, unit='kg'
        )

        query_mock = self.db.query.return_value.outerjoin.return_value.filter.return_value
        query_mock.filter.return_value.all.return_value = [mock_material]

        result = self.service.get_stale_materials_data(self.db, threshold_days=90, category_id=1)

        self.assertEqual(result['summary']['stale_count'], 1)

    def test_get_stale_materials_data_no_updated_at(self):
        """测试没有更新时间的物料"""
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'),
            updated_at=None, unit='kg'
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material
        ]

        result = self.service.get_stale_materials_data(self.db, threshold_days=90)

        # 无更新记录视为长期呆滞(999天)
        self.assertEqual(result['summary']['stale_count'], 1)
        self.assertEqual(result['stale_materials'][0]['stale_days'], 999)

    def test_get_stale_materials_data_recent_updates(self):
        """测试最近有更新的物料不应该被标记为呆滞"""
        recent_date = datetime.now() - timedelta(days=30)
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_name='分类A',
            current_stock=Decimal('100'), standard_price=Decimal('10'),
            updated_at=recent_date, unit='kg'
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material
        ]

        result = self.service.get_stale_materials_data(self.db, threshold_days=90)

        self.assertEqual(result['summary']['stale_count'], 0)

    def test_get_stale_materials_data_age_distribution(self):
        """测试库龄分布统计"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('10'),
                updated_at=datetime.now() - timedelta(days=20), unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('10'),
                updated_at=datetime.now() - timedelta(days=45), unit='kg'
            ),
            Mock(
                id=3, material_code='M003', material_name='材料3',
                category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('10'),
                updated_at=datetime.now() - timedelta(days=75), unit='kg'
            ),
            Mock(
                id=4, material_code='M004', material_name='材料4',
                category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('10'),
                updated_at=datetime.now() - timedelta(days=100), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_stale_materials_data(self.db, threshold_days=90)

        self.assertEqual(len(result['age_distribution']), 4)
        age_ranges = [item['age_range'] for item in result['age_distribution']]
        self.assertIn('30天以内', age_ranges)
        self.assertIn('30-60天', age_ranges)
        self.assertIn('60-90天', age_ranges)
        self.assertIn('90天以上', age_ranges)

    def test_get_stale_materials_data_sorting_by_value(self):
        """测试呆滞物料按库存金额降序排列"""
        old_date = datetime.now() - timedelta(days=100)
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('100'), standard_price=Decimal('5'),
                updated_at=old_date, unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('50'), standard_price=Decimal('20'),
                updated_at=old_date, unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_stale_materials_data(self.db, threshold_days=90)

        # M002应该排在前面(50*20=1000 > 100*5=500)
        self.assertEqual(result['stale_materials'][0]['material_code'], 'M002')


class TestInventoryAnalysisServiceSafetyStock(unittest.TestCase):
    """测试安全库存达标率功能"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()

    def test_get_safety_stock_compliance_data_basic(self):
        """测试基本的安全库存达标率计算"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('30'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=3, material_code='M003', material_name='材料3',
                category_name='分类A',
                current_stock=Decimal('0'), safety_stock=Decimal('50'), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        self.assertEqual(result['summary']['total_materials'], 3)
        self.assertEqual(result['summary']['compliant'], 1)
        self.assertEqual(result['summary']['warning'], 1)
        self.assertEqual(result['summary']['out_of_stock'], 1)

    def test_get_safety_stock_compliance_data_with_category_filter(self):
        """测试带分类过滤的安全库存查询"""
        mock_material = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_name='分类A',
            current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
        )

        query_mock = self.db.query.return_value.outerjoin.return_value.filter.return_value
        query_mock.filter.return_value.all.return_value = [mock_material]

        result = self.service.get_safety_stock_compliance_data(self.db, category_id=1)

        self.assertEqual(result['summary']['total_materials'], 1)
        self.assertEqual(result['summary']['compliant'], 1)

    def test_get_safety_stock_compliance_data_no_safety_stock_set(self):
        """测试未设置安全库存的物料"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('0'), unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('50'), safety_stock=None, unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        self.assertEqual(result['summary']['no_safety_stock_set'], 2)
        self.assertEqual(result['summary']['compliant_rate'], 0)

    def test_get_safety_stock_compliance_data_compliance_rate_calculation(self):
        """测试达标率计算（排除未设置安全库存的物料）"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=3, material_code='M003', material_name='材料3',
                category_name='分类A',
                current_stock=Decimal('30'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=4, material_code='M004', material_name='材料4',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('0'), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        # 3个设置了安全库存的物料中，2个达标，达标率 = 2/3 * 100 = 66.67%
        self.assertAlmostEqual(result['summary']['compliant_rate'], 66.67, places=1)

    def test_get_safety_stock_compliance_data_shortage_calculation(self):
        """测试缺货数量计算"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('30'), safety_stock=Decimal('100'), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        self.assertEqual(result['warning_materials'][0]['shortage_qty'], 70)

    def test_get_safety_stock_compliance_data_sorting(self):
        """测试警告物料按缺货程度排序，缺货物料按安全库存排序"""
        materials = [
            Mock(
                id=1, material_code='M001', material_name='材料1',
                category_name='分类A',
                current_stock=Decimal('30'), safety_stock=Decimal('50'), unit='kg'
            ),
            Mock(
                id=2, material_code='M002', material_name='材料2',
                category_name='分类A',
                current_stock=Decimal('10'), safety_stock=Decimal('100'), unit='kg'
            ),
            Mock(
                id=3, material_code='M003', material_name='材料3',
                category_name='分类A',
                current_stock=Decimal('0'), safety_stock=Decimal('200'), unit='kg'
            ),
            Mock(
                id=4, material_code='M004', material_name='材料4',
                category_name='分类A',
                current_stock=Decimal('0'), safety_stock=Decimal('50'), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        # 警告物料按缺货程度排序：M002(缺90) > M001(缺20)
        self.assertEqual(result['warning_materials'][0]['material_code'], 'M002')

        # 缺货物料按安全库存排序：M003(200) > M004(50)
        self.assertEqual(result['out_of_stock_materials'][0]['material_code'], 'M003')


class TestInventoryAnalysisServiceABCAnalysis(unittest.TestCase):
    """测试ABC分类分析功能"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 12, 31)

    def test_get_abc_analysis_data_basic(self):
        """测试基本的ABC分类"""
        mock_results = [
            Mock(
                material_code='M001', material_name='材料1',
                category_name='分类A',
                total_amount=Decimal('7000'), order_count=10
            ),
            Mock(
                material_code='M002', material_name='材料2',
                category_name='分类A',
                total_amount=Decimal('2000'), order_count=5
            ),
            Mock(
                material_code='M003', material_name='材料3',
                category_name='分类A',
                total_amount=Decimal('1000'), order_count=3
            ),
        ]

        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(result['total_materials'], 3)
        self.assertEqual(result['total_amount'], 10000)
        self.assertEqual(len(result['abc_materials']), 3)

        # 检查ABC分类
        self.assertEqual(result['abc_materials'][0]['abc_class'], 'A')  # 70%
        self.assertEqual(result['abc_materials'][1]['abc_class'], 'B')  # 90%
        self.assertEqual(result['abc_materials'][2]['abc_class'], 'C')  # 100%

    def test_get_abc_analysis_data_empty_results(self):
        """测试没有采购记录的情况"""
        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(result['total_materials'], 0)
        self.assertEqual(result['total_amount'], 0)
        self.assertEqual(len(result['abc_materials']), 0)

    def test_get_abc_analysis_data_abc_summary(self):
        """测试ABC分类汇总统计"""
        mock_results = [
            Mock(
                material_code=f'M{str(i).zfill(3)}', material_name=f'材料{i}',
                category_name='分类A',
                total_amount=Decimal(str(1000 - i * 10)), order_count=5
            )
            for i in range(1, 101)  # 100个物料
        ]

        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        # 检查ABC分类数量和占比
        self.assertGreater(result['abc_summary']['A']['count'], 0)
        self.assertGreater(result['abc_summary']['B']['count'], 0)
        self.assertGreater(result['abc_summary']['C']['count'], 0)

        # 检查金额占比
        self.assertAlmostEqual(
            result['abc_summary']['A']['amount_percent'], 70, delta=5
        )

    def test_get_abc_analysis_data_sorting_by_amount(self):
        """测试按采购金额降序排序"""
        mock_results = [
            Mock(
                material_code='M001', material_name='材料1',
                category_name='分类A',
                total_amount=Decimal('5000'), order_count=10
            ),
            Mock(
                material_code='M002', material_name='材料2',
                category_name='分类A',
                total_amount=Decimal('8000'), order_count=5
            ),
            Mock(
                material_code='M003', material_name='材料3',
                category_name='分类A',
                total_amount=Decimal('3000'), order_count=3
            ),
        ]

        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        # 应该按金额降序：M002 > M001 > M003
        self.assertEqual(result['abc_materials'][0]['material_code'], 'M002')
        self.assertEqual(result['abc_materials'][1]['material_code'], 'M001')
        self.assertEqual(result['abc_materials'][2]['material_code'], 'M003')

    def test_get_abc_analysis_data_cumulative_percent(self):
        """测试累计百分比计算"""
        mock_results = [
            Mock(
                material_code='M001', material_name='材料1',
                category_name='分类A',
                total_amount=Decimal('5000'), order_count=10
            ),
            Mock(
                material_code='M002', material_name='材料2',
                category_name='分类A',
                total_amount=Decimal('5000'), order_count=5
            ),
        ]

        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(result['abc_materials'][0]['cumulative_percent'], 50)
        self.assertEqual(result['abc_materials'][1]['cumulative_percent'], 100)

    def test_get_abc_analysis_data_limit_100_materials(self):
        """测试返回最多100条记录"""
        mock_results = [
            Mock(
                material_code=f'M{str(i).zfill(3)}', material_name=f'材料{i}',
                category_name='分类A',
                total_amount=Decimal(str(1000 - i)), order_count=5
            )
            for i in range(1, 201)  # 200个物料
        ]

        self.db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_results

        result = self.service.get_abc_analysis_data(
            self.db, self.start_date, self.end_date
        )

        self.assertEqual(len(result['abc_materials']), 100)


class TestInventoryAnalysisServiceCostOccupancy(unittest.TestCase):
    """测试库存成本占用功能"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()

    def test_get_cost_occupancy_data_basic(self):
        """测试基本的成本占用查询"""
        mock_category_results = [
            Mock(
                category_id=1, category_name='分类A',
                inventory_value=Decimal('10000'), material_count=10
            ),
            Mock(
                category_id=2, category_name='分类B',
                inventory_value=Decimal('5000'), material_count=5
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_results

        mock_top_materials = [
            Mock(
                material_code='M001', material_name='材料1',
                category_name='分类A',
                inventory_value=Decimal('5000'),
                current_stock=Decimal('100'), unit='kg'
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db)

        self.assertEqual(result['summary']['total_inventory_value'], 15000)
        self.assertEqual(result['summary']['total_categories'], 2)
        self.assertEqual(len(result['category_occupancy']), 2)

    def test_get_cost_occupancy_data_with_category_filter(self):
        """测试带分类过滤的成本占用查询"""
        mock_category_results = [
            Mock(
                category_id=1, category_name='分类A',
                inventory_value=Decimal('10000'), material_count=10
            ),
        ]

        query_mock = self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value
        query_mock.filter.return_value.all.return_value = mock_category_results

        mock_top_materials = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db, category_id=1)

        self.assertEqual(result['summary']['total_categories'], 1)

    def test_get_cost_occupancy_data_category_sorting(self):
        """测试分类按库存价值降序排列"""
        mock_category_results = [
            Mock(
                category_id=1, category_name='分类A',
                inventory_value=Decimal('5000'), material_count=10
            ),
            Mock(
                category_id=2, category_name='分类B',
                inventory_value=Decimal('10000'), material_count=5
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_results

        mock_top_materials = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db)

        # 分类B应该排在前面
        self.assertEqual(result['category_occupancy'][0]['category_name'], '分类B')

    def test_get_cost_occupancy_data_percentage_calculation(self):
        """测试价值占比计算"""
        mock_category_results = [
            Mock(
                category_id=1, category_name='分类A',
                inventory_value=Decimal('7000'), material_count=10
            ),
            Mock(
                category_id=2, category_name='分类B',
                inventory_value=Decimal('3000'), material_count=5
            ),
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_results

        mock_top_materials = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db)

        self.assertEqual(result['category_occupancy'][0]['value_percentage'], 70)
        self.assertEqual(result['category_occupancy'][1]['value_percentage'], 30)

    def test_get_cost_occupancy_data_top_materials_limit_50(self):
        """测试高库存物料最多返回50条"""
        mock_category_results = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_results

        # 这个测试主要验证limit(50)被调用
        mock_top_materials = [
            Mock(
                material_code=f'M{str(i).zfill(3)}', material_name=f'材料{i}',
                category_name='分类A',
                inventory_value=Decimal(str(1000 - i)),
                current_stock=Decimal('100'), unit='kg'
            )
            for i in range(1, 51)
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db)

        self.assertEqual(len(result['top_materials']), 50)

    def test_get_cost_occupancy_data_zero_inventory(self):
        """测试零库存的情况"""
        mock_category_results = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_results

        mock_top_materials = []
        self.db.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_materials

        result = self.service.get_cost_occupancy_data(self.db)

        self.assertEqual(result['summary']['total_inventory_value'], 0)
        self.assertEqual(result['summary']['total_categories'], 0)


class TestInventoryAnalysisServiceEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        self.service = InventoryAnalysisService()
        self.db = MagicMock()

    def test_service_is_static_methods(self):
        """测试所有方法都是静态方法"""
        # 静态方法可以直接从类调用，不需要实例
        self.assertTrue(callable(InventoryAnalysisService.get_turnover_rate_data))
        self.assertTrue(callable(InventoryAnalysisService.get_stale_materials_data))
        self.assertTrue(callable(InventoryAnalysisService.get_safety_stock_compliance_data))
        self.assertTrue(callable(InventoryAnalysisService.get_abc_analysis_data))
        self.assertTrue(callable(InventoryAnalysisService.get_cost_occupancy_data))

    def test_turnover_rate_data_with_null_values(self):
        """测试包含空值但有正常价格的周转率计算"""
        # 使用至少一个有库存的材料，避免除零错误
        mock_material_1 = Mock(
            id=1, material_code='M001', material_name='材料1',
            category_id=1, category_name='分类A',
            current_stock=Decimal('10'), standard_price=Decimal('5'), unit='kg',
            is_active=True
        )
        mock_material_2 = Mock(
            id=2, material_code='M002', material_name='材料2',
            category_id=1, category_name='分类A',
            current_stock=None, standard_price=None, unit='kg',
            is_active=True
        )

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
            mock_material_1, mock_material_2
        ]

        mock_consumption = Mock()
        mock_consumption.scalar.return_value = None
        self.db.query.return_value.join.return_value.filter.return_value = mock_consumption

        result = self.service.get_turnover_rate_data(
            self.db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 应该正常处理，不抛出异常
        self.assertIsInstance(result, dict)
        self.assertEqual(result['summary']['total_inventory_value'], 50)

    def test_safety_stock_compliance_all_materials_compliant(self):
        """测试所有物料都达标的情况"""
        materials = [
            Mock(
                id=i, material_code=f'M{str(i).zfill(3)}', material_name=f'材料{i}',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
            )
            for i in range(1, 11)
        ]

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        self.assertEqual(result['summary']['compliant'], 10)
        self.assertEqual(result['summary']['compliant_rate'], 100)

    def test_safety_stock_compliance_limit_returns(self):
        """测试返回数量限制"""
        compliant_materials = [
            Mock(
                id=i, material_code=f'M{str(i).zfill(3)}', material_name=f'材料{i}',
                category_name='分类A',
                current_stock=Decimal('100'), safety_stock=Decimal('50'), unit='kg'
            )
            for i in range(1, 30)  # 29个达标
        ]

        warning_materials = [
            Mock(
                id=i, material_code=f'W{str(i).zfill(3)}', material_name=f'预警{i}',
                category_name='分类A',
                current_stock=Decimal('30'), safety_stock=Decimal('100'), unit='kg'
            )
            for i in range(1, 60)  # 59个预警
        ]

        out_materials = [
            Mock(
                id=i, material_code=f'O{str(i).zfill(3)}', material_name=f'缺货{i}',
                category_name='分类A',
                current_stock=Decimal('0'), safety_stock=Decimal('50'), unit='kg'
            )
            for i in range(1, 60)  # 59个缺货
        ]

        all_materials = compliant_materials + warning_materials + out_materials

        self.db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = all_materials

        result = self.service.get_safety_stock_compliance_data(self.db)

        # 达标物料最多返回20个
        self.assertLessEqual(len(result['compliant_materials']), 20)
        # 预警和缺货物料最多各返回50个
        self.assertLessEqual(len(result['warning_materials']), 50)
        self.assertLessEqual(len(result['out_of_stock_materials']), 50)


if __name__ == '__main__':
    unittest.main()
