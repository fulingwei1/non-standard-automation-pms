# -*- coding: utf-8 -*-
"""
机台基本 CRUD 端点（重构版）

使用通用CRUD路由生成器和统一响应格式，去除重复代码。
保留所有项目相关的特殊端点和业务逻辑。
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.models.material import BomHeader
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.project import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)
from app.services.machine_service import MachineService, ProjectAggregationService

# 注意：machines端点有很多特殊逻辑，不完全适合通用CRUD路由生成器
# 这里只重构简单的列表和详情查询，保留所有特殊端点

router = APIRouter()

# ========== 列表查询端点 ==========

@router.get(
    "/",
    response_model=PaginatedResponse[MachineResponse],
    summary="机台列表",
    description="分页查询机台列表，支持筛选"
)
def list_machines(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量"
    ),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    stage: Optional[str] = Query(None, description="设备阶段筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> PaginatedResponse[MachineResponse]:
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

    return paginated_response(
        items=machines,
        total=total,
        page=page,
        page_size=page_size
    )


# ========== 详情查询端点 ==========

@router.get(
    "/{machine_id}",
    response_model=SuccessResponse[MachineResponse],
    summary="获取机台详情",
    description="根据ID获取机台详细信息"
)
def get_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> SuccessResponse[MachineResponse]:
    """
    获取机台详情
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    return success_response(data=machine, message="获取成功")


# ========== 创建端点（保留原逻辑，包含自动生成编码和项目聚合） ==========
# 注意：项目相关端点已迁移至 /projects/{project_id}/machines/ 子路由
# 以下端点已删除，请使用项目子路由：
# - GET /projects/{project_id}/machines -> GET /projects/{project_id}/machines/
# - POST /projects/{project_id}/machines -> POST /projects/{project_id}/machines/

@router.post(
    "/",
    response_model=SuccessResponse[MachineResponse],
    status_code=201,
    summary="创建机台",
    description="创建机台，机台编码自动生成格式：{项目编码}-PN{序号}"
)
def create_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:create")),
) -> SuccessResponse[MachineResponse]:
    """
    创建机台
    
    机台编码自动生成格式：{项目编码}-PN{序号}
    例如：PJ250712001-PN001
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == machine_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 准备机台数据
    machine_data = machine_in.model_dump()
    machine_service = MachineService(db)

    # 自动生成机台编码（如果未提供）
    if not machine_data.get("machine_code"):
        machine_code, machine_no = machine_service.generate_machine_code(machine_in.project_id)
        machine_data["machine_code"] = machine_code
        machine_data["machine_no"] = machine_no
    else:
        # 检查机台编码是否已存在
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
                detail="该机台编码已在此项目中存在",
            )

    machine = Machine(**machine_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(machine_in.project_id)

    return success_response(
        data=machine,
        message="机台创建成功",
        code=201
    )


# ========== 更新端点（保留原逻辑，包含阶段验证和项目聚合） ==========
# 注意：项目相关端点已迁移至 /projects/{project_id}/machines/ 子路由

@router.put(
    "/{machine_id}",
    response_model=SuccessResponse[MachineResponse],
    summary="更新机台",
    description="更新机台信息，支持阶段和健康度验证，自动更新项目聚合数据"
)
def update_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
    current_user: User = Depends(security.require_permission("machine:update")),
) -> SuccessResponse[MachineResponse]:
    """
    更新机台信息
    
    - 阶段变更会验证是否合法（只能向前推进）
    - 状态变更会验证是否在有效范围内
    - 更新后自动重新计算项目的聚合数据
    """
    from app.services.machine_service import VALID_HEALTH, VALID_STAGES

    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    update_data = machine_in.model_dump(exclude_unset=True)
    machine_service = MachineService(db)

    # 验证阶段变更是否合法
    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage not in VALID_STAGES:
            raise HTTPException(
                status_code=400,
                detail=f"无效的阶段值: {new_stage}，有效值为 S1-S9"
            )

        is_valid, error_msg = machine_service.validate_stage_transition(
            machine.stage, new_stage
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    # 验证健康度是否有效
    if "health" in update_data:
        new_health = update_data["health"]
        if new_health not in VALID_HEALTH:
            raise HTTPException(
                status_code=400,
                detail=f"无效的健康度: {new_health}，有效值为 H1-H4"
            )

    # 应用更新
    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(machine.project_id)

    return success_response(
        data=machine,
        message="机台更新成功"
    )


@router.put(
    "/{machine_id}/progress",
    response_model=SuccessResponse[MachineResponse],
    summary="更新机台进度",
    description="更新机台进度百分比，自动更新项目聚合数据"
)
def update_machine_progress(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    progress_pct: Decimal = Query(..., ge=0, le=100, description="进度百分比（0-100）"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> SuccessResponse[MachineResponse]:
    """
    更新机台进度
    
    更新后自动重新计算项目的聚合进度
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    machine.progress_pct = progress_pct
    db.add(machine)
    db.commit()
    db.refresh(machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(machine.project_id)

    return success_response(
        data=machine,
        message="机台进度更新成功"
    )


# ========== 删除端点（保留原逻辑，包含BOM检查） ==========

@router.delete(
    "/{machine_id}",
    response_model=SuccessResponse,
    status_code=200,
    summary="删除机台",
    description="删除机台，会检查是否有关联的BOM"
)
def delete_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> SuccessResponse:
    """
    删除机台
    
    会检查是否有关联的BOM，如果有则不允许删除
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 检查是否有关联的BOM
    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。"
        )

    db.delete(machine)
    db.commit()

    return success_response(
        data=None,
        message="机台已删除"
    )


# ========== 其他特殊端点（保留原逻辑） ==========

@router.get(
    "/{machine_id}/bom",
    response_model=SuccessResponse[List],
    summary="获取机台BOM列表",
    description="获取机台的BOM列表"
)
def get_machine_bom(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> SuccessResponse[List]:
    """
    获取机台的BOM列表
    注意：实际的BOM列表API在 /api/v1/bom/machines/{machine_id}/bom
    这里提供快捷访问
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
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

    return success_response(
        data=result,
        message="获取成功"
    )


# 注意：以下项目相关端点已迁移至 /projects/{project_id}/machines/ 子路由
# - GET /projects/{project_id}/summary -> GET /projects/{project_id}/machines/summary
# - POST /projects/{project_id}/recalculate -> POST /projects/{project_id}/machines/recalculate
