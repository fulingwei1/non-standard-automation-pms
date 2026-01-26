#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成覆盖率总结报告
从覆盖率JSON文件中提取关键信息
"""

import json
from pathlib import Path
from typing import Dict, List


def load_coverage_json(filepath: str) -> Dict:
    """加载覆盖率JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def extract_service_coverage(coverage_data: Dict, service_path: str) -> Dict:
    """提取服务的覆盖率信息"""
    files = coverage_data.get('files', {})
    
    for filepath, info in files.items():
        if service_path in filepath:
            summary = info.get('summary', {})
            return {
                'filepath': filepath,
                'total_statements': summary.get('num_statements', 0),
                'covered_statements': summary.get('covered_lines', 0),
                'missing_statements': summary.get('missing_lines', 0),
                'excluded_statements': summary.get('excluded_lines', 0),
                'coverage_percent': summary.get('percent_covered', 0.0)
            }
    
    return {}


def main():
    """主函数"""
    print("📊 生成覆盖率总结报告...")
    print("=" * 70)
    print()
    
    services = [
        {
            'name': 'data_sync_service',
            'path': 'app/services/data_sync_service',
            'json_file': 'coverage_data_sync.json'
        },
        {
            'name': 'project_import_service',
            'path': 'app/services/project_import_service',
            'json_file': 'coverage_project_import.json'
        },
        {
            'name': 'status_transition_service',
            'path': 'app/services/status_transition_service',
            'json_file': 'coverage_status_transition.json'
        }
    ]
    
    results = []
    
    for service in services:
        json_file = Path(service['json_file'])
        if not json_file.exists():
            print(f"⚠️  {service['name']}: 覆盖率文件不存在")
            continue
        
        coverage_data = load_coverage_json(str(json_file))
        coverage_info = extract_service_coverage(coverage_data, service['path'])
        
        if coverage_info:
            results.append({
                'name': service['name'],
                **coverage_info
            })
            print(f"✅ {service['name']}:")
            print(f"   覆盖率: {coverage_info['coverage_percent']:.1f}%")
            print(f"   总语句: {coverage_info['total_statements']}")
            print(f"   已覆盖: {coverage_info['covered_statements']}")
            print(f"   未覆盖: {coverage_info['missing_statements']}")
            print()
        else:
            print(f"⚠️  {service['name']}: 未找到覆盖率数据")
            print()
    
    # 生成报告
    if results:
        report_file = Path("reports/实际覆盖率检查报告.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 实际覆盖率检查报告\n\n")
            f.write("**检查时间**: 2026-01-22\n\n")
            f.write("## 📊 覆盖率统计\n\n")
            f.write("| 服务名称 | 总语句数 | 已覆盖 | 未覆盖 | 覆盖率 |\n")
            f.write("|---------|---------|--------|--------|--------|\n")
            
            for r in results:
                f.write(f"| {r['name']} | {r['total_statements']} | "
                       f"{r['covered_statements']} | {r['missing_statements']} | "
                       f"{r['coverage_percent']:.1f}% |\n")
            
            f.write("\n## 📈 详细分析\n\n")
            for r in results:
                f.write(f"### {r['name']}\n\n")
                f.write(f"- **文件路径**: {r['filepath']}\n")
                f.write(f"- **总语句数**: {r['total_statements']}\n")
                f.write(f"- **已覆盖语句**: {r['covered_statements']}\n")
                f.write(f"- **未覆盖语句**: {r['missing_statements']}\n")
                f.write(f"- **覆盖率**: {r['coverage_percent']:.1f}%\n")
                f.write(f"- **状态**: {'✅ 优秀' if r['coverage_percent'] >= 80 else '✅ 良好' if r['coverage_percent'] >= 60 else '⚠️ 需改进' if r['coverage_percent'] >= 40 else '❌ 不足'}\n")
                f.write("\n")
        
        print(f"📄 报告已保存到: {report_file}")


if __name__ == '__main__':
    main()
