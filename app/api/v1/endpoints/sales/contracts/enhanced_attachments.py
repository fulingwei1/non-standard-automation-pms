# -*- coding: utf-8 -*-
"""
合同附件管理 API
从 enhanced.py 拆分
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.sales.contract_enhanced import (
    ContractAttachmentCreate,
    ContractAttachmentResponse,
)
from app.services.sales.contract_enhanced import ContractEnhancedService

router = APIRouter()


@router.post(
    "/{contract_id}/attachments",
    response_model=ContractAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_attachment(
    contract_id: int,
    attachment_data: ContractAttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传附件"""
    attachment = ContractEnhancedService.add_attachment(
        db, contract_id, attachment_data, current_user.id
    )
    return attachment


@router.get("/{contract_id}/attachments", response_model=List[ContractAttachmentResponse])
def get_contract_attachments(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """附件列表"""
    attachments = ContractEnhancedService.get_attachments(db, contract_id)
    return attachments


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除附件"""
    success = ContractEnhancedService.delete_attachment(db, attachment_id)
    if not success:
        raise HTTPException(status_code=404, detail="附件不存在")


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载附件"""
    # TODO: 实现文件下载逻辑
    raise HTTPException(status_code=501, detail="下载功能待实现")
