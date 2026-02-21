# -*- coding: utf-8 -*-
"""
需求预测引擎单元测试

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.shortage.demand_forecast_engine import DemandForecastEngine
from app.models.shortage.smart_alert import MaterialDemandForecast
from app.core.exceptions import BusinessException


class TestDemandForecastEngineInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试构造函数"""
        mock_db = MagicMock(spec=Session)
        engine = DemandForecastEngine(mock_db)
        self.assertEqual(engine.db, mock_db)


class TestCalculationMethods(unittest.TestCase):
    """测试计算方法（纯业务逻辑，无数据库依赖）"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    # ========== _calculate_average() 测试 ==========

    def test_calculate_average_normal(self):
        """测试正常计算平均值"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._calculate_average(data)
        self.assertEqual(result, Decimal('20'))

    def test_calculate_average_empty(self):
        """测试空列表"""
        result = self.engine._calculate_average([])
        self.assertEqual(result, Decimal('0'))

    def test_calculate_average_single_value(self):
        """测试单个值"""
        data = [Decimal('100')]
        result = self.engine._calculate_average(data)
        self.assertEqual(result, Decimal('100'))

    def test_calculate_average_decimals(self):
        """测试小数精度"""
        data = [Decimal('10.5'), Decimal('20.7'), Decimal('30.3')]
        result = self.engine._calculate_average(data)
        expected = Decimal('61.5') / Decimal('3')
        self.assertEqual(result, expected)

    # ========== _calculate_std() 测试 ==========

    def test_calculate_std_normal(self):
        """测试正常计算标准差"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._calculate_std(data)
        # 标准差应该是 10
        self.assertAlmostEqual(float(result), 10.0, places=1)

    def test_calculate_std_single_value(self):
        """测试单个值（标准差为0）"""
        data = [Decimal('100')]
        result = self.engine._calculate_std(data)
        self.assertEqual(result, Decimal('0'))

    def test_calculate_std_empty(self):
        """测试空列表"""
        result = self.engine._calculate_std([])
        self.assertEqual(result, Decimal('0'))

    def test_calculate_std_same_values(self):
        """测试相同值（标准差为0）"""
        data = [Decimal('50'), Decimal('50'), Decimal('50')]
        result = self.engine._calculate_std(data)
        self.assertEqual(float(result), 0.0)

    # ========== _detect_seasonality() 测试 ==========

    def test_detect_seasonality_normal(self):
        """测试正常季节性检测"""
        # 最近7天平均100，历史平均50，季节因子应为2.0
        data = [Decimal('50')] * 20 + [Decimal('100')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('2.0'))

    def test_detect_seasonality_no_change(self):
        """测试无季节性变化"""
        data = [Decimal('100')] * 30
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('1.0'))

    def test_detect_seasonality_insufficient_data(self):
        """测试数据不足（<14天）"""
        data = [Decimal('100')] * 10
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('1.0'))

    def test_detect_seasonality_historical_zero(self):
        """测试历史平均为0"""
        data = [Decimal('0')] * 20 + [Decimal('100')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('1.0'))

    def test_detect_seasonality_clamped_upper(self):
        """测试季节因子上限（2.0）"""
        # 最近7天平均300，历史平均50，应被限制在2.0
        data = [Decimal('50')] * 20 + [Decimal('300')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('2.0'))

    def test_detect_seasonality_clamped_lower(self):
        """测试季节因子下限（0.5）"""
        # 最近7天平均10，历史平均100，应被限制在0.5
        data = [Decimal('100')] * 20 + [Decimal('10')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('0.5'))

    # ========== _moving_average_forecast() 测试 ==========

    def test_moving_average_forecast_normal(self):
        """测试正常移动平均预测"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40'), 
                Decimal('50'), Decimal('60'), Decimal('70')]
        result = self.engine._moving_average_forecast(data, window=7)
        expected = Decimal('40')  # (10+20+30+40+50+60+70)/7
        self.assertEqual(result, expected)

    def test_moving_average_forecast_custom_window(self):
        """测试自定义窗口大小"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        result = self.engine._moving_average_forecast(data, window=3)
        expected = Decimal('30')  # (20+30+40)/3
        self.assertEqual(result, expected)

    def test_moving_average_forecast_insufficient_data(self):
        """测试数据不足（自动调整窗口）"""
        data = [Decimal('10'), Decimal('20')]
        result = self.engine._moving_average_forecast(data, window=7)
        expected = Decimal('15')  # (10+20)/2
        self.assertEqual(result, expected)

    def test_moving_average_forecast_single_value(self):
        """测试单个值"""
        data = [Decimal('100')]
        result = self.engine._moving_average_forecast(data, window=7)
        self.assertEqual(result, Decimal('100'))

    # ========== _exponential_smoothing_forecast() 测试 ==========

    def test_exponential_smoothing_forecast_normal(self):
        """测试正常指数平滑预测"""
        data = [Decimal('100'), Decimal('110'), Decimal('120')]
        result = self.engine._exponential_smoothing_forecast(data, alpha=Decimal('0.3'))
        # S0 = 100
        # S1 = 0.3*110 + 0.7*100 = 33 + 70 = 103
        # S2 = 0.3*120 + 0.7*103 = 36 + 72.1 = 108.1
        expected = Decimal('108.1')
        self.assertAlmostEqual(float(result), float(expected), places=1)

    def test_exponential_smoothing_forecast_empty(self):
        """测试空数据"""
        result = self.engine._exponential_smoothing_forecast([])
        self.assertEqual(result, Decimal('0'))

    def test_exponential_smoothing_forecast_single_value(self):
        """测试单个值"""
        data = [Decimal('100')]
        result = self.engine._exponential_smoothing_forecast(data)
        self.assertEqual(result, Decimal('100'))

    def test_exponential_smoothing_forecast_default_alpha(self):
        """测试默认alpha值"""
        data = [Decimal('100'), Decimal('120')]
        result = self.engine._exponential_smoothing_forecast(data)
        # alpha默认0.3
        # S1 = 0.3*120 + 0.7*100 = 36 + 70 = 106
        expected = Decimal('106')
        self.assertEqual(result, expected)

    # ========== _linear_regression_forecast() 测试 ==========

    def test_linear_regression_forecast_normal(self):
        """测试正常线性回归预测"""
        # 线性增长数据: 10, 20, 30, 40
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        result = self.engine._linear_regression_forecast(data)
        # 趋势应该预测下一个为50
        self.assertAlmostEqual(float(result), 50.0, places=1)

    def test_linear_regression_forecast_flat_trend(self):
        """测试平稳趋势"""
        data = [Decimal('100')] * 5
        result = self.engine._linear_regression_forecast(data)
        self.assertAlmostEqual(float(result), 100.0, places=1)

    def test_linear_regression_forecast_single_value(self):
        """测试单个值"""
        data = [Decimal('100')]
        result = self.engine._linear_regression_forecast(data)
        self.assertEqual(result, Decimal('100'))

    def test_linear_regression_forecast_negative_result(self):
        """测试负数结果（应返回0）"""
        # 下降趋势
        data = [Decimal('100'), Decimal('50'), Decimal('0')]
        result = self.engine._linear_regression_forecast(data)
        # 预测值可能为负，但应被限制为0
        self.assertGreaterEqual(float(result), 0.0)

    def test_linear_regression_forecast_zero_denominator(self):
        """测试分母为0的情况（x全相同时不可能，但测试稳定性）"""
        data = [Decimal('10'), Decimal('20')]
        result = self.engine._linear_regression_forecast(data)
        # 应能正常处理
        self.assertIsInstance(result, Decimal)

    # ========== _calculate_confidence_interval() 测试 ==========

    def test_confidence_interval_95_percent(self):
        """测试95%置信区间"""
        forecast = Decimal('100')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        # 95%: z=1.96, margin=19.6
        self.assertAlmostEqual(float(lower), 80.4, places=1)
        self.assertAlmostEqual(float(upper), 119.6, places=1)

    def test_confidence_interval_90_percent(self):
        """测试90%置信区间"""
        forecast = Decimal('100')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 90.0)
        # 90%: z=1.645, margin=16.45
        self.assertAlmostEqual(float(lower), 83.55, places=1)
        self.assertAlmostEqual(float(upper), 116.45, places=1)

    def test_confidence_interval_low_confidence(self):
        """测试低置信度"""
        forecast = Decimal('100')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 80.0)
        # 其他: z=1.0, margin=10
        self.assertEqual(float(lower), 90.0)
        self.assertEqual(float(upper), 110.0)

    def test_confidence_interval_lower_bound_zero(self):
        """测试下限不低于0"""
        forecast = Decimal('10')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        # 下限应该>=0
        self.assertGreaterEqual(float(lower), 0.0)
        self.assertGreater(float(upper), float(lower))

    def test_confidence_interval_zero_std(self):
        """测试标准差为0"""
        forecast = Decimal('100')
        std = Decimal('0')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        self.assertEqual(lower, Decimal('100'))
        self.assertEqual(upper, Decimal('100'))


class TestForecastMaterialDemand(unittest.TestCase):
    """测试主预测方法（需要mock数据库）"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_exp_smoothing(self, mock_save):
        """测试指数平滑预测（完整流程）"""
        # Mock历史数据查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        # Mock历史需求数据
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=30)
        for i in range(30):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 100 + i * 2  # 递增趋势
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        # Mock预测编号生成
        mock_count_query = MagicMock()
        self.mock_db.query.side_effect = [mock_query, mock_count_query]
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = 5
        
        # 执行预测
        result = self.engine.forecast_material_demand(
            material_id=1,
            forecast_horizon_days=30,
            algorithm='EXP_SMOOTHING',
            historical_days=90
        )
        
        # 验证结果
        self.assertIsInstance(result, MaterialDemandForecast)
        self.assertEqual(result.material_id, 1)
        self.assertEqual(result.forecast_horizon_days, 30)
        self.assertEqual(result.algorithm, 'EXP_SMOOTHING')
        self.assertEqual(result.status, 'ACTIVE')
        self.assertGreater(result.forecasted_demand, Decimal('0'))
        self.assertGreater(result.upper_bound, result.lower_bound)
        
        # 验证保存被调用
        mock_save.assert_called_once()

    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_moving_average(self, mock_save):
        """测试移动平均预测"""
        # Mock历史数据查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=15)
        for i in range(15):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 100
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        # Mock预测编号
        mock_count_query = MagicMock()
        self.mock_db.query.side_effect = [mock_query, mock_count_query]
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = 0
        
        result = self.engine.forecast_material_demand(
            material_id=1,
            algorithm='MOVING_AVERAGE'
        )
        
        self.assertEqual(result.algorithm, 'MOVING_AVERAGE')
        self.assertGreater(result.forecasted_demand, Decimal('0'))

    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_linear_regression(self, mock_save):
        """测试线性回归预测"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=20)
        for i in range(20):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 50 + i * 5
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        mock_count_query = MagicMock()
        self.mock_db.query.side_effect = [mock_query, mock_count_query]
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = 0
        
        result = self.engine.forecast_material_demand(
            material_id=1,
            algorithm='LINEAR_REGRESSION'
        )
        
        self.assertEqual(result.algorithm, 'LINEAR_REGRESSION')

    def test_forecast_material_demand_invalid_algorithm(self):
        """测试不支持的算法"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=10)
        for i in range(10):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 100
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        with self.assertRaises(BusinessException) as context:
            self.engine.forecast_material_demand(
                material_id=1,
                algorithm='INVALID_ALGO'
            )
        
        self.assertIn("不支持的预测算法", str(context.exception))

    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_with_project(self, mock_save):
        """测试带项目ID的预测"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=10)
        for i in range(10):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 100
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        mock_count_query = MagicMock()
        self.mock_db.query.side_effect = [mock_query, mock_count_query]
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.scalar.return_value = 0
        
        result = self.engine.forecast_material_demand(
            material_id=1,
            project_id=100
        )
        
        self.assertEqual(result.project_id, 100)


class TestValidateForecastAccuracy(unittest.TestCase):
    """测试预测准确率验证"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    def test_validate_forecast_accuracy_normal(self):
        """测试正常验证准确率"""
        # Mock预测记录
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.id = 1
        mock_forecast.forecasted_demand = Decimal('100')
        mock_forecast.lower_bound = Decimal('80')
        mock_forecast.upper_bound = Decimal('120')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_forecast
        
        # 验证
        actual_demand = Decimal('95')
        result = self.engine.validate_forecast_accuracy(
            forecast_id=1,
            actual_demand=actual_demand
        )
        
        # 验证结果
        self.assertEqual(result['forecast_id'], 1)
        self.assertEqual(result['forecasted_demand'], 100.0)
        self.assertEqual(result['actual_demand'], 95.0)
        self.assertTrue(result['within_confidence_interval'])
        self.assertGreater(result['accuracy_score'], 0)
        
        # 验证数据库更新
        self.assertEqual(mock_forecast.actual_demand, actual_demand)
        self.assertEqual(mock_forecast.status, 'VALIDATED')
        self.assertIsNotNone(mock_forecast.validated_at)
        self.mock_db.commit.assert_called_once()

    def test_validate_forecast_accuracy_outside_interval(self):
        """测试实际值在置信区间外"""
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.id = 1
        mock_forecast.forecasted_demand = Decimal('100')
        mock_forecast.lower_bound = Decimal('80')
        mock_forecast.upper_bound = Decimal('120')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_forecast
        
        # 实际值超出上限
        result = self.engine.validate_forecast_accuracy(
            forecast_id=1,
            actual_demand=Decimal('150')
        )
        
        self.assertFalse(result['within_confidence_interval'])
        self.assertGreater(result['error_percentage'], 0)

    def test_validate_forecast_accuracy_zero_actual(self):
        """测试实际需求为0"""
        mock_forecast = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.id = 1
        mock_forecast.forecasted_demand = Decimal('100')
        mock_forecast.lower_bound = Decimal('80')
        mock_forecast.upper_bound = Decimal('120')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_forecast
        
        result = self.engine.validate_forecast_accuracy(
            forecast_id=1,
            actual_demand=Decimal('0')
        )
        
        # 实际为0时，误差百分比应为0
        self.assertEqual(result['error_percentage'], 0)

    def test_validate_forecast_accuracy_not_found(self):
        """测试预测记录不存在"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        with self.assertRaises(BusinessException) as context:
            self.engine.validate_forecast_accuracy(
                forecast_id=999,
                actual_demand=Decimal('100')
            )
        
        self.assertIn("预测记录不存在", str(context.exception))


class TestBatchForecastForProject(unittest.TestCase):
    """测试批量预测"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    @patch.object(DemandForecastEngine, 'forecast_material_demand')
    def test_batch_forecast_for_project_success(self, mock_forecast):
        """测试批量预测成功"""
        # Mock物料ID查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]
        
        # Mock forecast_material_demand
        mock_forecast_obj = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.return_value = mock_forecast_obj
        
        result = self.engine.batch_forecast_for_project(
            project_id=100,
            forecast_horizon_days=30
        )
        
        # 验证结果
        self.assertEqual(len(result), 3)
        self.assertEqual(mock_forecast.call_count, 3)

    @patch.object(DemandForecastEngine, 'forecast_material_demand')
    def test_batch_forecast_for_project_partial_failure(self, mock_forecast):
        """测试部分预测失败（应跳过错误继续）"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,), (3,)]
        
        # 第2个预测失败
        mock_forecast_obj = MagicMock(spec=MaterialDemandForecast)
        mock_forecast.side_effect = [
            mock_forecast_obj,
            Exception("预测失败"),
            mock_forecast_obj
        ]
        
        result = self.engine.batch_forecast_for_project(project_id=100)
        
        # 应该有2个成功
        self.assertEqual(len(result), 2)

    @patch.object(DemandForecastEngine, 'forecast_material_demand')
    def test_batch_forecast_for_project_no_materials(self, mock_forecast):
        """测试项目无物料"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.engine.batch_forecast_for_project(project_id=100)
        
        self.assertEqual(len(result), 0)
        mock_forecast.assert_not_called()


