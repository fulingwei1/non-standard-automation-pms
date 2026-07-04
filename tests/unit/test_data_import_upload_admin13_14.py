# -*- coding: utf-8 -*-
"""ADMIN-13/14: data import upload task persistence and error receipts."""

import io
from types import SimpleNamespace
from unittest.mock import patch

from app.api.v1.endpoints.data_import_export.import_upload import upload_and_import_data


class _UploadFile:
    filename = "projects.xlsx"

    def __init__(self, content: bytes = b"excel bytes"):
        self.file = io.BytesIO(content)


class _RecordingSession:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, obj):
        obj.id = len(self.added) + 1
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_upload_import_persists_real_task_fields_and_returns_failed_rows():
    db = _RecordingSession()
    failed_rows = [{"row_index": 3, "error": "project code is required"}]

    with patch(
        "app.api.v1.endpoints.data_import_export.import_upload.ImportExportEngine.import_data",
        return_value={
            "imported_count": 2,
            "updated_count": 1,
            "failed_count": 1,
            "failed_rows": failed_rows,
        },
    ) as import_data:
        response = upload_and_import_data(
            db=db,
            file=_UploadFile(),
            template_type="project",
            update_existing=True,
            current_user=SimpleNamespace(id=7),
        )

    import_data.assert_called_once()
    assert db.commits == 1
    assert db.rollbacks == 0
    assert len(db.added) == 1

    task = db.added[0]
    assert task.task_no.startswith("IMP-")
    assert task.import_type == "PROJECT"
    assert task.file_name == "projects.xlsx"
    assert task.file_size == len(b"excel bytes")
    assert task.imported_by == 7
    assert task.status == "PARTIAL"
    assert task.success_rows == 3
    assert task.failed_rows == 1
    assert task.validation_errors == failed_rows
    assert "project code is required" in task.error_message

    assert response.task_id == 1
    assert response.status == "PARTIAL"
    assert response.imported_count == 2
    assert response.updated_count == 1
    assert response.failed_count == 1
    assert response.failed_rows == failed_rows
