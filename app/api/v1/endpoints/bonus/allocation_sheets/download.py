# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 文件下载
"""
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.bonus import BonusAllocationSheet
from app.models.user import User

router = APIRouter()


@router.get("/allocation-sheets/{sheet_id}/download", response_class=FileResponse)
def download_allocation_sheet(
    *,
    db: Session = Depends(deps.get_db),
    sheet_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载已上传的分配明细表Excel文件，便于复核和留档
    """
    sheet = db.query(BonusAllocationSheet).filter(BonusAllocationSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="分配明细表不存在")

    if not sheet.file_path:
        raise HTTPException(status_code=404, detail="明细表文件不存在")

    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, sheet.file_path))
    if not file_path.startswith(upload_dir):
        raise HTTPException(status_code=400, detail="文件路径非法，拒绝下载")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除或不存在")

    filename = sheet.file_name or os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
