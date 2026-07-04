#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 守卫：权限覆盖率棘轮（只许升不许降）。

复用 scripts/audit_permission_coverage.py 的静态扫描，对比
scripts/permission_coverage_baseline.json 基线：
- NONE（裸奔）端点数不得超过基线；
- PERMISSION 覆盖率不得低于基线。
覆盖率提升后请同步收紧基线（棘轮）：python scripts/ci_guard_permission_coverage.py --update-baseline
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = ROOT / "scripts" / "permission_coverage_baseline.json"
AUDIT_JSON = ROOT / "PERMISSION_COVERAGE_AUDIT.json"


def run_audit() -> dict:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_permission_coverage.py"), "--json-only"],
        check=True,
        cwd=ROOT,
        capture_output=True,
    )
    summary = json.loads(AUDIT_JSON.read_text())["summary"]
    total = summary["total_endpoints"]
    by_protection = summary["by_protection"]
    none_count = by_protection.get("NONE", 0)
    perm_count = by_protection.get("PERMISSION", 0)
    return {
        "total": total,
        "none": none_count,
        "permission_pct": round(perm_count / total * 100, 1) if total else 0.0,
    }


def main() -> int:
    current = run_audit()

    if "--update-baseline" in sys.argv:
        BASELINE_FILE.write_text(
            json.dumps(
                {"max_none": current["none"], "min_permission_pct": current["permission_pct"]},
                indent=2,
            )
            + "\n"
        )
        print(f"基线已更新: {current}")
        return 0

    baseline = json.loads(BASELINE_FILE.read_text())
    failures = []
    if current["none"] > baseline["max_none"]:
        failures.append(
            f"NONE 端点数回退: {current['none']} > 基线 {baseline['max_none']}（新增了无认证端点）"
        )
    if current["permission_pct"] < baseline["min_permission_pct"]:
        failures.append(
            f"权限覆盖率回退: {current['permission_pct']}% < 基线 {baseline['min_permission_pct']}%"
        )

    print(f"权限覆盖: {current}（基线 {baseline}）")
    if failures:
        print("❌ 权限覆盖门禁失败:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("✅ 权限覆盖门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
