# -*- coding: utf-8 -*-
"""
研发项目文档管理 - 自动生成
从 rd_project.py 拆分
"""

# -*- coding: utf-8 -*-
"""
研发项目管理 API endpoints
包含：研发项目立项、审批、结项、费用归集、报表生成
适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "rd_projects"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
from app.models.user import User
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.project import ProjectDocument
from app.models.rd_project import (
    RdProject, RdProjectCategory, RdCost, RdCostType,
    RdCostAllocationRule, RdReportRecord
)
from app.schemas.rd_project import (
    RdProjectCategoryCreate, RdProjectCategoryUpdate, RdProjectCategoryResponse,
    RdProjectCreate, RdProjectUpdate, RdProjectResponse,
    RdProjectApproveRequest, RdProjectCloseRequest, RdProjectLinkRequest,
    RdCostTypeCreate, RdCostTypeResponse,
    RdCostCreate, RdCostUpdate, RdCostResponse,
    RdCostCalculateLaborRequest, RdCostSummaryResponse,
    RdCostAllocationRuleCreate, RdCostAllocationRuleResponse,
    RdReportRecordResponse
)
from app.schemas.timesheet import (
    TimesheetCreate, TimesheetUpdate, TimesheetResponse, TimesheetListResponse
)
from app.schemas.project import (
    ProjectDocumentCreate, ProjectDocumentUpdate, ProjectDocumentResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_project_no(db: Session) -> str:
    """生成研发项目编号：RD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_project = (
        db.query(RdProject)
        .filter(RdProject.project_no.like(f"RD-{today}-%"))
        .order_by(desc(RdProject.project_no))
        .first()
    )
    if max_project:
        seq = int(max_project.project_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RD-{today}-{seq:03d}"


def generate_cost_no(db: Session) -> str:
    """生成研发费用编号：RC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_cost = (
        db.query(RdCost)
        .filter(RdCost.cost_no.like(f"RC-{today}-%"))
        .order_by(desc(RdCost.cost_no))
        .first()
    )
    if max_cost:
        seq = int(max_cost.cost_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RC-{today}-{seq:03d}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/rd-project/documents",
    tags=["documents"]
)

# 共 4 个路由

# ==================== 研发项目文档管理 ====================

@router.get("/rd-projects/{project_id}/documents", response_model=ResponseModel)
def get_rd_project_documents(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    doc_category: Optional[str] = Query(None, description="文档分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    获取研发项目文档列表
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    offset = (page - 1) * page_size
    query = db.query(ProjectDocument).filter(ProjectDocument.rd_project_id == project_id)
    
    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)
    if doc_category:
        query = query.filter(ProjectDocument.doc_category == doc_category)
    if status:
        query = query.filter(ProjectDocument.status == status)
    
    total = query.count()
    documents = query.order_by(desc(ProjectDocument.created_at)).offset(offset).limit(page_size).all()
    
    return ResponseModel(
        code=200,
        message="success",
        data=PaginatedResponse(
            items=[ProjectDocumentResponse.model_validate(doc) for doc in documents],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    )


@router.post("/rd-projects/{project_id}/documents", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    doc_in: ProjectDocumentCreate,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    创建研发项目文档记录
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    doc_data = doc_in.model_dump()
    doc_data["rd_project_id"] = project_id
    doc_data["project_id"] = project.linked_project_id  # 如果有关联的非标项目，也记录
    doc_data["uploaded_by"] = current_user.id
    
    document = ProjectDocument(**doc_data)
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return ResponseModel(
        code=201,
        message="文档创建成功",
        data=ProjectDocumentResponse.model_validate(document)
    )


@router.post("/rd-projects/{project_id}/documents/upload", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def upload_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    file: UploadFile = File(..., description="上传的文件"),
    doc_type: str = Form(..., description="文档类型"),
    doc_category: Optional[str] = Form(None, description="文档分类"),
    doc_name: Optional[str] = Form(None, description="文档名称"),
    doc_no: Optional[str] = Form(None, description="文档编号"),
    version: str = Form("1.0", description="版本号"),
    description: Optional[str] = Form(None, description="描述"),
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    上传研发项目文档（包含文件上传）
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = DOCUMENT_UPLOAD_DIR / str(project_id) / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 创建文档记录
    doc_data = {
        "rd_project_id": project_id,
        "project_id": project.linked_project_id,
        "doc_type": doc_type,
        "doc_category": doc_category,
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


@router.get("/rd-projects/{project_id}/documents/{doc_id}/download")
def download_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    doc_id: int,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    下载研发项目文档
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")
    
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.rd_project_id == project_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    upload_dir = Path(settings.UPLOAD_DIR)
    file_path = upload_dir / document.file_path

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


