#!/usr/bin/env python3
"""
自动修复前端页面中的Mock数据使用情况
"""

import re
from pathlib import Path
from typing import List, Tuple

# 需要修复的文件列表
FILES_TO_FIX = {
    "AdministrativeManagerWorkstation.jsx": "frontend/src/pages",
    "AlertCenter.jsx": "frontend/src/pages",
    "AlertStatistics.jsx": "frontend/src/pages",
    "ArrivalManagement.jsx": "frontend/src/pages",
    "ArrivalTrackingList.jsx": "frontend/src/pages",
    "BudgetManagement.jsx": "frontend/src/pages",
    "CostAnalysis.jsx": "frontend/src/pages",
    "CustomerCommunication.jsx": "frontend/src/pages",
    "Documents.jsx": "frontend/src/pages",
    "ExceptionManagement.jsx": "frontend/src/pages",
    "GoodsReceiptDetail.jsx": "frontend/src/pages",
    "GoodsReceiptNew.jsx": "frontend/src/pages",
    "PurchaseOrderDetail.jsx": "frontend/src/pages",
    "PurchaseOrderFromBOM.jsx": "frontend/src/pages",
    "PurchaseRequestDetail.jsx": "frontend/src/pages",
    "PurchaseRequestList.jsx": "frontend/src/pages",
    "PurchaseRequestNew.jsx": "frontend/src/pages",
    "ScheduleBoard.jsx": "frontend/src/pages",
    "ServiceAnalytics.jsx": "frontend/src/pages",
    "ServiceRecord.jsx": "frontend/src/pages",
    "ShortageAlert.jsx": "frontend/src/pages",
    "SupplierManagementData.jsx": "frontend/src/pages",
    "PermissionManagement.jsx": "frontend/src/pages",
}


def remove_demo_account_check(content: str) -> str:
    """移除 isDemoAccount 检查逻辑"""

    # 模式1: const isDemoAccount = ...
    # 移除整个检查块，但保留后续逻辑
    pattern1 = r'\s*//(?:如果|检查是否).*?演示账号.*?\n\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\).*?\n\s*(?:if\s*\(isDemoAccount\)\s*\{[^}]*\})?'

    # 模式2: useMemo 中的 isDemoAccount
    pattern2 = r"\s*const isDemoAccount\s*=\s*useMemo\(\(\)\s*=>\s*\{[^}]+\}\s*,\s*\[.*?isDemoAccount.*?\]\)"

    # 模式3: useEffect 中的 isDemoAccount 检查
    pattern3 = r'\s*//(?:如果|检查是否).*?演示账号.*?\n\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\).*?\n\s*(?:if\s*\(isDemoAccount\).*?\{[^}]*\}\s*)?'

    # 模式4: 错误处理中的 isDemoAccount 检查
    pattern4 = r'\s*const isDemoAccount\s*=\s*(?:token|localStorage\.getItem\(.*?\))\?\.startsWith\([\'"]demo_token_[\'"]\).*?\n\s*(?:if\s*\(\!?isDemoAccount.*?\)\s*\{[^}]*\}\s*)?'

    # 移除这些模式
    for pattern in [pattern1, pattern3, pattern4]:
        content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

    # 移除 useMemo 定义
    content = re.sub(pattern2, "", content, flags=re.MULTILINE | re.DOTALL)

    return content


def remove_mock_data_initialization(content: str) -> str:
    """移除 Mock 数据初始化"""

    # 移除 const mockStats = {...}
    pattern1 = r"\n// Mock data.*?\nconst mock\w+\s*=\s*\{[^\}]*\}"
    content = re.sub(pattern1, "", content, flags=re.MULTILINE | re.DOTALL)

    # 移除 mockPendingApprovals, mockMeetings 等
    pattern2 = r"\nconst mock\w+\s*=\s*\[[^\]]*\]"
    content = re.sub(pattern2, "", content, flags=re.MULTILINE | re.DOTALL)

    return content


def remove_demo_stats(content: str) -> str:
    """移除 demoStats 相关代码"""

    # 移除 const demoStats = {...}
    pattern = r"\n(?://(?:演示|Demo)账号的(?:演示|demo)数据.*?\n)?const demoStats\s*=\s*\{[^\}]*\}"
    content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

    return content


def remove_demo_account_fallback(content: str) -> str:
    """移除错误处理中的 Demo 账号回退逻辑"""

    # 模式: if (isDemoAccount) { setStats(demoStats); ... }
    pattern = r"\s*// 如果是演示账号.*?\n\s*(?:if\s*\(\!?isDemoAccount.*?\)\s*\{[^}]*\}\s*)+"

    content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

    return content


