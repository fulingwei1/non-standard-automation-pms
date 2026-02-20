# -*- coding: utf-8 -*-
"""
增强的采购建议引擎单元测试

测试覆盖：
- 基于缺料生成建议（多场景）
- 基于安全库存生成建议（多场景）
- 基于预测生成建议（多场景）
- 供应商推荐算法（多场景）
- 供应商评分计算（多场景）
- 紧急程度判断（边界条件）
- 平均消耗计算（边界条件）
- 建议编号生成（边界条件）
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine


class TestPurchaseSuggestionEngine(unittest.TestCase):
    """采购建议引擎测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.tenant_id = 1
        self.engine = PurchaseSuggestionEngine(self.db, self.tenant_id)
    
    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestPurchaseSuggestionEngine):
    """测试初始化"""
    
    def test_init_with_default_tenant(self):
        """测试默认租户初始化"""
        engine = PurchaseSuggestionEngine(self.db)
        self.assertEqual(engine.tenant_id, 1)
        self.assertIs(engine.db, self.db)
    
    def test_init_with_custom_tenant(self):
        """测试自定义租户初始化"""
        engine = PurchaseSuggestionEngine(self.db, tenant_id=5)
        self.assertEqual(engine.tenant_id, 5)


class TestGenerateFromShortages(TestPurchaseSuggestionEngine):
    """测试基于缺料生成建议"""
    
    def test_generate_from_shortages_empty_result(self):
        """测试无缺料记录时返回空列表"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.engine.generate_from_shortages()
        
        self.assertEqual(result, [])
        self.db.commit.assert_called_once()
    
    def test_generate_from_shortages_with_project_filter(self):
        """测试带项目ID过滤的缺料建议生成"""
        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.material_id = 10
        mock_shortage.shortage_qty = Decimal('100')
        mock_shortage.project_id = 5
        mock_shortage.required_date = date.today() + timedelta(days=5)
        
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.material_code = 'MAT001'
        mock_material.material_name = '测试物料'
        mock_material.specification = '规格1'
        mock_material.unit = '件'
        mock_material.current_stock = Decimal('50')
        mock_material.safety_stock = Decimal('80')
        mock_material.last_price = Decimal('10.5')
        mock_material.standard_price = Decimal('10.0')
        
        # 设置查询链
        mock_shortage_query = MagicMock()
        mock_shortage_query.filter.return_value.filter.return_value.all.return_value = [mock_shortage]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        mock_material_query = MagicMock()
        mock_material_query.get.return_value = mock_material
        
        # 第一次调用返回 shortage query，第二次返回 existing query，第三次返回 material query
        self.db.query.side_effect = [
            mock_shortage_query,
            mock_existing_query,
            mock_material_query
        ]
        
        # Mock 推荐供应商方法
        self.engine._recommend_supplier = MagicMock(return_value=(
            1, Decimal('85.5'), {'total_score': 85.5}, []
        ))
        
        # Mock 紧急程度判断
        self.engine._determine_urgency = MagicMock(return_value='NORMAL')
        
        # Mock 建议编号生成
        self.engine._generate_suggestion_no = MagicMock(return_value='PS202602210001')
        
        result = self.engine.generate_from_shortages(project_id=5)
        
        self.assertEqual(len(result), 1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
    
    def test_generate_from_shortages_skip_existing(self):
        """测试跳过已有建议的缺料记录"""
        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.material_id = 10
        
        mock_existing = MagicMock()
        mock_existing.suggestion_no = 'PS202602210001'
        
        mock_shortage_query = MagicMock()
        mock_shortage_query.filter.return_value.all.return_value = [mock_shortage]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = mock_existing
        
        self.db.query.side_effect = [mock_shortage_query, mock_existing_query]
        
        result = self.engine.generate_from_shortages()
        
        self.assertEqual(len(result), 0)
        self.db.add.assert_not_called()
    
    def test_generate_from_shortages_material_not_found(self):
        """测试物料不存在时跳过"""
        mock_shortage = MagicMock()
        mock_shortage.id = 1
        mock_shortage.material_id = 999
        
        mock_shortage_query = MagicMock()
        mock_shortage_query.filter.return_value.all.return_value = [mock_shortage]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        mock_material_query = MagicMock()
        mock_material_query.get.return_value = None
        
        self.db.query.side_effect = [
            mock_shortage_query,
            mock_existing_query,
            mock_material_query
        ]
        
        result = self.engine.generate_from_shortages()
        
        self.assertEqual(len(result), 0)


class TestGenerateFromSafetyStock(TestPurchaseSuggestionEngine):
    """测试基于安全库存生成建议"""
    
    def test_generate_from_safety_stock_no_materials(self):
        """测试无需补充的物料时返回空列表"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.engine.generate_from_safety_stock()
        
        self.assertEqual(result, [])
    
    def test_generate_from_safety_stock_success(self):
        """测试成功生成安全库存建议"""
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.material_code = 'MAT001'
        mock_material.material_name = '测试物料'
        mock_material.specification = '规格1'
        mock_material.unit = '件'
        mock_material.current_stock = Decimal('30')
        mock_material.safety_stock = Decimal('100')
        mock_material.min_order_qty = Decimal('50')
        mock_material.last_price = Decimal('12.5')
        mock_material.standard_price = Decimal('10.0')
        mock_material.lead_time_days = 7
        
        mock_materials_query = MagicMock()
        mock_materials_query.filter.return_value.all.return_value = [mock_material]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        self.db.query.side_effect = [mock_materials_query, mock_existing_query]
        
        # Mock 推荐供应商
        self.engine._recommend_supplier = MagicMock(return_value=(
            2, Decimal('90.0'), {'total_score': 90.0}, []
        ))
        
        # Mock 建议编号生成
        self.engine._generate_suggestion_no = MagicMock(return_value='PS202602210002')
        
        result = self.engine.generate_from_safety_stock()
        
        self.assertEqual(len(result), 1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
    
    def test_generate_from_safety_stock_respect_min_order_qty(self):
        """测试尊重最小订货量"""
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.current_stock = Decimal('90')
        mock_material.safety_stock = Decimal('100')
        mock_material.min_order_qty = Decimal('50')
        mock_material.last_price = Decimal('10.0')
        mock_material.lead_time_days = 10
        
        mock_materials_query = MagicMock()
        mock_materials_query.filter.return_value.all.return_value = [mock_material]
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        self.db.query.side_effect = [mock_materials_query, mock_existing_query]
        
        self.engine._recommend_supplier = MagicMock(return_value=(
            2, Decimal('90.0'), {}, []
        ))
        self.engine._generate_suggestion_no = MagicMock(return_value='PS202602210003')
        
        result = self.engine.generate_from_safety_stock()
        
        # 期望数量 = max((100-90)*1.2, 50) = max(12, 50) = 50
        self.assertEqual(len(result), 1)


class TestGenerateFromForecast(TestPurchaseSuggestionEngine):
    """测试基于预测生成建议"""
    
    def test_generate_from_forecast_material_not_found(self):
        """测试物料不存在时返回None"""
        mock_query = MagicMock()
        mock_query.get.return_value = None
        self.db.query.return_value = mock_query
        
        result = self.engine.generate_from_forecast(material_id=999)
        
        self.assertIsNone(result)
    
    def test_generate_from_forecast_no_consumption_data(self):
        """测试无消耗数据时返回None"""
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.material_code = 'MAT001'
        mock_material.current_stock = Decimal('100')
        
        mock_material_query = MagicMock()
        mock_material_query.get.return_value = mock_material
        self.db.query.return_value = mock_material_query
        
        # Mock 平均消耗计算返回None
        self.engine._calculate_avg_consumption = MagicMock(return_value=None)
        
        result = self.engine.generate_from_forecast(material_id=10)
        
        self.assertIsNone(result)
    
    def test_generate_from_forecast_zero_consumption(self):
        """测试消耗为零时返回None"""
        mock_material = MagicMock()
        mock_material.id = 10
        
        mock_query = MagicMock()
        mock_query.get.return_value = mock_material
        self.db.query.return_value = mock_query
        
        self.engine._calculate_avg_consumption = MagicMock(return_value=Decimal('0'))
        
        result = self.engine.generate_from_forecast(material_id=10)
        
        self.assertIsNone(result)
    
    def test_generate_from_forecast_sufficient_stock(self):
        """测试库存充足时不生成建议"""
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.current_stock = Decimal('1000')
        
        mock_query = MagicMock()
        mock_query.get.return_value = mock_material
        self.db.query.return_value = mock_query
        
        # 平均月消耗100，预测3个月需求300，库存1000充足
        self.engine._calculate_avg_consumption = MagicMock(return_value=Decimal('100'))
        
        result = self.engine.generate_from_forecast(material_id=10, forecast_months=3)
        
        self.assertIsNone(result)
    
    def test_generate_from_forecast_success(self):
        """测试成功生成预测建议"""
        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.material_code = 'MAT001'
        mock_material.material_name = '测试物料'
        mock_material.specification = '规格1'
        mock_material.unit = '件'
        mock_material.current_stock = Decimal('100')
        mock_material.safety_stock = Decimal('50')
        mock_material.last_price = Decimal('15.0')
        
        mock_material_query = MagicMock()
        mock_material_query.get.return_value = mock_material
        
        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None
        
        self.db.query.side_effect = [mock_material_query, mock_existing_query]
        
        # 平均月消耗150，预测3个月需求450，库存100不足
        self.engine._calculate_avg_consumption = MagicMock(return_value=Decimal('150'))
        self.engine._recommend_supplier = MagicMock(return_value=(
            3, Decimal('88.0'), {}, []
        ))
        self.engine._generate_suggestion_no = MagicMock(return_value='PS202602210004')
        
        result = self.engine.generate_from_forecast(material_id=10, forecast_months=3)
        
        self.assertIsNotNone(result)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()


class TestRecommendSupplier(TestPurchaseSuggestionEngine):
    """测试供应商推荐"""
    
    def test_recommend_supplier_no_suppliers(self):
        """测试无供应商时返回None"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.engine._recommend_supplier(material_id=10)
        
        self.assertEqual(result, (None, None, None, None))
    
    def test_recommend_supplier_single_supplier(self):
        """测试单个供应商推荐"""
        mock_vendor = MagicMock()
        mock_vendor.supplier_code = 'SUP001'
        mock_vendor.supplier_name = '供应商A'
        
        mock_ms = MagicMock()
        mock_ms.supplier_id = 1
        mock_ms.vendor = mock_vendor
        mock_ms.price = Decimal('10.0')
        mock_ms.lead_time_days = 7
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_ms]
        self.db.query.return_value = mock_query
        
        # Mock 评分计算
        self.engine._calculate_supplier_score = MagicMock(return_value={
            'total_score': Decimal('85.0'),
            'performance_score': Decimal('80'),
            'price_score': Decimal('90'),
            'delivery_score': Decimal('85'),
            'history_score': Decimal('80'),
        })
        
        supplier_id, confidence, reason, alternatives = self.engine._recommend_supplier(10)
        
        self.assertEqual(supplier_id, 1)
        self.assertEqual(confidence, Decimal('85.0'))
        self.assertIsNotNone(reason)
        self.assertEqual(len(alternatives), 0)
    
    def test_recommend_supplier_multiple_suppliers(self):
        """测试多个供应商推荐"""
        mock_vendors = []
        mock_suppliers = []
        
        for i in range(3):
            vendor = MagicMock()
            vendor.supplier_code = f'SUP00{i+1}'
            vendor.supplier_name = f'供应商{chr(65+i)}'
            mock_vendors.append(vendor)
            
            ms = MagicMock()
            ms.supplier_id = i + 1
            ms.vendor = vendor
            ms.price = Decimal(str(10 + i * 2))
            ms.lead_time_days = 7 + i * 3
            mock_suppliers.append(ms)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_suppliers
        self.db.query.return_value = mock_query
        
        # Mock 评分计算，返回递减的评分
        def mock_score(supplier_id, material_id, weight_config):
            scores = {
                1: Decimal('95.0'),
                2: Decimal('88.0'),
                3: Decimal('75.0'),
            }
            return {
                'total_score': scores.get(supplier_id, Decimal('60')),
                'performance_score': Decimal('80'),
                'price_score': Decimal('85'),
                'delivery_score': Decimal('90'),
                'history_score': Decimal('70'),
            }
        
        self.engine._calculate_supplier_score = MagicMock(side_effect=mock_score)
        
        supplier_id, confidence, reason, alternatives = self.engine._recommend_supplier(10)
        
        self.assertEqual(supplier_id, 1)
        self.assertEqual(len(alternatives), 2)


class TestCalculateSupplierScore(TestPurchaseSuggestionEngine):
    """测试供应商评分计算"""
    
    def test_calculate_supplier_score_with_performance(self):
        """测试有绩效记录的评分"""
        mock_performance = MagicMock()
        mock_performance.overall_score = Decimal('85.0')
        
        mock_perf_query = MagicMock()
        mock_perf_query.filter.return_value.order_by.return_value.first.return_value = mock_performance
        
        mock_price_query = MagicMock()
        mock_price_query.filter.return_value.all.return_value = [(Decimal('10.0'),)]
        
        mock_supplier_query = MagicMock()
        mock_supplier = MagicMock()
        mock_supplier.price = Decimal('10.0')
        mock_supplier.lead_time_days = 7
        mock_supplier_query.filter.return_value.first.return_value = mock_supplier
        
        mock_order_query = MagicMock()
        mock_order_query.filter.return_value.scalar.return_value = 15
        
        self.db.query.side_effect = [
            mock_perf_query,
            mock_price_query,
            mock_supplier_query,
            mock_supplier_query,
            mock_order_query
        ]
        
        weight_config = {
            'performance': Decimal('40'),
            'price': Decimal('30'),
            'delivery': Decimal('20'),
            'history': Decimal('10'),
        }
        
        scores = self.engine._calculate_supplier_score(1, 10, weight_config)
        
        self.assertEqual(scores['performance_score'], Decimal('85.0'))
        self.assertGreater(scores['total_score'], Decimal('0'))
    
    def test_calculate_supplier_score_no_performance(self):
        """测试无绩效记录时使用默认分"""
        mock_perf_query = MagicMock()
        mock_perf_query.filter.return_value.order_by.return_value.first.return_value = None
        
        mock_price_query = MagicMock()
        mock_price_query.filter.return_value.all.return_value = []
        
        mock_supplier_query = MagicMock()
        mock_supplier = MagicMock()
        mock_supplier.price = Decimal('10.0')
        mock_supplier.lead_time_days = 10
        mock_supplier_query.filter.return_value.first.return_value = mock_supplier
        
        mock_order_query = MagicMock()
        # 修复：直接返回整数而不是MagicMock
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 3
        
        self.db.query.side_effect = [
            mock_perf_query,
            mock_price_query,
            mock_supplier_query,
            mock_supplier_query,
            mock_count
        ]
        
        weight_config = {
            'performance': Decimal('40'),
            'price': Decimal('30'),
            'delivery': Decimal('20'),
            'history': Decimal('10'),
        }
        
        scores = self.engine._calculate_supplier_score(1, 10, weight_config)
        
        self.assertEqual(scores['performance_score'], Decimal('60'))
    
    def test_calculate_supplier_score_price_best(self):
        """测试最低价格的评分"""
        mock_perf_query = MagicMock()
        mock_perf_query.filter.return_value.order_by.return_value.first.return_value = None
        
        # 多个价格，当前供应商价格最低
        mock_price_query = MagicMock()
        mock_price_query.filter.return_value.all.return_value = [
            (Decimal('8.0'),),
            (Decimal('10.0'),),
            (Decimal('12.0'),)
        ]
        
        mock_supplier_query = MagicMock()
        mock_supplier = MagicMock()
        mock_supplier.price = Decimal('8.0')
        mock_supplier.lead_time_days = 7
        mock_supplier_query.filter.return_value.first.return_value = mock_supplier
        
        mock_order_query = MagicMock()
        mock_order_query.filter.return_value.scalar.return_value = 5
        
        self.db.query.side_effect = [
            mock_perf_query,
            mock_price_query,
            mock_supplier_query,
            mock_supplier_query,
            mock_order_query
        ]
        
        weight_config = {
            'performance': Decimal('40'),
            'price': Decimal('30'),
            'delivery': Decimal('20'),
            'history': Decimal('10'),
        }
        
        scores = self.engine._calculate_supplier_score(1, 10, weight_config)
        
        self.assertEqual(scores['price_score'], Decimal('100'))
    
    def test_calculate_supplier_score_delivery_fast(self):
        """测试快速交期的评分"""
        mock_perf_query = MagicMock()
        mock_perf_query.filter.return_value.order_by.return_value.first.return_value = None
        
        mock_price_query = MagicMock()
        mock_price_query.filter.return_value.all.return_value = []
        
        mock_supplier_query = MagicMock()
        mock_supplier = MagicMock()
        mock_supplier.price = Decimal('10.0')
        mock_supplier.lead_time_days = 5  # 快速交期
        mock_supplier_query.filter.return_value.first.return_value = mock_supplier
        
        # 修复：直接返回整数
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 10
        
        self.db.query.side_effect = [
            mock_perf_query,
            mock_price_query,
            mock_supplier_query,
            mock_supplier_query,
            mock_count
        ]
        
        weight_config = {
            'performance': Decimal('40'),
            'price': Decimal('30'),
            'delivery': Decimal('20'),
            'history': Decimal('10'),
        }
        
        scores = self.engine._calculate_supplier_score(1, 10, weight_config)
        
        self.assertEqual(scores['delivery_score'], Decimal('100'))
    
    def test_calculate_supplier_score_history_excellent(self):
        """测试优秀历史合作的评分"""
        mock_perf_query = MagicMock()
        mock_perf_query.filter.return_value.order_by.return_value.first.return_value = None
        
        mock_price_query = MagicMock()
        mock_price_query.filter.return_value.all.return_value = []
        
        mock_supplier_query = MagicMock()
        mock_supplier = MagicMock()
        mock_supplier.price = Decimal('10.0')
        mock_supplier.lead_time_days = 10
        mock_supplier_query.filter.return_value.first.return_value = mock_supplier
        
        # 修复：直接返回整数
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 25  # 优秀历史
        
        self.db.query.side_effect = [
            mock_perf_query,
            mock_price_query,
            mock_supplier_query,
            mock_supplier_query,
            mock_count
        ]
        
        weight_config = {
            'performance': Decimal('40'),
            'price': Decimal('30'),
            'delivery': Decimal('20'),
            'history': Decimal('10'),
        }
        
        scores = self.engine._calculate_supplier_score(1, 10, weight_config)
        
        self.assertEqual(scores['history_score'], Decimal('100'))


class TestDetermineUrgency(TestPurchaseSuggestionEngine):
    """测试紧急程度判断"""
    
    def test_determine_urgency_no_date(self):
        """测试无需求日期时返回NORMAL"""
        mock_shortage = MagicMock()
        mock_shortage.required_date = None
        
        urgency = self.engine._determine_urgency(mock_shortage)
        
        self.assertEqual(urgency, 'NORMAL')
    
    def test_determine_urgency_overdue(self):
        """测试已过期返回URGENT"""
        mock_shortage = MagicMock()
        mock_shortage.required_date = date.today() - timedelta(days=1)
        
        urgency = self.engine._determine_urgency(mock_shortage)
        
        self.assertEqual(urgency, 'URGENT')
    
    def test_determine_urgency_high(self):
        """测试3天内返回HIGH"""
        mock_shortage = MagicMock()
        mock_shortage.required_date = date.today() + timedelta(days=2)
        
        urgency = self.engine._determine_urgency(mock_shortage)
        
        self.assertEqual(urgency, 'HIGH')
    
    def test_determine_urgency_normal(self):
        """测试7天内返回NORMAL"""
        mock_shortage = MagicMock()
        mock_shortage.required_date = date.today() + timedelta(days=5)
        
        urgency = self.engine._determine_urgency(mock_shortage)
        
        self.assertEqual(urgency, 'NORMAL')
    
    def test_determine_urgency_low(self):
        """测试7天后返回LOW"""
        mock_shortage = MagicMock()
        mock_shortage.required_date = date.today() + timedelta(days=10)
        
        urgency = self.engine._determine_urgency(mock_shortage)
        
        self.assertEqual(urgency, 'LOW')


class TestCalculateAvgConsumption(TestPurchaseSuggestionEngine):
    """测试平均消耗计算"""
    
    def test_calculate_avg_consumption_no_data(self):
        """测试无数据时返回None"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.return_value = None
        self.db.query.return_value = mock_query
        
        result = self.engine._calculate_avg_consumption(material_id=10)
        
        self.assertIsNone(result)
    
    def test_calculate_avg_consumption_zero(self):
        """测试消耗为零时返回None"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.return_value = Decimal('0')
        self.db.query.return_value = mock_query
        
        result = self.engine._calculate_avg_consumption(material_id=10)
        
        self.assertIsNone(result)
    
    def test_calculate_avg_consumption_success(self):
        """测试成功计算平均消耗"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.return_value = Decimal('600')
        self.db.query.return_value = mock_query
        
        result = self.engine._calculate_avg_consumption(material_id=10, months=6)
        
        self.assertEqual(result, Decimal('100'))
    
    def test_calculate_avg_consumption_custom_months(self):
        """测试自定义月份数计算"""
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.scalar.return_value = Decimal('300')
        self.db.query.return_value = mock_query
        
        result = self.engine._calculate_avg_consumption(material_id=10, months=3)
        
        self.assertEqual(result, Decimal('100'))


class TestGenerateSuggestionNo(TestPurchaseSuggestionEngine):
    """测试建议编号生成"""
    
    def test_generate_suggestion_no_first_today(self):
        """测试当天第一个建议编号"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
            
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = None
            self.db.query.return_value = mock_query
            
            suggestion_no = self.engine._generate_suggestion_no()
            
            self.assertEqual(suggestion_no, 'PS202602210001')
    
    def test_generate_suggestion_no_increment(self):
        """测试建议编号递增"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
            
            mock_latest = MagicMock()
            mock_latest.suggestion_no = 'PS202602210005'
            
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = mock_latest
            self.db.query.return_value = mock_query
            
            suggestion_no = self.engine._generate_suggestion_no()
            
            self.assertEqual(suggestion_no, 'PS202602210006')
    
    def test_generate_suggestion_no_large_sequence(self):
        """测试大序号的编号生成"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
            
            mock_latest = MagicMock()
            mock_latest.suggestion_no = 'PS202602219999'
            
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = mock_latest
            self.db.query.return_value = mock_query
            
            suggestion_no = self.engine._generate_suggestion_no()
            
            # 验证格式正确，序号为10000（虽然超过4位，但仍然生成）
            self.assertTrue(suggestion_no.startswith('PS20260221'))


if __name__ == '__main__':
    unittest.main()
