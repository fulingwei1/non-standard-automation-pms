# -*- coding: utf-8 -*-
"""
战略服务单元测试 - strategy_service.py

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime, date
from decimal import Decimal

from app.services.strategy import strategy_service
from app.schemas.strategy import StrategyCreate, StrategyUpdate


class MockStrategy:
    """Mock Strategy对象"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.code = kwargs.get('code', 'STR-2026')
        self.name = kwargs.get('name', '2026年度战略')
        self.vision = kwargs.get('vision', '成为行业领导者')
        self.mission = kwargs.get('mission', '为客户创造价值')
        self.slogan = kwargs.get('slogan', '创新引领未来')
        self.year = kwargs.get('year', 2026)
        self.start_date = kwargs.get('start_date', date(2026, 1, 1))
        self.end_date = kwargs.get('end_date', date(2026, 12, 31))
        self.status = kwargs.get('status', 'DRAFT')
        self.created_by = kwargs.get('created_by', 1)
        self.approved_by = kwargs.get('approved_by')
        self.approved_at = kwargs.get('approved_at')
        self.published_at = kwargs.get('published_at')
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())


class MockCSF:
    """Mock CSF对象"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.strategy_id = kwargs.get('strategy_id', 1)
        self.dimension = kwargs.get('dimension', 'FINANCIAL')
        self.code = kwargs.get('code', 'CSF-F-001')
        self.name = kwargs.get('name', '财务指标')
        self.weight = kwargs.get('weight', Decimal('25.00'))
        self.sort_order = kwargs.get('sort_order', 0)
        self.is_active = kwargs.get('is_active', True)


class MockKPI:
    """Mock KPI对象"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.csf_id = kwargs.get('csf_id', 1)
        self.code = kwargs.get('code', 'KPI-001')
        self.name = kwargs.get('name', 'KPI指标')
        self.is_active = kwargs.get('is_active', True)


