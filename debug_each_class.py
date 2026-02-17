#!/usr/bin/env python3
"""逐个测试每个类的导入"""
import sys
import traceback

classes_to_test = [
    "AnalyticsPeriod",
    "AnalyticsDimension",  
    "ForecastMethod",
    "TimesheetAnalyticsQuery",
    "ProjectForecastRequest",
    "CompletionForecastQuery",
    "WorkloadAlertQuery",
    "ChartDataPoint",
    "TrendChartData",
    "PieChartData",
    "HeatmapData",
]

print("="*60)
print("逐个测试类导入")
print("="*60)

for class_name in classes_to_test:
    try:
        print(f"\n测试导入 {class_name}...", end=" ")
        exec(f"from app.schemas.timesheet_analytics import {class_name}")
        print(f"✓ 成功")
    except RecursionError as e:
        print(f"✗ RecursionError!")
        print(f"   问题类: {class_name}")
        break
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        break