class TestGetForecastAccuracyReport(unittest.TestCase):
    """测试准确率报告"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    def test_get_forecast_accuracy_report_normal(self):
        """测试正常生成报告"""
        # Mock已验证的预测记录
        mock_forecasts = []
        for i in range(5):
            mock_f = MagicMock(spec=MaterialDemandForecast)
            mock_f.accuracy_score = Decimal('85.0')
            mock_f.mape = Decimal('15.0')
            mock_f.algorithm = 'EXP_SMOOTHING'
            mock_f.lower_bound = Decimal('80')
            mock_f.upper_bound = Decimal('120')
            mock_f.actual_demand = Decimal('95')
            mock_forecasts.append(mock_f)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_forecasts
        
        result = self.engine.get_forecast_accuracy_report(days=30)
        
        # 验证结果
        self.assertEqual(result['total_forecasts'], 5)
        self.assertEqual(result['average_accuracy'], 85.0)
        self.assertEqual(result['average_mape'], 15.0)
        self.assertEqual(result['within_ci_rate'], 100.0)
        self.assertIn('by_algorithm', result)

    def test_get_forecast_accuracy_report_multiple_algorithms(self):
        """测试多种算法的报告"""
        mock_forecasts = []
        
        # EXP_SMOOTHING: 2个
        for i in range(2):
            mock_f = MagicMock(spec=MaterialDemandForecast)
            mock_f.accuracy_score = Decimal('80.0')
            mock_f.mape = Decimal('20.0')
            mock_f.algorithm = 'EXP_SMOOTHING'
            mock_f.lower_bound = Decimal('80')
            mock_f.upper_bound = Decimal('120')
            mock_f.actual_demand = Decimal('95')
            mock_forecasts.append(mock_f)
        
        # MOVING_AVERAGE: 3个
        for i in range(3):
            mock_f = MagicMock(spec=MaterialDemandForecast)
            mock_f.accuracy_score = Decimal('90.0')
            mock_f.mape = Decimal('10.0')
            mock_f.algorithm = 'MOVING_AVERAGE'
            mock_f.lower_bound = Decimal('80')
            mock_f.upper_bound = Decimal('120')
            mock_f.actual_demand = Decimal('95')
            mock_forecasts.append(mock_f)
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_forecasts
        
        result = self.engine.get_forecast_accuracy_report()
        
        self.assertEqual(result['total_forecasts'], 5)
        self.assertIn('EXP_SMOOTHING', result['by_algorithm'])
        self.assertIn('MOVING_AVERAGE', result['by_algorithm'])
        self.assertEqual(result['by_algorithm']['EXP_SMOOTHING']['count'], 2)
        self.assertEqual(result['by_algorithm']['MOVING_AVERAGE']['count'], 3)

    def test_get_forecast_accuracy_report_no_data(self):
        """测试无数据"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.engine.get_forecast_accuracy_report()
        
        self.assertEqual(result['total_forecasts'], 0)
        self.assertEqual(result['average_accuracy'], 0)
        self.assertEqual(result['average_mape'], 0)
        self.assertEqual(result['within_ci_rate'], 0)

    def test_get_forecast_accuracy_report_with_material_filter(self):
        """测试按物料筛选"""
        mock_forecasts = [MagicMock(spec=MaterialDemandForecast)]
        mock_forecasts[0].accuracy_score = Decimal('85.0')
        mock_forecasts[0].mape = Decimal('15.0')
        mock_forecasts[0].algorithm = 'EXP_SMOOTHING'
        mock_forecasts[0].lower_bound = Decimal('80')
        mock_forecasts[0].upper_bound = Decimal('120')
        mock_forecasts[0].actual_demand = Decimal('95')
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_forecasts
        
        result = self.engine.get_forecast_accuracy_report(material_id=1)
        
        self.assertEqual(result['total_forecasts'], 1)


