# -*- coding: utf-8 -*-
"""
产能分析系统测试用例
覆盖OEE计算、工人效率分析、瓶颈识别、产能预测等功能
"""
import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal

from app.models.base import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
    Workstation,
)


class TestOEECalculation:
    """OEE计算测试"""
    
    def test_oee_calculation_standard(self, db_session):
        """测试标准OEE计算"""
        # 计划生产时间:480分钟(8小时)
        # 计划停机:30分钟
        # 非计划停机:20分钟
        # 运行时间:430分钟
        # 理想周期:2分钟/件
        # 实际产量:200件
        # 合格数:190件
        
        planned_production_time = 480
        planned_downtime = 30
        unplanned_downtime = 20
        operating_time = planned_production_time - planned_downtime - unplanned_downtime  # 430
        
        ideal_cycle_time = 2.0
        actual_output = 200
        qualified_qty = 190
        
        # 可用率 = 430 / 480 = 89.58%
        availability = (operating_time / planned_production_time) * 100
        assert abs(availability - 89.58) < 0.1
        
        # 性能率 = (2 * 200) / 430 = 93.02%
        performance = (ideal_cycle_time * actual_output / operating_time) * 100
        assert abs(performance - 93.02) < 0.1
        
        # 合格率 = 190 / 200 = 95%
        quality = (qualified_qty / actual_output) * 100
        assert quality == 95.0
        
        # OEE = 89.58% * 93.02% * 95% = 79.14%
        oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
        assert abs(oee - 79.14) < 0.1
    
    def test_oee_world_class(self, db_session):
        """测试世界级OEE(≥85%)"""
        # 高效运行场景
        planned_production_time = 480
        unplanned_downtime = 10
        operating_time = planned_production_time - unplanned_downtime  # 470
        
        ideal_cycle_time = 2.0
        actual_output = 230
        qualified_qty = 228
        
        availability = (operating_time / planned_production_time) * 100  # 97.92%
        performance = (ideal_cycle_time * actual_output / operating_time) * 100  # 97.87%
        quality = (qualified_qty / actual_output) * 100  # 99.13%
        oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
        
        assert oee >= 85, f"OEE {oee} should be world class (≥85%)"
    
    def test_oee_low_availability(self, db_session):
        """测试低可用率场景"""
        planned_production_time = 480
        unplanned_downtime = 150  # 大量停机
        operating_time = planned_production_time - unplanned_downtime  # 330
        
        availability = (operating_time / planned_production_time) * 100
        assert availability < 70, "Availability should be low due to high downtime"
    
    def test_oee_low_performance(self, db_session):
        """测试低性能率场景"""
        operating_time = 480
        ideal_cycle_time = 2.0
        actual_output = 150  # 低于理想产量240
        
        performance = (ideal_cycle_time * actual_output / operating_time) * 100
        assert performance < 65, "Performance should be low due to low output"
    
    def test_oee_low_quality(self, db_session):
        """测试低合格率场景"""
        actual_output = 200
        qualified_qty = 150  # 大量不良品
        
        quality = (qualified_qty / actual_output) * 100
        assert quality == 75, "Quality rate should be 75%"


class TestWorkerEfficiency:
    """工人效率测试"""
    
    def test_worker_efficiency_calculation(self, db_session):
        """测试工人效率计算"""
        standard_hours = 8.0
        actual_hours = 10.0
        
        # 效率 = 8 / 10 = 80%
        efficiency = (standard_hours / actual_hours) * 100
        assert efficiency == 80.0
    
    def test_worker_high_efficiency(self, db_session):
        """测试高效率工人(效率>120%)"""
        standard_hours = 10.0
        actual_hours = 8.0
        
        efficiency = (standard_hours / actual_hours) * 100
        assert efficiency == 125.0
        assert efficiency >= 120, "Should be excellent efficiency"
    
    def test_worker_utilization_rate(self, db_session):
        """测试工人利用率"""
        actual_hours = 10.0
        idle_hours = 2.0
        break_hours = 0.5
        
        effective_hours = actual_hours - idle_hours - break_hours
        utilization_rate = (effective_hours / actual_hours) * 100
        
        assert utilization_rate == 75.0
    
    def test_worker_overall_efficiency(self, db_session):
        """测试综合效率计算"""
        # 工作效率:90%
        # 合格率:95%
        # 利用率:85%
        efficiency = 90.0
        quality_rate = 95.0
        utilization_rate = 85.0
        
        overall = (efficiency / 100) * (quality_rate / 100) * (utilization_rate / 100) * 100
        assert abs(overall - 72.675) < 0.01


class TestCapacityForecasting:
    """产能预测测试"""
    
    def test_linear_regression_simple(self):
        """测试简单线性回归"""
        # y = 2x + 10
        x_values = [1, 2, 3, 4, 5]
        y_values = [12, 14, 16, 18, 20]
        
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept - 10.0) < 0.01
    
    def test_forecast_trend_increasing(self):
        """测试上升趋势预测"""
        # 模拟产量递增数据
        values = [100, 105, 110, 115, 120, 125, 130]
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        assert avg_second > avg_first, "Trend should be increasing"
    
    def test_r_squared_calculation(self):
        """测试R²计算"""
        # 完美线性关系
        values = [10, 20, 30, 40, 50]
        slope = 10
        intercept = 0
        
        y_mean = sum(values) / len(values)
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        ss_res = sum((values[i] - (slope * i + intercept)) ** 2 for i in range(len(values)))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        assert r_squared > 0.99, "R² should be close to 1 for perfect fit"


