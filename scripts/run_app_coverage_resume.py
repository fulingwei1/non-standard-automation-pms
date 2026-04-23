#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PYTHON = REPO / "venv/bin/python"
TEST_ROOT = REPO / "tests"
STATE_PATH = REPO / ".coverage_app_state.json"
DATA_FILE = REPO / ".coverage.appbatched"
TIMEOUT_SECONDS = 28


def iter_test_files() -> list[Path]:
    files = [
        p for p in TEST_ROOT.rglob("test_*.py") if p.is_file() and "_obsolete" not in p.parts
    ]

    def key(p: Path):
        rel = p.relative_to(REPO)
        top = rel.parts[1] if len(rel.parts) >= 2 else ""
        if top == "unit" and len(rel.parts) == 3:
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
    current_limit: int | None = None
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
    keep: list[str] = []
    for line in lines[-20:]:
        if any(token in line.lower() for token in ["passed", "failed", "error", "warning", "skipped", "xfailed", "interrupted"]):
            keep.append(line)
    return " | ".join(keep[-4:] or lines[-4:])


def load_state(total_batches: int) -> dict:
    if STATE_PATH.exists():
        data = json.loads(STATE_PATH.read_text())
    else:
        data = {
            "data_file": str(DATA_FILE.name),
            "total_batches": total_batches,
            "completed_batches": [],
            "started_at": time.time(),
            "updated_at": time.time(),
        }
    data["total_batches"] = total_batches
    data.setdefault("completed_batches", [])
    data.setdefault("skipped_single_file_timeouts", [])
    data.setdefault("failures", [])
    return data


def save_state(state: dict) -> None:
    state["updated_at"] = time.time()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def coverage_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["COVERAGE_FILE"] = str(DATA_FILE)
    return env


def run_files(files: list[Path], state: dict, depth: int = 0) -> None:
    rels = [str(p.relative_to(REPO)) for p in files]
    label = f"{rels[0]} .. {rels[-1]}" if len(rels) > 1 else rels[0]
    print(f"\n=== batch depth={depth} files={len(files)} :: {label}", flush=True)
    cmd = [
        str(PYTHON),
        "-m",
        "coverage",
        "run",
        "--source=app",
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
            env=coverage_env(),
        )
        elapsed = time.time() - started
        summary = summarize_output(proc.stdout + "\n" + proc.stderr)
        print(f"exit={proc.returncode} elapsed={elapsed:.1f}s :: {summary}", flush=True)
        if proc.returncode != 0:
            state["failures"].append({"files": rels, "summary": summary, "depth": depth})
            if len(state["failures"]) > 300:
                state["failures"] = state["failures"][-300:]
            save_state(state)
    except subprocess.TimeoutExpired:
        elapsed = time.time() - started
        print(f"timeout after {elapsed:.1f}s for {len(files)} files", flush=True)
        if len(files) == 1:
            print(f"single-file timeout skipped: {rels[0]}", flush=True)
            state["skipped_single_file_timeouts"].append(rels[0])
            save_state(state)
            return
        mid = len(files) // 2
        run_files(files[:mid], state, depth + 1)
        run_files(files[mid:], state, depth + 1)


def main() -> int:
    os.chdir(REPO)
    all_files = iter_test_files()
    batches = batched(all_files)
    state = load_state(len(batches))

    if not STATE_PATH.exists():
        subprocess.run(
            [str(PYTHON), "-m", "coverage", "erase"],
            cwd=REPO,
            check=False,
            env=coverage_env(),
        )

    completed = set(state["completed_batches"])
    print(f"repo={REPO}", flush=True)
    print(f"test_files={len(all_files)}", flush=True)
    print(f"seed_batches={len(batches)}", flush=True)
    print(f"resume_completed={len(completed)}", flush=True)

    for idx, batch in enumerate(batches, start=1):
        if idx in completed:
            continue
        print(f"\n##### seed batch {idx}/{len(batches)} #####", flush=True)
        run_files(batch, state)
        completed.add(idx)
        state["completed_batches"] = sorted(completed)
        save_state(state)

    print("\n=== combining coverage ===", flush=True)
    subprocess.run(
        [str(PYTHON), "-m", "coverage", "combine"],
        cwd=REPO,
        check=False,
        env=coverage_env(),
    )
    print("\n=== app coverage report ===", flush=True)
    subprocess.run(
        [str(PYTHON), "-m", "coverage", "report", "--include=app/*"],
        cwd=REPO,
        check=False,
        env=coverage_env(),
    )
    print("\n=== app coverage json ===", flush=True)
    subprocess.run(
        [
            str(PYTHON),
            "-m",
            "coverage",
            "json",
            "--include=app/*",
            "-o",
            "coverage_app_batched.json",
        ],
        cwd=REPO,
        check=False,
        env=coverage_env(),
    )
    state["finished_at"] = time.time()
    save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
