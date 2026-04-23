#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
PYTHON = REPO / "venv/bin/python"
TEST_ROOT = REPO / "tests"
TIMEOUT_SECONDS = 28


def iter_test_files() -> list[Path]:
    files = [
        p for p in TEST_ROOT.rglob("test_*.py") if "_obsolete" not in p.parts and p.is_file()
    ]

    def key(p: Path):
        rel = p.relative_to(REPO)
        parts = rel.parts
        if len(parts) >= 2:
            top = parts[1]
        else:
            top = ""
        if top == "unit" and len(parts) == 3:
            weight = 5
        elif top == "api":
            weight = 10
        elif top == "integration":
            weight = 20
        elif top in {"e2e", "performance", "scenarios"}:
            weight = 30
        else:
            weight = 15
        return (weight, str(rel))

    return sorted(files, key=key)


def initial_batch_size(path: Path) -> int:
    rel = path.relative_to(REPO)
    top = rel.parts[1] if len(rel.parts) >= 2 else ""
    if top == "unit" and len(rel.parts) == 3:
        return 25
    if top == "api":
        return 10
    if top == "integration":
        return 8
    if top in {"e2e", "performance", "scenarios"}:
        return 4
    return 12


def batched(files: list[Path]) -> list[list[Path]]:
    batches: list[list[Path]] = []
    current: list[Path] = []
    current_limit = None
    for f in files:
        limit = initial_batch_size(f)
        if not current:
            current = [f]
            current_limit = limit
            continue
        if limit != current_limit or len(current) >= current_limit:
            batches.append(current)
            current = [f]
            current_limit = limit
        else:
            current.append(f)
    if current:
        batches.append(current)
    return batches


def summarize_output(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "(no output)"
    keep = []
    for line in lines[-12:]:
        if any(token in line.lower() for token in ["passed", "failed", "error", "warning", "skipped", "xfailed", "interrupted"]):
            keep.append(line)
    return " | ".join(keep[-4:] or lines[-4:])


def run_files(files: list[Path], depth: int = 0) -> None:
    rels = [str(p.relative_to(REPO)) for p in files]
    label = f"{rels[0]} .. {rels[-1]}" if len(rels) > 1 else rels[0]
    print(f"\n=== batch depth={depth} files={len(files)} :: {label}", flush=True)
    cmd = [
        str(PYTHON),
        "-m",
        "coverage",
        "run",
        "--parallel-mode",
        "-m",
        "pytest",
        *rels,
        "--tb=no",
        "-q",
    ]
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        elapsed = time.time() - started
        summary = summarize_output(proc.stdout + "\n" + proc.stderr)
        print(f"exit={proc.returncode} elapsed={elapsed:.1f}s :: {summary}", flush=True)
    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - started
        print(f"timeout after {elapsed:.1f}s for {len(files)} files", flush=True)
        if len(files) == 1:
            print(f"single-file timeout skipped: {rels[0]}", flush=True)
            return
        mid = len(files) // 2
        run_files(files[:mid], depth + 1)
        run_files(files[mid:], depth + 1)


def main() -> int:
    os.chdir(REPO)
    all_files = iter_test_files()
    print(f"repo={REPO}", flush=True)
    print(f"test_files={len(all_files)}", flush=True)
    subprocess.run([str(PYTHON), "-m", "coverage", "erase"], cwd=REPO, check=False)

    for idx, batch in enumerate(batched(all_files), start=1):
        print(f"\n##### seed batch {idx}/{len(batched(all_files))} #####", flush=True)
        run_files(batch)

    print("\n=== combining coverage ===", flush=True)
    subprocess.run([str(PYTHON), "-m", "coverage", "combine"], cwd=REPO, check=False)
    print("\n=== coverage report ===", flush=True)
    subprocess.run([str(PYTHON), "-m", "coverage", "report"], cwd=REPO, check=False)
    print("\n=== coverage json ===", flush=True)
    subprocess.run(
        [str(PYTHON), "-m", "coverage", "json", "-o", "coverage_batched_full.json"],
        cwd=REPO,
        check=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
