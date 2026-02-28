#!/usr/bin/env python3
"""
分析前端页面中Mock数据的使用情况
"""

import re
from pathlib import Path

# 需要检查的目录
FRONTEND_PAGES_DIR = Path("/Users/flw/non-standard-automation-pm/frontend/src/pages")

# Mock数据模式
PATTERNS = [
    r'isDemoAccount',
    r'demo_token_',
    r'mockData\s*=',
    r'mock_data\s*=',
    r'演示账号',
    r'demoStats',
]

def find_mock_usage_in_file(file_path):
    """检查文件中是否包含Mock数据"""
    content = file_path.read_text(encoding='utf-8')
    matches = []

    for pattern in PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            # 获取匹配的行号和上下文
            lines = content.split('\n')
            line_num = content[:match.start()].count('\n') + 1
            if line_num <= len(lines):
                matches.append({
                    'pattern': pattern,
                    'line': line_num,
                    'content': lines[line_num - 1].strip()
                })

    return matches if matches else None

def scan_pages():
    """扫描所有页面文件"""
    results = []

    for file_path in FRONTEND_PAGES_DIR.rglob('*.jsx'):
        matches = find_mock_usage_in_file(file_path)
        if matches:
            results.append({
                'file': file_path.name,
                'path': str(file_path.relative_to(FRONTEND_PAGES_DIR)),
                'matches': matches
            })

    return results

def categorize_pages(results):
    """将页面分类"""
    categories = {
        'workstation': [],      # 工作台页面
        'dashboard': [],         # 仪表板页面
        'purchase': [],          # 采购相关
        'project': [],           # 项目相关
        'admin': [],             # 管理相关
        'other': []              # 其他
    }

    for result in results:
        filename = result['file'].lower()

        if 'workstation' in filename:
            categories['workstation'].append(result)
        elif 'dashboard' in filename:
            categories['dashboard'].append(result)
        elif 'purchase' in filename or 'receipt' in filename or 'arrival' in filename:
            categories['purchase'].append(result)
        elif 'project' in filename or 'contract' in filename:
            categories['project'].append(result)
        elif 'admin' in filename or 'permission' in filename or 'role' in filename or 'user' in filename:
            categories['admin'].append(result)
        else:
            categories['other'].append(result)

    return categories

def main():
    print("=" * 80)
    print("Mock数据分析报告")
    print("=" * 80)
    print()

    results = scan_pages()
    categories = categorize_pages(results)

    # 统计总数
    total_files = len(results)
    total_matches = sum(len(r['matches']) for r in results)

    print(f"📊 总体统计")
    print(f"   包含Mock数据的文件: {total_files}")
    print(f"   Mock数据引用总数: {total_matches}")
    print()

    # 按类别显示
    for category, files in categories.items():
        if files:
            print(f"📁 {category.upper()} ({len(files)} 个文件)")
            print("-" * 80)
            for f in sorted(files, key=lambda x: x['file']):
                print(f"   - {f['file']} ({len(f['matches'])} 处引用)")
            print()

    # 显示详细匹配
    print("=" * 80)
    print("详细匹配信息")
    print("=" * 80)
    print()

    for result in sorted(results, key=lambda x: x['file']):
        print(f"📄 {result['file']}")
        print(f"   路径: {result['path']}")
        print(f"   引用数: {len(result['matches'])}")
        for match in result['matches'][:5]:  # 只显示前5个
            print(f"   行 {match['line']}: {match['content']}")
        if len(result['matches']) > 5:
            print(f"   ... 还有 {len(result['matches']) - 5} 处")
        print()

    # 生成修复清单
    print("=" * 80)
    print("修复建议")
    print("=" * 80)
    print()

    print("修复步骤:")
    print("1. 移除 isDemoAccount 检测逻辑")
    print("2. 移除 mockData 初始化")
    print("3. 修复状态初始化为 null 或 []")
    print("4. 移除错误处理中的Mock回退")
    print("5. 添加 ApiIntegrationError 组件")
    print()

    print("优先级:")
    print("🔥 高优先级（工作台）:")
    for f in sorted(categories['workstation'], key=lambda x: x['file']):
        print(f"   - {f['path']}")
    print()

    print("⚡ 中优先级（仪表板）:")
    for f in sorted(categories['dashboard'], key=lambda x: x['file']):
        print(f"   - {f['path']}")
    print()

    print("📋 其他页面:")
    other_pages = categories['purchase'] + categories['project'] + categories['admin'] + categories['other']
    for f in sorted(other_pages, key=lambda x: x['file']):
        print(f"   - {f['path']}")
    print()

if __name__ == '__main__':
    main()
