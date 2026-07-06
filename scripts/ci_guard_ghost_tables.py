#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 守卫：幽灵表检测（有模型无业务写入方）。

审计共性发现：ShortageDailyReport 等模型定义完整但全仓零写入，
消费方以为功能存在实为断链。本守卫静态扫描：
- 收集 app/models 下所有 ORM 模型类名；
- 在 app/（排除 models/tests/migrations）里查找构造调用 `ClassName(`、
  `bulk_insert`, 或 `INSERT INTO tablename`；
- 将 scripts/import_*.py 与 scripts/enrich_*.py 视为生产主数据写入口径；
- 无任何写入证据的模型 = 幽灵候选；仅当出现**基线之外的新幽灵**时失败。
基线维护：python scripts/ci_guard_ghost_tables.py --update-baseline
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "app" / "models"
APP_DIR = ROOT / "app"
SCRIPTS_DIR = ROOT / "scripts"
BASELINE_FILE = ROOT / "scripts" / "ghost_tables_baseline.json"
SCRIPT_WRITE_GLOBS = ("import_*.py", "enrich_*.py")


def collect_models() -> dict:
    """{类名: 表名}"""
    models = {}
    for path in MODELS_DIR.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            tablename = None
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == "__tablename__" for t in stmt.targets
                    )
                    and isinstance(stmt.value, ast.Constant)
                ):
                    tablename = stmt.value.value
            if tablename:
                models[node.name] = tablename
    return models


def _iter_write_evidence_paths():
    for path in APP_DIR.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(("app/models/", "app/tests/")):
            continue
        yield path

    for pattern in SCRIPT_WRITE_GLOBS:
        yield from SCRIPTS_DIR.glob(pattern)


def collect_write_evidence() -> str:
    chunks = []
    seen = set()
    for path in _iter_write_evidence_paths():
        if path in seen:
            continue
        seen.add(path)
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(chunks)


def find_ghosts() -> list:
    models = collect_models()
    corpus = collect_write_evidence()
    ghosts = []
    for cls, table in sorted(models.items()):
        has_ctor = re.search(rf"\b{re.escape(cls)}\s*\(", corpus)
        has_sql = re.search(rf"INSERT(?:\s+OR\s+REPLACE)?\s+INTO {re.escape(table)}\b", corpus, re.I)
        if not has_ctor and not has_sql:
            ghosts.append(f"{cls}({table})")
    return ghosts


def main() -> int:
    ghosts = find_ghosts()

    if "--update-baseline" in sys.argv:
        BASELINE_FILE.write_text(json.dumps({"known_ghosts": ghosts}, indent=2) + "\n")
        print(f"基线已更新: {len(ghosts)} 个已知幽灵表")
        return 0

    known = set(json.loads(BASELINE_FILE.read_text())["known_ghosts"]) if BASELINE_FILE.exists() else set()
    new_ghosts = [g for g in ghosts if g not in known]
    resolved = [g for g in known if g not in ghosts]

    print(f"幽灵表: 当前 {len(ghosts)}，基线 {len(known)}")
    if resolved:
        print(f"ℹ️ 已消除 {len(resolved)} 个（可运行 --update-baseline 收紧）: {resolved[:5]}")
    if new_ghosts:
        print("❌ 新增幽灵表（有模型无业务写入方，请补写入口径或不要提交模型）:")
        for g in new_ghosts:
            print(f"  - {g}")
        return 1
    print("✅ 幽灵表门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
