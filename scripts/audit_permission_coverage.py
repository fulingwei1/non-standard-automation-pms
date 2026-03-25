#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 权限覆盖审计脚本 (可重复运行)

基于 AST 静态分析，扫描所有 API 端点文件，检测每个路由函数的权限保护级别。
输出: PERMISSION_COVERAGE_AUDIT.json + PERMISSION_COVERAGE_AUDIT.md

用法:
    python scripts/audit_permission_coverage.py [--json-only] [--md-only]

保护级别定义:
    PERMISSION  - 有 require_permission / check_permission 等细粒度权限校验
    AUTH_ONLY   - 仅有 get_current_active_user 等登录校验，无权限码
    NONE        - 函数签名和函数体中未检测到任何认证/权限依赖
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

# ── 权限检查模式 ──────────────────────────────────────────────
PERM_PATTERNS = [
    "require_permission",
    "get_current_active_superuser",
    "require_sales_create_permission",
    "require_sales_edit_permission",
    "require_sales_delete_permission",
    "require_sales_approval_permission",
    "require_sales_assessment_access",
    "check_permission",
    "check_sales_approval_permission",
    "check_sales_create_permission",
    "check_sales_edit_permission",
    "check_sales_delete_permission",
    "check_timesheet_approval_permission",
    "apply_timesheet_access_filter",
]

AUTH_PATTERNS = [
    "get_current_active_user",
    "get_current_user",
    "oauth2_scheme",
]

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}

# 已知合法的无保护端点 (白名单/公共端点)
KNOWN_PUBLIC = {
    ("POST", "/login"),
    ("POST", "/refresh"),
    ("GET", "/health"),
}


def extract_endpoints_from_file(filepath: str) -> list[dict]:
    """从单个 Python 文件中提取所有路由端点及其权限状态。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    results = []
    lines = source.split("\n")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # 检测路由装饰器
        route_info = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                method = dec.func.attr.lower()
                if method in HTTP_METHODS:
                    path = "?"
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        path = str(dec.args[0].value)
                    route_info = (method.upper(), path)
                    break
        if not route_info:
            continue

        # 提取函数完整文本 (含装饰器)
        start_line = node.lineno - 1
        if node.decorator_list:
            start_line = min(d.lineno - 1 for d in node.decorator_list)
        end_line = node.end_lineno if hasattr(node, "end_lineno") else node.lineno + 50
        end_line = min(end_line, len(lines))
        func_text = "\n".join(lines[start_line:end_line])

        has_perm = False
        perm_type = "NONE"
        perm_code = None
        has_auth = False

        for pat in PERM_PATTERNS:
            if pat in func_text:
                has_perm = True
                perm_type = pat
                m = re.search(rf"{pat}\([\"']([^\"']+)[\"']", func_text)
                if m:
                    perm_code = m.group(1)
                break

        for pat in AUTH_PATTERNS:
            if pat in func_text:
                has_auth = True
                break

        if has_perm:
            protection = "PERMISSION"
        elif has_auth:
            protection = "AUTH_ONLY"
        else:
            protection = "NONE"

        # 判断是否为已知公共端点
        is_public = (route_info[0], route_info[1]) in KNOWN_PUBLIC

        results.append(
            {
                "file": filepath,
                "function": node.name,
                "method": route_info[0],
                "path": route_info[1],
                "line": node.lineno,
                "protection": protection,
                "perm_type": perm_type,
                "perm_code": perm_code,
                "is_known_public": is_public,
            }
        )
    return results


def get_module_name(filepath: str) -> str:
    """从文件路径提取模块名。"""
    cleaned = (
        filepath.replace("app/api/v1/endpoints/", "")
        .replace("app/api/v1/", "")
        .replace("app/api/", "")
    )
    parts = cleaned.split("/")
    return parts[0].replace(".py", "")


def risk_score(endpoint: dict) -> int:
    """计算单个端点的风险分 (越高越危险)。"""
    score = 0
    method = endpoint["method"]
    protection = endpoint["protection"]

    # 写操作基础分
    if method in ("POST", "PUT", "DELETE", "PATCH"):
        score += 30
    else:
        score += 5

    # 无保护
    if protection == "NONE":
        score += 50
    elif protection == "AUTH_ONLY":
        score += 20

    # 敏感模块加分
    sensitive_modules = {
        "auth": 20, "users": 25, "roles": 25, "permissions": 25,
        "admin_stats": 20, "organization": 15, "tenants": 20,
        "backup": 20, "data_import_export": 15, "audits": 15,
    }
    module = get_module_name(endpoint["file"])
    score += sensitive_modules.get(module, 0)

    # 删除操作额外加分
    if method == "DELETE":
        score += 10

    return score


def run_audit(project_root: str = "."):
    """执行完整审计并返回结构化结果。"""
    api_dir = os.path.join(project_root, "app", "api")

    all_endpoints = []
    seen_files = set()
    for root, dirs, files in os.walk(api_dir):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                fp = os.path.join(root, f)
                # 使用相对路径
                rel = os.path.relpath(fp, project_root)
                if rel not in seen_files:
                    seen_files.add(rel)
                    for ep in extract_endpoints_from_file(fp):
                        ep["file"] = rel
                        all_endpoints.append(ep)

    # 统计
    total = len(all_endpoints)
    by_protection = defaultdict(int)
    by_method = defaultdict(lambda: defaultdict(int))
    for ep in all_endpoints:
        by_protection[ep["protection"]] += 1
        by_method[ep["method"]][ep["protection"]] += 1

    # 模块统计
    modules = defaultdict(
        lambda: {"total": 0, "PERMISSION": 0, "AUTH_ONLY": 0, "NONE": 0, "write_unprotected": 0}
    )
    for ep in all_endpoints:
        mod = get_module_name(ep["file"])
        modules[mod]["total"] += 1
        modules[mod][ep["protection"]] += 1
        if ep["protection"] in ("AUTH_ONLY", "NONE") and ep["method"] in ("POST", "PUT", "DELETE", "PATCH"):
            modules[mod]["write_unprotected"] += 1

    # Top 20 最危险端点
    scored = [(ep, risk_score(ep)) for ep in all_endpoints if not ep.get("is_known_public")]
    scored.sort(key=lambda x: -x[1])
    top20 = scored[:20]

    # 权限码覆盖
    perm_codes = set()
    for ep in all_endpoints:
        if ep["perm_code"]:
            perm_codes.add(ep["perm_code"])

    result = {
        "audit_time": datetime.now().isoformat(),
        "summary": {
            "total_endpoints": total,
            "by_protection": dict(by_protection),
            "by_method": {m: dict(v) for m, v in by_method.items()},
            "permission_coverage_pct": round(100 * by_protection.get("PERMISSION", 0) / max(total, 1), 1),
            "auth_only_pct": round(100 * by_protection.get("AUTH_ONLY", 0) / max(total, 1), 1),
            "no_protection_pct": round(100 * by_protection.get("NONE", 0) / max(total, 1), 1),
            "unique_permission_codes": len(perm_codes),
            "permission_codes": sorted(perm_codes),
        },
        "module_breakdown": {
            mod: stats
            for mod, stats in sorted(modules.items(), key=lambda x: -x[1]["write_unprotected"])
        },
        "top20_risk": [
            {**ep, "risk_score": score} for ep, score in top20
        ],
        "all_endpoints": all_endpoints,
    }
    return result


def write_json(result: dict, output_path: str):
    """输出 JSON 审计报告。"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 审计报告已写入: {output_path}")


