#!/usr/bin/env python3
"""
分析API测试中发现的runtime错误
从服务器日志中提取详细的错误信息
"""

import re
from collections import defaultdict
from pathlib import Path
import json
from datetime import datetime


def analyze_server_log():
    """分析服务器日志中的错误"""
    log_file = Path("server.log")
    
    if not log_file.exists():
        print("❌ 服务器日志文件不存在")
        return
    
    errors = defaultdict(list)
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # 只分析最近1000行
    recent_lines = lines[-1000:] if len(lines) > 1000 else lines
    
    i = 0
    while i < len(recent_lines):
        line = recent_lines[i]
        
        # 检测数据库错误
        if 'OperationalError' in line or 'no such column' in line:
            if 'no such column' in line:
                match = re.search(r'no such column: (\S+)', line)
                if match:
                    column = match.group(1)
                    errors['database_missing_columns'].append(column)
        
        # 检测导入错误
        if 'ImportError' in line or 'ModuleNotFoundError' in line:
            errors['import_errors'].append(line.strip())
        
        # 检测AttributeError
        if 'AttributeError' in line:
            errors['attribute_errors'].append(line.strip())
        
        # 检测未实现的API
        if 'Not Found' in line and 'Request:' in line:
            match = re.search(r'Request: (\S+)', line)
            if match:
                endpoint = match.group(1)
                errors['not_found_endpoints'].append(endpoint)
        
        # 检测500错误
        if 'INTERNAL_ERROR' in line and 'Request:' in line:
            match = re.search(r'Request: (\S+)', line)
            if match:
                endpoint = match.group(1)
                errors['internal_errors'].append(endpoint)
        
        # 检测循环导入
        if 'circular import' in line.lower():
            errors['circular_imports'].append(line.strip())
        
        i += 1
    
    return errors


def analyze_test_results():
    """分析测试结果"""
    report_file = Path("data/test_core_api_report.json")
    
    if not report_file.exists():
        print("❌ 测试报告文件不存在")
        return None
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 统计错误类型
    error_types = {
        '500_internal_error': [],
        '404_not_found': [],
        '422_validation_error': [],
        'other': []
    }
    
    for error in report['errors']:
        if '500' in error['error']:
            error_types['500_internal_error'].append(error)
        elif '404' in error['error']:
            error_types['404_not_found'].append(error)
        elif '422' in error['error']:
            error_types['422_validation_error'].append(error)
        else:
            error_types['other'].append(error)
    
    return error_types, report


