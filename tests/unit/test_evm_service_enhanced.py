# -*- coding: utf-8 -*-
"""
EVM Service 增强单元测试

覆盖 EVMCalculator 和 EVMService 的所有核心方法和边界条件
使用 unittest.mock 模拟所有数据库操作
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.evm_service import EVMCalculator, EVMService
from app.models import EarnedValueData, Project


class TestEVMCalculator(unittest.TestCase):
    """测试 EVMCalculator 类的所有计算方法"""
    
    def setUp(self):
        """测试前准备"""
        self.calc = EVMCalculator()
    
    # ============ 工具方法测试 ============
    
    def test_decimal_conversion_from_float(self):
        """测试从浮点数转换为 Decimal"""
        result = EVMCalculator.decimal(123.456)
        self.assertEqual(result, Decimal('123.456'))
        self.assertIsInstance(result, Decimal)
    
    def test_decimal_conversion_from_int(self):
        """测试从整数转换为 Decimal"""
        result = EVMCalculator.decimal(100)
        self.assertEqual(result, Decimal('100'))
    
    def test_decimal_conversion_from_decimal(self):
        """测试从 Decimal 转换为 Decimal"""
        input_val = Decimal('99.99')
        result = EVMCalculator.decimal(input_val)
        self.assertEqual(result, Decimal('99.99'))
    
    def test_round_decimal_default_places(self):
        """测试默认精度四舍五入（4位小数）"""
        result = EVMCalculator.round_decimal(Decimal('123.456789'))
        self.assertEqual(result, Decimal('123.4568'))
    
    def test_round_decimal_custom_places(self):
        """测试自定义精度四舍五入"""
        result = EVMCalculator.round_decimal(Decimal('123.456'), places=2)
        self.assertEqual(result, Decimal('123.46'))
    
    def test_round_decimal_none_value(self):
        """测试 None 值的四舍五入处理"""
        result = EVMCalculator.round_decimal(None, places=4)
        self.assertEqual(result, Decimal('0.0000'))
    
    # ============ 偏差指标测试 ============
    
    def test_schedule_variance_positive(self):
        """测试进度偏差 - 超前情况（SV > 0）"""
        ev = Decimal('120000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_variance(ev, pv)
        self.assertEqual(result, Decimal('20000.0000'))
    
    def test_schedule_variance_zero(self):
        """测试进度偏差 - 符合计划（SV = 0）"""
        ev = Decimal('100000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_variance(ev, pv)
        self.assertEqual(result, Decimal('0.0000'))
    
    def test_schedule_variance_negative(self):
        """测试进度偏差 - 落后情况（SV < 0）"""
        ev = Decimal('80000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_variance(ev, pv)
        self.assertEqual(result, Decimal('-20000.0000'))
    
    def test_cost_variance_positive(self):
        """测试成本偏差 - 节约情况（CV > 0）"""
        ev = Decimal('100000')
        ac = Decimal('80000')
        result = EVMCalculator.calculate_cost_variance(ev, ac)
        self.assertEqual(result, Decimal('20000.0000'))
    
    def test_cost_variance_zero(self):
        """测试成本偏差 - 符合预算（CV = 0）"""
        ev = Decimal('100000')
        ac = Decimal('100000')
        result = EVMCalculator.calculate_cost_variance(ev, ac)
        self.assertEqual(result, Decimal('0.0000'))
    
    def test_cost_variance_negative(self):
        """测试成本偏差 - 超支情况（CV < 0）"""
        ev = Decimal('80000')
        ac = Decimal('100000')
        result = EVMCalculator.calculate_cost_variance(ev, ac)
        self.assertEqual(result, Decimal('-20000.0000'))
    
    # ============ 绩效指数测试 ============
    
    def test_schedule_performance_index_above_one(self):
        """测试进度绩效指数 - 超前（SPI > 1）"""
        ev = Decimal('120000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_performance_index(ev, pv)
        self.assertEqual(result, Decimal('1.200000'))
    
    def test_schedule_performance_index_equal_one(self):
        """测试进度绩效指数 - 符合计划（SPI = 1）"""
        ev = Decimal('100000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_performance_index(ev, pv)
        self.assertEqual(result, Decimal('1.000000'))
    
    def test_schedule_performance_index_below_one(self):
        """测试进度绩效指数 - 落后（SPI < 1）"""
        ev = Decimal('80000')
        pv = Decimal('100000')
        result = EVMCalculator.calculate_schedule_performance_index(ev, pv)
        self.assertEqual(result, Decimal('0.800000'))
    
    def test_schedule_performance_index_zero_pv(self):
        """测试进度绩效指数 - PV为0的边界情况"""
        ev = Decimal('100000')
        pv = Decimal('0')
        result = EVMCalculator.calculate_schedule_performance_index(ev, pv)
        self.assertIsNone(result)
    
    def test_cost_performance_index_above_one(self):
        """测试成本绩效指数 - 效率高（CPI > 1）"""
        ev = Decimal('100000')
        ac = Decimal('80000')
        result = EVMCalculator.calculate_cost_performance_index(ev, ac)
        self.assertEqual(result, Decimal('1.250000'))
    
    def test_cost_performance_index_equal_one(self):
        """测试成本绩效指数 - 符合预算（CPI = 1）"""
        ev = Decimal('100000')
        ac = Decimal('100000')
        result = EVMCalculator.calculate_cost_performance_index(ev, ac)
        self.assertEqual(result, Decimal('1.000000'))
    
    def test_cost_performance_index_below_one(self):
        """测试成本绩效指数 - 效率低（CPI < 1）"""
        ev = Decimal('80000')
        ac = Decimal('100000')
        result = EVMCalculator.calculate_cost_performance_index(ev, ac)
        self.assertEqual(result, Decimal('0.800000'))
    
    def test_cost_performance_index_zero_ac(self):
        """测试成本绩效指数 - AC为0的边界情况"""
        ev = Decimal('100000')
        ac = Decimal('0')
        result = EVMCalculator.calculate_cost_performance_index(ev, ac)
        self.assertIsNone(result)
    
    # ============ 预测指标测试 ============
    
    def test_estimate_at_completion_with_cpi(self):
        """测试完工估算 - 提供CPI的标准计算"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        cpi = Decimal('0.8')  # EV/AC = 400000/500000
        result = EVMCalculator.calculate_estimate_at_completion(bac, ev, ac, cpi)
        # EAC = AC + (BAC - EV) / CPI = 500000 + 600000 / 0.8 = 1250000
        self.assertEqual(result, Decimal('1250000.0000'))
    
    def test_estimate_at_completion_auto_cpi(self):
        """测试完工估算 - 自动计算CPI"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        result = EVMCalculator.calculate_estimate_at_completion(bac, ev, ac)
        # CPI = 400000/500000 = 0.8, EAC = 500000 + 600000/0.8 = 1250000
        self.assertEqual(result, Decimal('1250000.0000'))
    
    def test_estimate_at_completion_zero_cpi(self):
        """测试完工估算 - CPI为0的边界情况"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        cpi = Decimal('0')
        result = EVMCalculator.calculate_estimate_at_completion(bac, ev, ac, cpi)
        # 使用简化公式: EAC = AC + (BAC - EV) = 500000 + 600000 = 1100000
        self.assertEqual(result, Decimal('1100000.0000'))
    
    def test_estimate_at_completion_none_cpi(self):
        """测试完工估算 - CPI为None的边界情况（AC=0）"""
        bac = Decimal('1000000')
        ev = Decimal('0')
        ac = Decimal('0')
        result = EVMCalculator.calculate_estimate_at_completion(bac, ev, ac)
        # CPI无法计算（AC=0），使用简化公式: EAC = 0 + 1000000 = 1000000
        self.assertEqual(result, Decimal('1000000.0000'))
    
    def test_estimate_to_complete(self):
        """测试完工尚需估算"""
        eac = Decimal('1250000')
        ac = Decimal('500000')
        result = EVMCalculator.calculate_estimate_to_complete(eac, ac)
        self.assertEqual(result, Decimal('750000.0000'))
    
    def test_estimate_to_complete_zero(self):
        """测试完工尚需估算 - 已完工的情况"""
        eac = Decimal('500000')
        ac = Decimal('500000')
        result = EVMCalculator.calculate_estimate_to_complete(eac, ac)
        self.assertEqual(result, Decimal('0.0000'))
    
    def test_variance_at_completion_positive(self):
        """测试完工偏差 - 预计节约（VAC > 0）"""
        bac = Decimal('1000000')
        eac = Decimal('900000')
        result = EVMCalculator.calculate_variance_at_completion(bac, eac)
        self.assertEqual(result, Decimal('100000.0000'))
    
    def test_variance_at_completion_zero(self):
        """测试完工偏差 - 符合预算（VAC = 0）"""
        bac = Decimal('1000000')
        eac = Decimal('1000000')
        result = EVMCalculator.calculate_variance_at_completion(bac, eac)
        self.assertEqual(result, Decimal('0.0000'))
    
    def test_variance_at_completion_negative(self):
        """测试完工偏差 - 预计超支（VAC < 0）"""
        bac = Decimal('1000000')
        eac = Decimal('1100000')
        result = EVMCalculator.calculate_variance_at_completion(bac, eac)
        self.assertEqual(result, Decimal('-100000.0000'))
    
    def test_to_complete_performance_index_based_on_bac(self):
        """测试完工尚需绩效指数 - 基于BAC"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        result = EVMCalculator.calculate_to_complete_performance_index(bac, ev, ac)
        # TCPI = (BAC - EV) / (BAC - AC) = 600000 / 500000 = 1.2
        self.assertEqual(result, Decimal('1.200000'))
    
    def test_to_complete_performance_index_based_on_eac(self):
        """测试完工尚需绩效指数 - 基于EAC"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        eac = Decimal('1250000')
        result = EVMCalculator.calculate_to_complete_performance_index(bac, ev, ac, eac)
        # TCPI = (BAC - EV) / (EAC - AC) = 600000 / 750000 = 0.8
        self.assertEqual(result, Decimal('0.800000'))
    
    def test_to_complete_performance_index_zero_funds_remaining(self):
        """测试完工尚需绩效指数 - 剩余资金为0的边界情况"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('1000000')  # AC = BAC
        result = EVMCalculator.calculate_to_complete_performance_index(bac, ev, ac)
        self.assertIsNone(result)
    
    # ============ 百分比计算测试 ============
    
    def test_percent_complete_normal(self):
        """测试完成百分比 - 正常情况"""
        value = Decimal('400000')
        bac = Decimal('1000000')
        result = EVMCalculator.calculate_percent_complete(value, bac)
        self.assertEqual(result, Decimal('40.00'))
    
    def test_percent_complete_zero_bac(self):
        """测试完成百分比 - BAC为0的边界情况"""
        value = Decimal('100000')
        bac = Decimal('0')
        result = EVMCalculator.calculate_percent_complete(value, bac)
        self.assertIsNone(result)
    
    def test_percent_complete_over_hundred(self):
        """测试完成百分比 - 超过100%的情况"""
        value = Decimal('1200000')
        bac = Decimal('1000000')
        result = EVMCalculator.calculate_percent_complete(value, bac)
        self.assertEqual(result, Decimal('120.00'))
    
    # ============ 综合计算测试 ============
    
    def test_calculate_all_metrics_complete(self):
        """测试一次性计算所有指标 - 完整场景"""
        pv = 100000
        ev = 90000
        ac = 95000
        bac = 1000000
        
        result = EVMCalculator.calculate_all_metrics(pv, ev, ac, bac)
        
        # 验证所有字段都存在
        expected_keys = [
            "pv", "ev", "ac", "bac",
            "sv", "cv",
            "spi", "cpi",
            "eac", "etc", "vac", "tcpi",
            "planned_percent_complete", "actual_percent_complete"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # 验证基础值
        self.assertEqual(result["pv"], Decimal('100000'))
        self.assertEqual(result["ev"], Decimal('90000'))
        self.assertEqual(result["ac"], Decimal('95000'))
        self.assertEqual(result["bac"], Decimal('1000000'))
        
        # 验证偏差
        self.assertEqual(result["sv"], Decimal('-10000.0000'))  # 90000 - 100000
        self.assertEqual(result["cv"], Decimal('-5000.0000'))   # 90000 - 95000
        
        # 验证绩效指数
        self.assertEqual(result["spi"], Decimal('0.900000'))    # 90000 / 100000
        self.assertAlmostEqual(float(result["cpi"]), 0.947368, places=5)  # 90000 / 95000
        
        # 验证百分比
        self.assertEqual(result["planned_percent_complete"], Decimal('10.00'))
        self.assertEqual(result["actual_percent_complete"], Decimal('9.00'))


class TestEVMService(unittest.TestCase):
    """测试 EVMService 类的所有业务方法"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = EVMService(self.mock_db)
    
    # ============ 初始化测试 ============
    
    def test_init_service(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.calculator)
        self.assertIsInstance(self.service.calculator, EVMCalculator)
    
    # ============ 周期标签生成测试 ============
    
    def test_generate_period_label_week(self):
        """测试生成周期标签 - 周"""
        period_date = date(2026, 2, 21)  # 2026年第8周
        result = self.service._generate_period_label("WEEK", period_date)
        self.assertEqual(result, "2026-W08")
    
    def test_generate_period_label_month(self):
        """测试生成周期标签 - 月"""
        period_date = date(2026, 2, 21)
        result = self.service._generate_period_label("MONTH", period_date)
        self.assertEqual(result, "2026-02")
    
    def test_generate_period_label_quarter_q1(self):
        """测试生成周期标签 - 第1季度"""
        period_date = date(2026, 2, 21)
        result = self.service._generate_period_label("QUARTER", period_date)
        self.assertEqual(result, "2026-Q1")
    
    def test_generate_period_label_quarter_q2(self):
        """测试生成周期标签 - 第2季度"""
        period_date = date(2026, 5, 15)
        result = self.service._generate_period_label("QUARTER", period_date)
        self.assertEqual(result, "2026-Q2")
    
    def test_generate_period_label_quarter_q3(self):
        """测试生成周期标签 - 第3季度"""
        period_date = date(2026, 8, 15)
        result = self.service._generate_period_label("QUARTER", period_date)
        self.assertEqual(result, "2026-Q3")
    
    def test_generate_period_label_quarter_q4(self):
        """测试生成周期标签 - 第4季度"""
        period_date = date(2026, 11, 15)
        result = self.service._generate_period_label("QUARTER", period_date)
        self.assertEqual(result, "2026-Q4")
    
    def test_generate_period_label_other(self):
        """测试生成周期标签 - 其他类型（默认日期格式）"""
        period_date = date(2026, 2, 21)
        result = self.service._generate_period_label("DAILY", period_date)
        self.assertEqual(result, "2026-02-21")
    
    # ============ 创建EVM数据测试 ============
    
    @patch('app.services.evm_service.save_obj')
    def test_create_evm_data_success(self, mock_save):
        """测试创建EVM数据 - 成功场景"""
        # Mock项目查询
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 调用创建方法
        result = self.service.create_evm_data(
            project_id=1,
            period_type="MONTH",
            period_date=date(2026, 2, 21),
            pv=Decimal('100000'),
            ev=Decimal('90000'),
            ac=Decimal('95000'),
            bac=Decimal('1000000'),
            currency="CNY",
            data_source="MANUAL",
            created_by=1,
            notes="测试数据"
        )
        
        # 验证返回值
        self.assertIsInstance(result, EarnedValueData)
        self.assertEqual(result.project_id, 1)
        self.assertEqual(result.project_code, "PRJ001")
        self.assertEqual(result.period_type, "MONTH")
        self.assertEqual(result.period_label, "2026-02")
        self.assertEqual(result.currency, "CNY")
        self.assertEqual(result.data_source, "MANUAL")
        self.assertEqual(result.created_by, 1)
        self.assertEqual(result.notes, "测试数据")
        
        # 验证计算的指标
        self.assertEqual(result.planned_value, Decimal('100000'))
        self.assertEqual(result.earned_value, Decimal('90000'))
        self.assertEqual(result.actual_cost, Decimal('95000'))
        self.assertEqual(result.budget_at_completion, Decimal('1000000'))
        self.assertEqual(result.schedule_variance, Decimal('-10000.0000'))
        self.assertEqual(result.cost_variance, Decimal('-5000.0000'))
        
        # 验证保存被调用
        mock_save.assert_called_once_with(self.mock_db, result)
    
    @patch('app.services.evm_service.save_obj')
    def test_create_evm_data_project_not_found(self, mock_save):
        """测试创建EVM数据 - 项目不存在"""
        # Mock项目查询返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.create_evm_data(
                project_id=999,
                period_type="MONTH",
                period_date=date(2026, 2, 21),
                pv=Decimal('100000'),
                ev=Decimal('90000'),
                ac=Decimal('95000'),
                bac=Decimal('1000000')
            )
        
        self.assertIn("项目不存在", str(context.exception))
        mock_save.assert_not_called()
    
    # ============ 获取最新EVM数据测试 ============
    
    def test_get_latest_evm_data_with_period_type(self):
        """测试获取最新EVM数据 - 指定周期类型"""
        # Mock查询结果
        mock_evm_data = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_evm_data
        
        result = self.service.get_latest_evm_data(project_id=1, period_type="MONTH")
        
        self.assertEqual(result, mock_evm_data)
        self.mock_db.query.assert_called_once()
    
    def test_get_latest_evm_data_without_period_type(self):
        """测试获取最新EVM数据 - 不指定周期类型"""
        mock_evm_data = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_evm_data
        
        result = self.service.get_latest_evm_data(project_id=1)
        
        self.assertEqual(result, mock_evm_data)
    
    def test_get_latest_evm_data_not_found(self):
        """测试获取最新EVM数据 - 无数据"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.get_latest_evm_data(project_id=999)
        
        self.assertIsNone(result)
    
    # ============ 获取EVM趋势测试 ============
    
    def test_get_evm_trend_with_limit(self):
        """测试获取EVM趋势 - 带数量限制"""
        mock_data_list = [MagicMock(), MagicMock(), MagicMock()]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_data_list
        
        result = self.service.get_evm_trend(project_id=1, period_type="MONTH", limit=3)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result, mock_data_list)
    
    def test_get_evm_trend_without_limit(self):
        """测试获取EVM趋势 - 不限制数量"""
        mock_data_list = [MagicMock() for _ in range(10)]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_data_list
        
        result = self.service.get_evm_trend(project_id=1, period_type="MONTH")
        
        self.assertEqual(len(result), 10)
    
    # ============ 绩效分析测试 ============
    
    def test_analyze_performance_excellent(self):
        """测试绩效分析 - 优秀状态（SPI >= 1.1, CPI >= 1.1）"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal('1.15')
        mock_evm.cost_performance_index = Decimal('1.20')
        
        result = self.service.analyze_performance(mock_evm)
        
        self.assertEqual(result["overall_status"], "EXCELLENT")
        self.assertEqual(result["schedule_status"], "EXCELLENT")
        self.assertEqual(result["cost_status"], "EXCELLENT")
        self.assertIn("超前", result["schedule_description"])
        self.assertIn("优秀", result["cost_description"])
    
    def test_analyze_performance_good(self):
        """测试绩效分析 - 良好状态（0.95 <= SPI < 1.1, 0.95 <= CPI < 1.1）"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal('1.00')
        mock_evm.cost_performance_index = Decimal('0.98')
        
        result = self.service.analyze_performance(mock_evm)
        
        # 当进度和成本都是GOOD或EXCELLENT时，overall_status为EXCELLENT
        self.assertEqual(result["overall_status"], "EXCELLENT")
        self.assertEqual(result["schedule_status"], "GOOD")
        self.assertEqual(result["cost_status"], "GOOD")
        self.assertIn("正常", result["schedule_description"])
        self.assertIn("正常", result["cost_description"])
    
    def test_analyze_performance_warning(self):
        """测试绩效分析 - 警告状态（0.8 <= SPI < 0.95, 0.8 <= CPI < 0.95）"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal('0.90')
        mock_evm.cost_performance_index = Decimal('0.85')
        
        result = self.service.analyze_performance(mock_evm)
        
        self.assertEqual(result["overall_status"], "WARNING")
        self.assertEqual(result["schedule_status"], "WARNING")
        self.assertEqual(result["cost_status"], "WARNING")
        self.assertIn("轻微落后", result["schedule_description"])
        self.assertIn("轻微超支", result["cost_description"])
    
    def test_analyze_performance_critical(self):
        """测试绩效分析 - 严重状态（SPI < 0.8, CPI < 0.8）"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal('0.70')
        mock_evm.cost_performance_index = Decimal('0.65')
        
        result = self.service.analyze_performance(mock_evm)
        
        self.assertEqual(result["overall_status"], "CRITICAL")
        self.assertEqual(result["schedule_status"], "CRITICAL")
        self.assertEqual(result["cost_status"], "CRITICAL")
        self.assertIn("严重落后", result["schedule_description"])
        self.assertIn("严重超支", result["cost_description"])
    
    def test_analyze_performance_mixed_status(self):
        """测试绩效分析 - 混合状态（一个好，一个差）"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = Decimal('1.10')
        mock_evm.cost_performance_index = Decimal('0.75')
        
        result = self.service.analyze_performance(mock_evm)
        
        # 有一个CRITICAL，整体应该是CRITICAL
        self.assertEqual(result["overall_status"], "CRITICAL")
        self.assertEqual(result["schedule_status"], "EXCELLENT")
        self.assertEqual(result["cost_status"], "CRITICAL")
    
    def test_analyze_performance_none_values(self):
        """测试绩效分析 - 处理None值"""
        mock_evm = MagicMock()
        mock_evm.schedule_performance_index = None
        mock_evm.cost_performance_index = None
        
        result = self.service.analyze_performance(mock_evm)
        
        # None被转换为0，应该判定为CRITICAL
        self.assertEqual(result["overall_status"], "CRITICAL")
        self.assertEqual(result["spi"], 0.0)
        self.assertEqual(result["cpi"], 0.0)


if __name__ == '__main__':
    unittest.main()
