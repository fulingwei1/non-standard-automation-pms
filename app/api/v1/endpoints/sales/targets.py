# -*- coding: utf-8 -*-
"""
销售目标管理 API endpoints
"""

from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import SalesTarget
from app.models.organization import Department
from app.schemas.sales import (
    SalesTargetCreate, SalesTargetUpdate, SalesTargetResponse
)
from app.schemas.common import PaginatedResponse
from app.services.sales_team_service import SalesTeamService
from .utils import get_user_role_code

router = APIRouter()


# ==================== 销售目标管理 ====================


@router.get("/targets", response_model=PaginatedResponse)
def get_sales_targets(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    target_scope: Optional[str] = Query(None, description="目标范围筛选：PERSONAL/TEAM/DEPARTMENT"),
    target_type: Optional[str] = Query(None, description="目标类型筛选"),
    target_period: Optional[str] = Query(None, description="目标周期筛选：MONTHLY/QUARTERLY/YEARLY"),
    period_value: Optional[str] = Query(None, description="周期值筛选：2025-01/2025-Q1/2025"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.5: 获取销售目标列表
    支持多种筛选条件，并根据用户角色返回可见的目标
    """
    query = db.query(SalesTarget)

    # 根据用户角色确定可见范围
    user_role_code = get_user_role_code(db, current_user)

    if user_role_code == 'SALES_DIR':
        # 销售总监可以看到所有目标
        pass
    elif user_role_code == 'SALES_MANAGER':
        # 销售经理可以看到自己部门的目标
        # 注意：User表没有department_id字段，需要根据department字符串匹配
        dept_name = getattr(current_user, 'department', None)
        if dept_name:
            # 查找对应的部门ID
            dept = db.query(Department).filter(Department.dept_name == dept_name).first()
            if dept:
                query = query.filter(
                    or_(
                        SalesTarget.department_id == dept.id,
                        SalesTarget.user_id == current_user.id
                    )
                )
            else:
                query = query.filter(SalesTarget.user_id == current_user.id)
        else:
            query = query.filter(SalesTarget.user_id == current_user.id)
    else:
        # 其他角色只能看到自己的目标
        query = query.filter(SalesTarget.user_id == current_user.id)

    # 应用筛选条件
    if target_scope:
        query = query.filter(SalesTarget.target_scope == target_scope)
    if target_type:
        query = query.filter(SalesTarget.target_type == target_type)
    if target_period:
        query = query.filter(SalesTarget.target_period == target_period)
    if period_value:
        query = query.filter(SalesTarget.period_value == period_value)
    if user_id:
        query = query.filter(SalesTarget.user_id == user_id)
    if department_id:
        query = query.filter(SalesTarget.department_id == department_id)
    if status:
        query = query.filter(SalesTarget.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    targets = query.order_by(desc(SalesTarget.created_at)).offset(offset).limit(page_size).all()

    team_service = SalesTeamService(db)

    # 计算实际完成值和完成率
    items = []
    for target in targets:
        actual_value, completion_rate = team_service.calculate_target_performance(target)

        # 获取用户/部门名称
        user_name = None
        if target.user_id:
            user = db.query(User).filter(User.id == target.user_id).first()
            user_name = user.real_name or user.username if user else None

        department_name = None
        if target.department_id:
            dept = db.query(Department).filter(Department.id == target.department_id).first()
            department_name = dept.dept_name if dept else None

        items.append({
            "id": target.id,
            "target_scope": target.target_scope,
            "user_id": target.user_id,
            "department_id": target.department_id,
            "team_id": target.team_id,
            "target_type": target.target_type,
            "target_period": target.target_period,
            "period_value": target.period_value,
            "target_value": float(target.target_value),
            "description": target.description,
            "status": target.status,
            "created_by": target.created_by,
            "actual_value": float(actual_value),
            "completion_rate": completion_rate,
            "user_name": user_name,
            "department_name": department_name,
            "created_at": target.created_at,
            "updated_at": target.updated_at,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/targets", response_model=SalesTargetResponse, status_code=201)
def create_sales_target(
    *,
    db: Session = Depends(deps.get_db),
    target_data: SalesTargetCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.5: 创建销售目标
    """
    # 验证目标范围和数据
    if target_data.target_scope == "PERSONAL" and not target_data.user_id:
        raise HTTPException(status_code=400, detail="个人目标必须指定用户ID")
    if target_data.target_scope == "DEPARTMENT" and not target_data.department_id:
        raise HTTPException(status_code=400, detail="部门目标必须指定部门ID")

    # 创建目标
    target = SalesTarget(
        target_scope=target_data.target_scope,
        user_id=target_data.user_id,
        department_id=target_data.department_id,
        team_id=target_data.team_id,
        target_type=target_data.target_type,
        target_period=target_data.target_period,
        period_value=target_data.period_value,
        target_value=target_data.target_value,
        description=target_data.description,
        status=target_data.status or "ACTIVE",
        created_by=current_user.id,
    )

    db.add(target)
    db.commit()
    db.refresh(target)

    # 获取用户/部门名称
    user_name = None
    if target.user_id:
        user = db.query(User).filter(User.id == target.user_id).first()
        user_name = user.real_name or user.username if user else None

    department_name = None
    if target.department_id:
        dept = db.query(Department).filter(Department.id == target.department_id).first()
        department_name = dept.dept_name if dept else None

    return SalesTargetResponse(
        id=target.id,
        target_scope=target.target_scope,
        user_id=target.user_id,
        department_id=target.department_id,
        team_id=target.team_id,
        target_type=target.target_type,
        target_period=target.target_period,
        period_value=target.period_value,
        target_value=target.target_value,
        description=target.description,
        status=target.status,
        created_by=target.created_by,
        actual_value=None,
        completion_rate=None,
        user_name=user_name,
        department_name=department_name,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


@router.put("/targets/{target_id}", response_model=SalesTargetResponse)
def update_sales_target(
    *,
    db: Session = Depends(deps.get_db),
    target_id: int,
    target_data: SalesTargetUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.5: 更新销售目标
    """
    target = db.query(SalesTarget).filter(SalesTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    # 权限检查：只能修改自己创建的目标或自己部门的目标
    if target.created_by != current_user.id:
        user_role_code = get_user_role_code(db, current_user)
        if user_role_code != 'SALES_DIR':
            # User表没有department_id，需要通过department字符串匹配
            dept_name = getattr(current_user, 'department', None)
            if dept_name:
                dept = db.query(Department).filter(Department.dept_name == dept_name).first()
                if dept and target.department_id != dept.id:
                    raise HTTPException(status_code=403, detail="无权修改此目标")
            else:
                raise HTTPException(status_code=403, detail="无权修改此目标")

    # 更新字段
    if target_data.target_value is not None:
        target.target_value = target_data.target_value
    if target_data.description is not None:
        target.description = target_data.description
    if target_data.status is not None:
        target.status = target_data.status

    db.commit()
    db.refresh(target)

    # 获取用户/部门名称
    user_name = None
    if target.user_id:
        user = db.query(User).filter(User.id == target.user_id).first()
        user_name = user.real_name or user.username if user else None

    department_name = None
    if target.department_id:
        dept = db.query(Department).filter(Department.id == target.department_id).first()
        department_name = dept.dept_name if dept else None

    return SalesTargetResponse(
        id=target.id,
        target_scope=target.target_scope,
        user_id=target.user_id,
        department_id=target.department_id,
        team_id=target.team_id,
        target_type=target.target_type,
        target_period=target.target_period,
        period_value=target.period_value,
        target_value=target.target_value,
        description=target.description,
        status=target.status,
        created_by=target.created_by,
        actual_value=None,
        completion_rate=None,
        user_name=user_name,
        department_name=department_name,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )
