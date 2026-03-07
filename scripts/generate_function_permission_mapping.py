#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成系统功能与权限映射关系
统计所有API端点和对应的权限配置
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def extract_api_endpoints() -> Dict[str, List[Dict]]:
    """提取所有API端点"""
    endpoints = defaultdict(list)
    endpoints_dir = PROJECT_ROOT / "app" / "api" / "v1" / "endpoints"

    if not endpoints_dir.exists():
        return endpoints

    for file_path in endpoints_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue

        module_name = file_path.stem
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取路由装饰器
        # @router.get("/path")
        # @router.post("/path")
        # @router.put("/path")
        # @router.delete("/path")
        pattern = r'@router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)

        for method, path in matches:
            # 提取权限检查
            permission = None
            # 查找 require_permission
            perm_pattern = r'require_permission\s*\(["\']([^"\']+)["\']'
            perm_match = re.search(perm_pattern, content)
            if perm_match:
                permission = perm_match.group(1)

            # 查找函数定义
            func_pattern = rf'def\s+(\w+)\s*\([^)]*\)[^:]*:'
            re.findall(func_pattern, content)

            endpoints[module_name].append(
                {
                    "method": method.upper(),
                    "path": path,
                    "permission": permission,
                    "module": module_name,
                }
            )

    return dict(endpoints)


def extract_permissions_from_db() -> List[Dict]:
    """从数据库迁移文件中提取权限定义"""
    permissions = []
    migrations_dir = PROJECT_ROOT / "migrations"

    # 查找所有权限相关的迁移文件
    permission_files = [
        f
        for f in migrations_dir.glob("*permission*.sql")
        if "seed" in f.name or "permission" in f.name
    ]

    for file_path in permission_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取权限插入语句
        # 支持两种字段名：perm_code/permission_code, perm_name/permission_name
        pattern = (
            r"INSERT\s+(?:OR\s+IGNORE\s+)?INTO\s+permissions\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)"
        )
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)

        for columns_str, values_str in matches:
            # 解析列名
            columns = [c.strip() for c in columns_str.split(",")]
            # 解析VALUES中的值
            values = [v.strip().strip("'\"") for v in values_str.split(",")]

            # 创建列名到值的映射
            perm_dict = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    perm_dict[col.lower()] = values[i]

            # 统一字段名（支持perm_code和permission_code）
            code = perm_dict.get("perm_code") or perm_dict.get("permission_code") or ""
            name = perm_dict.get("perm_name") or perm_dict.get("permission_name") or ""
            module = perm_dict.get("module") or ""
            resource = perm_dict.get("resource") or ""
            action = perm_dict.get("action") or ""

            if code:
                permissions.append(
                    {
                        "code": code,
                        "name": name,
                        "module": module,
                        "resource": resource,
                        "action": action,
                        "source_file": file_path.name,
                    }
                )

    return permissions


def extract_permissions_from_code() -> List[Dict]:
    """从代码中提取权限使用情况"""
    permissions_used = []
    endpoints_dir = PROJECT_ROOT / "app" / "api" / "v1" / "endpoints"

    if not endpoints_dir.exists():
        return permissions_used

    for file_path in endpoints_dir.glob("*.py"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找所有 require_permission 调用
        pattern = r'require_permission\s*\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)

        for perm_code in matches:
            permissions_used.append(
                {
                    "code": perm_code,
                    "file": file_path.name,
                    "module": file_path.stem,
                }
            )

    return permissions_used


def generate_mapping_report() -> str:
    """生成功能与权限映射报告"""
    endpoints = extract_api_endpoints()
    db_permissions = extract_permissions_from_db()
    code_permissions = extract_permissions_from_code()

    report = []
    report.append("# 系统功能与权限映射关系\n")
    report.append(
        f"> 生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    report.append("\n## 一、统计概览\n")

    # 统计
    total_endpoints = sum(len(v) for v in endpoints.values())
    total_db_permissions = len(db_permissions)
    total_code_permissions = len(set(p["code"] for p in code_permissions))
    modules_count = len(endpoints)

    report.append(f"- **API模块数量**：{modules_count}")
    report.append(f"- **API端点总数**：{total_endpoints}")
    report.append(f"- **数据库权限总数**：{total_db_permissions}")
    report.append(f"- **代码中使用权限总数**：{total_code_permissions}")
    report.append("\n")

    # API端点列表
    report.append("## 二、API端点列表\n")
    report.append("| 模块 | 方法 | 路径 | 权限要求 |\n")
    report.append("|------|------|------|----------|\n")

    for module, module_endpoints in sorted(endpoints.items()):
        for ep in sorted(module_endpoints, key=lambda x: (x["method"], x["path"])):
            permission = ep.get("permission") or "-"
            report.append(f"| {module} | {ep['method']} | {ep['path']} | {permission} |\n")

    # 权限列表
    report.append("\n## 三、数据库权限列表\n")
    report.append("| 权限编码 | 权限名称 | 模块 | 资源 | 操作 | 来源文件 |\n")
    report.append("|---------|---------|------|------|------|----------|\n")

    for perm in sorted(db_permissions, key=lambda x: (x.get("module", ""), x.get("code", ""))):
        report.append(
            f"| {perm.get('code', '')} | {perm.get('name', '')} | {perm.get('module', '')} | {perm.get('resource', '')} | {perm.get('action', '')} | {perm.get('source_file', '')} |\n"
        )

    # 权限使用情况
    report.append("\n## 四、权限使用情况\n")
    report.append("| 权限编码 | 使用模块 | 使用文件 |\n")
    report.append("|---------|---------|----------|\n")

    perm_usage = defaultdict(set)
    for perm in code_permissions:
        perm_usage[perm["code"]].add((perm["module"], perm["file"]))

    for perm_code in sorted(perm_usage.keys()):
        usages = perm_usage[perm_code]
        modules = ", ".join(set(m for m, _ in usages))
        files = ", ".join(set(f for _, f in usages))
        report.append(f"| {perm_code} | {modules} | {files} |\n")

    # 未使用的权限
    db_perm_codes = set(p.get("code", "") for p in db_permissions)
    used_perm_codes = set(p["code"] for p in code_permissions)
    unused_perms = db_perm_codes - used_perm_codes

    if unused_perms:
        report.append("\n## 五、未使用的权限\n")
        report.append("以下权限在数据库中定义但未在代码中使用：\n\n")
        for perm_code in sorted(unused_perms):
            perm = next((p for p in db_permissions if p.get("code") == perm_code), None)
            if perm:
                report.append(
                    f"- `{perm_code}` - {perm.get('name', '')} ({perm.get('module', '')})\n"
                )

    # 代码中使用但未定义的权限
    undefined_perms = used_perm_codes - db_perm_codes
    if undefined_perms:
        report.append("\n## 六、未定义的权限\n")
        report.append("以下权限在代码中使用但未在数据库中定义：\n\n")
        for perm_code in sorted(undefined_perms):
            report.append(f"- `{perm_code}`\n")

    return "".join(report)


if __name__ == "__main__":
    report = generate_mapping_report()

    # 保存报告
    output_file = PROJECT_ROOT / "docs" / "FUNCTION_PERMISSION_MAPPING.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 功能权限映射报告已生成：{output_file}")
    print(f"📊 报告内容预览：")
    print(report[:1000] + "..." if len(report) > 1000 else report)
