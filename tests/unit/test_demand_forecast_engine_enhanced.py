# -*- coding: utf-8 -*-
"""
物料需求预测引擎增强单元测试

覆盖所有核心方法和边界条件，使用 Mock 模拟数据库操作
目标：30-40个测试用例，覆盖率70%+
"""
import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List

from app.services.shortage.demand_forecast_engine import DemandForecastEngine
from app.models.shortage.smart_alert import MaterialDemandForecast
from app.core.exceptions import BusinessException


class TestDemandForecastEngine(unittest.TestCase):
    """需求预测引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.engine = DemandForecastEngine(db=self.mock_db)
    
    def tearDown(self):
        """测试后清理"""
        self.mock_db.reset_mock()
    
    # ========== 初始化测试 ==========
    
    def test_init_with_db_session(self):
        """测试：使用数据库会话初始化"""
        engine = DemandForecastEngine(db=self.mock_db)
        self.assertEqual(engine.db, self.mock_db)
    
    # ========== forecast_material_demand 测试 ==========
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_exp_smoothing_success(self, mock_save):
        """测试：指数平滑预测成功"""
        # 准备历史数据
        historical_data = [Decimal('10'), Decimal('15'), Decimal('20'), Decimal('25')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC202602210001'):
                forecast = self.engine.forecast_material_demand(
                    material_id=1,
                    forecast_horizon_days=30,
                    algorithm='EXP_SMOOTHING'
                )
        
        self.assertIsInstance(forecast, MaterialDemandForecast)
        self.assertEqual(forecast.material_id, 1)
        self.assertEqual(forecast.algorithm, 'EXP_SMOOTHING')
        self.assertGreater(forecast.forecasted_demand, Decimal('0'))
        mock_save.assert_called_once()
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_moving_average_success(self, mock_save):
        """测试：移动平均预测成功"""
        historical_data = [Decimal('10'), Decimal('12'), Decimal('14'), Decimal('16'), 
                          Decimal('18'), Decimal('20'), Decimal('22'), Decimal('24')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC202602210002'):
                forecast = self.engine.forecast_material_demand(
                    material_id=2,
                    algorithm='MOVING_AVERAGE'
                )
        
        self.assertEqual(forecast.algorithm, 'MOVING_AVERAGE')
        self.assertGreater(forecast.forecasted_demand, Decimal('0'))
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_linear_regression_success(self, mock_save):
        """测试：线性回归预测成功"""
        historical_data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC202602210003'):
                forecast = self.engine.forecast_material_demand(
                    material_id=3,
                    algorithm='LINEAR_REGRESSION'
                )
        
        self.assertEqual(forecast.algorithm, 'LINEAR_REGRESSION')
        self.assertGreater(forecast.forecasted_demand, Decimal('0'))
    
    def test_forecast_material_demand_no_historical_data(self):
        """测试：无历史数据时抛出异常"""
        with patch.object(self.engine, '_collect_historical_demand', return_value=[]):
            with self.assertRaises(BusinessException) as context:
                self.engine.forecast_material_demand(material_id=1)
            self.assertIn("历史数据不足", str(context.exception))
    
    def test_forecast_material_demand_unsupported_algorithm(self):
        """测试：不支持的算法抛出异常"""
        historical_data = [Decimal('10'), Decimal('20')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with self.assertRaises(BusinessException) as context:
                self.engine.forecast_material_demand(
                    material_id=1,
                    algorithm='UNSUPPORTED_ALGO'
                )
            self.assertIn("不支持的预测算法", str(context.exception))
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_with_project_id(self, mock_save):
        """测试：带项目ID的预测"""
        historical_data = [Decimal('5'), Decimal('10'), Decimal('15')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC202602210004'):
                forecast = self.engine.forecast_material_demand(
                    material_id=4,
                    project_id=100
                )
        
        self.assertEqual(forecast.project_id, 100)
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_forecast_material_demand_confidence_interval_calculation(self, mock_save):
        """测试：置信区间计算正确"""
        historical_data = [Decimal('10'), Decimal('20'), Decimal('30')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC202602210005'):
                forecast = self.engine.forecast_material_demand(material_id=5)
        
        self.assertLessEqual(forecast.lower_bound, forecast.forecasted_demand)
        self.assertGreaterEqual(forecast.upper_bound, forecast.forecasted_demand)
        self.assertGreaterEqual(forecast.lower_bound, Decimal('0'))
    
    # ========== validate_forecast_accuracy 测试 ==========
    
    def test_validate_forecast_accuracy_success(self):
        """测试：验证预测准确率成功"""
        mock_forecast = MaterialDemandForecast(
            id=1,
            forecasted_demand=Decimal('100'),
            lower_bound=Decimal('80'),
            upper_bound=Decimal('120')
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_forecast
        
        result = self.engine.validate_forecast_accuracy(
            forecast_id=1,
            actual_demand=Decimal('95')
        )
        
        self.assertEqual(result['forecast_id'], 1)
        self.assertEqual(result['forecasted_demand'], 100.0)
        self.assertEqual(result['actual_demand'], 95.0)
        self.assertTrue(result['within_confidence_interval'])
        self.assertGreater(result['accuracy_score'], 0)
    
    def test_validate_forecast_accuracy_forecast_not_found(self):
        """测试：预测记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(BusinessException) as context:
            self.engine.validate_forecast_accuracy(
                forecast_id=999,
                actual_demand=Decimal('100')
            )
        self.assertIn("预测记录不存在", str(context.exception))
    
    def test_validate_forecast_accuracy_outside_confidence_interval(self):
        """测试：实际值在置信区间外"""
        mock_forecast = MaterialDemandForecast(
            id=2,
            forecasted_demand=Decimal('100'),
            lower_bound=Decimal('80'),
            upper_bound=Decimal('120')
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_forecast
        
        result = self.engine.validate_forecast_accuracy(
            forecast_id=2,
            actual_demand=Decimal('150')
        )
        
        self.assertFalse(result['within_confidence_interval'])
        self.assertGreater(result['error_percentage'], 0)
    
    def test_validate_forecast_accuracy_zero_actual_demand(self):
        """测试：实际需求为零"""
        mock_forecast = MaterialDemandForecast(
            id=3,
            forecasted_demand=Decimal('100'),
            lower_bound=Decimal('80'),
            upper_bound=Decimal('120')
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_forecast
        
        result = self.engine.validate_forecast_accuracy(
            forecast_id=3,
            actual_demand=Decimal('0')
        )
        
        self.assertEqual(result['error_percentage'], 0)
    
    # ========== 边界条件和数据质量测试 ==========
    
    def test_forecast_with_sparse_historical_data(self):
        """测试：稀疏历史数据的预测"""
        # 只有很少的非零数据点
        sparse_data = [Decimal('0'), Decimal('0'), Decimal('10'), Decimal('0'), Decimal('0')]
        result = self.engine._moving_average_forecast(sparse_data)
        self.assertGreaterEqual(result, Decimal('0'))
    
    def test_forecast_with_high_variance_data(self):
        """测试：高方差数据的预测"""
        high_variance_data = [Decimal('5'), Decimal('100'), Decimal('2'), Decimal('95'), Decimal('8')]
        std = self.engine._calculate_std(high_variance_data)
        self.assertGreater(std, Decimal('30'))  # 高标准差
    
    def test_confidence_interval_wider_for_higher_variance(self):
        """测试：高方差导致更宽的置信区间"""
        forecast = Decimal('100')
        low_std = Decimal('5')
        high_std = Decimal('20')
        
        lower1, upper1 = self.engine._calculate_confidence_interval(forecast, low_std, 95.0)
        lower2, upper2 = self.engine._calculate_confidence_interval(forecast, high_std, 95.0)
        
        # 高方差的置信区间应该更宽
        self.assertLess(upper1 - lower1, upper2 - lower2)
    
    def test_exponential_smoothing_with_zero_alpha(self):
        """测试：alpha=0的指数平滑（完全不更新）"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._exponential_smoothing_forecast(data, alpha=Decimal('0'))
        # alpha=0时，结果应该等于初始值
        self.assertEqual(result, Decimal('10'))
    
    def test_exponential_smoothing_with_one_alpha(self):
        """测试：alpha=1的指数平滑（只看最新值）"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._exponential_smoothing_forecast(data, alpha=Decimal('1'))
        # alpha=1时，结果应该等于最后一个值
        self.assertEqual(result, Decimal('30'))
    
    # ========== 计算方法测试 ==========
    
    def test_calculate_average_normal_data(self):
        """测试：计算正常数据的平均值"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._calculate_average(data)
        self.assertEqual(result, Decimal('20'))
    
    def test_calculate_average_empty_data(self):
        """测试：空数据的平均值"""
        result = self.engine._calculate_average([])
        self.assertEqual(result, Decimal('0'))
    
    def test_calculate_average_single_value(self):
        """测试：单个值的平均值"""
        data = [Decimal('42')]
        result = self.engine._calculate_average(data)
        self.assertEqual(result, Decimal('42'))
    
    def test_calculate_std_normal_data(self):
        """测试：计算标准差"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        result = self.engine._calculate_std(data)
        self.assertGreater(result, Decimal('0'))
    
    def test_calculate_std_insufficient_data(self):
        """测试：数据不足时的标准差"""
        data = [Decimal('10')]
        result = self.engine._calculate_std(data)
        self.assertEqual(result, Decimal('0'))
    
    def test_calculate_std_identical_values(self):
        """测试：相同值的标准差"""
        data = [Decimal('10'), Decimal('10'), Decimal('10')]
        result = self.engine._calculate_std(data)
        self.assertEqual(result, Decimal('0'))
    
    # ========== 季节性检测测试 ==========
    
    def test_detect_seasonality_upward_trend(self):
        """测试：检测上升趋势"""
        data = [Decimal('10')] * 10 + [Decimal('20')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertGreater(result, Decimal('1'))
    
    def test_detect_seasonality_downward_trend(self):
        """测试：检测下降趋势"""
        data = [Decimal('20')] * 10 + [Decimal('10')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertLess(result, Decimal('1'))
    
    def test_detect_seasonality_stable(self):
        """测试：稳定数据无季节性"""
        data = [Decimal('10')] * 20
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('1.0'))
    
    def test_detect_seasonality_insufficient_data(self):
        """测试：数据不足时返回1.0"""
        data = [Decimal('10')] * 5
        result = self.engine._detect_seasonality(data)
        self.assertEqual(result, Decimal('1.0'))
    
    def test_detect_seasonality_extreme_values_capped(self):
        """测试：极端值被限制在0.5-2.0"""
        data = [Decimal('1')] * 10 + [Decimal('100')] * 7
        result = self.engine._detect_seasonality(data)
        self.assertLessEqual(result, Decimal('2.0'))
    
    # ========== 移动平均预测测试 ==========
    
    def test_moving_average_forecast_standard_window(self):
        """测试：标准窗口移动平均"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40'),
                Decimal('50'), Decimal('60'), Decimal('70'), Decimal('80')]
        result = self.engine._moving_average_forecast(data, window=7)
        # Average of last 7: (20+30+40+50+60+70+80)/7 = 350/7 = 50
        self.assertEqual(result, Decimal('50'))
    
    def test_moving_average_forecast_small_dataset(self):
        """测试：小数据集移动平均"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._moving_average_forecast(data, window=7)
        self.assertEqual(result, Decimal('20'))  # Average of all 3
    
    def test_moving_average_forecast_custom_window(self):
        """测试：自定义窗口移动平均"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        result = self.engine._moving_average_forecast(data, window=2)
        self.assertEqual(result, Decimal('35'))  # Average of last 2
    
    # ========== 指数平滑预测测试 ==========
    
    def test_exponential_smoothing_forecast_standard(self):
        """测试：标准指数平滑"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._exponential_smoothing_forecast(data)
        self.assertGreater(result, Decimal('0'))
    
    def test_exponential_smoothing_forecast_empty_data(self):
        """测试：空数据指数平滑"""
        result = self.engine._exponential_smoothing_forecast([])
        self.assertEqual(result, Decimal('0'))
    
    def test_exponential_smoothing_forecast_single_value(self):
        """测试：单值指数平滑"""
        data = [Decimal('42')]
        result = self.engine._exponential_smoothing_forecast(data)
        self.assertEqual(result, Decimal('42'))
    
    def test_exponential_smoothing_forecast_custom_alpha(self):
        """测试：自定义alpha的指数平滑"""
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        result = self.engine._exponential_smoothing_forecast(data, alpha=Decimal('0.5'))
        self.assertGreater(result, Decimal('0'))
    
    # ========== 线性回归预测测试 ==========
    
    def test_linear_regression_forecast_upward_trend(self):
        """测试：上升趋势线性回归"""
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        result = self.engine._linear_regression_forecast(data)
        self.assertGreater(result, Decimal('40'))
    
    def test_linear_regression_forecast_downward_trend(self):
        """测试：下降趋势线性回归（结果不为负）"""
        data = [Decimal('40'), Decimal('30'), Decimal('20'), Decimal('10')]
        result = self.engine._linear_regression_forecast(data)
        self.assertGreaterEqual(result, Decimal('0'))
    
    def test_linear_regression_forecast_single_value(self):
        """测试：单值线性回归"""
        data = [Decimal('25')]
        result = self.engine._linear_regression_forecast(data)
        self.assertEqual(result, Decimal('25'))
    
    def test_linear_regression_forecast_flat_trend(self):
        """测试：平稳趋势线性回归"""
        data = [Decimal('20'), Decimal('20'), Decimal('20'), Decimal('20')]
        result = self.engine._linear_regression_forecast(data)
        self.assertEqual(result, Decimal('20'))
    
    # ========== 置信区间计算测试 ==========
    
    def test_calculate_confidence_interval_95_percent(self):
        """测试：95%置信区间"""
        forecast = Decimal('100')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        
        self.assertLess(lower, forecast)
        self.assertGreater(upper, forecast)
        self.assertGreaterEqual(lower, Decimal('0'))
    
    def test_calculate_confidence_interval_90_percent(self):
        """测试：90%置信区间"""
        forecast = Decimal('50')
        std = Decimal('5')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 90.0)
        
        self.assertLess(upper - lower, Decimal('20'))  # Smaller than 95%
    
    def test_calculate_confidence_interval_zero_std(self):
        """测试：零标准差的置信区间"""
        forecast = Decimal('100')
        std = Decimal('0')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        
        self.assertEqual(lower, forecast)
        self.assertEqual(upper, forecast)
    
    def test_calculate_confidence_interval_negative_lower_bound(self):
        """测试：下限不为负"""
        forecast = Decimal('5')
        std = Decimal('10')
        lower, upper = self.engine._calculate_confidence_interval(forecast, std, 95.0)
        
        self.assertGreaterEqual(lower, Decimal('0'))
    
    # ========== 预测编号生成测试 ==========
    
    def test_generate_forecast_no_first_of_day(self):
        """测试：生成当天第一个预测编号"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        
        with patch('app.services.shortage.demand_forecast_engine.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20260221'
            mock_datetime.now.return_value.date.return_value = date(2026, 2, 21)
            
            forecast_no = self.engine._generate_forecast_no()
        
        self.assertEqual(forecast_no, 'FC202602210001')
    
    def test_generate_forecast_no_multiple_forecasts(self):
        """测试：生成当天多个预测编号"""
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        
        with patch('app.services.shortage.demand_forecast_engine.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20260221'
            mock_datetime.now.return_value.date.return_value = date(2026, 2, 21)
            
            forecast_no = self.engine._generate_forecast_no()
        
        self.assertEqual(forecast_no, 'FC202602210006')
    
    # ========== 批量预测测试 ==========
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_batch_forecast_for_project_success(self, mock_save):
        """测试：项目批量预测成功"""
        mock_material_ids = [(1,), (2,), (3,)]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_material_ids
        
        historical_data = [Decimal('10'), Decimal('20'), Decimal('30')]
        
        with patch.object(self.engine, '_collect_historical_demand', return_value=historical_data):
            with patch.object(self.engine, '_generate_forecast_no', side_effect=['FC001', 'FC002', 'FC003']):
                forecasts = self.engine.batch_forecast_for_project(project_id=100)
        
        self.assertEqual(len(forecasts), 3)
        self.assertTrue(all(isinstance(f, MaterialDemandForecast) for f in forecasts))
    
    @patch('app.services.shortage.demand_forecast_engine.save_obj')
    def test_batch_forecast_for_project_partial_failure(self, mock_save):
        """测试：部分物料预测失败"""
        mock_material_ids = [(1,), (2,)]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_material_ids
        
        def mock_collect_side_effect(material_id, days, project_id):
            if material_id == 1:
                return [Decimal('10'), Decimal('20')]
            else:
                return []  # Will cause BusinessException
        
        with patch.object(self.engine, '_collect_historical_demand', side_effect=mock_collect_side_effect):
            with patch.object(self.engine, '_generate_forecast_no', return_value='FC001'):
                forecasts = self.engine.batch_forecast_for_project(project_id=100)
        
        self.assertEqual(len(forecasts), 1)  # Only material 1 succeeded
    
    def test_batch_forecast_for_project_no_materials(self):
        """测试：项目无物料"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        forecasts = self.engine.batch_forecast_for_project(project_id=999)
        
        self.assertEqual(len(forecasts), 0)
    
    # ========== 准确率报告测试 ==========
    
    def test_get_forecast_accuracy_report_success(self):
        """测试：获取准确率报告成功"""
        mock_forecasts = [
            MaterialDemandForecast(
                algorithm='EXP_SMOOTHING',
                accuracy_score=Decimal('90'),
                mape=Decimal('10'),
                forecasted_demand=Decimal('100'),
                actual_demand=Decimal('90'),
                lower_bound=Decimal('80'),
                upper_bound=Decimal('120')
            ),
            MaterialDemandForecast(
                algorithm='LINEAR_REGRESSION',
                accuracy_score=Decimal('85'),
                mape=Decimal('15'),
                forecasted_demand=Decimal('50'),
                actual_demand=Decimal('60'),
                lower_bound=Decimal('40'),
                upper_bound=Decimal('60')
            )
        ]
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_forecasts
        
        report = self.engine.get_forecast_accuracy_report(days=30)
        
        self.assertEqual(report['total_forecasts'], 2)
        self.assertEqual(report['average_accuracy'], 87.5)
        self.assertEqual(report['average_mape'], 12.5)
        self.assertIn('by_algorithm', report)
    
    def test_get_forecast_accuracy_report_no_data(self):
        """测试：无验证数据的准确率报告"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        report = self.engine.get_forecast_accuracy_report()
        
        self.assertEqual(report['total_forecasts'], 0)
        self.assertEqual(report['average_accuracy'], 0)
        self.assertEqual(report['average_mape'], 0)
    
    def test_get_forecast_accuracy_report_with_material_filter(self):
        """测试：带物料ID过滤的准确率报告"""
        mock_forecast = MaterialDemandForecast(
            algorithm='EXP_SMOOTHING',
            accuracy_score=Decimal('92'),
            mape=Decimal('8'),
            forecasted_demand=Decimal('100'),
            actual_demand=Decimal('92'),
            lower_bound=Decimal('80'),
            upper_bound=Decimal('120')
        )
        
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_forecast]
        
        report = self.engine.get_forecast_accuracy_report(material_id=1, days=30)
        
        self.assertEqual(report['total_forecasts'], 1)
        self.assertGreater(report['average_accuracy'], 0)


if __name__ == '__main__':
    unittest.main()
