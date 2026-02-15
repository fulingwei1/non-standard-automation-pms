# -*- coding: utf-8 -*-
"""
EVM计算器单元测试

测试所有PMBOK标准的挣值管理公式，确保计算精度和正确性
覆盖20+测试用例，验证边界条件和异常情况
"""

import pytest
from decimal import Decimal

from app.services.evm_service import EVMCalculator


class TestEVMCalculator:
    """EVM计算器测试类"""
    
    @pytest.fixture
    def calculator(self):
        """返回EVMCalculator实例"""
        return EVMCalculator()
    
    # ==================== 基础公式测试 ====================
    
    def test_schedule_variance_ahead(self, calculator):
        """测试进度偏差 - 进度超前场景 (SV > 0)"""
        ev = Decimal('120000')
        pv = Decimal('100000')
        sv = calculator.calculate_schedule_variance(ev, pv)
        
        assert sv == Decimal('20000.0000')
        assert sv > 0  # 进度超前
    
    def test_schedule_variance_behind(self, calculator):
        """测试进度偏差 - 进度落后场景 (SV < 0)"""
        ev = Decimal('80000')
        pv = Decimal('100000')
        sv = calculator.calculate_schedule_variance(ev, pv)
        
        assert sv == Decimal('-20000.0000')
        assert sv < 0  # 进度落后
    
    def test_schedule_variance_on_track(self, calculator):
        """测试进度偏差 - 进度正常场景 (SV = 0)"""
        ev = Decimal('100000')
        pv = Decimal('100000')
        sv = calculator.calculate_schedule_variance(ev, pv)
        
        assert sv == Decimal('0.0000')
    
    def test_cost_variance_under_budget(self, calculator):
        """测试成本偏差 - 成本节约场景 (CV > 0)"""
        ev = Decimal('100000')
        ac = Decimal('80000')
        cv = calculator.calculate_cost_variance(ev, ac)
        
        assert cv == Decimal('20000.0000')
        assert cv > 0  # 成本节约
    
    def test_cost_variance_over_budget(self, calculator):
        """测试成本偏差 - 成本超支场景 (CV < 0)"""
        ev = Decimal('100000')
        ac = Decimal('120000')
        cv = calculator.calculate_cost_variance(ev, ac)
        
        assert cv == Decimal('-20000.0000')
        assert cv < 0  # 成本超支
    
    def test_cost_variance_on_budget(self, calculator):
        """测试成本偏差 - 成本正常场景 (CV = 0)"""
        ev = Decimal('100000')
        ac = Decimal('100000')
        cv = calculator.calculate_cost_variance(ev, ac)
        
        assert cv == Decimal('0.0000')
    
    # ==================== 绩效指数测试 ====================
    
    def test_schedule_performance_index_good(self, calculator):
        """测试进度绩效指数 - 进度超前 (SPI > 1)"""
        ev = Decimal('120000')
        pv = Decimal('100000')
        spi = calculator.calculate_schedule_performance_index(ev, pv)
        
        assert spi == Decimal('1.200000')
        assert spi > 1  # 进度超前
    
    def test_schedule_performance_index_poor(self, calculator):
        """测试进度绩效指数 - 进度落后 (SPI < 1)"""
        ev = Decimal('80000')
        pv = Decimal('100000')
        spi = calculator.calculate_schedule_performance_index(ev, pv)
        
        assert spi == Decimal('0.800000')
        assert spi < 1  # 进度落后
    
    def test_schedule_performance_index_pv_zero(self, calculator):
        """测试进度绩效指数 - PV为0的边界情况"""
        ev = Decimal('100000')
        pv = Decimal('0')
        spi = calculator.calculate_schedule_performance_index(ev, pv)
        
        assert spi is None  # 无法计算
    
    def test_cost_performance_index_good(self, calculator):
        """测试成本绩效指数 - 成本效率高 (CPI > 1)"""
        ev = Decimal('100000')
        ac = Decimal('80000')
        cpi = calculator.calculate_cost_performance_index(ev, ac)
        
        assert cpi == Decimal('1.250000')
        assert cpi > 1  # 成本效率高
    
    def test_cost_performance_index_poor(self, calculator):
        """测试成本绩效指数 - 成本效率低 (CPI < 1)"""
        ev = Decimal('100000')
        ac = Decimal('120000')
        cpi = calculator.calculate_cost_performance_index(ev, ac)
        
        assert cpi == Decimal('0.833333')
        assert cpi < 1  # 成本效率低
    
    def test_cost_performance_index_ac_zero(self, calculator):
        """测试成本绩效指数 - AC为0的边界情况"""
        ev = Decimal('100000')
        ac = Decimal('0')
        cpi = calculator.calculate_cost_performance_index(ev, ac)
        
        assert cpi is None  # 无法计算
    
    # ==================== 预测指标测试 ====================
    
    def test_estimate_at_completion_standard(self, calculator):
        """测试完工估算 - 标准公式 EAC = AC + (BAC - EV) / CPI"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')  # CPI = 0.8
        
        eac = calculator.calculate_estimate_at_completion(bac, ev, ac)
        
        # EAC = 500000 + (1000000 - 400000) / 0.8 = 500000 + 750000 = 1250000
        assert eac == Decimal('1250000.0000')
    
    def test_estimate_at_completion_cpi_zero(self, calculator):
        """测试完工估算 - CPI为0时的简化公式"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('0')  # CPI无法计算
        
        eac = calculator.calculate_estimate_at_completion(bac, ev, ac)
        
        # EAC = AC + (BAC - EV) = 0 + 600000 = 600000
        assert eac == Decimal('600000.0000')
    
    def test_estimate_to_complete(self, calculator):
        """测试完工尚需估算 ETC = EAC - AC"""
        eac = Decimal('1250000')
        ac = Decimal('500000')
        
        etc = calculator.calculate_estimate_to_complete(eac, ac)
        
        assert etc == Decimal('750000.0000')
    
    def test_variance_at_completion_favorable(self, calculator):
        """测试完工偏差 - 预计节约 (VAC > 0)"""
        bac = Decimal('1000000')
        eac = Decimal('950000')
        
        vac = calculator.calculate_variance_at_completion(bac, eac)
        
        assert vac == Decimal('50000.0000')
        assert vac > 0  # 预计节约
    
    def test_variance_at_completion_unfavorable(self, calculator):
        """测试完工偏差 - 预计超支 (VAC < 0)"""
        bac = Decimal('1000000')
        eac = Decimal('1250000')
        
        vac = calculator.calculate_variance_at_completion(bac, eac)
        
        assert vac == Decimal('-250000.0000')
        assert vac < 0  # 预计超支
    
    def test_to_complete_performance_index_bac(self, calculator):
        """测试完工尚需绩效指数 - 基于BAC"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        
        tcpi = calculator.calculate_to_complete_performance_index(bac, ev, ac)
        
        # TCPI = (1000000 - 400000) / (1000000 - 500000) = 600000 / 500000 = 1.2
        assert tcpi == Decimal('1.200000')
    
    def test_to_complete_performance_index_eac(self, calculator):
        """测试完工尚需绩效指数 - 基于EAC"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('500000')
        eac = Decimal('1250000')
        
        tcpi = calculator.calculate_to_complete_performance_index(bac, ev, ac, eac)
        
        # TCPI = (1000000 - 400000) / (1250000 - 500000) = 600000 / 750000 = 0.8
        assert tcpi == Decimal('0.800000')
    
    def test_to_complete_performance_index_funds_zero(self, calculator):
        """测试完工尚需绩效指数 - 剩余资金为0"""
        bac = Decimal('1000000')
        ev = Decimal('400000')
        ac = Decimal('1000000')  # 资金已用完
        
        tcpi = calculator.calculate_to_complete_performance_index(bac, ev, ac)
        
        assert tcpi is None  # 无法计算
    
    # ==================== 百分比计算测试 ====================
    
    def test_percent_complete_normal(self, calculator):
        """测试完成百分比 - 正常情况"""
        value = Decimal('250000')
        bac = Decimal('1000000')
        
        percent = calculator.calculate_percent_complete(value, bac)
        
        assert percent == Decimal('25.00')
    
    def test_percent_complete_over_100(self, calculator):
        """测试完成百分比 - 超过100%的情况"""
        value = Decimal('1200000')
        bac = Decimal('1000000')
        
        percent = calculator.calculate_percent_complete(value, bac)
        
        assert percent == Decimal('120.00')
    
    def test_percent_complete_bac_zero(self, calculator):
        """测试完成百分比 - BAC为0"""
        value = Decimal('250000')
        bac = Decimal('0')
        
        percent = calculator.calculate_percent_complete(value, bac)
        
        assert percent is None
    
    # ==================== 综合计算测试 ====================
    
    def test_calculate_all_metrics_normal_case(self, calculator):
        """测试一次性计算所有指标 - 正常场景"""
        pv = Decimal('500000')
        ev = Decimal('450000')
        ac = Decimal('480000')
        bac = Decimal('2000000')
        
        metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        # 验证基础值
        assert metrics['pv'] == Decimal('500000')
        assert metrics['ev'] == Decimal('450000')
        assert metrics['ac'] == Decimal('480000')
        assert metrics['bac'] == Decimal('2000000')
        
        # 验证偏差
        assert metrics['sv'] == Decimal('-50000.0000')  # EV - PV
        assert metrics['cv'] == Decimal('-30000.0000')  # EV - AC
        
        # 验证绩效指数
        assert metrics['spi'] == Decimal('0.900000')  # EV / PV = 450000 / 500000
        assert metrics['cpi'] == Decimal('0.937500')  # EV / AC = 450000 / 480000
        
        # 验证百分比
        assert metrics['planned_percent_complete'] == Decimal('25.00')  # PV / BAC
        assert metrics['actual_percent_complete'] == Decimal('22.50')  # EV / BAC
    
    def test_calculate_all_metrics_edge_case(self, calculator):
        """测试一次性计算所有指标 - 边界场景（项目刚开始）"""
        pv = Decimal('0')
        ev = Decimal('0')
        ac = Decimal('0')
        bac = Decimal('1000000')
        
        metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        # SPI和CPI应该为None（分母为0）
        assert metrics['spi'] is None
        assert metrics['cpi'] is None
        
        # 百分比应该为0
        assert metrics['planned_percent_complete'] == Decimal('0.00')
        assert metrics['actual_percent_complete'] == Decimal('0.00')
    
    # ==================== 精度测试 ====================
    
    def test_decimal_precision(self, calculator):
        """测试Decimal精度 - 避免浮点误差"""
        # 使用会产生浮点误差的数字
        ev = Decimal('333.33')
        pv = Decimal('1000.00')
        
        spi = calculator.calculate_schedule_performance_index(ev, pv)
        
        # 应该精确到6位小数
        assert spi == Decimal('0.333330')
        
        # 验证不是浮点数
        assert isinstance(spi, Decimal)
    
    def test_rounding_behavior(self, calculator):
        """测试四舍五入行为"""
        # 测试ROUND_HALF_UP
        value1 = Decimal('123.45555')  # 应该四舍五入到123.4556
        rounded1 = calculator.round_decimal(value1, 4)
        assert rounded1 == Decimal('123.4556')
        
        value2 = Decimal('123.45554')  # 应该四舍五入到123.4555
        rounded2 = calculator.round_decimal(value2, 4)
        assert rounded2 == Decimal('123.4555')


