#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化验证脚本 - 不依赖应用配置
"""

import sys

print("=" * 60)
print("成本预测功能验证")
print("=" * 60)

# 1. 检查文件存在
print("\n1. 检查文件存在性...")
import os

files_to_check = [
    "app/models/project/cost_forecast.py",
    "app/services/cost_forecast_service.py",
    "app/api/v1/endpoints/projects/costs/forecast.py",
    "migrations/20250214_cost_forecast_module_sqlite.sql",
    "migrations/20250214_cost_forecast_module_mysql.sql",
    "tests/test_cost_forecast.py",
    "docs/cost_forecast_guide.md",
]

all_exist = True
for file_path in files_to_check:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"   ✓ {file_path} ({size} bytes)")
    else:
        print(f"   ✗ {file_path} 不存在")
        all_exist = False

# 2. 检查数据库表
print("\n2. 检查数据库表...")
try:
    import sqlite3

    conn = sqlite3.connect("data/app.db")
    cursor = conn.cursor()

    # 检查表是否存在
    tables = ["cost_forecasts", "cost_alerts", "cost_alert_rules"]
    for table in tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        if cursor.fetchone():
            # 统计记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table} 表存在 ({count} 条记录)")
        else:
            print(f"   ✗ {table} 表不存在")

    conn.close()
except Exception as e:
    print(f"   ✗ 数据库检查失败: {e}")

# 3. 检查依赖包
print("\n3. 检查Python依赖包...")
packages = {"pandas": "2.2.3", "scikit-learn": "1.3.2"}

for package, expected_version in packages.items():
    try:
        if package == "scikit-learn":
            import sklearn

            installed_version = sklearn.__version__
            package_obj = sklearn
        else:
            exec(f"import {package}")
            package_obj = eval(package)
            installed_version = package_obj.__version__

        print(f"   ✓ {package} {installed_version} 已安装")
        if installed_version != expected_version:
            print(f"      ⚠ 建议版本: {expected_version}")
    except ImportError:
        print(f"   ✗ {package} 未安装")
        print(f"      执行: pip install {package}=={expected_version}")

# 4. 代码统计
print("\n4. 代码统计...")
code_files = {
    "模型层": "app/models/project/cost_forecast.py",
    "服务层": "app/services/cost_forecast_service.py",
    "API层": "app/api/v1/endpoints/projects/costs/forecast.py",
    "测试": "tests/test_cost_forecast.py",
    "文档": "docs/cost_forecast_guide.md",
}

total_lines = 0
for name, file_path in code_files.items():
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = len(f.readlines())
            total_lines += lines
            print(f"   {name}: {lines} 行")

print(f"\n   总代码量: {total_lines} 行")

# 5. 测试用例统计
print("\n5. 测试用例统计...")
try:
    with open("tests/test_cost_forecast.py", "r", encoding="utf-8") as f:
        content = f.read()
        test_count = content.count("def test_")
        print(f"   ✓ 发现 {test_count} 个测试用例")

        # 统计测试分类
        categories = {
            "数据模型": 0,
            "预测算法": 0,
            "趋势分析": 0,
            "预警检测": 0,
            "API端点": 0,
        }

        for line in content.split("\n"):
            if line.strip().startswith("def test_"):
                if "_model_" in line or "_creation" in line:
                    categories["数据模型"] += 1
                elif "_forecast" in line and "api" not in line:
                    categories["预测算法"] += 1
                elif "_trend" in line or "_burn_down" in line:
                    categories["趋势分析"] += 1
                elif "_alert" in line and "api" not in line.lower():
                    categories["预警检测"] += 1
                elif "_api_" in line:
                    categories["API端点"] += 1

        for category, count in categories.items():
            print(f"      - {category}: {count} 个")
except Exception as e:
    print(f"   ✗ 测试统计失败: {e}")

# 总结
print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)

if all_exist:
    print("\n✅ 所有文件都已创建")
else:
    print("\n⚠ 部分文件缺失")

print("\n下一步操作:")
print("1. 安装scikit-learn: pip install scikit-learn==1.3.2")
print("2. 运行数据库迁移（如果未执行）:")
print("   sqlite3 data/app.db < migrations/20250214_cost_forecast_module_sqlite.sql")
print("3. 运行测试: pytest tests/test_cost_forecast.py -v")
print("4. 查看文档: cat docs/cost_forecast_guide.md")
print("5. 启动服务: ./start.sh")
