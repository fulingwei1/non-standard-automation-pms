# -*- coding: utf-8 -*-
"""
机台文档管理端点
"""

import uuid
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Machine, ProjectDocument
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import ProjectDocumentResponse

router = APIRouter()

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "machines"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/{machine_id}/documents/upload", response_model=ResponseModel, status_code=201)
async def upload_machine_document(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    file: UploadFile = File(..., description="上传的文件"),
    doc_type: str = Form(..., description="文档类型：CIRCUIT_DIAGRAM/PLC_PROGRAM/LABELWORK_PROGRAM/BOM_DOCUMENT/FAT_DOCUMENT/SAT_DOCUMENT/OTHER"),
    doc_category: Optional[str] = Form(None, description="文档分类"),
    doc_name: Optional[str] = Form(None, description="文档名称"),
    doc_no: Optional[str] = Form(None, description="文档编号"),
    version: str = Form("1.0", description="版本号"),
    description: Optional[str] = Form(None, description="描述"),
    machine_stage: Optional[str] = Form(None, description="关联的设备生命周期阶段（S1-S9）"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    上传设备文档（支持文件上传和版本管理）

    支持的文档类型：
    - CIRCUIT_DIAGRAM: 电路图（需要电气工程师、PLC工程师或研发工程师权限）
    - PLC_PROGRAM: PLC程序（需要PLC工程师、电气工程师或研发工程师权限）
    - LABELWORK_PROGRAM: Labelwork程序（需要电气工程师、PLC工程师或研发工程师权限）
    - BOM_DOCUMENT: BOM文档（需要PMC、物料工程师或项目经理权限）
    - FAT_DOCUMENT: FAT验收文档（需要质量工程师或项目经理权限）
    - SAT_DOCUMENT: SAT验收文档（需要质量工程师或项目经理权限）
    - OTHER: 其他文档（项目成员都可以上传）

    注意：不同文档类型需要不同的角色权限，系统会自动检查。
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 验证文档类型
    valid_doc_types = [
        "CIRCUIT_DIAGRAM", "PLC_PROGRAM", "LABELWORK_PROGRAM",
        "BOM_DOCUMENT", "FAT_DOCUMENT", "SAT_DOCUMENT", "OTHER"
    ]
    if doc_type.upper() not in valid_doc_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的文档类型。有效值：{', '.join(valid_doc_types)}"
        )

    # 检查用户是否有权限上传该类型的文档
    if not security.has_machine_document_permission(current_user, doc_type):
        doc_type_names = {
            "CIRCUIT_DIAGRAM": "电路图",
            "PLC_PROGRAM": "PLC程序",
            "LABELWORK_PROGRAM": "Labelwork程序",
            "BOM_DOCUMENT": "BOM文档",
            "FAT_DOCUMENT": "FAT文档",
            "SAT_DOCUMENT": "SAT文档",
            "OTHER": "其他文档",
        }
        doc_type_display = doc_type_names.get(doc_type.upper(), doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限上传{doc_type_display}类型的文档。请联系管理员分配相应角色权限。"
        )

    # 验证设备阶段（如果提供）
    if machine_stage:
        valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
        if machine_stage not in valid_stages:
            raise HTTPException(
                status_code=400,
                detail=f"无效的设备阶段。有效值：{', '.join(valid_stages)}"
            )

    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = DOCUMENT_UPLOAD_DIR / str(machine_id) / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存文件
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 创建文档记录
    doc_data = {
        "project_id": machine.project_id,
        "machine_id": machine_id,
        "doc_type": doc_type,
        "doc_category": doc_category or machine_stage,  # 如果没有分类，使用阶段作为分类
        "doc_name": doc_name or file.filename,
        "doc_no": doc_no,
        "version": version,
        "file_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
        "file_name": file.filename,
        "file_size": len(content),
        "file_type": file.content_type or file_ext[1:] if file_ext else None,
        "description": description,
        "uploaded_by": current_user.id,
        "status": "DRAFT",
    }

    document = ProjectDocument(**doc_data)
    db.add(document)
    db.commit()
    db.refresh(document)

    return ResponseModel(
        code=201,
        message="文档上传成功",
        data=ProjectDocumentResponse.model_validate(document)
    )


@router.get("/{machine_id}/documents", response_model=ResponseModel)
def get_machine_documents(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    group_by_type: bool = Query(True, description="是否按类型分组"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取设备的所有文档（按类型分类）

    注意：只返回用户有权限访问的文档。如果用户没有权限访问某类文档，
    该类文档将不会出现在列表中。
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.machine_id == machine_id)

    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)

    all_documents = query.order_by(desc(ProjectDocument.created_at)).all()

    # 权限过滤：只返回用户有权限访问的文档
    accessible_documents = []
    for doc in all_documents:
        if security.has_machine_document_permission(current_user, doc.doc_type):
            accessible_documents.append(doc)

    if group_by_type:
        # 按类型分组
        grouped = {}
        for doc in accessible_documents:
            dtype = doc.doc_type
            if dtype not in grouped:
                grouped[dtype] = []
            grouped[dtype].append(ProjectDocumentResponse.model_validate(doc))

        return ResponseModel(
            code=200,
            message="success",
            data={
                "machine_id": machine_id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                "machine_stage": machine.stage,
                "documents_by_type": grouped,
                "total_count": len(accessible_documents),
                "filtered_count": len(all_documents) - len(accessible_documents)  # 被过滤掉的文档数量
            }
        )
    else:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "machine_id": machine_id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                "machine_stage": machine.stage,
                "documents": [ProjectDocumentResponse.model_validate(doc) for doc in accessible_documents],
                "total_count": len(accessible_documents),
                "filtered_count": len(all_documents) - len(accessible_documents)  # 被过滤掉的文档数量
            }
        )


