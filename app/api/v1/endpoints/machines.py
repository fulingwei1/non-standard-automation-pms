from typing import Any, List, Optional
from decimal import Decimal
from pathlib import Path
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from fastapi import HTTPException
from app.models.project import Machine, Project, ProjectDocument
from app.models.service import ServiceRecord
from app.schemas.project import (
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    ProjectDocumentResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "machines"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_model=PaginatedResponse[MachineResponse])
def read_machines(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    stage: Optional[str] = Query(None, description="设备阶段筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台列表（支持分页、筛选）
    """
    query = db.query(Machine)
    
    if project_id:
        query = query.filter(Machine.project_id == project_id)
    if stage:
        query = query.filter(Machine.stage == stage)
    if status:
        query = query.filter(Machine.status == status)
    if health:
        query = query.filter(Machine.health == health)

    total = query.count()
    offset = (page - 1) * page_size
    machines = query.order_by(desc(Machine.created_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=machines,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/projects/{project_id}/machines", response_model=List[MachineResponse])
def get_project_machines(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取项目的机台列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    machines = db.query(Machine).filter(Machine.project_id == project_id).order_by(Machine.machine_no).all()
    return machines


@router.post("/", response_model=MachineResponse)
def create_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """
    Create new machine.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == machine_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if machine code exists in project
    existing = (
        db.query(Machine)
        .filter(
            Machine.project_id == machine_in.project_id,
            Machine.machine_code == machine_in.machine_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Machine with this code already exists in this project.",
        )

    machine = Machine(**machine_in.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.post("/projects/{project_id}/machines", response_model=MachineResponse)
def create_project_machine(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    为项目创建机台
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 确保project_id一致
    machine_data = machine_in.model_dump()
    machine_data['project_id'] = project_id
    
    # 检查机台编码是否已存在
    existing = (
        db.query(Machine)
        .filter(
            Machine.project_id == project_id,
            Machine.machine_code == machine_in.machine_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="该机台编码已在此项目中存在",
        )
    
    machine = Machine(**machine_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}", response_model=MachineResponse)
def read_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    Get machine by ID.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    Update a machine.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.put("/{machine_id}/progress", response_model=MachineResponse)
def update_machine_progress(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    progress_pct: Decimal = Query(..., ge=0, le=100, description="进度百分比（0-100）"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    更新机台进度
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    machine.progress_pct = progress_pct
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}/bom", response_model=List)
def get_machine_bom(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台的BOM列表
    注意：实际的BOM列表API在 /api/v1/bom/machines/{machine_id}/bom
    这里提供快捷访问
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    # 通过BOM API获取，这里返回提示信息
    from app.models.material import BomHeader
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


@router.get("/{machine_id}/service-history", response_model=ResponseModel)
def get_machine_service_history(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    设备档案（服务历史记录）
    获取机台的所有服务记录，包括安装、调试、维修、保养等
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    # 查询服务记录（通过machine_no匹配）
    query = db.query(ServiceRecord).filter(ServiceRecord.machine_no == machine.machine_no)
    
    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(desc(ServiceRecord.service_date)).offset(offset).limit(page_size).all()
    
    # 构建服务历史列表
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
    
    # 统计信息
    total_records = total
    total_hours = sum([float(r.duration_hours or 0) for r in records])
    avg_satisfaction = None
    satisfaction_scores = [r.customer_satisfaction for r in records if r.customer_satisfaction]
    if satisfaction_scores:
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "machine_id": machine_id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "summary": {
                "total_records": total_records,
                "total_service_hours": round(total_hours, 2),
                "avg_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None
            },
            "items": history_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
    )


@router.delete("/{machine_id}", status_code=200)
def delete_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> Any:
    """
    删除机台
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 检查是否有关联的BOM
    from app.models.material import BomHeader
    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。"
        )

    db.delete(machine)
    db.commit()
    
    return ResponseModel(code=200, message="机台已删除")


# ==================== 设备文档管理 ====================

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
        doc_name = doc_type_names.get(doc_type.upper(), doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限上传{doc_name}类型的文档。请联系管理员分配相应角色权限。"
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
            doc_type = doc.doc_type
            if doc_type not in grouped:
                grouped[doc_type] = []
            grouped[doc_type].append(ProjectDocumentResponse.model_validate(doc))
        
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
        doc_name = doc_type_names.get(document.doc_type.upper(), document.doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限下载{doc_name}类型的文档。请联系管理员分配相应角色权限。"
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
        doc_name = doc_type_names.get(document.doc_type.upper(), document.doc_type)
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限查看{doc_name}类型的文档版本。请联系管理员分配相应角色权限。"
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
