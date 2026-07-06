# -*- coding: utf-8 -*-
"""ADMIN-19: project_documents 附件孤儿文件扫描与清理。"""

from types import SimpleNamespace
from unittest.mock import MagicMock


def _db_with_documents(file_paths):
    db = MagicMock()
    db.query.return_value.all.return_value = [
        SimpleNamespace(file_path=file_path) for file_path in file_paths
    ]
    return db


def test_scan_project_document_orphans_reports_unreferenced_files(tmp_path):
    from app.services.document_file_lifecycle import scan_project_document_orphans

    referenced = tmp_path / "project-a" / "kept.pdf"
    orphan = tmp_path / "project-a" / "orphan.pdf"
    referenced.parent.mkdir()
    referenced.write_bytes(b"kept")
    orphan.write_bytes(b"orphan")

    db = _db_with_documents(["project-a/kept.pdf", "/demo/fake.pdf"])

    result = scan_project_document_orphans(db, tmp_path)

    assert result["scanned_count"] == 2
    assert result["orphan_count"] == 1
    assert result["deleted_count"] == 0
    assert result["orphans"] == [str(orphan)]
    assert orphan.exists()


def test_cleanup_project_document_orphans_deletes_only_unreferenced_files(tmp_path):
    from app.services.document_file_lifecycle import scan_project_document_orphans

    referenced = tmp_path / "project-b" / "kept.pdf"
    orphan = tmp_path / "project-b" / "orphan.pdf"
    referenced.parent.mkdir()
    referenced.write_bytes(b"kept")
    orphan.write_bytes(b"orphan")

    db = _db_with_documents(["project-b/kept.pdf"])

    result = scan_project_document_orphans(db, tmp_path, delete=True)

    assert result["orphan_count"] == 1
    assert result["deleted_count"] == 1
    assert referenced.exists()
    assert not orphan.exists()
