#!/bin/bash
# -*- coding: utf-8 -*-
"""
Services 层覆盖率提升脚本
快速开始提升 Services 层测试覆盖率
"""

set -e

echo "🚀 Services 层覆盖率提升工具"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查覆盖率数据
if [ ! -f "reports/zero_coverage_services.json" ]; then
    echo "📊 正在分析零覆盖率服务..."
    python3 scripts/analyze_zero_coverage_services.py
fi

# 显示当前状态
echo "📈 当前状态:"
python3 -c "
import json
with open('reports/zero_coverage_services.json', 'r') as f:
    data = json.load(f)
    print(f\"   零覆盖率服务: {data['total']} 个\")
    print(f\"   总未覆盖代码: {data['total_statements']} 行\")
    print(f\"   前5个最大服务:\")
    for i, svc in enumerate(data['services'][:5], 1):
        print(f\"     {i}. {svc['service_name']:40s} - {svc['statements']:4d} 行\")
"

echo ""
echo "请选择操作:"
echo "  1) 查看零覆盖率服务列表"
echo "  2) 为单个服务生成测试框架"
echo "  3) 批量生成测试框架（前N个服务）"
echo "  4) 检查已有测试的覆盖率"
echo "  5) 运行所有服务测试"
echo "  6) 生成覆盖率报告"
echo "  7) 查看提升方案文档"
echo "  0) 退出"
echo ""

read -p "请输入选项 [0-7]: " choice

case $choice in
    1)
        echo ""
        echo "📋 零覆盖率服务列表（前20个）:"
        python3 -c "
import json
with open('reports/zero_coverage_services.json', 'r') as f:
    data = json.load(f)
    for i, svc in enumerate(data['services'][:20], 1):
        test_file = f\"tests/unit/test_{svc['service_name']}.py\"
        import os
        exists = '✅' if os.path.exists(test_file) else '❌'
        print(f\"  {i:2d}. {exists} {svc['service_name']:40s} - {svc['statements']:4d} 行\")
"
        ;;
    2)
        read -p "请输入服务名称（如: notification_dispatcher）: " service_name
        echo ""
        echo "🔧 为 $service_name 生成测试框架..."
        
        # 检查服务是否存在
        service_file="app/services/${service_name}.py"
        if [ ! -f "$service_file" ]; then
            echo "${RED}❌ 服务文件不存在: $service_file${NC}"
            exit 1
        fi
        
        # 生成测试实现指南
        echo "📝 生成测试实现指南..."
        python3 scripts/implement_service_tests.py "$service_name" \
            --output "reports/guides/${service_name}_guide.md" 2>/dev/null || echo "⚠️  无法生成指南，继续..."
        
        # 检查测试文件是否存在
        test_file="tests/unit/test_${service_name}.py"
        if [ -f "$test_file" ]; then
            echo "${YELLOW}⚠️  测试文件已存在: $test_file${NC}"
            read -p "是否覆盖? [y/N]: " overwrite
            if [ "$overwrite" != "y" ]; then
                echo "已取消"
                exit 0
            fi
        fi
        
        # 使用模板创建测试文件
        if [ ! -f "$test_file" ]; then
            echo "📄 创建测试文件..."
            python3 scripts/generate_service_tests_batch.py \
                --service "$service_name" \
                --output "$test_file" 2>/dev/null || {
                echo "⚠️  使用模板创建..."
                cp tests/templates/test_service_template.py "$test_file"
                # 替换服务名
                sed -i '' "s/YourService/${service_name^}/g" "$test_file" 2>/dev/null || \
                sed -i "s/YourService/${service_name^}/g" "$test_file"
            }
            echo "${GREEN}✅ 测试文件已创建: $test_file${NC}"
        fi
        
        echo ""
        echo "📝 下一步:"
        echo "  1. 编辑测试文件: vim $test_file"
        echo "  2. 实现测试用例（参考: reports/guides/${service_name}_guide.md）"
        echo "  3. 运行测试: pytest $test_file -v"
        echo "  4. 检查覆盖率: pytest $test_file --cov=app/services/$service_name --cov-report=term-missing"
        ;;
    3)
        read -p "请输入要生成的数量 [默认: 10]: " count
        count=${count:-10}
        read -p "请输入起始位置 [默认: 0]: " start
        start=${start:-0}
        
        echo ""
        echo "🔧 批量生成测试框架（从第 $start 个开始，生成 $count 个）..."
        python3 scripts/generate_service_tests_batch.py \
            --batch-size "$count" \
            --start "$start" \
            --output-dir tests/unit
        
        echo ""
        echo "${GREEN}✅ 已生成 $count 个测试文件框架${NC}"
        echo "📝 下一步: 逐个实现测试用例"
        ;;
    4)
        echo ""
        echo "📊 检查已有测试的覆盖率..."
        echo ""
        
        # 检查几个主要服务的覆盖率
        services=(
            "notification_dispatcher"
            "timesheet_report_service"
            "status_transition_service"
            "sales_team_service"
            "win_rate_prediction_service"
        )
        
        for service in "${services[@]}"; do
            test_file="tests/unit/test_${service}.py"
            service_file="app/services/${service}.py"
            
            if [ -f "$test_file" ] && [ -f "$service_file" ]; then
                echo "检查 $service..."
                pytest "$test_file" \
                    --cov="app/services/${service}" \
                    --cov-report=term-missing \
                    -q 2>&1 | grep -E "(TOTAL|app/services)" || echo "  测试运行失败或覆盖率数据不可用"
            else
                echo "${YELLOW}⚠️  $service: 测试文件或服务文件不存在${NC}"
            fi
        done
        ;;
    5)
        echo ""
        echo "🧪 运行所有服务测试..."
        pytest tests/unit/ -k "service" -v --tb=short
        ;;
    6)
        echo ""
        echo "📊 生成覆盖率报告..."
        pytest --cov=app/services \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-report=json \
            -q
        
        echo ""
        echo "${GREEN}✅ 覆盖率报告已生成:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - JSON: coverage.json"
        echo "  - 终端: 见上方输出"
        ;;
    7)
        echo ""
        echo "📚 打开提升方案文档..."
        if [ -f "docs/Services层覆盖率提升方案.md" ]; then
            if command -v code &> /dev/null; then
                code "docs/Services层覆盖率提升方案.md"
            elif command -v open &> /dev/null; then
                open "docs/Services层覆盖率提升方案.md"
            else
                cat "docs/Services层覆盖率提升方案.md" | head -100
                echo ""
                echo "... (使用编辑器打开完整文档)"
            fi
        else
            echo "${RED}❌ 文档不存在${NC}"
        fi
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "${GREEN}✅ 完成${NC}"