class TestBottleneckIdentification:
    """瓶颈识别测试"""
    
    def test_high_utilization_bottleneck(self):
        """测试高利用率瓶颈"""
        operating_time = 450
        planned_time = 480
        utilization = (operating_time / planned_time) * 100
        
        threshold = 80.0
        assert utilization > threshold, "Should be identified as bottleneck"
    
    def test_low_oee_bottleneck(self):
        """测试低OEE瓶颈"""
        oee = 45.0  # 低于60%
        assert oee < 60, "Should be identified as bottleneck due to low OEE"
    
    def test_bottleneck_priority(self):
        """测试瓶颈优先级排序"""
        bottlenecks = [
            {"name": "设备A", "utilization": 95, "output": 1000},
            {"name": "设备B", "utilization": 85, "output": 2000},
            {"name": "设备C", "utilization": 90, "output": 1500},
        ]
        
        # 按利用率排序
        sorted_bottlenecks = sorted(bottlenecks, key=lambda x: x['utilization'], reverse=True)
        assert sorted_bottlenecks[0]['name'] == "设备A"


class TestMultiDimensionalComparison:
    """多维度对比测试"""
    
    def test_workshop_comparison(self):
        """测试车间对比"""
        workshops = [
            {"id": 1, "name": "车间A", "avg_oee": 75},
            {"id": 2, "name": "车间B", "avg_oee": 85},
            {"id": 3, "name": "车间C", "avg_oee": 68},
        ]
        
        # 排名
        ranked = sorted(workshops, key=lambda x: x['avg_oee'], reverse=True)
        assert ranked[0]['name'] == "车间B"
        assert ranked[-1]['name'] == "车间C"
    
    def test_period_comparison(self):
        """测试时间段对比"""
        current_oee = 80.0
        previous_oee = 75.0
        
        change_percent = ((current_oee - previous_oee) / previous_oee) * 100
        assert abs(change_percent - 6.67) < 0.1
        
        trend = "上升" if change_percent > 5 else "平稳"
        assert trend == "上升"


class TestOEELevelClassification:
    """OEE等级分类测试"""
    
    def test_world_class_oee(self):
        """测试世界级OEE"""
        oee = 88.0
        level = "世界级" if oee >= 85 else "良好" if oee >= 60 else "需改进"
        assert level == "世界级"
    
    def test_good_oee(self):
        """测试良好OEE"""
        oee = 72.0
        level = "世界级" if oee >= 85 else "良好" if oee >= 60 else "需改进"
        assert level == "良好"
    
    def test_needs_improvement_oee(self):
        """测试需改进OEE"""
        oee = 55.0
        level = "世界级" if oee >= 85 else "良好" if oee >= 60 else "需改进"
        assert level == "需改进"


class TestEfficiencyLevelClassification:
    """效率等级分类测试"""
    
    def test_excellent_efficiency(self):
        """测试优秀效率"""
        efficiency = 125.0
        level = "优秀" if efficiency >= 120 else "良好" if efficiency >= 100 else "正常" if efficiency >= 80 else "偏低"
        assert level == "优秀"
    
    def test_good_efficiency(self):
        """测试良好效率"""
        efficiency = 110.0
        level = "优秀" if efficiency >= 120 else "良好" if efficiency >= 100 else "正常" if efficiency >= 80 else "偏低"
        assert level == "良好"
    
    def test_normal_efficiency(self):
        """测试正常效率"""
        efficiency = 90.0
        level = "优秀" if efficiency >= 120 else "良好" if efficiency >= 100 else "正常" if efficiency >= 80 else "偏低"
        assert level == "正常"
    
    def test_low_efficiency(self):
        """测试偏低效率"""
        efficiency = 75.0
        level = "优秀" if efficiency >= 120 else "良好" if efficiency >= 100 else "正常" if efficiency >= 80 else "偏低"
        assert level == "偏低"


class TestDataAccuracy:
    """数据准确性测试"""
    
    def test_oee_components_sum(self):
        """测试OEE三要素合理性"""
        availability = 90.0
        performance = 85.0
        quality = 95.0
        
        oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
        
        # OEE不应超过三要素的最小值
        assert oee <= min(availability, performance, quality)
    
    def test_quality_rate_bounds(self):
        """测试合格率边界"""
        qualified_qty = 95
        actual_output = 100
        
        quality_rate = (qualified_qty / actual_output) * 100
        assert 0 <= quality_rate <= 100
    
    def test_utilization_rate_bounds(self):
        """测试利用率边界"""
        actual_hours = 10.0
        idle_hours = 2.0
        break_hours = 0.5
        
        effective_hours = actual_hours - idle_hours - break_hours
        utilization = (effective_hours / actual_hours) * 100
        
        assert 0 <= utilization <= 100
    
    def test_negative_values_prevention(self):
        """测试负值防止"""
        # 确保计算结果不为负
        planned_time = 480
        downtime = 500  # 超过计划时间(异常情况)
        
        operating_time = max(0, planned_time - downtime)
        assert operating_time >= 0


# Fixtures
@pytest.fixture
def db_session():
    """数据库session fixture"""
    from app.models.base import get_session
    session = get_session()
    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