class TestEVMCalculatorRealWorldScenarios:
    """真实场景测试"""
    
    @pytest.fixture
    def calculator(self):
        return EVMCalculator()
    
    def test_project_ahead_schedule_under_budget(self, calculator):
        """场景1：进度超前、成本节约（理想状态）"""
        pv = Decimal('500000')
        ev = Decimal('600000')  # 超额完成
        ac = Decimal('550000')  # 成本节约
        bac = Decimal('2000000')
        
        metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        assert metrics['sv'] > 0  # 进度超前
        assert metrics['cv'] > 0  # 成本节约
        assert metrics['spi'] > 1  # SPI = 1.2
        assert metrics['cpi'] > 1  # CPI ≈ 1.09
    
    def test_project_behind_schedule_over_budget(self, calculator):
        """场景2：进度落后、成本超支（风险状态）"""
        pv = Decimal('500000')
        ev = Decimal('400000')  # 未完成计划工作
        ac = Decimal('550000')  # 成本超支
        bac = Decimal('2000000')
        
        metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        assert metrics['sv'] < 0  # 进度落后
        assert metrics['cv'] < 0  # 成本超支
        assert metrics['spi'] < 1  # SPI = 0.8
        assert metrics['cpi'] < 1  # CPI ≈ 0.73
        
        # 预测完工成本会超支
        assert metrics['eac'] > bac
        assert metrics['vac'] < 0
    
    def test_project_near_completion(self, calculator):
        """场景3：项目接近完成（95%进度）"""
        pv = Decimal('1900000')
        ev = Decimal('1900000')
        ac = Decimal('1950000')
        bac = Decimal('2000000')
        
        metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        # 完成百分比接近95%
        assert metrics['actual_percent_complete'] == Decimal('95.00')
        
        # 剩余工作预算
        etc = metrics['etc']
        assert etc > 0 and etc < Decimal('100000')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
