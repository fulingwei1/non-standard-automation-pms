# -*- coding: utf-8 -*-
"""
项目机台自定义端点

包含汇总、重新计算、进度更新、BOM查询、文档管理、服务历史等功能
"""

import uuid
from decimal import Decimal
from pathlib import Path as FilePath
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.auth import check_permission
from app.core.config import settings
from app.models.material import BomHeader
from app.models.project import Machine, Project, ProjectDocument
from app.models.service import ServiceRecord
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import MachineResponse, ProjectDocumentResponse
from app.utils.permission_helpers import check_project_access_or_raise
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()

# 文档类型到权限代码的映射
DOC_TYPE_PERMISSION_MAP = {
    "CIRCUIT_DIAGRAM": "machine:doc_circuit",
    "PLC_PROGRAM": "machine:doc_plc",
    "LABELWORK_PROGRAM": "machine:doc_vision",
    "VISION_PROGRAM": "machine:doc_vision",
    "MOTION_PROGRAM": "machine:doc_motion",
    "ROBOT_PROGRAM": "machine:doc_robot",
    "OPERATION_MANUAL": "machine:doc_manual",
    "DRAWING": "machine:doc_drawing",
    "BOM_DOCUMENT": "machine:doc_bom",
    "FAT_DOCUMENT": "machine:doc_other",
    "SAT_DOCUMENT": "machine:doc_other",
    "OTHER": "machine:doc_other",
}


def has_machine_document_permission_db(user: User, doc_type: str, db: Session) -> bool:
    """检查用户是否有访问特定文档类型的权限"""
    perm_code = DOC_TYPE_PERMISSION_MAP.get(doc_type.upper(), "machine:doc_other")
    return check_permission(user, perm_code, db)

# 文档上传目录
DOCUMENT_UPLOAD_DIR = FilePath(settings.UPLOAD_DIR) / "documents" / "machines"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/summary")
def get_project_machine_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取项目机台汇总信息

    返回：
    - total_machines: 机台总数
    - stage_distribution: 阶段分布
    - health_distribution: 健康度分布
    - avg_progress: 平均进度
    - completed_count: 已完成数量（S9）
    - at_risk_count: 有风险数量（H2）
    - blocked_count: 阻塞数量（H3）
    """
    from app.services.machine_service import ProjectAggregationService

    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    aggregation_service = ProjectAggregationService(db)
    summary = aggregation_service.get_project_machine_summary(project_id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "project_stage": project.stage,
            "project_health": project.health,
            "project_progress": float(project.progress_pct or 0),
            **summary,
        },
    )


@router.post("/recalculate")
def recalculate_project_aggregation(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    重新计算项目聚合数据

    当项目的进度、阶段或健康度与机台不一致时，
    可以调用此接口强制重新计算。
    """
    from app.services.machine_service import ProjectAggregationService

    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    aggregation_service = ProjectAggregationService(db)
    updated_project = aggregation_service.update_project_aggregation(project_id)

    return ResponseModel(
        code=200,
        message="重新计算完成",
        data={
            "project_id": updated_project.id,
            "project_code": updated_project.project_code,
            "stage": updated_project.stage,
            "health": updated_project.health,
            "progress_pct": float(updated_project.progress_pct or 0),
        },
    )


