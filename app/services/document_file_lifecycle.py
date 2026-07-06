# -*- coding: utf-8 -*-
"""Project document file lifecycle helpers."""

from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy.orm import Session

from app.models.project import ProjectDocument


def _resolve_inside_upload_dir(file_path: str, upload_dir: Path) -> Optional[Path]:
    path = Path(file_path)
    if not path.is_absolute():
        path = upload_dir / path

    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(upload_dir.resolve())
    except ValueError:
        return None
    return resolved_path


def _iter_referenced_file_paths(db: Session, upload_dir: Path) -> set[Path]:
    referenced: set[Path] = set()
    for document in db.query(ProjectDocument).all():
        file_path = getattr(document, "file_path", None)
        if not file_path:
            continue

        resolved_path = _resolve_inside_upload_dir(str(file_path), upload_dir)
        if resolved_path:
            referenced.add(resolved_path)
    return referenced


def scan_project_document_orphans(
    db: Session,
    upload_dir: Union[str, Path],
    *,
    delete: bool = False,
) -> dict[str, Any]:
    """
    Scan files under the project document upload directory and find files that
    are not referenced by any project_documents.file_path row.
    """
    root = Path(upload_dir).resolve()
    if not root.exists():
        return {
            "upload_dir": str(root),
            "scanned_count": 0,
            "referenced_count": 0,
            "orphan_count": 0,
            "deleted_count": 0,
            "orphans": [],
            "deleted": [],
        }

    referenced_paths = _iter_referenced_file_paths(db, root)
    scanned_files = sorted(path.resolve() for path in root.rglob("*") if path.is_file())
    orphan_paths = [path for path in scanned_files if path not in referenced_paths]

    deleted_paths: list[Path] = []
    if delete:
        for orphan_path in orphan_paths:
            if orphan_path.is_file():
                orphan_path.unlink()
                deleted_paths.append(orphan_path)

    return {
        "upload_dir": str(root),
        "scanned_count": len(scanned_files),
        "referenced_count": len(referenced_paths),
        "orphan_count": len(orphan_paths),
        "deleted_count": len(deleted_paths),
        "orphans": [str(path) for path in orphan_paths],
        "deleted": [str(path) for path in deleted_paths],
    }
