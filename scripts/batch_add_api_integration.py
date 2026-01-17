#!/usr/bin/env python3
import re
from pathlib import Path

FRONTEND_DIR = Path("frontend/src/pages")

# API服务映射
API_MODULES = {
    'chairman': 'chairmanApi',
    'engineer': 'engineerApi',
    'sales': 'salesApi',
    'finance': 'financeApi',
    'customer_service': 'serviceApi',
    'procurement': 'purchaseApi',
    'production': 'productionApi',
    'manufacturing': 'manufacturingApi',
    'pmo': 'pmoApi',
    'admin': 'adminApi',
    'administrative': 'administrativeApi',
    'performance': 'performanceApi',
    'project': 'projectApi',
    'approval': 'approvalApi',
    'meeting': 'meetingApi',
    'vehicle': 'vehicleApi',
    'attendance': 'attendanceApi',
    'leave': 'leaveApi',
    'overtime': 'overtimeApi',
    'budget': 'budgetApi',
    'cost': 'costApi',
    'contract': 'contractApi',
    'document': 'documentApi',
    'knowledge': 'knowledgeApi',
    'material': 'materialApi',
    'supplier': 'supplierApi',
    'shortage': 'shortageApi',
}

def add_basic_api_integration(file_path: Path) -> dict:
    """为页面添加基础API集成"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    changes = []

    # 1. 检查并添加API导入
    if 'from "../services/api"' not in content:
        import_pattern = r"(import \{[^}]+\}\s*from ['\"]([^'\"]+)['\"])"
        match = re.search(import_pattern, content)
        if match:
            existing_imports = match.group(1)
            if 'services/api' not in existing_imports:
                # 在现有导入后添加api导入
                new_import = f"{existing_imports}, api"
                content = re.sub(import_pattern, f"import {{ {new_import} }} from '{match.group(2)}'", content)
                changes.append("添加API导入")

    # 2. 检查并添加基础状态定义
    if 'useState' in content:
        # 检查是否已有相关状态
        has_data_state = 'useState([])' in content or 'useState({})' in content or 'useState(null)' in content
        has_loading_state = 'useState(true)' in content or 'useState(false)' in content
        has_error_state = 'useState(null)' in content

        if not has_data_state or not has_loading_state or not has_error_state:
            # 在组件函数开始处添加状态
            function_start = r"(export default function \w+\(\) \{)"
            state_declarations = """
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
"""
            content = re.sub(function_start, r"\1" + state_declarations, content)
            changes.append("添加基础状态定义")

    # 3. 检查并移除Mock数据定义
    mock_patterns = [
        r"// Mock data.*?\nconst mock\w+\s*=\s*\{[^\}]*\}",
        r"// Mock data.*?\nconst mock\w+\s*=\s*\[[^\]]*\]",
        r"const demoStats\s*=\s*\{[^\}]*\}",
        r"const mockCurrentPeriod\s*=\s*\{[^\}]*\}",
    ]

    for pattern in mock_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
            changes.append("移除Mock数据定义")

    # 4. 检查并移除isDemoAccount检查
    demo_patterns = [
        r'\s*// Check if demo account.*?\n\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\([^)]+\))\?\.startsWith\([\'"]demo_token_[\'"]\)[^;]*;',
        r'\s*const isDemoAccount\s*=\s*useMemo\(\(\)\s*=>\s*\{[^}]+\}\s*,\s*\[[^\]]*\]);',
    ]

    for pattern in demo_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, '', content)
            changes.append("移除isDemoAccount检查")

    # 如果有修改，保存文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return {'file': file_path.name, 'changes': changes, 'success': True}

    return {'file': file_path.name, 'changes': [], 'success': False}

def batch_integrate(files_list):
    """批量处理文件"""
    print(f"开始批量API集成...")
    print(f"处理 {len(files_list)} 个文件")
    print()

    results = []
    for file_info in files_list:
        file_path = FRONTEND_DIR / file_info['filename']
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_info['filename']}")
            continue

        print(f"处理: {file_info['filename']}")
        result = add_basic_api_integration(file_path)
        results.append(result)

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
    print("批量API集成完成")
    print("=" * 80)
    print(f"处理文件数: {len(results)}")
    print(f"成功修改: {len(successful)}")
    print(f"总修改项: {total_changes}")
    print()

    return results

# 高优先级页面列表
HIGH_PRIORITY_FILES = [
    {'filename': 'ChairmanWorkstation.jsx', 'module': 'chairman'},
    {'filename': 'EngineerWorkstation.jsx', 'module': 'engineer'},
    {'filename': 'SalesManagerWorkstation.jsx', 'module': 'sales'},
    {'filename': 'FinanceManagerDashboard.jsx', 'module': 'finance'},
    {'filename': 'CustomerServiceDashboard.jsx', 'module': 'customer_service'},
    {'filename': 'ProcurementManagerDashboard.jsx', 'module': 'procurement'},
    {'filename': 'ProductionManagerDashboard.jsx', 'module': 'production'},
    {'filename': 'ManufacturingDirectorDashboard.jsx', 'module': 'manufacturing'},
    {'filename': 'PerformanceManagement.jsx', 'module': 'performance'},
    {'filename': 'ProjectBoard.jsx', 'module': 'project'},
    {'filename': 'AdminDashboard.jsx', 'module': 'admin'},
    {'filename': 'AdministrativeManagerWorkstation.jsx', 'module': 'administrative'},
    {'filename': 'SalesDirectorWorkstation.jsx', 'module': 'sales'},
    {'filename': 'GeneralManagerWorkstation.jsx', 'module': 'admin'},
    {'filename': 'PMODashboard.jsx', 'module': 'pmo'},
    {'filename': 'SalesWorkstation.jsx', 'module': 'sales'},
]

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # 测试模式：只处理一个文件
        print("测试模式：处理单个文件")
        test_file = HIGH_PRIORITY_FILES[0]
        result = add_basic_api_integration(FRONTEND_DIR / test_file['filename'])
        print(f"结果: {result}")
    else:
        # 批量处理模式
        batch_integrate(HIGH_PRIORITY_FILES)
