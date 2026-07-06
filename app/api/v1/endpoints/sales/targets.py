# -*- coding: utf-8 -*-
"""
销售目标管理 API endpoints
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.organization import Department
from app.models.sales import SalesTarget
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import SalesTargetCreate, SalesTargetResponse, SalesTargetUpdate
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.db_helpers import get_or_404

from .utils import get_user_role_code

router = APIRouter()


# ==================== 销售目标管理 ====================


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _sales_target_audit_value(target: SalesTarget) -> dict[str, Any]:
    fields = [
        "id",
        "tenant_id",
        "target_scope",
        "user_id",
        "department_id",
        "team_id",
        "target_type",
        "target_period",
        "period_value",
        "target_value",
        "description",
        "status",
        "created_by",
    ]
    return {field: _audit_scalar(getattr(target, field, None)) for field in fields}


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_sales_target_operation(
    db: Session,
    target: SalesTarget,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.TARGET,
        entity_id=target.id,
        operation_type=operation_type,
        operator=operator,
        entity_code=f"{target.target_type}-{target.period_value}",
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=target.description,
    )


@router.get("/targets", response_model=PaginatedResponse)
def get_sales_targets(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    target_scope: Optional[str] = Query(None, description="目标范围筛选：PERSONAL/TEAM/DEPARTMENT"),
    target_type: Optional[str] = Query(None, description="目标类型筛选"),
    target_period: Optional[str] = Query(
        None, description="目标周期筛选：MONTHLY/QUARTERLY/YEARLY"
    ),
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

    if user_role_code == "SALES_DIR":
        # 销售总监可以看到所有目标
        pass
    elif user_role_code == "SALES_MANAGER":
        # 销售经理可以看到自己部门的目标
        # 注意：User表没有department_id字段，需要根据department字符串匹配
        dept_name = getattr(current_user, "department", None)
        if dept_name:
            # 查找对应的部门ID
            dept = db.query(Department).filter(Department.dept_name == dept_name).first()
            if dept:
                query = query.filter(
                    or_(
                        SalesTarget.department_id == dept.id, SalesTarget.user_id == current_user.id
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
    targets = apply_pagination(
        query.order_by(desc(SalesTarget.created_at)), pagination.offset, pagination.limit
    ).all()

    # 计算实际完成值和完成率（SALES-08：个人目标按真实业务数据实时回填）
    from app.services.sales_team_service import SalesTeamService

    performance_service = SalesTeamService(db)
    items = []
    for target in targets:
        # 口径：LEAD/OPPORTUNITY 按 owner 计数，CONTRACT_AMOUNT 按合同负责人金额，
        # COLLECTION_AMOUNT 按发票实收；达成率 = actual/target*100。
        # 团队/部门级目标暂无归集口径，返回 0（见 FUNCTIONAL_AUDIT_TRACKER SALES-08 备注）。
        actual_value, completion_rate = performance_service.calculate_target_performance(target)

        # 获取用户/部门名称
        user_name = None
        if target.user_id:
            user = db.query(User).filter(User.id == target.user_id).first()
            user_name = user.real_name or user.username if user else None

        department_name = None
        if target.department_id:
            dept = db.query(Department).filter(Department.id == target.department_id).first()
            department_name = dept.dept_name if dept else None

        items.append(
            {
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
            }
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
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
    db.flush()
    _log_sales_target_operation(
        db,
        target,
        SalesOperationType.CREATE,
        current_user,
        new_value=_sales_target_audit_value(target),
        operation_desc="创建销售目标",
    )
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
    target = get_or_404(db, SalesTarget, target_id, detail="目标不存在")

    # 权限检查：只能修改自己创建的目标或自己部门的目标
    if target.created_by != current_user.id:
        user_role_code = get_user_role_code(db, current_user)
        if user_role_code != "SALES_DIR":
            # User表没有department_id，需要通过department字符串匹配
            dept_name = getattr(current_user, "department", None)
            if dept_name:
                dept = db.query(Department).filter(Department.dept_name == dept_name).first()
                if dept and target.department_id != dept.id:
                    raise HTTPException(status_code=403, detail="无权修改此目标")
            else:
                raise HTTPException(status_code=403, detail="无权修改此目标")

    old_value = _sales_target_audit_value(target)

    # 更新字段
    if target_data.target_value is not None:
        target.target_value = target_data.target_value
    if target_data.description is not None:
        target.description = target_data.description
    if target_data.status is not None:
        target.status = target_data.status

    db.flush()
    _log_sales_target_operation(
        db,
        target,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=_sales_target_audit_value(target),
        operation_desc="更新销售目标",
    )
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
