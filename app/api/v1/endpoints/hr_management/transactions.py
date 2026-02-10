# -*- coding: utf-8 -*-
"""
人事事务端点（入职、离职、转正、调岗、晋升、调薪）
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.date_range import get_month_range_by_ym
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.organization import (
    Employee,
    EmployeeHrProfile,
    HrTransaction,
)
from app.models.user import User
from app.schemas.organization import (
    HrTransactionCreate,
    HrTransactionResponse,
)

router = APIRouter()


@router.get("/transactions")
def get_hr_transactions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    transaction_type: Optional[str] = Query(None, description="事务类型筛选"),
    transaction_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取人事事务列表"""
    query = db.query(HrTransaction).join(Employee, HrTransaction.employee_id == Employee.id)

    if transaction_type:
        query = query.filter(HrTransaction.transaction_type == transaction_type)
    if transaction_status:
        query = query.filter(HrTransaction.status == transaction_status)
    if employee_id:
        query = query.filter(HrTransaction.employee_id == employee_id)
    if start_date:
        query = query.filter(HrTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(HrTransaction.transaction_date <= end_date)

    total = query.count()
    transactions = query.order_by(HrTransaction.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for t in transactions:
        item = {
            "id": t.id,
            "employee_id": t.employee_id,
            "employee_name": t.employee.name if t.employee else None,
            "employee_code": t.employee.employee_code if t.employee else None,
            "transaction_type": t.transaction_type,
            "transaction_date": str(t.transaction_date) if t.transaction_date else None,
            "status": t.status,
            "created_at": str(t.created_at) if t.created_at else None,
        }
        # 根据事务类型添加相关字段
        if t.transaction_type == "onboarding":
            item.update({
                "onboard_date": str(t.onboard_date) if t.onboard_date else None,
                "initial_position": t.initial_position,
                "initial_department": t.initial_department,
            })
        elif t.transaction_type == "resignation":
            item.update({
                "resignation_date": str(t.resignation_date) if t.resignation_date else None,
                "last_working_date": str(t.last_working_date) if t.last_working_date else None,
                "resignation_reason": t.resignation_reason,
            })
        elif t.transaction_type == "confirmation":
            item.update({
                "confirmation_date": str(t.confirmation_date) if t.confirmation_date else None,
                "probation_evaluation": t.probation_evaluation,
            })
        elif t.transaction_type in ["promotion", "salary_adjustment"]:
            item.update({
                "from_level": t.from_level,
                "to_level": t.to_level,
                "from_salary": float(t.from_salary) if t.from_salary else None,
                "to_salary": float(t.to_salary) if t.to_salary else None,
                "salary_change_ratio": float(t.salary_change_ratio) if t.salary_change_ratio else None,
            })
        elif t.transaction_type == "transfer":
            item.update({
                "from_department": t.from_department,
                "to_department": t.to_department,
                "from_position": t.from_position,
                "to_position": t.to_position,
            })
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total)
    }


@router.post("/transactions", response_model=HrTransactionResponse)
def create_hr_transaction(
    transaction_in: HrTransactionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:create")),
) -> Any:
    """创建人事事务"""
    # 验证员工存在
    employee = db.query(Employee).filter(Employee.id == transaction_in.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    transaction = HrTransaction(
        **transaction_in.model_dump(),
        applicant_id=current_user.id,
        status="pending"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.put("/transactions/{transaction_id}/approve")
def approve_hr_transaction(
    transaction_id: int,
    approval_remark: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """审批人事事务"""
    transaction = db.query(HrTransaction).filter(HrTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="事务不存在")

    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail="只能审批待处理的事务")

    transaction.status = "approved"
    transaction.approver_id = current_user.id
    transaction.approved_at = datetime.now()
    transaction.approval_remark = approval_remark

    # 根据事务类型执行相应操作
    employee = transaction.employee
    profile = employee.hr_profile

    if transaction.transaction_type == "resignation":
        employee.is_active = False
        employee.employment_status = "resigned"
        if profile:
            profile.resignation_date = transaction.resignation_date

    elif transaction.transaction_type == "confirmation":
        employee.employment_type = "regular"
        if profile:
            profile.is_confirmed = True
            profile.probation_end_date = transaction.confirmation_date

    elif transaction.transaction_type == "transfer":
        if transaction.to_department:
            employee.department = transaction.to_department
        if transaction.to_position:
            employee.role = transaction.to_position
        if profile:
            if transaction.to_department:
                # 更新部门信息
                dept_parts = transaction.to_department.split("-")
                profile.dept_level1 = dept_parts[0] if len(dept_parts) > 0 else None
                profile.dept_level2 = dept_parts[1] if len(dept_parts) > 1 else None
                profile.dept_level3 = dept_parts[2] if len(dept_parts) > 2 else None
            if transaction.to_position:
                profile.position = transaction.to_position

    elif transaction.transaction_type == "promotion":
        if profile and transaction.to_level:
            profile.job_level = transaction.to_level

    transaction.status = "completed"
    db.commit()

    return {"success": True, "message": "事务审批完成"}


@router.get("/transactions/statistics")
def get_transaction_statistics(
    db: Session = Depends(deps.get_db),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取人事事务统计"""
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    start_date, end_date = get_month_range_by_ym(year, month)

    # 按类型统计本月事务
    type_stats = db.query(
        HrTransaction.transaction_type,
        func.count(HrTransaction.id)
    ).filter(
        HrTransaction.transaction_date >= start_date,
        HrTransaction.transaction_date <= end_date
    ).group_by(HrTransaction.transaction_type).all()

    # 统计待处理事务
    pending_count = db.query(HrTransaction).filter(
        HrTransaction.status == "pending"
    ).count()

    # 本月入职人数
    onboarding_count = db.query(HrTransaction).filter(
        HrTransaction.transaction_type == "onboarding",
        HrTransaction.transaction_date >= start_date,
        HrTransaction.transaction_date <= end_date,
        HrTransaction.status.in_(["approved", "completed"])
    ).count()

    # 本月离职人数
    resignation_count = db.query(HrTransaction).filter(
        HrTransaction.transaction_type == "resignation",
        HrTransaction.transaction_date >= start_date,
        HrTransaction.transaction_date <= end_date,
        HrTransaction.status.in_(["approved", "completed"])
    ).count()

    # 待转正人数（试用期即将到期）
    probation_due = db.query(Employee).join(EmployeeHrProfile).filter(
        Employee.is_active == True,
        Employee.employment_type == "probation",
        EmployeeHrProfile.probation_end_date <= now.date() + timedelta(days=30)
    ).count()

    return {
        "year": year,
        "month": month,
        "by_type": {t[0]: t[1] for t in type_stats},
        "pending_count": pending_count,
        "onboarding_count": onboarding_count,
        "resignation_count": resignation_count,
        "probation_due_count": probation_due,
    }