class TestGenerateForecastNo(unittest.TestCase):
    """测试预测编号生成"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    def test_generate_forecast_no_first_of_day(self):
        """测试当天第一个预测"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        
        result = self.engine._generate_forecast_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"FC{today}0001"
        self.assertEqual(result, expected)

    def test_generate_forecast_no_sequential(self):
        """测试顺序编号"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        result = self.engine._generate_forecast_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"FC{today}0006"
        self.assertEqual(result, expected)

    def test_generate_forecast_no_none_count(self):
        """测试count为None"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.engine._generate_forecast_no()
        
        today = datetime.now().strftime('%Y%m%d')
        expected = f"FC{today}0001"
        self.assertEqual(result, expected)


class TestCollectHistoricalDemand(unittest.TestCase):
    """测试历史需求数据收集"""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.engine = DemandForecastEngine(self.mock_db)

    def test_collect_historical_demand_normal(self):
        """测试正常收集历史数据"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        # Mock 5天的数据
        mock_results = []
        base_date = datetime.now().date() - timedelta(days=5)
        for i in range(5):
            mock_row = MagicMock()
            mock_row.demand_date = base_date + timedelta(days=i)
            mock_row.daily_demand = 100 + i * 10
            mock_results.append(mock_row)
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.engine._collect_historical_demand(
            material_id=1,
            days=10,
            project_id=None
        )
        
        # 应该有10天的数据（包括0需求的天）
        self.assertEqual(len(result), 10)
        self.assertIsInstance(result[0], Decimal)

    def test_collect_historical_demand_with_gaps(self):
        """测试有缺失日期（应填充0）"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        
        # 只有2天有数据
        base_date = datetime.now().date() - timedelta(days=5)
        mock_results = [
            MagicMock(demand_date=base_date, daily_demand=100),
            MagicMock(demand_date=base_date + timedelta(days=3), daily_demand=200)
        ]
        
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        result = self.engine._collect_historical_demand(
            material_id=1,
            days=5,
            project_id=None
        )
        
        # 应该有5天数据，缺失的填0
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], Decimal('100'))
        self.assertEqual(result[1], Decimal('0'))
        self.assertEqual(result[2], Decimal('0'))
        self.assertEqual(result[3], Decimal('200'))

    def test_collect_historical_demand_with_project(self):
        """测试带项目ID"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.engine._collect_historical_demand(
            material_id=1,
            days=10,
            project_id=100
        )
        
        # 验证filter被调用（包含project_id过滤）
        self.assertGreater(mock_query.filter.call_count, 0)


if __name__ == "__main__":
    unittest.main()
