# -*- coding: utf-8 -*-
"""
报表生成 - 下载功能
"""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.report_center import ReportGeneration
from app.models.user import User

router = APIRouter()


@router.get("/download/{report_id}")
def download_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("report:read")),
):
    """
    下载已导出的报表文件
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == report_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="报表不存在")

    if not generation.export_path:
        raise HTTPException(status_code=404, detail="报表文件不存在，请先导出")

    # 安全检查：验证文件路径在允许的目录内
    export_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "reports"))
    file_path = os.path.abspath(generation.export_path)

    if not file_path.startswith(export_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="报表文件不存在，请先导出")

    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)

    # 设置 MIME 类型
    media_type_map = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')

    # 生成下载文件名
    filename = f"{generation.report_title or 'report'}_{generation.id}{ext}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.get("/download-file")
def download_file(
    *,
    path: str = Query(..., description="文件路径（相对于报表目录）"),
    current_user: User = Depends(security.require_permission("report:read")),
):
    """
    直接下载文件（仅限报表目录内的文件）

    安全限制：只允许下载 UPLOAD_DIR/reports 目录下的文件
    """
    # 安全检查：只允许访问报表目录
    export_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "reports"))
    os.makedirs(export_dir, exist_ok=True)

    # 将用户输入视为相对路径，拼接到报表目录
    file_path = os.path.abspath(os.path.join(export_dir, path))

    # 验证解析后的路径仍在报表目录内
    if not file_path.startswith(export_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)

    # 设置 MIME 类型
    media_type_map = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')

    # 生成下载文件名
    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