class TestCreateStrategy(unittest.TestCase):
    """测试创建战略"""

    def test_create_strategy_success(self):
        """测试成功创建战略"""
        mock_db = MagicMock()
        
        data = StrategyCreate(
            code='STR-2026',
            name='2026年度战略',
            vision='成为行业领导者',
            mission='为客户创造价值',
            slogan='创新引领未来',
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        
        # Mock refresh行为
        def mock_refresh(obj):
            obj.id = 1
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        result = strategy_service.create_strategy(mock_db, data, created_by=1)
        
        # 验证
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证创建的对象
        created_obj = mock_db.add.call_args[0][0]
        self.assertEqual(created_obj.code, 'STR-2026')
        self.assertEqual(created_obj.name, '2026年度战略')
        self.assertEqual(created_obj.status, 'DRAFT')
        self.assertEqual(created_obj.created_by, 1)

    def test_create_strategy_minimal_fields(self):
        """测试只填写必填字段创建战略"""
        mock_db = MagicMock()
        
        data = StrategyCreate(
            code='STR-2027',
            name='2027战略',
            year=2027
        )
        
        result = strategy_service.create_strategy(mock_db, data, created_by=2)
        
        mock_db.add.assert_called_once()
        created_obj = mock_db.add.call_args[0][0]
        self.assertEqual(created_obj.code, 'STR-2027')
        self.assertIsNone(created_obj.vision)
        self.assertIsNone(created_obj.mission)


class TestGetStrategy(unittest.TestCase):
    """测试获取战略"""

    def test_get_strategy_found(self):
        """测试成功获取战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, code='STR-2026')
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_strategy
        
        result = strategy_service.get_strategy(mock_db, 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.code, 'STR-2026')
        mock_db.query.assert_called_once()

    def test_get_strategy_not_found(self):
        """测试战略不存在"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        result = strategy_service.get_strategy(mock_db, 999)
        
        self.assertIsNone(result)


class TestGetStrategyByCode(unittest.TestCase):
    """测试根据编码获取战略"""

    def test_get_strategy_by_code_found(self):
        """测试成功根据编码获取"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(code='STR-2026')
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_strategy
        
        result = strategy_service.get_strategy_by_code(mock_db, 'STR-2026')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.code, 'STR-2026')

    def test_get_strategy_by_code_not_found(self):
        """测试编码不存在"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        result = strategy_service.get_strategy_by_code(mock_db, 'STR-9999')
        
        self.assertIsNone(result)


class TestGetStrategyByYear(unittest.TestCase):
    """测试根据年度获取战略"""

    def test_get_strategy_by_year_found(self):
        """测试成功根据年度获取"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(year=2026)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_strategy
        
        result = strategy_service.get_strategy_by_year(mock_db, 2026)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)

    def test_get_strategy_by_year_not_found(self):
        """测试年度不存在"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        result = strategy_service.get_strategy_by_year(mock_db, 1999)
        
        self.assertIsNone(result)


class TestGetActiveStrategy(unittest.TestCase):
    """测试获取当前生效的战略"""

    def test_get_active_strategy_found(self):
        """测试获取生效战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(status='ACTIVE')
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_strategy
        
        result = strategy_service.get_active_strategy(mock_db)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ACTIVE')

    def test_get_active_strategy_none(self):
        """测试没有生效战略"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        result = strategy_service.get_active_strategy(mock_db)
        
        self.assertIsNone(result)


class TestListStrategies(unittest.TestCase):
    """测试获取战略列表"""

    def test_list_strategies_no_filter(self):
        """测试无筛选条件获取列表"""
        mock_db = MagicMock()
        
        strategies = [
            MockStrategy(id=1, year=2026),
            MockStrategy(id=2, year=2025)
        ]
        
        # Mock完整的查询链
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = strategies
        
        items, total = strategy_service.list_strategies(mock_db)
        
        self.assertEqual(len(items), 2)
        self.assertEqual(total, 2)

    def test_list_strategies_with_year_filter(self):
        """测试年度筛选"""
        mock_db = MagicMock()
        
        strategies = [MockStrategy(id=1, year=2026)]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = strategies
        
        items, total = strategy_service.list_strategies(mock_db, year=2026)
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].year, 2026)

    def test_list_strategies_with_status_filter(self):
        """测试状态筛选"""
        mock_db = MagicMock()
        
        strategies = [MockStrategy(id=1, status='ACTIVE')]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = strategies
        
        items, total = strategy_service.list_strategies(mock_db, status='ACTIVE')
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].status, 'ACTIVE')

    def test_list_strategies_pagination(self):
        """测试分页"""
        mock_db = MagicMock()
        
        strategies = [MockStrategy(id=i) for i in range(3, 6)]  # 3条记录（第2页）
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10  # 总共10条
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = strategies
        
        items, total = strategy_service.list_strategies(mock_db, skip=2, limit=3)
        
        self.assertEqual(len(items), 3)
        self.assertEqual(total, 10)

    def test_list_strategies_empty(self):
        """测试空列表"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.all.return_value = []
        
        items, total = strategy_service.list_strategies(mock_db)
        
        self.assertEqual(len(items), 0)
        self.assertEqual(total, 0)


class TestUpdateStrategy(unittest.TestCase):
    """测试更新战略"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_update_strategy_success(self, mock_get):
        """测试成功更新战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, name='旧名称')
        mock_get.return_value = mock_strategy
        
        data = StrategyUpdate(name='新名称', vision='新愿景')
        
        result = strategy_service.update_strategy(mock_db, 1, data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, '新名称')
        self.assertEqual(result.vision, '新愿景')
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_update_strategy_not_found(self, mock_get):
        """测试更新不存在的战略"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        data = StrategyUpdate(name='新名称')
        
        result = strategy_service.update_strategy(mock_db, 999, data)
        
        self.assertIsNone(result)
        mock_db.commit.assert_not_called()

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_update_strategy_partial(self, mock_get):
        """测试部分更新"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, name='原名称', vision='原愿景')
        mock_get.return_value = mock_strategy
        
        # 只更新 name
        data = StrategyUpdate(name='新名称')
        
        result = strategy_service.update_strategy(mock_db, 1, data)
        
        self.assertEqual(result.name, '新名称')
        # vision 不应该被更新（因为exclude_unset=True）


class TestPublishStrategy(unittest.TestCase):
    """测试发布战略"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_publish_strategy_success(self, mock_get):
        """测试成功发布战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, year=2026, status='DRAFT')
        mock_get.return_value = mock_strategy
        
        # Mock 同年度其他战略查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.update.return_value = None
        
        result = strategy_service.publish_strategy(mock_db, 1, approved_by=2)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ACTIVE')
        self.assertEqual(result.approved_by, 2)
        self.assertIsNotNone(result.approved_at)
        self.assertIsNotNone(result.published_at)
        mock_db.commit.assert_called_once()

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_publish_strategy_archives_same_year(self, mock_get):
        """测试发布时归档同年度其他战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, year=2026, status='DRAFT')
        mock_get.return_value = mock_strategy
        
        # Mock 同年度其他战略查询
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = None
        
        result = strategy_service.publish_strategy(mock_db, 1, approved_by=2)
        
        # 验证调用了update归档同年度战略
        mock_filter.update.assert_called_once_with({"status": "ARCHIVED"})

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_publish_strategy_not_found(self, mock_get):
        """测试发布不存在的战略"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        result = strategy_service.publish_strategy(mock_db, 999, approved_by=2)
        
        self.assertIsNone(result)
        mock_db.commit.assert_not_called()


class TestArchiveStrategy(unittest.TestCase):
    """测试归档战略"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_archive_strategy_success(self, mock_get):
        """测试成功归档战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, status='ACTIVE')
        mock_get.return_value = mock_strategy
        
        result = strategy_service.archive_strategy(mock_db, 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'ARCHIVED')
        mock_db.commit.assert_called_once()

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_archive_strategy_not_found(self, mock_get):
        """测试归档不存在的战略"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        result = strategy_service.archive_strategy(mock_db, 999)
        
        self.assertIsNone(result)
        mock_db.commit.assert_not_called()


class TestDeleteStrategy(unittest.TestCase):
    """测试删除战略（软删除）"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_delete_strategy_success(self, mock_get):
        """测试成功删除战略"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, is_active=True)
        mock_get.return_value = mock_strategy
        
        result = strategy_service.delete_strategy(mock_db, 1)
        
        self.assertTrue(result)
        self.assertFalse(mock_strategy.is_active)
        mock_db.commit.assert_called_once()

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_delete_strategy_not_found(self, mock_get):
        """测试删除不存在的战略"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        result = strategy_service.delete_strategy(mock_db, 999)
        
        self.assertFalse(result)
        mock_db.commit.assert_not_called()


class TestGetStrategyDetail(unittest.TestCase):
    """测试获取战略详情"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    @patch('app.services.strategy.health_calculator.calculate_strategy_health')
    def test_get_strategy_detail_success(self, mock_health, mock_get):
        """测试成功获取战略详情"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, code='STR-2026')
        mock_get.return_value = mock_strategy
        mock_health.return_value = 85
        
        # Mock CSF count query
        csf_query = MagicMock()
        csf_filter = MagicMock()
        csf_query.filter.return_value = csf_filter
        csf_filter.count.return_value = 4
        
        # Mock KPI count query
        kpi_query = MagicMock()
        kpi_join = MagicMock()
        kpi_filter = MagicMock()
        kpi_query.join.return_value = kpi_join
        kpi_join.filter.return_value = kpi_filter
        kpi_filter.count.return_value = 12
        
        # Mock AnnualKeyWork count query
        work_query = MagicMock()
        work_join = MagicMock()
        work_filter = MagicMock()
        work_query.join.return_value = work_join
        work_join.filter.return_value = work_filter
        work_filter.count.return_value = 8
        
        # 按调用顺序设置返回值
        mock_db.query.side_effect = [csf_query, kpi_query, work_query]
        
        result = strategy_service.get_strategy_detail(mock_db, 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.code, 'STR-2026')
        self.assertEqual(result.csf_count, 4)
        self.assertEqual(result.kpi_count, 12)
        self.assertEqual(result.annual_work_count, 8)
        self.assertEqual(result.health_score, 85)

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_get_strategy_detail_not_found(self, mock_get):
        """测试战略不存在"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        result = strategy_service.get_strategy_detail(mock_db, 999)
        
        self.assertIsNone(result)


