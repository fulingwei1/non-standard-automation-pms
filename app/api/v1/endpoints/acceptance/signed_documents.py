# -*- coding: utf-8 -*-
"""
验收报告 - 客户签署文件管理

包含客户签署文件的上传和下载
"""

import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.acceptance import AcceptanceOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.acceptance import AcceptanceOrderResponse

from .order_crud import read_acceptance_order

router = APIRouter()


@router.post("/acceptance-orders/{order_id}/upload-signed-document", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
async def upload_customer_signed_document(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    file: UploadFile = File(..., description="客户签署的验收单文件"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传客户签署的验收单文件

    上传后，验收单将被标记为正式完成（is_officially_completed=True）
    只有状态为COMPLETED且验收结果为PASSED的验收单才能上传签署文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # 验证验收单状态
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成状态的验收单才能上传客户签署文件")

    if order.overall_result != "PASSED":
        raise HTTPException(status_code=400, detail="只有验收通过的验收单才能上传客户签署文件")

    # 验证项目关联
    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="关联的项目不存在")

    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, "acceptance_signed_documents")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    unique_filename = f"{order.order_no}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 保存文件
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 计算相对路径（相对于UPLOAD_DIR）
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR)

    # 更新验收单
    order.customer_signed_file_path = relative_path
    order.is_officially_completed = True
    order.officially_completed_at = datetime.now()

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.get("/acceptance-orders/{order_id}/download-signed-document", response_class=FileResponse)
def download_customer_signed_document(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载客户签署的验收单文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if not order.customer_signed_file_path:
        raise HTTPException(status_code=404, detail="客户签署文件不存在")

    # 安全检查：解析为规范路径，防止路径遍历攻击
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, order.customer_signed_file_path))

    if not file_path.startswith(upload_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    filename = os.path.basename(file_path)
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )
