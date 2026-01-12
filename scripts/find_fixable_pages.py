#!/usr/bin/env python3
import re
from pathlib import Path

FRONTEND_DIR = Path("frontend/src/pages")

# 所有可能需要API集成的页面
ALL_CANDIDATE_FILES = [
    # 工作台
    'SalesManagerWorkstation.jsx',
    'AdminDashboard.jsx',
    'CustomerServiceDashboard.jsx',
    
    # 列表页面
    'LeaveManagement.jsx',
    'OvertimeManagement.jsx',
    'InvoiceManagement.jsx',
    'PaymentManagement.jsx',
    
    # 管理页面
    'UserManagement.jsx',
    'DepartmentManagement.jsx',
    'RoleManagement.jsx',
    'PermissionManagement.jsx',
    
    # 采购相关
    'SupplierList.jsx',
    'MaterialStock.jsx',
    'WarehouseManagement.jsx',
    'ShippingManagement.jsx',
    
    # 其他功能页面
    'BudgetManagement.jsx',
    'CostAnalysis.jsx',
    'DocumentList.jsx',
]

def needs_fix(file_path: Path) -> dict:
    """检查文件是否需要修复"""
    if not file_path.exists():
        return {'file': file_path.name, 'exists': False, 'needs_fix': False}
    
    content = file_path.read_text(encoding='utf-8')
    
    issues = []
    
    # 检查1：是否有Mock数据
    if re.search(r'const mock\w+\s*=\s*', content):
        issues.append({
            'type': 'has_mock_data',
            'severity': 'high',
            'message': '仍有Mock数据定义'
        })
    
    # 检查2：是否有isDemoAccount
    if 'isDemoAccount' in content or 'demo_token_' in content:
        issues.append({
            'type': 'has_isDemoAccount',
            'severity': 'high',
            'message': '仍有isDemoAccount检查'
        })
    
    # 检查3：是否缺少API导入
    if 'from "../services/api"' not in content:
        issues.append({
            'type': 'missing_api_import',
            'severity': 'high',
            'message': '缺少API导入'
        })
    
    # 检查4：是否缺少状态定义
    if 'useState' not in content:
        issues.append({
            'type': 'missing_state',
            'severity': 'medium',
            'message': '缺少useState状态定义'
        })
    
    return {
        'file': file_path.name,
        'exists': True,
        'issues': issues,
        'needs_fix': any(issue['severity'] == 'high' for issue in issues),
        'total_issues': len(issues)
    }

def quick_fix_file(file_path: Path) -> dict:
    """快速修复文件"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    changes = []
    
    # 修复1：添加API导入
    if 'from "../services/api"' not in content:
        import_pattern = r"(import \{[^}]+\}\s*from ['\"]([^'\"]+)['\"])"
        match = re.search(import_pattern, content)
        if match:
            # 在现有导入后添加api导入
            api_import = "import { api } from '../services/api'\n"
            content = re.sub(import_pattern, f"\\1\\n{api_import}", content)
            changes.append("添加API导入")
    
    # 修复2：移除Mock数据
    content = re.sub(r"// Mock data.*?\nconst mock\w+\s*=\s*[^;]+", '', content)
    content = re.sub(r"const demoStats\s*=\s*\{[^}]+\}", '', content)
    
    # 修复3：移除isDemoAccount
    content = re.sub(r"\s*// Check if demo account.*?\n\s*const isDemoAccount\s*=\s*[^;]+", '', content)
    
    # 修复4：添加基础状态（如果缺失）
    if 'useState([])' not in content and 'useState({})' not in content and 'useState(null)' not in content:
        function_start = r"(export default function \w+\(\) \{)"
        state_declarations = """
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
"""
        content = re.sub(function_start, f"\\1{state_declarations}", content)
        changes.append("添加基础状态定义")
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return {'file': file_path.name, 'changes': changes, 'success': True}
    
    return {'file': file_path.name, 'changes': [], 'success': False}

def main():
    print("=" * 80)
    print("查找需要修复的页面...")
    print("=" * 80)
    print()
    
    fixable_files = []
    for filename in ALL_CANDIDATE_FILES:
        file_path = FRONTEND_DIR / filename
        result = needs_fix(file_path)
        if result['exists'] and result['needs_fix']:
            fixable_files.append((file_path, result))
            print(f"✓ 找到需要修复的文件: {filename}")
            for issue in result['issues']:
                severity = '🔴' if issue['severity'] == 'high' else '🟡'
                print(f"  {severity} {issue['type']}: {issue['message']}")
            print()
    
    print("=" * 80)
    print(f"找到 {len(fixable_files)} 个需要修复的文件")
    print()
    
    # 逐个修复
    print("开始修复...")
    print()
    
    results = []
    for file_path, check_result in fixable_files:
        print(f"修复: {file_path.name}")
        fix_result = quick_fix_file(file_path)
        results.append(fix_result)
        
        if fix_result['success']:
            print(f"  ✅ 成功 - 修改: {len(fix_result['changes'])} 项")
            for change in fix_result['changes']:
                print(f"     - {change}")
        else:
            print(f"  ⏭️  无需修改")
        print()
    
    # 统计
    successful = [r for r in results if r['success']]
    total_changes = sum(len(r['changes']) for r in successful)
    
    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print(f"处理文件数: {len(results)}")
    print(f"成功修复: {len(successful)}")
    print(f"总修改项: {total_changes}")
    print()
    
    return results

if __name__ == '__main__':
    main()