@router.get("/{machine_id}/documents/{doc_id}/download")
def download_machine_document(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    doc_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    下载设备文档

    注意：下载文档需要相应的权限，不同文档类型需要不同的角色权限。
    如果权限不足，请联系管理员分配相应角色权限。
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.machine_id == machine_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查用户是否有权限下载该类型的文档
    if not security.has_machine_document_permission(current_user, document.doc_type):
        doc_type_names = {
            "CIRCUIT_DIAGRAM": "电路图",
            "PLC_PROGRAM": "PLC程序",
            "LABELWORK_PROGRAM": "Labelwork程序",
            "BOM_DOCUMENT": "BOM文档",
            "FAT_DOCUMENT": "FAT文档",
            "SAT_DOCUMENT": "SAT文档",
            "OTHER": "其他文档",
        }
        doc_type_display = doc_type_names.get(document.doc_type.upper(), document.doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限下载{doc_type_display}类型的文档。请联系管理员分配相应角色权限。"
        )

    file_path = Path(document.file_path)
    upload_dir = Path(settings.UPLOAD_DIR)

    # 如果是相对路径，转换为绝对路径
    if not file_path.is_absolute():
        file_path = upload_dir / file_path

    # 安全检查：解析为规范路径，防止路径遍历攻击
    resolved_path = file_path.resolve()
    upload_dir_resolved = upload_dir.resolve()

    try:
        resolved_path.relative_to(upload_dir_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(resolved_path),
        filename=document.file_name,
        media_type='application/octet-stream'
    )


@router.get("/{machine_id}/documents/{doc_id}/versions", response_model=List[ProjectDocumentResponse])
def get_machine_document_versions(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    doc_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取设备文档的所有版本

    注意：只返回用户有权限访问的版本。如果用户没有权限访问该文档类型，
    将返回空列表。
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.machine_id == machine_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查用户是否有权限访问该类型的文档
    if not security.has_machine_document_permission(current_user, document.doc_type):
        doc_type_names = {
            "CIRCUIT_DIAGRAM": "电路图",
            "PLC_PROGRAM": "PLC程序",
            "LABELWORK_PROGRAM": "Labelwork程序",
            "BOM_DOCUMENT": "BOM文档",
            "FAT_DOCUMENT": "FAT文档",
            "SAT_DOCUMENT": "SAT文档",
            "OTHER": "其他文档",
        }
        doc_type_display = doc_type_names.get(document.doc_type.upper(), document.doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限查看{doc_type_display}类型的文档版本。请联系管理员分配相应角色权限。"
        )

    # 根据文档编号或名称查找所有版本
    query = db.query(ProjectDocument).filter(
        ProjectDocument.machine_id == machine_id
    )

    if document.doc_no:
        query = query.filter(ProjectDocument.doc_no == document.doc_no)
    else:
        # 如果没有文档编号，使用文档名称匹配
        query = query.filter(ProjectDocument.doc_name == document.doc_name)

    all_versions = query.order_by(desc(ProjectDocument.created_at)).all()

    # 权限过滤：只返回用户有权限访问的版本
    accessible_versions = [
        doc for doc in all_versions
        if security.has_machine_document_permission(current_user, doc.doc_type)
    ]

    return accessible_versions
