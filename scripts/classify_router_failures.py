#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据启动日志中的路由失败项，输出修复优先级建议。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

CRITICAL_PREFIXES = {
    "auth",
    "users",
    "roles",
    "permissions",
    "projects",
    "sales",
    "production",
    "timesheet",
    "approvals",
    "customers",
    "suppliers",
    "materials",
    "purchase",
    "bom",
    "inventory",
    "shortage",
    "acceptance",
    "warehouse",
    "notifications",
    "issues",
    "scheduler",
    "service",
    "itr",
    "tenants",
    "dashboard",
    "report",
}

WARNING_CANDIDATES = {
    "culture-wall",
    "culture-wall-config",
    "pitfalls",
    "lessons",
    "pm-involvement",
    "project-contributions",
    "presale-mobile",
    "presale-ai-requirement",
    "presale-analytics",
    "solution-credits",
    "management-rhythm",
    "kit-check",
    "ai-strategy",
    "business-support",
    "business-support-orders",
}


KEY_RE = re.compile(r"关键模块加载失败\[([^\]]+)\]")


def extract_keys(text: str) -> list[str]:
    keys = KEY_RE.findall(text)
    # 去重保序
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def is_critical(key: str) -> bool:
    # 允许 key 形如 customers/suppliers、materials/purchase/bom
    parts = [p.strip() for p in key.split("/") if p.strip()]
    return any(p in CRITICAL_PREFIXES for p in parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", nargs="?", help="日志文件路径；不传则读取标准输入")
    args = parser.parse_args()

    if args.log:
        text = Path(args.log).read_text(encoding="utf-8", errors="ignore")
    else:
        import sys

        text = sys.stdin.read()

    keys = extract_keys(text)
    if not keys:
        print("未检测到关键模块失败键（格式：关键模块加载失败[xxx]）")
        return 0

    hard_fix: list[str] = []
    can_warn: list[str] = []
    unknown: list[str] = []

    for k in keys:
        if is_critical(k):
            hard_fix.append(k)
        elif k in WARNING_CANDIDATES:
            can_warn.append(k)
        else:
            unknown.append(k)

    print("=== 路由失败分层建议 ===")
    print(f"总失败项: {len(keys)}")

    print("\n[必须修复（保留 fail-fast）]")
    if hard_fix:
        for k in hard_fix:
            print(f"- {k}")
    else:
        print("- 无")

    print("\n[可临时降级 warning]")
    if can_warn:
        for k in can_warn:
            print(f"- {k}")
    else:
        print("- 无")

    print("\n[待人工判断]")
    if unknown:
        for k in unknown:
            print(f"- {k}")
    else:
        print("- 无")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
