#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跟踪测试覆盖率提升进度
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict


def get_current_coverage() -> Dict:
    """获取当前覆盖率数据"""
    # 运行覆盖率测试
    result = subprocess.run(
        ["python3", "-m", "pytest", "--cov=app", "--cov-report=json", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("⚠️  测试运行有错误，但继续分析覆盖率...")
    
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        return {}
    
    with open(coverage_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_services_coverage(coverage_data: Dict) -> Dict:
    """分析服务层覆盖率"""
    files = coverage_data.get('files', {})
    
    services_stats = {
        'total_files': 0,
        'covered_files': 0,
        'zero_coverage_files': 0,
        'total_statements': 0,
        'covered_statements': 0,
        'zero_coverage_services': []
    }
    
    for filepath, info in files.items():
        if not filepath.startswith('app/services/'):
            continue
        
        if '__init__' in filepath or '__pycache__' in filepath:
            continue
        
        summary = info.get('summary', {})
        percent = summary.get('percent_covered', 0)
        statements = summary.get('num_statements', 0)
        covered = summary.get('covered_lines', 0)
        
        services_stats['total_files'] += 1
        services_stats['total_statements'] += statements
        services_stats['covered_statements'] += covered
        
        if percent > 0:
            services_stats['covered_files'] += 1
        else:
            services_stats['zero_coverage_files'] += 1
            if statements > 0:
                service_name = filepath.replace('app/services/', '').replace('.py', '')
                services_stats['zero_coverage_services'].append({
                    'filepath': filepath,
                    'service_name': service_name,
                    'statements': statements
                })
    
    # 计算总体覆盖率
    if services_stats['total_statements'] > 0:
        services_stats['overall_coverage'] = (
            services_stats['covered_statements'] / services_stats['total_statements'] * 100
        )
    else:
        services_stats['overall_coverage'] = 0
    
    return services_stats


def generate_progress_report(previous_stats: Dict = None) -> str:
    """生成进度报告"""
    coverage_data = get_current_coverage()
    if not coverage_data:
        return "❌ 无法获取覆盖率数据"
    
    # 总体覆盖率
    totals = coverage_data.get('totals', {})
    overall_percent = totals.get('percent_covered', 0)
    overall_statements = totals.get('num_statements', 0)
    overall_covered = totals.get('covered_lines', 0)
    
    # 服务层覆盖率
    services_stats = analyze_services_coverage(coverage_data)
    
    # 生成报告
    report = f"""# 测试覆盖率提升进度报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 总体覆盖率

- **总体覆盖率**: {overall_percent:.2f}%
- **总代码语句数**: {overall_statements:,}
- **已覆盖语句数**: {overall_covered:,}
- **未覆盖语句数**: {overall_statements - overall_covered:,}

---

## 🔧 服务层覆盖率

- **服务文件总数**: {services_stats['total_files']}
- **已覆盖文件数**: {services_stats['covered_files']}
- **零覆盖率文件数**: {services_stats['zero_coverage_files']}
- **服务层覆盖率**: {services_stats['overall_coverage']:.2f}%
- **服务层总语句数**: {services_stats['total_statements']:,}
- **服务层已覆盖语句数**: {services_stats['covered_statements']:,}

---

## 📈 进度对比

"""
    
    if previous_stats:
        prev_overall = previous_stats.get('overall_percent', 0)
        prev_services = previous_stats.get('services_coverage', 0)
        
        overall_diff = overall_percent - prev_overall
        services_diff = services_stats['overall_coverage'] - prev_services
        
        report += f"""
- **总体覆盖率变化**: {prev_overall:.2f}% → {overall_percent:.2f}% ({overall_diff:+.2f}%)
- **服务层覆盖率变化**: {prev_services:.2f}% → {services_stats['overall_coverage']:.2f}% ({services_diff:+.2f}%)
"""
    else:
        report += "\n(首次运行，无对比数据)\n"
    
    report += f"""
---

## 🎯 零覆盖率服务文件

当前还有 **{services_stats['zero_coverage_files']}** 个服务文件覆盖率为 0%

### 前20个最大零覆盖率服务:

"""
    
    # 按代码量排序
    zero_coverage = sorted(
        services_stats['zero_coverage_services'],
        key=lambda x: x['statements'],
        reverse=True
    )[:20]
    
    for i, service in enumerate(zero_coverage, 1):
        report += f"{i:2d}. `{service['service_name']}` - {service['statements']} 行\n"
    
    report += f"""
---

## 📝 下一步行动

1. **继续生成测试文件**: 
   ```bash
   python3 scripts/generate_service_tests_batch.py --batch-size 20 --start {len(zero_coverage)}
   ```

2. **实现测试用例**: 为已生成的测试文件实现具体测试逻辑

3. **运行测试验证**: 
   ```bash
   pytest tests/unit/ -v --cov=app/services --cov-report=term-missing
   ```

4. **检查覆盖率提升**: 定期运行此脚本跟踪进度

---

## 💡 建议

- 优先处理代码量大的服务文件（前30个）
- 每个服务至少达到 60% 覆盖率
- 重点关注核心业务逻辑的测试覆盖
"""
    
    return report


def save_progress_history(current_stats: Dict):
    """保存进度历史"""
    history_file = Path("reports/coverage_progress_history.json")
    
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history.append({
        'timestamp': datetime.now().isoformat(),
        'stats': current_stats
    })
    
    # 只保留最近30条记录
    history = history[-30:]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    print("🔍 分析测试覆盖率...")
    
    # 获取历史数据
    history_file = Path("reports/coverage_progress_history.json")
    previous_stats = None
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
            if history:
                previous_stats = history[-1].get('stats', {})
    
    # 生成报告
    report = generate_progress_report(previous_stats)
    
    # 保存报告
    report_file = Path("reports/coverage_progress_report.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 进度报告已保存到: {report_file}")
    
    # 获取当前统计数据
    coverage_data = get_current_coverage()
    if coverage_data:
        totals = coverage_data.get('totals', {})
        services_stats = analyze_services_coverage(coverage_data)
        
        current_stats = {
            'overall_percent': totals.get('percent_covered', 0),
            'overall_statements': totals.get('num_statements', 0),
            'services_coverage': services_stats['overall_coverage'],
            'zero_coverage_count': services_stats['zero_coverage_files']
        }
        
        save_progress_history(current_stats)
        print(f"💾 进度历史已更新")
    
    # 输出摘要
    print("\n" + "="*60)
    if "## 📊 总体覆盖率" in report and "## 📈 进度对比" in report:
        print(report.split("## 📊 总体覆盖率")[1].split("## 📈 进度对比")[0])
    else:
        print(report)
    print("="*60)


if __name__ == "__main__":
    main()
