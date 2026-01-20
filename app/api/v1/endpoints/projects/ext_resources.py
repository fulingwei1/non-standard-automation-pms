# -*- coding: utf-8 -*-
"""
项目资源管理
包含：资源分配CRUD、资源负载、资源统计
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.pmo import PmoResourceAllocation
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/projects/{project_id}/resources", response_model=ResponseModel)
def get_project_resources(
    project_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="状态"),
    resource_role: Optional[str] = Query(None, description="角色"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目资源分配列表

    Args:
        project_id: 项目ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        status: 状态筛选
        resource_role: 角色筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 资源列表
    """
    query = db.query(PmoResourceAllocation).filter(PmoResourceAllocation.project_id == project_id)

    if status:
        query = query.filter(PmoResourceAllocation.status == status)
    if resource_role:
        query = query.filter(PmoResourceAllocation.resource_role == resource_role)

    total = query.count()
    resources = query.order_by(PmoResourceAllocation.start_date).offset(skip).limit(limit).all()

    resources_data = [{
        "id": r.id,
        "resource_id": r.resource_id,
        "resource_name": r.resource_name,
        "resource_dept": r.resource_dept,
        "resource_role": r.resource_role,
        "allocation_percent": r.allocation_percent,
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "planned_hours": r.planned_hours,
        "actual_hours": r.actual_hours,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in resources]

    # 汇总
    total_planned = sum(r.planned_hours or 0 for r in resources)
    total_actual = sum(r.actual_hours or 0 for r in resources)

    return ResponseModel(
        code=200,
        message="获取资源分配列表成功",
        data={
            "total": total,
            "total_planned_hours": total_planned,
            "total_actual_hours": total_actual,
            "items": resources_data
        }
    )


@router.get("/projects/{project_id}/resources/summary", response_model=ResponseModel)
def get_resource_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目资源汇总

    Args:
        project_id: 项目ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 资源汇总
    """
    # 按角色汇总
    by_role = db.query(
        PmoResourceAllocation.resource_role,
        func.count(PmoResourceAllocation.id).label("count"),
        func.sum(PmoResourceAllocation.planned_hours).label("planned"),
        func.sum(PmoResourceAllocation.actual_hours).label("actual")
    ).filter(
        PmoResourceAllocation.project_id == project_id
    ).group_by(PmoResourceAllocation.resource_role).all()

    # 按部门汇总
    by_dept = db.query(
        PmoResourceAllocation.resource_dept,
        func.count(PmoResourceAllocation.id).label("count")
    ).filter(
        PmoResourceAllocation.project_id == project_id
    ).group_by(PmoResourceAllocation.resource_dept).all()

    # 总人数和工时
    totals = db.query(
        func.count(func.distinct(PmoResourceAllocation.resource_id)).label("total_members"),
        func.sum(PmoResourceAllocation.planned_hours).label("total_planned"),
        func.sum(PmoResourceAllocation.actual_hours).label("total_actual")
    ).filter(
        PmoResourceAllocation.project_id == project_id
    ).first()

    return ResponseModel(
        code=200,
        message="获取资源汇总成功",
        data={
            "project_id": project_id,
            "total_members": totals.total_members or 0 if totals else 0,
            "total_planned_hours": totals.total_planned or 0 if totals else 0,
            "total_actual_hours": totals.total_actual or 0 if totals else 0,
            "by_role": [{"role": r.resource_role, "count": r.count, "planned_hours": r.planned or 0, "actual_hours": r.actual or 0} for r in by_role],
            "by_dept": [{"dept": d.resource_dept, "count": d.count} for d in by_dept],
        }
    )


@router.post("/projects/{project_id}/resources", response_model=ResponseModel)
def create_resource_allocation(
    project_id: int,
    resource_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建资源分配

    Args:
        project_id: 项目ID
        resource_data: 资源数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已分配
    existing = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.resource_id == resource_data.get("resource_id"),
        PmoResourceAllocation.status != "RELEASED"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该资源已分配到此项目")

    allocation = PmoResourceAllocation(
        project_id=project_id,
        task_id=resource_data.get("task_id"),
        resource_id=resource_data.get("resource_id"),
        resource_name=resource_data.get("resource_name"),
        resource_dept=resource_data.get("resource_dept"),
        resource_role=resource_data.get("resource_role"),
        allocation_percent=resource_data.get("allocation_percent", 100),
        start_date=date.fromisoformat(resource_data["start_date"]) if resource_data.get("start_date") else None,
        end_date=date.fromisoformat(resource_data["end_date"]) if resource_data.get("end_date") else None,
        planned_hours=resource_data.get("planned_hours"),
        status="PLANNED",
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    return ResponseModel(
        code=200,
        message="资源分配成功",
        data={"id": allocation.id}
    )


@router.put("/projects/resources/{allocation_id}", response_model=ResponseModel)
def update_resource_allocation(
    allocation_id: int,
    resource_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新资源分配

    Args:
        allocation_id: 分配ID
        resource_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    allocation = db.query(PmoResourceAllocation).filter(PmoResourceAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="资源分配不存在")

    updatable = [
        "resource_role", "allocation_percent", "planned_hours",
        "actual_hours", "status"
    ]
    for field in updatable:
        if field in resource_data:
            setattr(allocation, field, resource_data[field])

    if "start_date" in resource_data:
        allocation.start_date = date.fromisoformat(resource_data["start_date"]) if resource_data["start_date"] else None
    if "end_date" in resource_data:
        allocation.end_date = date.fromisoformat(resource_data["end_date"]) if resource_data["end_date"] else None

    db.commit()

    return ResponseModel(code=200, message="资源分配更新成功", data={"id": allocation.id})


@router.post("/projects/resources/{allocation_id}/release", response_model=ResponseModel)
def release_resource(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    释放资源

    Args:
        allocation_id: 分配ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 释放结果
    """
    allocation = db.query(PmoResourceAllocation).filter(PmoResourceAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="资源分配不存在")

    if allocation.status == "RELEASED":
        raise HTTPException(status_code=400, detail="该资源已释放")

    allocation.status = "RELEASED"
    allocation.end_date = date.today()
    db.commit()

    return ResponseModel(code=200, message="资源已释放", data={"id": allocation.id})


@router.delete("/projects/resources/{allocation_id}", response_model=ResponseModel)
def delete_resource_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除资源分配

    Args:
        allocation_id: 分配ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    allocation = db.query(PmoResourceAllocation).filter(PmoResourceAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="资源分配不存在")

    if allocation.actual_hours and allocation.actual_hours > 0:
        raise HTTPException(status_code=400, detail="已有实际工时记录，不能删除")

    db.delete(allocation)
    db.commit()

    return ResponseModel(code=200, message="资源分配删除成功", data={"id": allocation_id})


@router.get("/resources/workload", response_model=ResponseModel)
def get_resource_workload(
    resource_id: int = Query(..., description="资源ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取资源工作负载

    Args:
        resource_id: 资源ID
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 工作负载
    """
    query = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.resource_id == resource_id,
        PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"])
    )

    if start_date:
        query = query.filter(PmoResourceAllocation.end_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(PmoResourceAllocation.start_date <= date.fromisoformat(end_date))

    allocations = query.all()

    projects = [{
        "project_id": a.project_id,
        "resource_role": a.resource_role,
        "allocation_percent": a.allocation_percent,
        "start_date": a.start_date.isoformat() if a.start_date else None,
        "end_date": a.end_date.isoformat() if a.end_date else None,
        "planned_hours": a.planned_hours,
        "actual_hours": a.actual_hours,
    } for a in allocations]

    total_allocation = sum(a.allocation_percent or 0 for a in allocations)

    return ResponseModel(
        code=200,
        message="获取工作负载成功",
        data={
            "resource_id": resource_id,
            "total_allocation_percent": total_allocation,
            "is_overloaded": total_allocation > 100,
            "projects": projects
        }
    )