class TestGetStrategyMapData(unittest.TestCase):
    """测试获取战略地图数据"""

    @patch('app.services.strategy.strategy_service.get_strategy')
    @patch('app.services.strategy.health_calculator.calculate_strategy_health')
    @patch('app.services.strategy.health_calculator.calculate_csf_health')
    def test_get_strategy_map_data_success(self, mock_csf_health, mock_strategy_health, mock_get):
        """测试成功获取战略地图"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, code='STR-2026', name='2026战略')
        mock_get.return_value = mock_strategy
        mock_strategy_health.return_value = 85
        
        # Mock CSF数据
        csfs = [
            MockCSF(id=1, dimension='FINANCIAL', code='CSF-F-001', name='财务CSF', weight=Decimal('30.00')),
            MockCSF(id=2, dimension='FINANCIAL', code='CSF-F-002', name='财务CSF2', weight=Decimal('20.00')),
        ]
        
        # Mock CSF查询（每个维度调用一次，共4次）
        csf_query_results = [
            csfs,  # FINANCIAL
            [],    # CUSTOMER
            [],    # INTERNAL
            [],    # LEARNING
        ]
        
        mock_csf_query = MagicMock()
        mock_db.query.side_effect = [mock_csf_query] * 8  # 4个维度，每个2次调用（query + KPI count）
        mock_csf_query.filter.return_value.order_by.return_value.all.side_effect = csf_query_results
        
        # Mock KPI count
        kpi_query = MagicMock()
        kpi_query.filter.return_value.count.return_value = 3
        mock_db.query.side_effect = [
            # FINANCIAL dimension
            mock_csf_query,  # CSF query
            kpi_query, kpi_query,  # KPI counts for 2 CSFs
            # CUSTOMER dimension
            mock_csf_query,
            # INTERNAL dimension
            mock_csf_query,
            # LEARNING dimension
            mock_csf_query,
        ]
        
        # Mock CSF health
        mock_csf_health.return_value = {
            'score': 80,
            'level': 'GOOD',
            'kpi_completion_rate': 0.75
        }
        
        result = strategy_service.get_strategy_map_data(mock_db, 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.strategy_code, 'STR-2026')
        self.assertEqual(result.overall_health_score, 85)
        self.assertEqual(len(result.dimensions), 4)
        
        # 验证第一个维度（FINANCIAL）
        financial_dim = result.dimensions[0]
        self.assertEqual(financial_dim.dimension, 'FINANCIAL')
        self.assertEqual(financial_dim.dimension_name, '财务维度')
        self.assertEqual(len(financial_dim.csfs), 2)
        
        # 验证维度健康度计算（加权平均）
        # (80*30 + 80*20) / 50 = 80
        self.assertEqual(financial_dim.health_score, 80)

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_get_strategy_map_data_not_found(self, mock_get):
        """测试战略不存在"""
        mock_db = MagicMock()
        mock_get.return_value = None
        
        result = strategy_service.get_strategy_map_data(mock_db, 999)
        
        self.assertIsNone(result)

    @patch('app.services.strategy.strategy_service.get_strategy')
    @patch('app.services.strategy.health_calculator.calculate_strategy_health')
    @patch('app.services.strategy.health_calculator.calculate_csf_health')
    def test_get_strategy_map_data_empty_csfs(self, mock_csf_health, mock_strategy_health, mock_get):
        """测试无CSF的情况"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1)
        mock_get.return_value = mock_strategy
        mock_strategy_health.return_value = None
        
        # Mock空CSF列表
        mock_csf_query = MagicMock()
        mock_db.query.return_value = mock_csf_query
        mock_csf_query.filter.return_value.order_by.return_value.all.return_value = []
        
        result = strategy_service.get_strategy_map_data(mock_db, 1)
        
        self.assertIsNotNone(result)
        # 所有维度应该都是空的
        for dim in result.dimensions:
            self.assertEqual(len(dim.csfs), 0)
            self.assertIsNone(dim.health_score)


