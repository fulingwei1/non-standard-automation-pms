#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析API端点的构成，区分哪些需要权限检查，哪些不需要
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

endpoints_dir = Path(__file__).parent.parent / "app" / "api" / "v1" / "endpoints"

# 分类定义
PUBLIC_APIS = {
    # 认证相关（无需权限，但需要认证）
    "/login", "/logout", "/refresh", "/me", "/password",
    # 健康检查
    "/health",
}

# 可能需要认证但不需要特定权限的API（用户自己的数据）
SELF_DATA_APIS = {
    "/my",  # 我的数据
    "/me",  # 我的信息
}

# 业务模块分类
BUSINESS_MODULES = {
    "项目管理": ["projects", "stages", "milestones", "members", "project_workspace",
              "project_roles", "project_contributions", "project_evaluation"],
    "物料管理": ["materials", "bom", "material_demands", "suppliers"],
    "采购管理": ["purchase", "outsourcing"],
    "销售管理": ["sales", "presale", "presales_integration", "customers"],
    "生产管理": ["production", "assembly_kit", "kit_check", "kit_rate"],
    "验收管理": ["acceptance"],
    "工程变更": ["ecn"],
    "财务管理": ["budget", "costs", "bonus"],
    "绩效管理": ["performance", "work_log", "timesheet"],
    "预警管理": ["alerts", "shortage", "shortage_alerts"],
    "系统管理": ["users", "roles", "audits", "organization"],
    "其他功能": ["documents", "notifications", "report_center", "data_import_export",
              "scheduler", "task_center", "issues", "service", "installation_dispatch",
              "hr_management", "engineers", "staff_matching", "technical_review",
              "technical_spec", "qualification", "rd_project", "pmo", "progress",
              "workload", "business_support", "business_support_orders",
              "culture_wall", "culture_wall_config", "advantage_products",
              "hourly_rate", "admin_stats", "management_rhythm"],
}

