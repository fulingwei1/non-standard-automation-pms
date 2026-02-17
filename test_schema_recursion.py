#!/usr/bin/env python3
"""
测试schema递归错误
"""
import sys
import traceback

def test_import():
    """测试导入"""
    try:
        print("尝试导入 timesheet_analytics schemas...")
        from app.schemas.timesheet_analytics import (
            TimesheetAnalyticsQuery,
            ProjectForecastRequest,
            TrendChartData,
            TimesheetTrendResponse
        )
        print("✓ 导入成功!")
        return True
    except RecursionError as e:
        print(f"✗ RecursionError: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ 其他错误: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def test_model_creation():
    """测试模型实例化"""
    try:
        from app.schemas.timesheet_analytics import TimesheetAnalyticsQuery
        from datetime import date
        
        print("\n尝试创建 TimesheetAnalyticsQuery 实例...")
        query = TimesheetAnalyticsQuery(
            period_type='DAILY',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        print(f"✓ 实例创建成功: {query}")
        return True
    except Exception as e:
        print(f"✗ 实例化失败: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def test_model_validation():
    """测试模型验证"""
    try:
        from app.schemas.timesheet_analytics import TimesheetAnalyticsQuery
        from datetime import date
        
        print("\n尝试验证模型...")
        # 应该报错
        query = TimesheetAnalyticsQuery(
            period_type='INVALID',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        print(f"✗ 验证失败 - 应该抛出异常")
        return False
    except ValueError as e:
        print(f"✓ 验证成功 - 正确抛出 ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ 验证失败: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("Pydantic Schema 递归错误测试")
    print("="*60)
    
    results = []
    
    # 测试1: 导入
    results.append(("导入测试", test_import()))
    
    # 如果导入成功，继续其他测试
    if results[0][1]:
        results.append(("实例化测试", test_model_creation()))
        results.append(("验证测试", test_model_validation()))
    
    print("\n" + "="*60)
    print("测试结果汇总:")
    print("="*60)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    # 退出码
    all_passed = all(r[1] for r in results)
    sys.exit(0 if all_passed else 1)
