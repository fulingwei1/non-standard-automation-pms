#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan or clean files under uploads/documents that project_documents no longer reference."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session  # noqa: E402
from app.services.document_file_lifecycle import scan_project_document_orphans  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upload-dir",
        default=os.environ.get("UPLOAD_DIR", str(Path("uploads"))) + "/documents",
        help="Project document upload directory. Defaults to UPLOAD_DIR/documents or uploads/documents.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete orphan files. Omit for dry-run scan only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with get_db_session() as db:
        result = scan_project_document_orphans(
            db,
            args.upload_dir,
            delete=args.delete,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