def analyze_endpoints():
    """分析所有API端点"""
    results = {
        "by_file": defaultdict(list),
        "by_method": defaultdict(int),
        "by_module": defaultdict(list),
        "public": [],
        "self_data": [],
        "needs_permission": [],
        "maybe_public": [],
    }

    total_count = 0

    for file_path in sorted(endpoints_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        module_name = file_path.stem
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 查找路由装饰器
        route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'

        for i, line in enumerate(lines, 1):
            match = re.search(route_pattern, line)
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                total_count += 1

                endpoint_info = {
                    "file": module_name,
                    "method": method,
                    "path": path,
                    "line": i,
                }

                results["by_file"][module_name].append(endpoint_info)
                results["by_method"][method] += 1

                # 分类
                is_public = any(public_path in path for public_path in PUBLIC_APIS)
                is_self_data = any(self_path in path for self_path in SELF_DATA_APIS)

                if is_public:
                    results["public"].append(endpoint_info)
                elif is_self_data:
                    results["self_data"].append(endpoint_info)
                elif path.startswith("/") and len(path.split("/")) <= 2:
                    # 可能是公开的列表接口
                    results["maybe_public"].append(endpoint_info)
                else:
                    results["needs_permission"].append(endpoint_info)

                # 按模块分类
                for module_type, files in BUSINESS_MODULES.items():
                    if module_name in files:
                        results["by_module"][module_type].append(endpoint_info)
                        break
                else:
                    results["by_module"]["未分类"].append(endpoint_info)

    return results, total_count

def print_report(results: Dict, total_count: int):
    """打印分析报告"""
    print("=" * 80)
    print("API端点构成分析报告")
    print("=" * 80)
    print()

    print(f"📊 总体统计:")
    print(f"  总端点数: {total_count}")
    print(f"  涉及文件: {len(results['by_file'])} 个")
    print()

    print(f"📋 按HTTP方法分类:")
    for method, count in sorted(results["by_method"].items()):
        print(f"  {method:6} {count:4} 个")
    print()

    print(f"🔐 权限需求分类:")
    print(f"  🔓 公开API（无需认证）: {len(results['public'])} 个")
    print(f"  👤 个人数据API（需认证，无需特定权限）: {len(results['self_data'])} 个")
    print(f"  ⚠️  可能需要权限: {len(results['maybe_public'])} 个")
    print(f"  🔒 需要权限检查: {len(results['needs_permission'])} 个")
    print()

    print(f"📦 按业务模块分类:")
    for module_type, endpoints in sorted(results["by_module"].items()):
        if endpoints:
            print(f"  {module_type:12} {len(endpoints):4} 个端点")
    print()

    print(f"📄 按文件分类（前20个）:")
    sorted_files = sorted(results["by_file"].items(), key=lambda x: len(x[1]), reverse=True)
    for file_name, endpoints in sorted_files[:20]:
        print(f"  {file_name:30} {len(endpoints):4} 个端点")
    print()

    # 详细分析
    print("=" * 80)
    print("详细分析：哪些端点需要权限检查？")
    print("=" * 80)
    print()

    print("✅ 不需要权限检查的端点类型:")
    print("  1. 公开API（认证相关、健康检查）")
    print(f"     - 数量: {len(results['public'])} 个")
    print("     - 示例: /auth/login, /health")
    print()
    print("  2. 个人数据API（用户查看自己的数据）")
    print(f"     - 数量: {len(results['self_data'])} 个")
    print("     - 示例: /my/performance, /me")
    print("     - 说明: 这些API通常只需要认证，不需要特定权限")
    print()

    print("⚠️  需要评估的端点:")
    print(f"  3. 可能的公开接口（简单路径）")
    print(f"     - 数量: {len(results['maybe_public'])} 个")
    print("     - 说明: 需要人工判断是否为公开接口")
    print()

    print("🔒 必须配置权限的端点:")
    print(f"  4. 业务操作API")
    print(f"     - 数量: {len(results['needs_permission'])} 个")
    print("     - 说明: 所有业务相关的CRUD操作都需要权限检查")
    print()

    # 按模块统计需要权限的端点
    print("=" * 80)
    print("各模块需要权限的端点数量:")
    print("=" * 80)
    print()

    module_permission_needs = defaultdict(int)
    for endpoint in results["needs_permission"]:
        file_name = endpoint["file"]
        for module_type, files in BUSINESS_MODULES.items():
            if file_name in files:
                module_permission_needs[module_type] += 1
                break
        else:
            module_permission_needs["未分类"] += 1

    for module_type, count in sorted(module_permission_needs.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {module_type:15} {count:4} 个端点需要权限检查")
    print()

    # 建议
    print("=" * 80)
    print("💡 建议:")
    print("=" * 80)
    print()

    needs_permission_count = len(results["needs_permission"])
    public_count = len(results["public"]) + len(results["self_data"])

    print(f"1. 实际需要权限检查的端点: {needs_permission_count} 个")
    print(f"   （占总数的 {needs_permission_count/total_count*100:.1f}%）")
    print()
    print(f"2. 不需要权限检查的端点: {public_count} 个")
    print(f"   （占总数的 {public_count/total_count*100:.1f}%）")
    print()
    print("3. 权限检查优先级:")
    print("   🔴 高优先级（立即处理）:")
    print("      - 用户管理、角色管理（系统安全）")
    print("      - 财务相关（资金安全）")
    print("      - 项目管理（核心业务）")
    print()
    print("   🟡 中优先级（1-2周内）:")
    print("      - 物料管理、采购管理")
    print("      - 销售管理、生产管理")
    print("      - 验收管理、工程变更")
    print()
    print("   🟢 低优先级（逐步完善）:")
    print("      - 报表、统计、通知等辅助功能")
    print()

if __name__ == "__main__":
    results, total_count = analyze_endpoints()
    print_report(results, total_count)