def remove_mock_usage_from_catch(content: str) -> str:
    """移除 catch 块中的 Mock 数据使用"""

    # 模式: } catch (err) { if (isDemoAccount) { setData(mockData); } }
    pattern = r"}\s*catch\s*\([^)]*\)\s*\{\s*(?:if\s*\(!?isDemoAccount.*?\)\s*\{[^}]*\}\s*)?(?:if\s*\(\!?isDemoAccount.*?\)\s*\{[^}]*\}\s*)?(?:else\s*\{[^}]*\})?\s*\}"

    # 更简单的模式：只移除 isDemoAccount 相关
    pattern2 = r"if\s*\(!?isDemoAccount.*?\)\s*\{[^}]*\}"

    content = re.sub(pattern2, "", content, flags=re.MULTILINE | re.DOTALL)

    return content


def fix_state_initialization(content: str) -> str:
    """修复状态初始化，移除 mockData 引用"""

    # 模式: const [data, setData] = useState(mockData)
    pattern = r"state=\{useState\(mock\w+\)\}"
    replacement = "state={useState(null)}"
    content = re.sub(pattern, replacement, content)

    return content


def remove_mock_data_comments(content: str) -> str:
    """移除 Mock 数据相关注释"""

    patterns = [
        r"// Mock data.*?已移除.*?使用真实API.*?\n",
        r"// 演示账号的演示数据.*?\n",
        r"// 如果是演示账号.*?\n",
        r"// 演示账号不加载数据.*?\n",
        r"// 演示账号不调用真实API.*?\n",
    ]

    for pattern in patterns:
        content = re.sub(pattern, "", content)

    return content


def add_api_integration_error_if_missing(content: str) -> str:
    """如果文件中没有 ApiIntegrationError 导入，添加导入"""

    if "ApiIntegrationError" not in content:
        # 在其他 UI 导入后添加
        import_pattern = r"(from ['\"].*components/ui['\"]\s*;)"
        replacement = r"\1import { ApiIntegrationError } from '../components/ui'\n"
        content = re.sub(import_pattern, replacement, content)

    return content


def check_and_fix_file(file_path: Path) -> Tuple[bool, List[str]]:
    """检查并修复单个文件"""
    if not file_path.exists():
        return False, [f"文件不存在: {file_path}"]

    content = file_path.read_text(encoding="utf-8")
    original_content = content
    changes = []

    # 1. 移除 isDemoAccount 检查
    if "isDemoAccount" in content:
        content = remove_demo_account_check(content)
        changes.append("移除 isDemoAccount 检查逻辑")

    # 2. 移除 Mock 数据初始化
    if "mockStats" in content or "mockData" in content:
        content = remove_mock_data_initialization(content)
        changes.append("移除 Mock 数据初始化")

    # 3. 移除 demoStats
    if "demoStats" in content:
        content = remove_demo_stats(content)
        changes.append("移除 demoStats")

    # 4. 添加 ApiIntegrationError 导入（如果缺失）
    content = add_api_integration_error_if_missing(content)

    # 5. 移除 Mock 数据相关注释
    if "演示账号" in content or "Mock data" in content:
        content = remove_mock_data_comments(content)
        changes.append("移除 Mock 数据相关注释")

    # 检查是否还有 Mock 数据引用
    if "mockData" in content or "mockStats" in content or "demoStats" in content:
        changes.append(f"⚠️ 仍然包含 Mock 数据引用")

    # 如果有修改，保存文件
    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True, changes

    return False, ["无需修改"]


def main():
    print("=" * 80)
    print("Mock数据修复工具")
    print("=" * 80)
    print()

    base_path = Path("/Users/flw/non-standard-automation-pm")
    results = []

    for filename, relative_dir in FILES_TO_FIX.items():
        file_path = base_path / relative_dir / filename
        modified, changes = check_and_fix_file(file_path)
        results.append({"file": filename, "modified": modified, "changes": changes})

    # 显示结果
    print(f"共处理 {len(results)} 个文件")
    print()

    modified_files = [r for r in results if r["modified"]]
    print(f"✅ 已修改: {len(modified_files)} 个文件")
    print()

    if modified_files:
        for result in modified_files:
            print(f"📄 {result['file']}")
            for change in result["changes"]:
                print(f"   - {change}")
            print()

    unmodified_files = [r for r in results if not r["modified"]]
    if unmodified_files:
        print(f"⏭️  无需修改: {len(unmodified_files)} 个文件")
        for result in unmodified_files:
            print(f"   - {result['file']}")
        print()

    # 生成总结
    print("=" * 80)
    print("修复总结")
    print("=" * 80)
    print(f"总文件数: {len(results)}")
    print(f"已修改: {len(modified_files)}")
    print(f"无需修改: {len(unmodified_files)}")
    print()
    print("下一步:")
    print("1. 运行 linter 检查: cd frontend && npm run lint")
    print("2. 测试修改后的页面")
    print("3. 提交代码")


if __name__ == "__main__":
    main()
