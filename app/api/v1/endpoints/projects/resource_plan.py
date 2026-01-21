# -*- coding: utf-8 -*-
"""
项目阶段资源计划 API

按阶段规划人员需求，支持分配、冲突检测、时间线视图
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.project import (
    AssignmentStatusEnum,
    Project,
    ProjectStage,
    ProjectStageResourcePlan,
    ResourceConflict,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== Schemas ====================

class ResourcePlanCreate(BaseModel):
    """创建资源计划"""
    stage_code: str = Field(..., description="阶段编码 S1-S9")
    role_code: str = Field(..., description="角色编码")
    role_name: Optional[str] = Field(None, description="角色名称")
    headcount: int = Field(1, ge=1, description="需求人数")
    allocation_pct: Decimal = Field(Decimal("100"), ge=0, le=100, description="分配比例%")
    planned_start: Optional[date] = Field(None, description="计划开始日期")
    planned_end: Optional[date] = Field(None, description="计划结束日期")
    remark: Optional[str] = Field(None, description="备注")
    staffing_need_id: Optional[int] = Field(None, description="关联的人员需求ID")


class ResourcePlanUpdate(BaseModel):
    """更新资源计划"""
    role_name: Optional[str] = None
    headcount: Optional[int] = Field(None, ge=1)
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remark: Optional[str] = None


class AssignEmployeeRequest(BaseModel):
    """分配员工请求"""
    employee_id: int = Field(..., description="员工ID")


class ResourcePlanResponse(BaseModel):
    """资源计划响应"""
    id: int
    project_id: int
    stage_code: str
    role_code: str
    role_name: Optional[str]
    headcount: int
    allocation_pct: float
    assignment_status: str
    assigned_employee_id: Optional[int]
    assigned_employee_name: Optional[str] = None
    planned_start: Optional[date]
    planned_end: Optional[date]
    remark: Optional[str]

    class Config:
        from_attributes = True


# ==================== API Endpoints ====================

@router.get("/projects/{project_id}/resource-plan", response_model=ResponseModel)
def get_project_resource_plan(
    project_id: int,
    db: Session = Depends(get_db),
    stage_code: Optional[str] = Query(None, description="阶段编码筛选"),
    status: Optional[str] = Query(None, description="分配状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目资源计划列表
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 构建查询
    query = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.project_id == project_id
    )

    if stage_code:
        query = query.filter(ProjectStageResourcePlan.stage_code == stage_code)
    if status:
        query = query.filter(ProjectStageResourcePlan.assignment_status == status)

    plans = query.order_by(
        ProjectStageResourcePlan.stage_code,
        ProjectStageResourcePlan.role_code
    ).all()

    # 补充员工姓名
    result = []
    for plan in plans:
        plan_dict = {
            "id": plan.id,
            "project_id": plan.project_id,
            "stage_code": plan.stage_code,
            "role_code": plan.role_code,
            "role_name": plan.role_name,
            "headcount": plan.headcount,
            "allocation_pct": float(plan.allocation_pct) if plan.allocation_pct else 100.0,
            "assignment_status": plan.assignment_status,
            "assigned_employee_id": plan.assigned_employee_id,
            "assigned_employee_name": plan.assigned_employee.username if plan.assigned_employee else None,
            "planned_start": plan.planned_start,
            "planned_end": plan.planned_end,
            "remark": plan.remark,
        }
        result.append(plan_dict)

    return ResponseModel(data=result)


@router.post("/projects/{project_id}/resource-plan", response_model=ResponseModel)
def create_resource_plan(
    project_id: int,
    plan_in: ResourcePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建阶段资源需求
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 创建资源计划
    plan = ProjectStageResourcePlan(
        project_id=project_id,
        stage_code=plan_in.stage_code,
        role_code=plan_in.role_code,
        role_name=plan_in.role_name,
        headcount=plan_in.headcount,
        allocation_pct=plan_in.allocation_pct,
        planned_start=plan_in.planned_start,
        planned_end=plan_in.planned_end,
        remark=plan_in.remark,
        staffing_need_id=plan_in.staffing_need_id,
        created_by=current_user.id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return ResponseModel(data={"id": plan.id, "message": "资源计划创建成功"})


@router.get("/projects/{project_id}/resource-plan/summary", response_model=ResponseModel)
def get_resource_plan_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取资源计划摘要（按阶段汇总）
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目阶段信息
    stages = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).order_by(ProjectStage.stage_order).all()

    # 获取所有资源计划
    plans = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.project_id == project_id
    ).all()

    # 按阶段组织
    stage_map = {}
    for plan in plans:
        if plan.stage_code not in stage_map:
            stage_map[plan.stage_code] = []
        stage_map[plan.stage_code].append(plan)

    # 构建摘要
    stage_summaries = []
    total_required = 0
    total_assigned = 0

    for stage in stages:
        stage_plans = stage_map.get(stage.stage_code, [])
        requirements = []

        for plan in stage_plans:
            total_required += plan.headcount
            assigned_count = 1 if plan.assigned_employee_id else 0
            total_assigned += assigned_count

            requirements.append({
                "plan_id": plan.id,
                "role_code": plan.role_code,
                "role_name": plan.role_name,
                "headcount": plan.headcount,
                "allocation_pct": float(plan.allocation_pct) if plan.allocation_pct else 100.0,
                "status": plan.assignment_status,
                "assigned_employees": [
                    {"id": plan.assigned_employee_id, "name": plan.assigned_employee.username}
                ] if plan.assigned_employee else [],
            })

        fill_rate = (sum(1 for p in stage_plans if p.assigned_employee_id) / len(stage_plans) * 100) if stage_plans else 0

        stage_summaries.append({
            "stage_code": stage.stage_code,
            "stage_name": stage.stage_name,
            "planned_start": stage.planned_start_date,
            "planned_end": stage.planned_end_date,
            "requirements": requirements,
            "fill_rate": round(fill_rate, 1),
        })

    overall_fill_rate = (total_assigned / total_required * 100) if total_required > 0 else 0

    return ResponseModel(data={
        "project_id": project_id,
        "project_no": project.project_no,
        "project_name": project.project_name,
        "stages": stage_summaries,
        "overall_fill_rate": round(overall_fill_rate, 1),
        "total_required": total_required,
        "total_assigned": total_assigned,
    })


@router.post("/projects/{project_id}/resource-plan/{plan_id}/assign", response_model=ResponseModel)
def assign_employee_to_plan(
    project_id: int,
    plan_id: int,
    request: AssignEmployeeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分配人员到资源计划
    """
    # 获取计划
    plan = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.id == plan_id,
        ProjectStageResourcePlan.project_id == project_id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")

    # 验证员工
    employee = db.query(User).filter(User.id == request.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    # 检查冲突
    conflicts = _detect_conflicts_for_assignment(db, request.employee_id, plan)

    # 分配员工
    plan.assigned_employee_id = request.employee_id
    plan.assignment_status = (
        AssignmentStatusEnum.CONFLICT.value if conflicts
        else AssignmentStatusEnum.ASSIGNED.value
    )

    # 记录冲突
    for conflict_data in conflicts:
        conflict = ResourceConflict(
            employee_id=request.employee_id,
            plan_a_id=plan_id,
            plan_b_id=conflict_data["plan_id"],
            overlap_start=conflict_data["overlap_start"],
            overlap_end=conflict_data["overlap_end"],
            total_allocation=conflict_data["total_allocation"],
            over_allocation=conflict_data["over_allocation"],
            severity=conflict_data["severity"],
        )
        db.add(conflict)

    db.commit()

    return ResponseModel(data={
        "message": "分配成功" if not conflicts else "分配成功，但存在资源冲突",
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
    })


@router.post("/projects/{project_id}/resource-plan/{plan_id}/release", response_model=ResponseModel)
def release_employee_from_plan(
    project_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    释放人员
    """
    plan = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.id == plan_id,
        ProjectStageResourcePlan.project_id == project_id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")

    # 释放
    plan.assigned_employee_id = None
    plan.assignment_status = AssignmentStatusEnum.RELEASED.value

    # 解决相关冲突
    db.query(ResourceConflict).filter(
        or_(
            ResourceConflict.plan_a_id == plan_id,
            ResourceConflict.plan_b_id == plan_id,
        )
    ).update({"is_resolved": 1, "resolution_note": "资源已释放"})

    db.commit()

    return ResponseModel(data={"message": "释放成功"})


@router.get("/projects/{project_id}/resource-plan/timeline", response_model=ResponseModel)
def get_resource_timeline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取资源时间线视图（用于甘特图展示）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    plans = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.project_id == project_id,
        ProjectStageResourcePlan.planned_start.isnot(None),
        ProjectStageResourcePlan.planned_end.isnot(None),
    ).order_by(ProjectStageResourcePlan.planned_start).all()

    timeline = []
    for plan in plans:
        timeline.append({
            "id": plan.id,
            "stage_code": plan.stage_code,
            "role_code": plan.role_code,
            "role_name": plan.role_name,
            "employee_name": plan.assigned_employee.username if plan.assigned_employee else None,
            "start": plan.planned_start.isoformat() if plan.planned_start else None,
            "end": plan.planned_end.isoformat() if plan.planned_end else None,
            "allocation_pct": float(plan.allocation_pct) if plan.allocation_pct else 100.0,
            "status": plan.assignment_status,
        })

    return ResponseModel(data={
        "project_id": project_id,
        "project_name": project.project_name,
        "timeline": timeline,
    })


# ==================== Helper Functions ====================

def _detect_conflicts_for_assignment(
    db: Session,
    employee_id: int,
    new_plan: ProjectStageResourcePlan,
) -> List[Dict[str, Any]]:
    """
    检测分配时的资源冲突
    """
    if not new_plan.planned_start or not new_plan.planned_end:
        return []

    # 查找该员工的其他分配
    existing_plans = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.assigned_employee_id == employee_id,
        ProjectStageResourcePlan.id != new_plan.id,
        ProjectStageResourcePlan.assignment_status.in_([
            AssignmentStatusEnum.ASSIGNED.value,
            AssignmentStatusEnum.CONFLICT.value,
        ]),
        ProjectStageResourcePlan.planned_start.isnot(None),
        ProjectStageResourcePlan.planned_end.isnot(None),
    ).all()

    conflicts = []
    for existing in existing_plans:
        # 检查时间重叠
        overlap_start = max(new_plan.planned_start, existing.planned_start)
        overlap_end = min(new_plan.planned_end, existing.planned_end)

        if overlap_start <= overlap_end:
            # 计算重叠期间的总分配
            new_alloc = float(new_plan.allocation_pct) if new_plan.allocation_pct else 100.0
            existing_alloc = float(existing.allocation_pct) if existing.allocation_pct else 100.0
            total_alloc = new_alloc + existing_alloc
            over_alloc = max(0, total_alloc - 100)

            # 确定严重程度
            if total_alloc > 150:
                severity = "HIGH"
            elif total_alloc > 120:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            if total_alloc > 100:
                conflicts.append({
                    "plan_id": existing.id,
                    "project_id": existing.project_id,
                    "stage_code": existing.stage_code,
                    "overlap_start": overlap_start,
                    "overlap_end": overlap_end,
                    "total_allocation": total_alloc,
                    "over_allocation": over_alloc,
                    "severity": severity,
                })

    return conflicts
