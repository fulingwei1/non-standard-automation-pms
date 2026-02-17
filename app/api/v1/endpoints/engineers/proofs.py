# -*- coding: utf-8 -*-
"""
工程师完成证明管理 API 端点
包含：证明材料上传、查询、删除
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Project
from app.models.task_center import TaskCompletionProof, TaskUnified
from app.models.user import User
from app.schemas import engineer as schemas
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

logger = logging.getLogger(__name__)


def validate_file_upload(file: UploadFile, content: bytes) -> None:
    """
    验证上传文件的大小和类型

    Args:
        file: 上传的文件对象
        content: 文件内容字节

    Raises:
        HTTPException: 文件大小超限或类型不允许时抛出
    """
    # 验证文件大小
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大允许 {max_size_mb:.0f}MB"
        )

    # 验证文件类型
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型 '{file_ext}'，允许的类型: {allowed}"
            )

router = APIRouter()


@router.post("/tasks/{task_id}/completion-proofs/upload", response_model=schemas.ProofUploadResponse)
async def upload_completion_proof(
    task_id: int,
    file: UploadFile = File(...),
    proof_type: str = Form(...),
    file_category: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    上传任务完成证明材料
    """
    # 验证任务
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能为自己的任务上传证明")

    # 验证proof_type
    valid_proof_types = ['DOCUMENT', 'PHOTO', 'VIDEO', 'TEST_REPORT', 'DATA']
    if proof_type not in valid_proof_types:
        raise HTTPException(status_code=400, detail=f"无效的证明类型，必须是: {', '.join(valid_proof_types)}")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小和类型
    validate_file_upload(file, content)

    # 保存文件
    import uuid
    upload_dir = f"uploads/task_proofs/{task_id}"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 写入文件
    with open(file_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    # 创建证明记录
    proof = TaskCompletionProof(
        task_id=task_id,
        proof_type=proof_type,
        file_category=file_category,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        file_type=file_ext.lstrip('.'),
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now()
    )

    db.add(proof)
    db.commit()
    db.refresh(proof)

    return schemas.ProofUploadResponse.model_validate(proof)


@router.get("/tasks/{task_id}/completion-proofs", response_model=schemas.TaskProofListResponse)
def get_task_completion_proofs(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取任务的所有完成证明材料
    """
    # 验证任务存在
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看证明材料")

    # 查询证明材料
    proofs = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).order_by(TaskCompletionProof.uploaded_at.desc()).all()

    # 构建响应
    proof_responses = [schemas.ProofUploadResponse.model_validate(p) for p in proofs]

    return schemas.TaskProofListResponse(
        task_id=task_id,
        proofs=proof_responses,
        total_count=len(proof_responses)
    )


@router.delete("/tasks/{task_id}/completion-proofs/{proof_id}")
def delete_completion_proof(
    task_id: int,
    proof_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    删除任务完成证明材料
    """
    # 获取证明材料
    proof = db.query(TaskCompletionProof).filter(
        and_(
            TaskCompletionProof.id == proof_id,
            TaskCompletionProof.task_id == task_id
        )
    ).first()

    if not proof:
        raise HTTPException(status_code=404, detail="证明材料不存在")

    # 验证任务
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    # 验证权限（只有上传者和任务执行人可以删除）
    if proof.uploaded_by != current_user.id and task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限删除此证明材料")

    # 删除文件
    if os.path.exists(proof.file_path):
        try:
            os.remove(proof.file_path)
        except Exception as e:
            logger.warning(f"Could not delete file {proof.file_path}: {e}")

    # 删除数据库记录
    db.delete(proof)
    db.commit()

    return {"message": "证明材料已删除", "proof_id": proof_id}