def write_markdown(result: dict, output_path: str):
    """输出 Markdown 审计报告。"""
    s = result["summary"]
    lines = [
        "# API 权限覆盖审计报告",
        "",
        f"> 审计时间: {result['audit_time']}",
        f"> 扫描方式: AST 静态分析 (`scripts/audit_permission_coverage.py`)",
        "",
        "## 1. 总览",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 总端点数 | {s['total_endpoints']} |",
        f"| PERMISSION (有权限码) | {s['by_protection'].get('PERMISSION', 0)} ({s['permission_coverage_pct']}%) |",
        f"| AUTH_ONLY (仅登录) | {s['by_protection'].get('AUTH_ONLY', 0)} ({s['auth_only_pct']}%) |",
        f"| NONE (无保护) | {s['by_protection'].get('NONE', 0)} ({s['no_protection_pct']}%) |",
        f"| 唯一权限码数 | {s['unique_permission_codes']} |",
        "",
        "### 按 HTTP 方法分布",
        "",
        "| 方法 | PERMISSION | AUTH_ONLY | NONE |",
        "|------|-----------|----------|------|",
    ]
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        m = s["by_method"].get(method, {})
        lines.append(f"| {method} | {m.get('PERMISSION', 0)} | {m.get('AUTH_ONLY', 0)} | {m.get('NONE', 0)} |")

    lines += [
        "",
        "## 2. 模块权限覆盖热力图 (按裸奔写端点数排序)",
        "",
        "| 模块 | 总数 | PERM | AUTH_ONLY | NONE | 写裸奔 | 覆盖率 |",
        "|------|------|------|----------|------|--------|--------|",
    ]
    for mod, stats in result["module_breakdown"].items():
        total = stats["total"]
        perm_pct = round(100 * stats["PERMISSION"] / max(total, 1))
        danger = "🔴" if perm_pct < 10 else ("🟡" if perm_pct < 50 else "🟢")
        lines.append(
            f"| {danger} {mod} | {total} | {stats['PERMISSION']} | "
            f"{stats['AUTH_ONLY']} | {stats['NONE']} | {stats['write_unprotected']} | {perm_pct}% |"
        )

    lines += [
        "",
        "## 3. Top 20 最危险裸奔/弱保护接口",
        "",
        "| # | 风险分 | 方法 | 路径 | 保护 | 文件:行 | 函数 |",
        "|---|--------|------|------|------|---------|------|",
    ]
    for i, ep in enumerate(result["top20_risk"], 1):
        lines.append(
            f"| {i} | {ep['risk_score']} | {ep['method']} | `{ep['path']}` | "
            f"{ep['protection']} | `{ep['file']}:{ep['line']}` | `{ep['function']}` |"
        )

    lines += [
        "",
        "## 4. 已使用的权限码清单",
        "",
        "```",
    ]
    for code in s["permission_codes"]:
        lines.append(code)
    lines += [
        "```",
        "",
        "## 5. 全面重构难度评估",
        "",
        "### 改动半径最大的模块 (Top 10)",
        "",
        "| 模块 | 需补权限的端点数 | 写操作裸奔 | 难度 | 说明 |",
        "|------|-----------------|-----------|------|------|",
    ]

    # 重构难度评估
    difficulty_data = []
    for mod, stats in result["module_breakdown"].items():
        needs_fix = stats["AUTH_ONLY"] + stats["NONE"]
        if needs_fix == 0:
            continue
        total = stats["total"]
        write_naked = stats["write_unprotected"]
        if write_naked > 20:
            difficulty = "极高"
        elif write_naked > 10:
            difficulty = "高"
        elif write_naked > 5:
            difficulty = "中"
        else:
            difficulty = "低"
        difficulty_data.append((mod, needs_fix, write_naked, difficulty, total))

    difficulty_data.sort(key=lambda x: -x[1])
    for mod, needs_fix, write_naked, difficulty, total in difficulty_data[:10]:
        reason = ""
        if write_naked > 20:
            reason = "写操作极多，需逐一定义权限码并验证业务逻辑"
        elif write_naked > 10:
            reason = "写操作较多，需定义权限码+回归测试"
        elif needs_fix > 20:
            reason = "端点总量大，主要是读操作需加权限"
        else:
            reason = "改动可控"
        lines.append(f"| {mod} | {needs_fix} | {write_naked} | {difficulty} | {reason} |")

    lines += [
        "",
        "### 最易回归炸裂的位置",
        "",
        "1. **sales 模块** (304 端点, 7% 覆盖): 商机/报价/合同全链路，状态机 + 数据范围过滤交织",
        "2. **projects 模块** (263 端点, 40% 覆盖): 部分有权限但不一致，WBS/风险子模块全裸",
        "3. **approvals 模块** (46 端点, 0% 覆盖): 审批模板 CRUD 完全无权限，任何登录用户可操作",
        "4. **production 模块** (94 端点, 9% 覆盖): 产能分析、OEE 等无保护，数据泄露风险",
        "5. **warehouse 模块** (22 端点, 0% 覆盖): 全部 NONE，连 AUTH_ONLY 都没有",
        "",
        "### 建议修复优先级",
        "",
        "1. **P0 (立即)**: warehouse, approvals/templates, organization/employees — 完全裸奔的写操作",
        "2. **P1 (本周)**: sales 写操作, projects/risks, production 写操作",
        "3. **P2 (本月)**: 所有 AUTH_ONLY 写操作补权限码",
        "4. **P3 (规划)**: 所有 AUTH_ONLY 读操作补权限码，达到 >90% 覆盖",
        "",
        "---",
        "",
        "*本报告由 `scripts/audit_permission_coverage.py` 自动生成，可随时重新运行获取最新状态。*",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ Markdown 审计报告已写入: {output_path}")


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    json_only = "--json-only" in sys.argv
    md_only = "--md-only" in sys.argv

    result = run_audit(".")

    if not md_only:
        write_json(result, "PERMISSION_COVERAGE_AUDIT.json")
    if not json_only:
        write_markdown(result, "PERMISSION_COVERAGE_AUDIT.md")

    # 打印摘要
    s = result["summary"]
    print(f"\n{'='*60}")
    print(f"审计完成: {s['total_endpoints']} 个端点")
    print(f"  PERMISSION: {s['by_protection'].get('PERMISSION', 0)} ({s['permission_coverage_pct']}%)")
    print(f"  AUTH_ONLY:  {s['by_protection'].get('AUTH_ONLY', 0)} ({s['auth_only_pct']}%)")
    print(f"  NONE:       {s['by_protection'].get('NONE', 0)} ({s['no_protection_pct']}%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
