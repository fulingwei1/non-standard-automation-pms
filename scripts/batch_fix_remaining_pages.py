#!/usr/bin/env python3
import re
from pathlib import Path

FRONTEND_DIR = Path("frontend/src/pages")

# 中优先级页面（列表、管理、表单、详情）
MEDIUM_PRIORITY_FILES = [
    'LeaveManagement.jsx',
    'OvertimeManagement.jsx',
    'InvoiceManagement.jsx',
    'BudgetApproval.jsx',
    'CostAccounting.jsx',
    'MaterialStock.jsx',
    'MaterialInbound.jsx',
    'MaterialOutbound.jsx',
    'WarehouseManagement.jsx',
    'ShippingManagement.jsx',
    'ReturnManagement.jsx',
    'SupplierEvaluation.jsx',
    'SupplierList.jsx',
    'SupplierQuotation.jsx',
    'SupplierContract.jsx',
    'CustomerList.jsx',
    'CustomerOrderHistory.jsx',
    'CustomerFeedback.jsx',
    'PurchaseRequisition.jsx',
    'MaterialRequest.jsx',
    'MachineMaintenanceList.jsx',
    'MachineMaintenanceDetail.jsx',
    'ProductionPlanList.jsx',
    'ProductionPlanDetail.jsx',
    'QualityInspectionList.jsx',
    'QualityInspectionDetail.jsx',
]

# 低优先级页面（辅助功能、配置）
LOW_PRIORITY_FILES = [
    'About.jsx',
    'Help.jsx',
    'Settings.jsx',
    'Profile.jsx',
    'ChangePassword.jsx',
    'NotificationsSettings.jsx',
    'LanguageSettings.jsx',
    'ThemeSettings.jsx',
    'SystemInfo.jsx',
    'Logs.jsx',
    'Backup.jsx',
    'Restore.jsx',
    'IntegrationSettings.jsx',
    'SecuritySettings.jsx',
    'PrivacyPolicy.jsx',
    'TermsOfService.jsx',
    'ContactSupport.jsx',
    'FAQ.jsx',
    'UserGuide.jsx',
    'VersionHistory.jsx',
    'DashboardSettings.jsx',
    'RoleManagement.jsx',
    'UserManagement.jsx',
    'DepartmentManagement.jsx',
    'PositionManagement.jsx',
    'PermissionManagement.jsx',
    'MenuManagement.jsx',
    'DictionaryManagement.jsx',
    'WorkflowManagement.jsx',
]

def quick_fix_file(file_path: Path) -> dict:
    """快速修复文件"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    changes = []

    # 修复1：添加API导入（如果缺失）
    if 'from "../services/api"' not in content:
        import_pattern = r"(import \{[^}]+\}\s*from ['\"]([^'\"]+)['\"])"
        match = re.search(import_pattern, content)
        if match:
            existing_imports = match.group(1)
            if 'services/api' not in existing_imports:
                # 在现有导入后添加api导入
                api_import = "import { api } from '../services/api'\n"
                content = re.sub(import_pattern, f"\\1\\n{api_import}", content)
                changes.append("添加API导入")

    # 修复2：添加基础状态定义（如果缺失）
    if 'useState([])' not in content and 'useState({})' not in content and 'useState(null)' not in content:
        # 在组件函数开始处添加状态
        function_start = r"(export default function \w+\(\) \{)"
        state_declarations = """
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
"""
        content = re.sub(function_start, f"\\1{state_declarations}", content)
        changes.append("添加基础状态定义")

    # 修复3：移除Mock数据定义
    mock_patterns = [
        r"// Mock data.*?\nconst mock\w+\s*=\s*",
        r"const mock\w+\s*=\s*\{",
        r"const mock\w+\s*=\s*\[",
    ]

    for pattern in mock_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
            changes.append("移除Mock数据定义")
            break

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return {'file': file_path.name, 'changes': changes, 'success': True}

    return {'file': file_path.name, 'changes': [], 'success': False}

def batch_fix_files(files_list, batch_name):
    """批量修复文件"""
    print(f"\n{'=' * 80}")
    print(f"批量修复：{batch_name}")
    print(f"检查 {len(files_list)} 个文件")
    print()

    results = []
    for filename in files_list:
        file_path = FRONTEND_DIR / filename
        if not file_path.exists():
            print(f"⚠️  文件不存在: {filename}")
            continue

        print(f"处理: {filename}")
        result = quick_fix_file(file_path)

        if result['success']:
            print(f"  ✅ 成功 - 修改: {len(result['changes'])} 项")
            for change in result['changes']:
                print(f"     - {change}")
        else:
            print(f"  ⏭️  无需修改")
        print()

    # 统计
    successful = [r for r in results if r['success']]
    total_changes = sum(len(r['changes']) for r in successful)

    print("=" * 80)
    print(f"批量修复：{batch_name}完成")
    print("=" * 80)
    print(f"处理文件数: {len(results)}")
    print(f"修复文件数: {len(successful)}")
    print(f"总修改项: {total_changes}")
    print()

    return results

def main():
    print("=" * 80)
    print("批量修复剩余页面")
    print("=" * 80)
    print()

    # 第一批：中优先级页面（25个）
    print("第一批：中优先级页面（25个）")
    print()
    medium_results = batch_fix_files(MEDIUM_PRIORITY_FILES, "中优先级")

    # 第二批：低优先级页面（28个）
    print("=" * 80)
    print("第二批：低优先级页面（28个）")
    print()
    low_results = batch_fix_files(LOW_PRIORITY_FILES, "低优先级")

    # 汇总统计
    all_results = medium_results + low_results
    successful = [r for r in all_results if r['success']]
    total_changes = sum(len(r['changes']) for r in successful)

    print("=" * 80)
    print("批量修复总结")
    print("=" * 80)
    print(f"总处理文件数: {len(all_results)}")
    print(f"总修复文件数: {len(successful)}")
    print(f"总修改项: {total_changes}")
    print()

    return all_results

if __name__ == '__main__':
    main()
