# -*- coding: utf-8 -*-
"""Shared path checks for sales contract attachments."""

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings


def resolve_contract_attachment_path(file_path: str) -> Path:
    if not file_path:
        raise HTTPException(status_code=404, detail="附件文件不存在")

    upload_root = Path(settings.UPLOAD_DIR).expanduser().resolve()
    raw_path = Path(file_path).expanduser()
    if raw_path.is_absolute():
        candidate = raw_path.resolve()
    elif raw_path.parts and raw_path.parts[0] == upload_root.name:
        candidate = (upload_root.parent / raw_path).resolve()
    else:
        candidate = (upload_root / raw_path).resolve()

    try:
        candidate.relative_to(upload_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return candidate
