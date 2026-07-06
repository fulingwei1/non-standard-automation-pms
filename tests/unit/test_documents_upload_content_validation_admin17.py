# -*- coding: utf-8 -*-
"""ADMIN-17: 文档上传入口必须使用统一内容校验。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.documents import crud_refactored


class FakeUploadFile:
    filename = "fake.pdf"
    content_type = "application/pdf"

    async def read(self):
        return b"MZ\x90\x00not-a-real-pdf"


@pytest.mark.asyncio
async def test_upload_project_document_rejects_mismatched_pdf_content():
    db = MagicMock()
    current_user = SimpleNamespace(id=99)

    with (
        patch.object(crud_refactored, "get_or_404", return_value=SimpleNamespace(id=1)),
        patch.object(crud_refactored.FileUploadService, "save_file") as save_file,
        patch.object(crud_refactored, "_build_document_response", return_value={}),
        patch.object(crud_refactored, "success_response", return_value={"ok": True}),
    ):
        save_file.return_value = ("/tmp/fake.pdf", "1/fake.pdf")
        with pytest.raises(HTTPException) as exc:
            await crud_refactored.upload_document_file(
                db=db,
                project_id=1,
                file=FakeUploadFile(),
                machine_id=None,
                doc_type="DESIGN",
                doc_category=None,
                doc_name=None,
                doc_no=None,
                version="1.0",
                description=None,
                current_user=current_user,
            )

    assert exc.value.status_code == 400
    assert "文件内容与扩展名不匹配" in str(exc.value.detail)
    save_file.assert_not_called()
