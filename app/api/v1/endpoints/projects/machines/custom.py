# -*- coding: utf-8 -*-
"""
项目机台自定义端点

包含汇总、重新计算、进度更新、BOM查询、文档管理、服务历史等功能
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.schemas.common import ResponseModel
from app.schemas.project import MachineResponse, ProjectDocumentResponse
from app.utils.permission_helpers import check_project_access_or_raise
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.db_helpers import get_or_404
from app.models.project import Machine, Project, ProjectDocument
from app.models.user import User
from app.services.machine_custom import MachineCustomService

router = APIRouter()


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
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    service = MachineCustomService(db)
    updated_machine = service.update_machine_progress(machine, progress_pct)

    return updated_machine


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

    service = MachineCustomService(db)
    bom_list = service.get_machine_bom_list(machine_id)

    return bom_list


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

    service = MachineCustomService(db)
    document = await service.upload_document(
        machine=machine,
        file=file,
        doc_type=doc_type,
        user=current_user,
        doc_category=doc_category,
        doc_name=doc_name,
        doc_no=doc_no,
        version=version,
        description=description,
        machine_stage=machine_stage,
    )

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

    service = MachineCustomService(db)
    result = service.get_machine_documents(
        machine=machine,
        user=current_user,
        doc_type=doc_type,
        group_by_type=group_by_type
    )

    return ResponseModel(
        code=200,
        message="success",
        data=result
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

    service = MachineCustomService(db)
    file_path, filename = service.get_document_download_path(document, current_user)

    return FileResponse(
        path=str(file_path),
        filename=filename,
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

    service = MachineCustomService(db)
    versions = service.get_document_versions(document, current_user)

    return versions


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

    service = MachineCustomService(db)
    result = service.get_service_history(
        machine=machine,
        page=pagination.page,
        page_size=pagination.page_size
    )

    return ResponseModel(
        code=200,
        message="success",
        data=result
    )
