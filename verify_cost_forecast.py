#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
成本预测功能验证脚本

快速验证所有组件是否正确导入和工作
"""

import sys
from datetime import date, timedelta
from decimal import Decimal

# 验证模型导入
print("1. 验证数据模型导入...")
try:
    from app.models.project import CostAlert, CostAlertRule, CostForecast

    print("   ✓ CostForecast 导入成功")
    print("   ✓ CostAlert 导入成功")
    print("   ✓ CostAlertRule 导入成功")
except ImportError as e:
    print(f"   ✗ 模型导入失败: {e}")
    sys.exit(1)

# 验证服务层导入
print("\n2. 验证服务层导入...")
try:
    from app.services.cost_forecast_service import CostForecastService

    print("   ✓ CostForecastService 导入成功")
except ImportError as e:
    print(f"   ✗ 服务层导入失败: {e}")
    sys.exit(1)

# 验证依赖包
print("\n3. 验证依赖包...")
try:
    import pandas as pd

    print(f"   ✓ pandas {pd.__version__} 已安装")
except ImportError:
    print("   ✗ pandas 未安装")

try:
    import sklearn

    print(f"   ✓ scikit-learn {sklearn.__version__} 已安装")
except ImportError:
    print("   ⚠ scikit-learn 未安装（需要执行: pip install scikit-learn==1.3.2）")

# 验证API路由
print("\n4. 验证API路由...")
try:
    from app.api.v1.endpoints.projects.costs.forecast import router

    routes = [route.path for route in router.routes]
    print(f"   ✓ 发现 {len(routes)} 个API端点:")
    for route_path in routes:
        print(f"      - {route_path}")
except ImportError as e:
    print(f"   ✗ API路由导入失败: {e}")
    sys.exit(1)

# 数据库验证
print("\n5. 验证数据库表...")
try:
    from sqlalchemy import create_engine, inspect

    # 连接到SQLite数据库
    engine = create_engine("sqlite:///data/app.db")
    inspector = inspect(engine)

    required_tables = ["cost_forecasts", "cost_alerts", "cost_alert_rules"]
    for table_name in required_tables:
        if inspector.has_table(table_name):
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            print(f"   ✓ {table_name} 表存在 ({len(columns)} 列)")
        else:
            print(f"   ✗ {table_name} 表不存在")

    # 检查预警规则
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()

    rule_count = session.query(CostAlertRule).count()
    print(f"   ✓ 找到 {rule_count} 个预警规则")

    session.close()
except Exception as e:
    print(f"   ✗ 数据库验证失败: {e}")

# 功能测试（简单验证）
print("\n6. 功能测试...")
try:
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///data/app.db")
    Session = sessionmaker(bind=engine)
    db = Session()

    service = CostForecastService(db)
    print("   ✓ CostForecastService 实例化成功")

    # 测试内部方法
    from app.models.project import Project

    # 查找一个测试项目
    project = db.query(Project).first()
    if project:
        print(f"   ✓ 找到测试项目: {project.project_code}")

        # 测试预警规则加载
        rules = service._get_alert_rules(project.id)
        print(f"   ✓ 预警规则加载成功 ({len(rules)} 个规则)")
    else:
        print("   ⚠ 数据库中没有项目数据（无法进行完整测试）")

    db.close()
except Exception as e:
    print(f"   ✗ 功能测试失败: {e}")
    import traceback

    traceback.print_exc()

# 总结
print("\n" + "=" * 50)
print("验证完成！")
print("=" * 50)
print("\n下一步:")
print("1. 安装缺失的依赖: pip install scikit-learn==1.3.2")
print("2. 运行测试: pytest tests/test_cost_forecast.py -v")
print("3. 查看文档: docs/cost_forecast_guide.md")
print("4. 启动服务: ./start.sh")