def generate_analysis_report():
    """生成错误分析报告"""
    print("=" * 80)
    print("API错误分析报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 分析日志错误
    print("## 1. 服务器日志错误分析\n")
    log_errors = analyze_server_log()
    
    if log_errors:
        if log_errors.get('database_missing_columns'):
            print("### 🔴 数据库列缺失错误")
            unique_columns = set(log_errors['database_missing_columns'])
            for column in sorted(unique_columns):
                print(f"  - {column}")
            print()
        
        if log_errors.get('not_found_endpoints'):
            print("### 🔴 未实现的API端点（404错误）")
            unique_endpoints = set(log_errors['not_found_endpoints'])
            for endpoint in sorted(unique_endpoints):
                print(f"  - {endpoint}")
            print()
        
        if log_errors.get('internal_errors'):
            print("### 🔴 500内部错误的API端点")
            unique_endpoints = set(log_errors['internal_errors'])
            for endpoint in sorted(unique_endpoints):
                print(f"  - {endpoint}")
            print()
        
        if log_errors.get('import_errors'):
            print("### 🔴 导入错误")
            for error in log_errors['import_errors'][:10]:  # 显示前10个
                print(f"  - {error[:100]}")
            print()
        
        if log_errors.get('circular_imports'):
            print("### 🔴 循环导入错误")
            for error in log_errors['circular_imports']:
                print(f"  - {error[:100]}")
            print()
    
    # 2. 分析测试结果
    print("\n## 2. API测试结果分析\n")
    result = analyze_test_results()
    
    if result:
        error_types, report = result
        
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"成功率: {report['summary']['success_rate']}\n")
        
        print("### 错误类型分布\n")
        print(f"- 500内部错误: {len(error_types['500_internal_error'])} 个")
        print(f"- 404未找到: {len(error_types['404_not_found'])} 个")
        print(f"- 422验证错误: {len(error_types['422_validation_error'])} 个")
        print(f"- 其他错误: {len(error_types['other'])} 个\n")
        
        print("### 模块错误详情\n")
        for module, stats in report['modules'].items():
            total = stats['total']
            passed = stats['passed']
            failed = stats['failed']
            rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"{status} {module}: {passed}/{total} 通过 ({rate})")
        print()
    
    # 3. 生成修复建议
    print("\n## 3. 修复建议\n")
    
    suggestions = []
    
    if log_errors and log_errors.get('database_missing_columns'):
        suggestions.append({
            "priority": "🔴 P0 - 紧急",
            "issue": "数据库模式不匹配",
            "description": f"发现 {len(set(log_errors['database_missing_columns']))} 个缺失的数据库列",
            "action": "运行数据库迁移或检查模型定义是否与数据库一致",
            "command": "alembic upgrade head 或检查最近的迁移脚本"
        })
    
    if error_types and len(error_types['404_not_found']) > 10:
        suggestions.append({
            "priority": "🟡 P1 - 高",
            "issue": "大量API未实现",
            "description": f"{len(error_types['404_not_found'])} 个API返回404",
            "action": "检查路由注册是否完整，验证API路径是否正确",
            "command": "检查 app/api/v1/__init__.py 中的路由注册"
        })
    
    if error_types and len(error_types['500_internal_error']) > 5:
        suggestions.append({
            "priority": "🔴 P0 - 紧急",
            "issue": "大量500内部错误",
            "description": f"{len(error_types['500_internal_error'])} 个API返回500",
            "action": "查看详细的服务器日志，修复runtime错误",
            "command": "tail -f server.log | grep ERROR"
        })
    
    if log_errors and log_errors.get('import_errors'):
        suggestions.append({
            "priority": "🟡 P1 - 高",
            "issue": "模块导入错误",
            "description": f"发现 {len(log_errors['import_errors'])} 个导入错误",
            "action": "检查依赖是否安装完整，模块路径是否正确",
            "command": "pip install -r requirements.txt"
        })
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"### 建议 {i}: {suggestion['issue']}")
        print(f"**优先级:** {suggestion['priority']}")
        print(f"**问题:** {suggestion['description']}")
        print(f"**修复:** {suggestion['action']}")
        print(f"**命令:** `{suggestion['command']}`")
        print()
    
    # 保存到文件
    report_content = []
    report_content.append("# API错误分析与修复报告\n")
    report_content.append(f"**生成时间:** {datetime.now().isoformat()}\n")
    
    report_content.append("## 问题总结\n")
    
    if log_errors:
        if log_errors.get('database_missing_columns'):
            report_content.append("### 数据库列缺失\n")
            for column in sorted(set(log_errors['database_missing_columns'])):
                report_content.append(f"- {column}\n")
            report_content.append("\n")
    
    if result:
        report_content.append("### API测试结果\n")
        report_content.append(f"- 总测试: {report['summary']['total_tests']}\n")
        report_content.append(f"- 通过: {report['summary']['passed']}\n")
        report_content.append(f"- 失败: {report['summary']['failed']}\n")
        report_content.append(f"- 成功率: {report['summary']['success_rate']}\n\n")
    
    report_content.append("## 修复建议\n\n")
    for i, suggestion in enumerate(suggestions, 1):
        report_content.append(f"### {i}. {suggestion['issue']}\n\n")
        report_content.append(f"**优先级:** {suggestion['priority']}\n\n")
        report_content.append(f"**问题:** {suggestion['description']}\n\n")
        report_content.append(f"**修复:** {suggestion['action']}\n\n")
        report_content.append(f"**命令:**\n```bash\n{suggestion['command']}\n```\n\n")
    
    Path("data/api_error_analysis.md").write_text("".join(report_content), encoding='utf-8')
    
    print("\n" + "=" * 80)
    print("✅ 分析完成！报告已保存到: data/api_error_analysis.md")
    print("=" * 80)


if __name__ == "__main__":
    generate_analysis_report()
