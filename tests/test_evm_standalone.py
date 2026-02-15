#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVM计算器独立测试脚本（不依赖完整应用环境）

直接运行: python3 tests/test_evm_standalone.py
"""

import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.evm_service import EVMCalculator


def test_schedule_variance():
    """测试进度偏差计算"""
    calculator = EVMCalculator()
    
    # 场景1：进度超前
    sv1 = calculator.calculate_schedule_variance(Decimal('120000'), Decimal('100000'))
    assert sv1 == Decimal('20000.0000'), f"Expected 20000.0000, got {sv1}"
    print("✓ 进度偏差 - 进度超前")
    
    # 场景2：进度落后
    sv2 = calculator.calculate_schedule_variance(Decimal('80000'), Decimal('100000'))
    assert sv2 == Decimal('-20000.0000'), f"Expected -20000.0000, got {sv2}"
    print("✓ 进度偏差 - 进度落后")
    
    # 场景3：进度正常
    sv3 = calculator.calculate_schedule_variance(Decimal('100000'), Decimal('100000'))
    assert sv3 == Decimal('0.0000'), f"Expected 0.0000, got {sv3}"
    print("✓ 进度偏差 - 进度正常")


def test_cost_variance():
    """测试成本偏差计算"""
    calculator = EVMCalculator()
    
    # 场景1：成本节约
    cv1 = calculator.calculate_cost_variance(Decimal('100000'), Decimal('80000'))
    assert cv1 == Decimal('20000.0000'), f"Expected 20000.0000, got {cv1}"
    print("✓ 成本偏差 - 成本节约")
    
    # 场景2：成本超支
    cv2 = calculator.calculate_cost_variance(Decimal('100000'), Decimal('120000'))
    assert cv2 == Decimal('-20000.0000'), f"Expected -20000.0000, got {cv2}"
    print("✓ 成本偏差 - 成本超支")


def test_performance_indexes():
    """测试绩效指数计算"""
    calculator = EVMCalculator()
    
    # SPI测试
    spi1 = calculator.calculate_schedule_performance_index(Decimal('120000'), Decimal('100000'))
    assert spi1 == Decimal('1.200000'), f"Expected 1.200000, got {spi1}"
    print("✓ SPI - 进度超前")
    
    spi2 = calculator.calculate_schedule_performance_index(Decimal('80000'), Decimal('100000'))
    assert spi2 == Decimal('0.800000'), f"Expected 0.800000, got {spi2}"
    print("✓ SPI - 进度落后")
    
    # CPI测试
    cpi1 = calculator.calculate_cost_performance_index(Decimal('100000'), Decimal('80000'))
    assert cpi1 == Decimal('1.250000'), f"Expected 1.250000, got {cpi1}"
    print("✓ CPI - 成本效率高")
    
    cpi2 = calculator.calculate_cost_performance_index(Decimal('100000'), Decimal('120000'))
    assert cpi2 == Decimal('0.833333'), f"Expected 0.833333, got {cpi2}"
    print("✓ CPI - 成本效率低")


def test_forecast_metrics():
    """测试预测指标计算"""
    calculator = EVMCalculator()
    
    bac = Decimal('1000000')
    ev = Decimal('400000')
    ac = Decimal('500000')
    
    # EAC测试
    eac = calculator.calculate_estimate_at_completion(bac, ev, ac)
    assert eac == Decimal('1250000.0000'), f"Expected 1250000.0000, got {eac}"
    print("✓ EAC - 完工估算")
    
    # ETC测试
    etc = calculator.calculate_estimate_to_complete(eac, ac)
    assert etc == Decimal('750000.0000'), f"Expected 750000.0000, got {etc}"
    print("✓ ETC - 完工尚需估算")
    
    # VAC测试
    vac = calculator.calculate_variance_at_completion(bac, eac)
    assert vac == Decimal('-250000.0000'), f"Expected -250000.0000, got {vac}"
    print("✓ VAC - 完工偏差")
    
    # TCPI测试
    tcpi = calculator.calculate_to_complete_performance_index(bac, ev, ac)
    assert tcpi == Decimal('1.200000'), f"Expected 1.200000, got {tcpi}"
    print("✓ TCPI - 完工尚需绩效指数")


def test_calculate_all_metrics():
    """测试一次性计算所有指标"""
    calculator = EVMCalculator()
    
    pv = Decimal('500000')
    ev = Decimal('450000')
    ac = Decimal('480000')
    bac = Decimal('2000000')
    
    metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
    
    # 验证所有指标都被计算
    assert 'sv' in metrics
    assert 'cv' in metrics
    assert 'spi' in metrics
    assert 'cpi' in metrics
    assert 'eac' in metrics
    assert 'etc' in metrics
    assert 'vac' in metrics
    assert 'tcpi' in metrics
    assert 'planned_percent_complete' in metrics
    assert 'actual_percent_complete' in metrics
    
    # 验证关键值
    assert metrics['sv'] == Decimal('-50000.0000')
    assert metrics['cv'] == Decimal('-30000.0000')
    assert metrics['spi'] == Decimal('0.900000')
    assert metrics['cpi'] == Decimal('0.937500')
    
    print("✓ 综合计算 - 所有指标计算正确")


def test_edge_cases():
    """测试边界情况"""
    calculator = EVMCalculator()
    
    # PV为0时SPI应该返回None
    spi_none = calculator.calculate_schedule_performance_index(Decimal('100'), Decimal('0'))
    assert spi_none is None
    print("✓ 边界测试 - PV=0时SPI返回None")
    
    # AC为0时CPI应该返回None
    cpi_none = calculator.calculate_cost_performance_index(Decimal('100'), Decimal('0'))
    assert cpi_none is None
    print("✓ 边界测试 - AC=0时CPI返回None")
    
    # BAC为0时百分比应该返回None
    percent_none = calculator.calculate_percent_complete(Decimal('100'), Decimal('0'))
    assert percent_none is None
    print("✓ 边界测试 - BAC=0时百分比返回None")


def test_decimal_precision():
    """测试Decimal精度"""
    calculator = EVMCalculator()
    
    # 测试精度保持
    ev = Decimal('333.33')
    pv = Decimal('1000.00')
    spi = calculator.calculate_schedule_performance_index(ev, pv)
    
    assert spi == Decimal('0.333330')
    assert isinstance(spi, Decimal)
    print("✓ 精度测试 - Decimal计算精确")
    
    # 测试四舍五入
    value = Decimal('123.45555')
    rounded = calculator.round_decimal(value, 4)
    assert rounded == Decimal('123.4556')
    print("✓ 精度测试 - 四舍五入正确")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("EVM计算器单元测试")
    print("=" * 60)
    
    try:
        test_schedule_variance()
        test_cost_variance()
        test_performance_indexes()
        test_forecast_metrics()
        test_calculate_all_metrics()
        test_edge_cases()
        test_decimal_precision()
        
        print("=" * 60)
        print("✅ 所有测试通过！(26个测试用例)")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("=" * 60)
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
