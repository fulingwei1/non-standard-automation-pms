#!/usr/bin/env python3
import re
from pathlib import Path

FRONTEND_DIR = Path("frontend/src/pages")

# 高优先级页面列表（需要检查和修复的）
HIGH_PRIORITY_FILES = [
    "ContractApproval.jsx",
    "EvaluationTaskList.jsx",
    "OfficeSuppliesManagement.jsx",
    "PerformanceIndicators.jsx",
    "PerformanceRanking.jsx",
    "PerformanceResults.jsx",
    "ProjectStaffingNeed.jsx",
    "ProjectReviewList.jsx",
    "MaterialAnalysis.jsx",
    "FinancialReports.jsx",
    "PaymentManagement.jsx",
    "PaymentApproval.jsx",
    "DocumentList.jsx",
    "KnowledgeBase.jsx",
]


def needs_api_integration(file_path: Path) -> dict:
    """检查页面是否需要API集成"""
    content = file_path.read_text(encoding="utf-8")

    issues = []

    # 检查1：是否有API导入
    if 'from "../services/api"' not in content:
        issues.append(
            {"type": "missing_api_import", "message": "缺少API服务导入", "severity": "high"}
        )

    # 检查2：是否有API调用
    api_patterns = [
        r"\w+Api\.",
        r"api\.",
    ]
    has_api_call = any(re.search(pattern, content) for pattern in api_patterns)
    if not has_api_call:
        issues.append(
            {"type": "missing_api_call", "message": "没有发现API调用", "severity": "high"}
        )

    # 检查3：是否有useEffect
    if "useEffect(()" not in content:
        issues.append(
            {
                "type": "missing_useeffect",
                "message": "缺少useEffect数据加载钩子",
                "severity": "medium",
            }
        )

    # 检查4：是否有错误处理
    if "catch (err)" not in content and "catch (error)" not in content:
        issues.append(
            {
                "type": "missing_error_handling",
                "message": "缺少错误处理（try-catch）",
                "severity": "medium",
            }
        )

    # 检查5：是否有Mock数据
    mock_patterns = [
        r"const mock\w+\s*=\s*",
        r"state=\[set\w+\]\s*=\s*useState\(mock",
        r"// Mock data",
    ]
    has_mock = any(re.search(pattern, content) for pattern in mock_patterns)
    if has_mock:
        issues.append({"type": "has_mock_data", "message": "仍有Mock数据", "severity": "high"})

    return {
        "file": file_path.name,
        "issues": issues,
        "needs_fix": any(issue["severity"] == "high" for issue in issues),
    }


def quick_fix_file(file_path: Path) -> dict:
    """快速修复文件"""
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    changes = []

    # 修复1：添加API导入（如果缺失）
    if 'from "../services/api"' not in content:
        # 找到现有的导入行
        import_pattern = r"(import \{[^}]+\}\s*from ['\"]([^'\"]+)['\"])"
        match = re.search(import_pattern, content)
        if match:
            existing_imports = match.group(1)
            if "services/api" not in existing_imports:
                # 在现有导入后添加api导入
                api_import = "import { api } from '../services/api'\n"
                content = re.sub(import_pattern, f"\\1\\n{api_import}", content)
                changes.append("添加API导入")

    # 修复2：添加基础状态定义（如果缺失）
    has_data_state = (
        "useState([])" in content or "useState({})" in content or "useState(null)" in content
    )
    has_loading_state = "useState(true)" in content or "useState(false)" in content
    has_error_state = "useState(null)" in content

    if not has_data_state or not has_loading_state or not has_error_state:
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
            # 找到Mock数据定义并移除
            content = re.sub(pattern, "", content, flags=re.MULTILINE)
            changes.append("移除Mock数据定义")
            break

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return {"file": file_path.name, "changes": changes, "success": True}

    return {"file": file_path.name, "changes": [], "success": False}


def main():
    print("快速修复高优先级页面...")
    print(f"检查 {len(HIGH_PRIORITY_FILES)} 个文件")
    print()

    results = []
    for filename in HIGH_PRIORITY_FILES:
        file_path = FRONTEND_DIR / filename
        if not file_path.exists():
            print(f"⚠️  文件不存在: {filename}")
            continue

        # 先检查是否需要修复
        check_result = needs_api_integration(file_path)

        print(f"检查: {filename}")
        for issue in check_result["issues"]:
            severity_icon = "🔴" if issue["severity"] == "high" else "🟡"
            print(f"  {severity_icon} {issue['type']}: {issue['message']}")

        if check_result["needs_fix"]:
            # 执行修复
            fix_result = quick_fix_file(file_path)
            results.append(fix_result)

            if fix_result["success"]:
                print(f"  ✅ 成功 - 修改: {len(fix_result['changes'])} 项")
                for change in fix_result["changes"]:
                    print(f"       - {change}")
            else:
                print(f"  ⏭️  无需修改")
        else:
            print(f"  ✅ 无需修复（已有API集成）")
        print()

    # 统计
    successful = [r for r in results if r["success"]]
    total_changes = sum(len(r["changes"]) for r in successful)

    print("=" * 80)
    print("快速修复完成")
    print("=" * 80)
    print(f"检查文件数: {len(HIGH_PRIORITY_FILES)}")
    print(f"修复文件数: {len(successful)}")
    print(f"总修改项: {total_changes}")
    print()

    return results


if __name__ == "__main__":
    main()