class TestStrategyServiceWrapper(unittest.TestCase):
    """测试StrategyService包装类"""

    def test_service_wrapper_create(self):
        """测试包装类的create方法"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        data = StrategyCreate(code='STR-2026', name='测试', year=2026)
        
        with patch('app.services.strategy.strategy_service.create_strategy') as mock_create:
            mock_create.return_value = MockStrategy()
            result = service.create(data, created_by=1)
            
            mock_create.assert_called_once_with(mock_db, data, 1)

    def test_service_wrapper_get(self):
        """测试包装类的get方法"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.get_strategy') as mock_get:
            mock_get.return_value = MockStrategy()
            result = service.get(1)
            
            mock_get.assert_called_once_with(mock_db, 1)

    def test_service_wrapper_list(self):
        """测试包装类的list方法"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.list_strategies') as mock_list:
            mock_list.return_value = ([MockStrategy()], 1)
            items, total = service.list(year=2026, skip=0, limit=20)
            
            mock_list.assert_called_once_with(mock_db, year=2026, status=None, skip=0, limit=20)

    def test_service_wrapper_get_strategies_with_pagination(self):
        """测试包装类的get_strategies方法（分页转换）"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.list_strategies') as mock_list:
            mock_list.return_value = ([MockStrategy()], 1)
            # 传入 page/page_size 参数
            items, total = service.get_strategies(page=2, page_size=10)
            
            # 应该转换为 skip=10, limit=10
            mock_list.assert_called_once()
            call_kwargs = mock_list.call_args[1]
            self.assertEqual(call_kwargs['skip'], 10)
            self.assertEqual(call_kwargs['limit'], 10)

    def test_service_wrapper_publish(self):
        """测试包装类的publish方法"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.publish_strategy') as mock_publish:
            mock_publish.return_value = MockStrategy(status='ACTIVE')
            result = service.publish(1, approved_by=2)
            
            mock_publish.assert_called_once_with(mock_db, 1, 2)

    def test_service_wrapper_get_metrics(self):
        """测试包装类的get_metrics方法"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.get_strategy_detail') as mock_detail:
            # Mock返回对象
            mock_response = MagicMock()
            mock_response.csf_count = 4
            mock_response.kpi_count = 12
            mock_response.annual_work_count = 8
            mock_response.health_score = 85
            mock_detail.return_value = mock_response
            
            result = service.get_metrics(1)
            
            self.assertEqual(result['csf_count'], 4)
            self.assertEqual(result['kpi_count'], 12)
            self.assertEqual(result['annual_work_count'], 8)
            self.assertEqual(result['health_score'], 85)

    def test_service_wrapper_get_metrics_not_found(self):
        """测试包装类的get_metrics方法（战略不存在）"""
        mock_db = MagicMock()
        service = strategy_service.StrategyService(mock_db)
        
        with patch('app.services.strategy.strategy_service.get_strategy_detail') as mock_detail:
            mock_detail.return_value = None
            
            result = service.get_metrics(999)
            
            self.assertEqual(result, {})


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_create_strategy_with_none_dates(self):
        """测试创建战略时日期为None"""
        mock_db = MagicMock()
        
        data = StrategyCreate(
            code='STR-2026',
            name='测试',
            year=2026,
            start_date=None,
            end_date=None
        )
        
        result = strategy_service.create_strategy(mock_db, data, created_by=1)
        
        created_obj = mock_db.add.call_args[0][0]
        self.assertIsNone(created_obj.start_date)
        self.assertIsNone(created_obj.end_date)

    @patch('app.services.strategy.strategy_service.get_strategy')
    def test_update_strategy_empty_update(self, mock_get):
        """测试空更新（无字段变更）"""
        mock_db = MagicMock()
        mock_strategy = MockStrategy(id=1, name='原名称')
        mock_get.return_value = mock_strategy
        
        # 空的更新数据
        data = StrategyUpdate()
        
        result = strategy_service.update_strategy(mock_db, 1, data)
        
        # 应该仍然提交
        mock_db.commit.assert_called_once()

    def test_list_strategies_zero_limit(self):
        """测试limit为0的情况"""
        mock_db = MagicMock()
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.all.return_value = []
        
        items, total = strategy_service.list_strategies(mock_db, limit=0)
        
        self.assertEqual(len(items), 0)
        self.assertEqual(total, 100)


if __name__ == "__main__":
    unittest.main()
