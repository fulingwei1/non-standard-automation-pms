# -*- coding: utf-8 -*-
"""ADMIN-19: 删除文档记录时同步清理上传目录内的附件文件。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.api.v1.endpoints.documents import operations


def test_delete_document_removes_uploaded_file(tmp_path, monkeypatch):
    monkeypatch.setattr(operations, "DOCUMENT_UPLOAD_DIR", tmp_path)
    uploaded_file = tmp_path / "projects" / "quote.pdf"
    uploaded_file.parent.mkdir()
    uploaded_file.write_bytes(b"contract attachment")

    document = SimpleNamespace(id=1, project_id=None, file_path="projects/quote.pdf")
    db = MagicMock()

    with patch.object(operations, "get_or_404", return_value=document):
        response = operations.delete_document(db=db, doc_id=1, current_user=MagicMock())

    assert response.code == 200
    assert not uploaded_file.exists()
    db.delete.assert_called_once_with(document)
    db.commit.assert_called_once()
