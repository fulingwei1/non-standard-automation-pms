#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 守卫：AI 输出写库必须过 mock 检测闸。

审计共性根因：AI mock 降级无标记静默污染真数据（演示方案以 0.8 置信度入库）。
项目规范：任何"调 AI（generate_solution）且把结果写库（db/session.add）"的文件，
必须引用 is_mock_response（或登记在基线豁免清单，注明理由）。

基线维护：python scripts/ci_guard_ai_mock.py --update-baseline
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
BASELINE_FILE = ROOT / "scripts" / "ai_mock_guard_baseline.json"

AI_CALL = re.compile(r"\.generate_solution\s*\(")
DB_WRITE = re.compile(r"\b(?:db|session|self\.db)\.(?:add|add_all|bulk_save_objects)\s*\(")
GUARD = re.compile(r"is_mock_response|-mock")


def find_unguarded() -> list:
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("app/tests/") or rel == "app/services/ai_client_service.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if AI_CALL.search(text) and DB_WRITE.search(text) and not GUARD.search(text):
            offenders.append(rel)
    return sorted(offenders)


def main() -> int:
    offenders = find_unguarded()

    if "--update-baseline" in sys.argv:
        BASELINE_FILE.write_text(json.dumps({"exempt": offenders}, indent=2) + "\n")
        print(f"基线已更新: {len(offenders)} 个既有豁免")
        return 0

    exempt = set(json.loads(BASELINE_FILE.read_text())["exempt"]) if BASELINE_FILE.exists() else set()
    new_offenders = [o for o in offenders if o not in exempt]
    resolved = [e for e in exempt if e not in offenders]

    print(f"AI 写库未过 mock 闸: 当前 {len(offenders)}，豁免基线 {len(exempt)}")
    if resolved:
        print(f"ℹ️ 已治理 {len(resolved)} 个（可运行 --update-baseline 收紧）")
    if new_offenders:
        print("❌ 新增违规（调 AI 且写库但未引用 is_mock_response）:")
        for o in new_offenders:
            print(f"  - {o}")
        print("修复：写库前调用 app.services.ai_client_service.is_mock_response 把关，")
        print("或（确属误报）--update-baseline 登记豁免并在 PR 说明理由。")
        return 1
    print("✅ AI mock 门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
