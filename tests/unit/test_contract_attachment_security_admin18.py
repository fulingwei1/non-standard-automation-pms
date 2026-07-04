# -*- coding: utf-8 -*-
"""ADMIN-18: contract attachment downloads must stay inside upload root."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.sales.contracts.enhanced import (
    download_attachment as legacy_download_attachment,
)
from app.api.v1.endpoints.sales.contracts.enhanced_attachments import (
    download_attachment as split_download_attachment,
)
from app.core.config import settings


def _db_with_attachment(file_path: str):
    attachment = SimpleNamespace(
        id=1,
        file_path=file_path,
        file_name="contract.pdf",
        file_type="application/pdf",
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = attachment
    return db


@pytest.mark.parametrize(
    "download_func",
    [split_download_attachment, legacy_download_attachment],
)
def test_contract_attachment_download_rejects_absolute_path_outside_upload_dir(
    download_func,
    tmp_path,
    monkeypatch,
):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    with pytest.raises(HTTPException) as exc:
        download_func(1, db=_db_with_attachment(str(secret_file)), current_user=object())

    assert exc.value.status_code == 403


@pytest.mark.parametrize(
    "download_func",
    [split_download_attachment, legacy_download_attachment],
)
def test_contract_attachment_download_allows_file_inside_upload_dir(
    download_func,
    tmp_path,
    monkeypatch,
):
    upload_dir = tmp_path / "uploads"
    contract_dir = upload_dir / "contracts"
    contract_dir.mkdir(parents=True)
    attachment_file = contract_dir / "contract.pdf"
    attachment_file.write_text("ok", encoding="utf-8")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    response = download_func(
        1,
        db=_db_with_attachment("contracts/contract.pdf"),
        current_user=object(),
    )

    assert response.path == str(attachment_file.resolve())
