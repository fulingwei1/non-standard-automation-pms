# -*- coding: utf-8 -*-
"""
项目机台 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
复杂逻辑通过覆盖端点实现
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.project import (
    MachineCreate,
    MachineUpdate,
    MachineResponse
)


def filter_by_stage(query, stage: str):
    """自定义阶段筛选器"""
    return query.filter(Machine.stage == stage)


def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(Machine.status == status)


def filter_by_health(query, health: str):
    """自定义健康度筛选器"""
    return query.filter(Machine.health == health)


# 使用项目中心CRUD路由基类创建路由
base_router = create_project_crud_router(
    model=Machine,
    create_schema=MachineCreate,
    update_schema=MachineUpdate,
    response_schema=MachineResponse,
    permission_prefix="machine",
    project_id_field="project_id",
    keyword_fields=["machine_name", "machine_code", "specification"],
    default_order_by="created_at",
    default_order_direction="desc",
    custom_filters={
        "stage": filter_by_stage,      # 支持 ?stage=S1 筛选
        "status": filter_by_status,    # 支持 ?status=ST01 筛选
        "health": filter_by_health,   # 支持 ?health=H1 筛选
    },
)

# 创建新的router，先添加覆盖的端点，再添加基类的其他端点
router = APIRouter()

# 覆盖创建端点，添加自动生成编码和聚合数据更新逻辑
# 注意：在FastAPI中，后注册的路由会覆盖先注册的路由（如果路径和方法相同）
# 所以我们需要先添加覆盖端点，再添加基类的其他端点
@router.post("/", response_model=MachineResponse, status_code=201)
def create_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_in: MachineCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """
    为项目创建机台（覆盖基类端点，添加自动生成编码逻辑）
    
    机台编码自动生成格式：{项目编码}-PN{序号}
    例如：PJ250712001-PN001
    """
    from app.services.machine_service import MachineService, ProjectAggregationService
    from app.utils.permission_helpers import check_project_access_or_raise
    
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建机台")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 准备机台数据，强制使用路径中的 project_id
    machine_data = machine_in.model_dump(exclude_unset=True)
    machine_data["project_id"] = project_id
    machine_service = MachineService(db)
    
    # 自动生成机台编码（如果未提供或为None）
    # 注意：exclude_unset=True 会排除未设置的字段，所以需要从原始Schema获取
    provided_machine_code = getattr(machine_in, 'machine_code', None)
    
    # 确保machine_code一定存在
    if provided_machine_code is None or (isinstance(provided_machine_code, str) and not provided_machine_code.strip()):
        # 自动生成编码
        machine_code, machine_no = machine_service.generate_machine_code(project_id)
        machine_data["machine_code"] = machine_code
        machine_data["machine_no"] = machine_no
    else:
        # 使用提供的编码，检查是否已存在
        existing = db.query(Machine).filter(
            Machine.project_id == project_id,
            Machine.machine_code == provided_machine_code,
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="该机台编码已在此项目中存在",
            )
        machine_data["machine_code"] = provided_machine_code
        # 如果提供了machine_no，使用提供的；否则使用默认值1
        if "machine_no" not in machine_data:
            machine_data["machine_no"] = getattr(machine_in, 'machine_no', None) or 1
    
    # 双重保险：确保machine_code已设置（防止任何意外情况）
    if "machine_code" not in machine_data or not machine_data.get("machine_code"):
        machine_code, machine_no = machine_service.generate_machine_code(project_id)
        machine_data["machine_code"] = machine_code
        machine_data["machine_no"] = machine_no
    
    machine = Machine(**machine_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)
    
    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)
    
    return machine


# 覆盖更新端点，添加阶段验证和聚合数据更新逻辑
@router.put("/{machine_id}", response_model=MachineResponse)
def update_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    machine_in: MachineUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    更新项目机台信息（覆盖基类端点，添加阶段验证逻辑）
    
    - 阶段变更会验证是否合法（只能向前推进）
    - 状态变更会验证是否在有效范围内
    - 更新后自动重新计算项目的聚合数据
    """
    from app.services.machine_service import (
        MachineService,
        ProjectAggregationService,
        VALID_HEALTH,
        VALID_STAGES,
    )
    from app.utils.permission_helpers import check_project_access_or_raise
    
    check_project_access_or_raise(db, current_user, project_id)
    
    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    update_data = machine_in.model_dump(exclude_unset=True)
    machine_service = MachineService(db)
    
    # 验证阶段变更是否合法
    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage not in VALID_STAGES:
            raise HTTPException(
                status_code=400, detail=f"无效的阶段值: {new_stage}，有效值为 S1-S9"
            )
        
        is_valid, error_msg = machine_service.validate_stage_transition(machine.stage, new_stage)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
    
    # 验证健康度是否有效
    if "health" in update_data:
        new_health = update_data["health"]
        if new_health not in VALID_HEALTH:
            raise HTTPException(
                status_code=400, detail=f"无效的健康度: {new_health}，有效值为 H1-H4"
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
    aggregation_service.update_project_aggregation(project_id)
    
    return machine


# 覆盖删除端点，添加BOM检查逻辑
@router.delete("/{machine_id}", status_code=204)
def delete_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:delete")),
):
    """删除项目机台（覆盖基类端点，添加BOM检查逻辑）"""
    from app.models.material import BomHeader
    from app.utils.permission_helpers import check_project_access_or_raise
    
    check_project_access_or_raise(db, current_user, project_id)
    
    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    # 检查是否有关联的BOM
    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。",
        )
    
    db.delete(machine)
    db.commit()


# 从基类router中复制其他端点（列表、详情），排除已覆盖的端点
# 注意：我们需要手动复制列表和详情端点，因为创建、更新、删除已经被覆盖
for route in base_router.routes:
    # 只复制列表和详情端点，跳过创建、更新、删除（已覆盖）
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        # 列表端点: GET /
        if route.path == "/" and "GET" in route.methods:
            router.routes.append(route)
        # 详情端点: GET /{item_id}
        elif route.path == "/{item_id}" and "GET" in route.methods:
            router.routes.append(route)
