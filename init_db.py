#!/usr/bin/env python3
import runpy
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root))
    runpy.run_path(str(repo_root / "scripts" / "init_db.py"), run_name="__main__")


if __name__ == "__main__":
    main()
