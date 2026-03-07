#!/usr/bin/env python3
"""
自动生成拆分后的API模块文件
"""
import re
from collections import defaultdict
from pathlib import Path


def extract_api_blocks(api_js_path):
    """从api.js中提取所有API模块定义，保留完整的格式"""
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 更精确的匹配，支持嵌套对象
    pattern = r"export const (\w+) = \{((?:[^{}]|\{[^{}]*\})*)\}"

    modules = {}
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        body = match.group(2)
        start_pos = match.start()

        # 查找前后的注释
        lines_before = content[:start_pos].split("\n")
        comments = []
        for line in reversed(lines_before[-5:]):
            if line.strip().startswith("//"):
                comments.insert(0, line)
            elif line.strip():
                break

        modules[name] = {"body": body, "comments": comments}

    return modules, content


def get_categorization():
    """返回手动优化的分类映射"""
    return {
        # Auth
        "authApi": "auth",
        "userApi": "auth",
        "roleApi": "auth",
        "orgApi": "auth",
        "organizationApi": "auth",
        # Project
        "projectApi": "project",
        "machineApi": "project",
        "stageApi": "project",
        "milestoneApi": "project",
        "memberApi": "project",
        "costApi": "project",
        "settlementApi": "project",
        "documentApi": "project",
        "projectWorkspaceApi": "project",
        "projectContributionApi": "project",
        "financialCostApi": "project",
        "projectRolesApi": "project",
        "projectRoleApi": "project",
        "projectReviewApi": "project",
        "costOverrunApi": "project",
        # Sales
        "customerApi": "sales",
        "leadApi": "sales",
        "opportunityApi": "sales",
        "quoteApi": "sales",
        "salesTemplateApi": "sales",
        "contractApi": "sales",
        "invoiceApi": "sales",
        "paymentApi": "sales",
        "receivableApi": "sales",
        "paymentPlanApi": "sales",
        "disputeApi": "sales",
        "salesTeamApi": "sales",
        "salesTargetApi": "sales",
        "salesStatisticsApi": "sales",
        "salesApi": "sales",
        "salesReportApi": "sales",
        "presalesIntegrationApi": "sales",
        "lossAnalysisApi": "sales",
        "presaleExpenseApi": "sales",
        "priorityApi": "sales",
        "pipelineAnalysisApi": "sales",
        "accountabilityApi": "sales",
        # Operations
        "supplierApi": "operations",
        "purchaseApi": "operations",
        "shortageApi": "operations",
        "productionApi": "operations",
        "materialApi": "operations",
        "materialDemandApi": "operations",
        "shortageAlertApi": "operations",
        "bomApi": "operations",
        "kitCheckApi": "operations",
        # Quality
        "alertApi": "quality",
        "issueApi": "quality",
        "acceptanceApi": "quality",
        "ecnApi": "quality",
        "issueTemplateApi": "quality",
        "healthApi": "quality",
        "delayAnalysisApi": "quality",
        "informationGapApi": "quality",
        "crossAnalysisApi": "quality",
        # HR
        "employeeApi": "hr",
        "departmentApi": "hr",
        "hrApi": "hr",
        "performanceApi": "hr",
        "bonusApi": "hr",
        "timesheetApi": "hr",
        "hrManagementApi": "hr",
        # Service & Support
        "serviceApi": "service",
        "installationDispatchApi": "service",
        # PMO & Admin
        "pmoApi": "admin",
        "presaleApi": "admin",
        "outsourcingApi": "admin",
        "businessSupportApi": "admin",
        "exceptionApi": "admin",
        "adminApi": "admin",
        "managementRhythmApi": "admin",
        "cultureWallApi": "admin",
        "workLogApi": "admin",
        "auditApi": "admin",
        # Technical & R&D
        "technicalReviewApi": "technical",
        "engineersApi": "technical",
        "technicalAssessmentApi": "technical",
        "qualificationApi": "technical",
        "rdProjectApi": "technical",
        "rdReportApi": "technical",
        "assemblyKitApi": "technical",
        "schedulerApi": "technical",
        "staffMatchingApi": "technical",
        "advantageProductApi": "technical",
        "itrApi": "technical",
        # Shared & Reports
        "notificationApi": "shared",
        "taskCenterApi": "shared",
        "workloadApi": "shared",
        "reportCenterApi": "shared",
        "progressApi": "shared",
        "financialReportApi": "shared",
        "dataImportExportApi": "shared",
        "hourlyRateApi": "shared",
    }


def generate_module_file(category, modules_data, api_config_content):
    """生成单个分类的模块文件"""
    lines = [
        "/**",
        f" * {category.upper()} 模块 API",
        " * 自动生成，请勿手动编辑",
        " */",
        'import api from "../config";',
        "",
    ]

    for module_name, module_info in modules_data:
        # 添加注释
        if module_info["comments"]:
            lines.extend([""] + module_info["comments"] + [""])

        # 添加导出
        body = module_info["body"].rstrip()
        lines.append(f"export const {module_name} = {{")
        lines.append(body)
        lines.append("};")
        lines.append("")

    return "\n".join(lines)


def main():
    base_path = Path("/Users/flw/non-standard-automation-pm/frontend/src/services")
    api_js_path = base_path / "api.js"
    config_path = base_path / "config.js"

    print("📖 读取 api.js...")
    modules, full_content = extract_api_blocks(api_js_path)
    print(f"✅ 找到 {len(modules)} 个API模块")

    # 读取config内容以获取api实例
    print("📖 读取 config.js...")
    with open(config_path, "r", encoding="utf-8") as f:
        api_config_content = f.read()

    # 获取分类
    categorization = get_categorization()

    # 按分类组织模块
    categorized = defaultdict(list)
    for name, info in modules.items():
        category = categorization.get(name, "other")
        categorized[category].append((name, info))

    # 打印分类统计
    print("\n📊 模块分类统计:")
    for category, mods in sorted(categorized.items()):
        print(f"  {category}: {len(mods)} 个模块")

    # 创建必要的目录
    categories_to_create = [
        "sales",
        "operations",
        "quality",
        "hr",
        "shared",
        "service",
        "admin",
        "technical",
        "other",
    ]
    for cat in categories_to_create:
        cat_dir = base_path / cat
        if not cat_dir.exists():
            cat_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建目录: {cat}")

    # 生成各分类的文件
    print("\n📝 生成模块文件...")
    for category, mods in categorized.items():
        if category in ["auth", "project"]:
            continue  # 已手动创建

        file_path = base_path / category / "index.js"
        content = generate_module_file(category, mods, api_config_content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✅ {category}/index.js ({len(mods)} 个模块)")

    print("\n✅ 所有模块文件生成完成！")


if __name__ == "__main__":
    main()