@router.put("/{machine_id}/progress", response_model=MachineResponse)
def update_project_machine_progress(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    progress_pct: Decimal = Query(..., ge=0, le=100, description="进度百分比（0-100）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    更新机台进度

    更新后自动重新计算项目的聚合进度
    """
    from app.services.machine_service import ProjectAggregationService

    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    machine.progress_pct = progress_pct
    save_obj(db, machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)

    return machine


@router.get("/{machine_id}/bom")
def get_project_machine_bom(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台的BOM列表
    """
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    bom_headers = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .order_by(desc(BomHeader.created_at))
        .all()
    )

    result = []
    for bom in bom_headers:
        result.append({
            "id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            "version": bom.version,
            "is_latest": bom.is_latest,
            "status": bom.status,
            "total_items": bom.total_items,
            "total_amount": float(bom.total_amount) if bom.total_amount else 0,
        })

    return result


# ==================== 文档管理 ====================


@router.post("/{machine_id}/documents/upload", response_model=ResponseModel, status_code=201)
async def upload_machine_document(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    file: UploadFile = File(..., description="上传的文件"),
    doc_type: str = Form(..., description="文档类型"),
    doc_category: Optional[str] = Form(None, description="文档分类"),
    doc_name: Optional[str] = Form(None, description="文档名称"),
    doc_no: Optional[str] = Form(None, description="文档编号"),
    version: str = Form("1.0", description="版本号"),
    description: Optional[str] = Form(None, description="描述"),
    machine_stage: Optional[str] = Form(None, description="关联的设备生命周期阶段"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """上传设备文档"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    valid_doc_types = [
        "CIRCUIT_DIAGRAM", "PLC_PROGRAM", "LABELWORK_PROGRAM",
        "BOM_DOCUMENT", "FAT_DOCUMENT", "SAT_DOCUMENT", "OTHER"
    ]
    if doc_type.upper() not in valid_doc_types:
        raise HTTPException(status_code=400, detail=f"无效的文档类型。有效值：{', '.join(valid_doc_types)}")

    if not has_machine_document_permission_db(current_user, doc_type, db):
        raise HTTPException(status_code=403, detail="您没有权限上传此类型的文档")

    file_ext = FilePath(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = DOCUMENT_UPLOAD_DIR / str(machine_id) / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    doc_data = {
        "project_id": project_id,
        "machine_id": machine_id,
        "doc_type": doc_type,
        "doc_category": doc_category or machine_stage,
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
    save_obj(db, document)

    return ResponseModel(
        code=201,
        message="文档上传成功",
        data=ProjectDocumentResponse.model_validate(document)
    )


@router.get("/{machine_id}/documents", response_model=ResponseModel)
def get_machine_documents(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    group_by_type: bool = Query(True, description="是否按类型分组"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取设备的所有文档"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.machine_id == machine_id)
    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)

    all_documents = query.order_by(desc(ProjectDocument.created_at)).all()

    accessible_documents = [
        doc for doc in all_documents
        if has_machine_document_permission_db(current_user, doc.doc_type, db)
    ]

    if group_by_type:
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
                "documents_by_type": grouped,
                "total_count": len(accessible_documents),
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
                "documents": [ProjectDocumentResponse.model_validate(doc) for doc in accessible_documents],
                "total_count": len(accessible_documents),
            }
        )


@router.get("/{machine_id}/documents/{doc_id}/download")
def download_machine_document(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """下载设备文档"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.machine_id == machine_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not has_machine_document_permission_db(current_user, document.doc_type, db):
        raise HTTPException(status_code=403, detail="您没有权限下载此类型的文档")

    file_path = FilePath(document.file_path)
    upload_dir = FilePath(settings.UPLOAD_DIR)

    if not file_path.is_absolute():
        file_path = upload_dir / file_path

    resolved_path = file_path.resolve()
    try:
        resolved_path.relative_to(upload_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(resolved_path),
        filename=document.file_name,
        media_type='application/octet-stream'
    )


@router.get("/{machine_id}/documents/{doc_id}/versions", response_model=List[ProjectDocumentResponse])
def get_machine_document_versions(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取设备文档的所有版本"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.machine_id == machine_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not has_machine_document_permission_db(current_user, document.doc_type, db):
        raise HTTPException(status_code=403, detail="您没有权限查看此类型的文档版本")

    query = db.query(ProjectDocument).filter(ProjectDocument.machine_id == machine_id)
    if document.doc_no:
        query = query.filter(ProjectDocument.doc_no == document.doc_no)
    else:
        query = query.filter(ProjectDocument.doc_name == document.doc_name)

    all_versions = query.order_by(desc(ProjectDocument.created_at)).all()
    return [
        doc for doc in all_versions
        if has_machine_document_permission_db(current_user, doc.doc_type, db)
    ]


# ==================== 服务历史 ====================


@router.get("/{machine_id}/service-history", response_model=ResponseModel)
def get_machine_service_history(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取机台服务历史记录"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    query = db.query(ServiceRecord).filter(ServiceRecord.machine_no == machine.machine_no)

    total = query.count()
    records = apply_pagination(query.order_by(desc(ServiceRecord.service_date)), pagination.offset, pagination.limit).all()

    history_items = []
    for record in records:
        history_items.append({
            "id": record.id,
            "record_no": record.record_no,
            "service_type": record.service_type,
            "service_date": record.service_date.isoformat() if record.service_date else None,
            "service_content": record.service_content,
            "service_result": record.service_result,
            "issues_found": record.issues_found,
            "solution_provided": record.solution_provided,
            "duration_hours": float(record.duration_hours) if record.duration_hours else None,
            "service_engineer_name": record.service_engineer_name,
            "customer_satisfaction": record.customer_satisfaction,
            "customer_feedback": record.customer_feedback,
            "location": record.location,
            "created_at": record.created_at.isoformat() if record.created_at else None
        })

    total_hours = sum([float(r.duration_hours or 0) for r in records])
    satisfaction_scores = [r.customer_satisfaction for r in records if r.customer_satisfaction]
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None

    return ResponseModel(
        code=200,
        message="success",
        data={
            "machine_id": machine_id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "summary": {
                "total_records": total,
                "total_service_hours": round(total_hours, 2),
                "avg_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None
            },
            "items": history_items,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total": total,
                "pages": (total + pagination.page_size - 1) // pagination.page_size
            }
        }
    )
