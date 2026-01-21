#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析零覆盖率服务文件并生成测试推进计划
"""

import json
import os
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict


def load_coverage_data() -> Dict:
    """加载覆盖率数据"""
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("❌ coverage.json 不存在，请先运行: pytest --cov=app --cov-report=json")
        return {}
    
    with open(coverage_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_zero_coverage_services() -> List[Tuple[str, int, float]]:
    """分析所有零覆盖率的服务文件"""
    data = load_coverage_data()
    if not data:
        return []
    
    files = data.get('files', {})
    zero_coverage_services = []
    
    for filepath, info in files.items():
        if not filepath.startswith('app/services/'):
            continue
        
        # 跳过 __init__.py 和 __pycache__
        if '__init__' in filepath or '__pycache__' in filepath:
            continue
        
        summary = info.get('summary', {})
        percent = summary.get('percent_covered', 0)
        statements = summary.get('num_statements', 0)
        
        # 只关注零覆盖率且有一定代码量的文件
        if percent == 0 and statements > 0:
            # 提取服务文件名
            service_name = filepath.replace('app/services/', '').replace('.py', '')
            zero_coverage_services.append((filepath, statements, percent))
    
    # 按代码行数降序排序（优先处理大文件）
    zero_coverage_services.sort(key=lambda x: x[1], reverse=True)
    
    return zero_coverage_services


def categorize_services(services: List[Tuple[str, int, float]]) -> Dict[str, List[Tuple[str, int, float]]]:
    """按业务模块分类服务"""
    categories = defaultdict(list)
    
    for filepath, statements, percent in services:
        # 提取模块名
        parts = filepath.replace('app/services/', '').split('/')
        if len(parts) > 1:
            category = parts[0]  # 子目录名
        else:
            # 从文件名推断类别
            filename = parts[0].replace('.py', '')
            if 'sales' in filename:
                category = 'sales'
            elif 'cost' in filename or 'budget' in filename or 'revenue' in filename:
                category = 'financial'
            elif 'timesheet' in filename or 'work_log' in filename:
                category = 'timesheet'
            elif 'report' in filename:
                category = 'reporting'
            elif 'import' in filename or 'sync' in filename:
                category = 'data_import'
            elif 'alert' in filename or 'notification' in filename:
                category = 'alerting'
            elif 'approval' in filename or 'workflow' in filename:
                category = 'workflow'
            elif 'shortage' in filename:
                category = 'shortage'
            elif 'staff' in filename or 'matching' in filename:
                category = 'staffing'
            else:
                category = 'other'
        
        categories[category].append((filepath, statements, percent))
    
    return categories


def generate_test_plan(services: List[Tuple[str, int, float]]) -> str:
    """生成测试推进计划"""
    categories = categorize_services(services)
    
    plan = f"""# 103个服务文件测试覆盖率推进计划

## 📊 总体统计

- **零覆盖率服务文件总数**: {len(services)}
- **总代码语句数**: {sum(s[1] for s in services):,}
- **目标覆盖率**: 60%+ (每个服务)

---

## 📋 按模块分类

"""
    
    # 按模块统计
    for category, items in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        total_statements = sum(s[1] for s in items)
        plan += f"### {category.upper()} ({len(items)} 个文件, {total_statements:,} 行)\n\n"
        
        # 显示前10个最大的文件
        for i, (filepath, statements, percent) in enumerate(items[:10], 1):
            service_name = filepath.replace('app/services/', '').replace('.py', '')
            plan += f"{i}. `{service_name}` - {statements} 行\n"
        
        if len(items) > 10:
            plan += f"   ... 还有 {len(items) - 10} 个文件\n"
        
        plan += "\n"
    
    plan += """
---

## 🎯 推进策略

### 阶段1: 高优先级服务（前30个，按代码量排序）
- 优先处理代码量最大的服务
- 每个服务至少达到 60% 覆盖率
- 预计提升覆盖率: +5-8%

### 阶段2: 中等优先级服务（31-70个）
- 批量生成测试桩
- 逐步完善测试用例
- 预计提升覆盖率: +8-12%

### 阶段3: 低优先级服务（71-103个）
- 快速覆盖主要功能
- 确保关键路径测试
- 预计提升覆盖率: +5-7%

---

## 📝 执行步骤

1. **批量生成测试桩**: 使用 `scripts/generate_service_tests_batch.py`
2. **实现核心测试**: 为每个服务编写主要功能的测试
3. **运行测试验证**: 确保测试通过并提升覆盖率
4. **持续迭代**: 逐步完善边界情况和异常处理测试

---

## 📈 预期成果

- **总体覆盖率**: 从 40% 提升到 60%+
- **服务层覆盖率**: 从 9.3% 提升到 60%+
- **新增测试文件**: 103 个
- **新增测试用例**: 500+ 个

"""
    
    return plan


def main():
    """主函数"""
    print("🔍 分析零覆盖率服务文件...")
    
    services = analyze_zero_coverage_services()
    
    if not services:
        print("❌ 未找到零覆盖率服务文件，或覆盖率数据不存在")
        print("   请先运行: pytest --cov=app --cov-report=json")
        return
    
    print(f"\n✅ 找到 {len(services)} 个零覆盖率服务文件")
    print(f"   总代码语句数: {sum(s[1] for s in services):,}")
    
    # 生成测试计划
    plan = generate_test_plan(services)
    
    # 保存计划
    plan_file = Path("reports/服务文件测试推进计划.md")
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    with open(plan_file, 'w', encoding='utf-8') as f:
        f.write(plan)
    
    print(f"\n📝 测试计划已保存到: {plan_file}")
    
    # 输出前20个最大的文件
    print("\n📋 前20个最大零覆盖率服务文件:")
    for i, (filepath, statements, percent) in enumerate(services[:20], 1):
        service_name = filepath.replace('app/services/', '').replace('.py', '')
        print(f"  {i:2d}. {service_name:50s} - {statements:4d} 行")
    
    # 保存服务列表到JSON（供其他脚本使用）
    services_data = {
        'total': len(services),
        'total_statements': sum(s[1] for s in services),
        'services': [
            {
                'filepath': filepath,
                'service_name': filepath.replace('app/services/', '').replace('.py', ''),
                'statements': statements,
                'coverage': percent
            }
            for filepath, statements, percent in services
        ]
    }
    
    json_file = Path("reports/zero_coverage_services.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(services_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 服务列表已保存到: {json_file}")


if __name__ == "__main__":
    main()
