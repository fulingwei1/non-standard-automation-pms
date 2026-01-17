# -*- coding: utf-8 -*-
"""
人事仪表板统计端点
"""

from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import (
    ContractReminder,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
)
from app.models.user import User

router = APIRouter()


@router.get("/dashboard/overview")
def get_hr_dashboard_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取人事管理仪表板概览数据"""
    today = date.today()
    this_month_start = date(today.year, today.month, 1)

    # 在职员工总数
    total_active = db.query(Employee).filter(Employee.is_active == True).count()

    # 试用期员工数
    probation_count = db.query(Employee).filter(
        Employee.is_active == True,
        Employee.employment_type == "probation"
    ).count()

    # 本月入职
    onboarding_this_month = db.query(HrTransaction).filter(
        HrTransaction.transaction_type == "onboarding",
        HrTransaction.transaction_date >= this_month_start,
        HrTransaction.status.in_(["approved", "completed"])
    ).count()

    # 本月离职
    resignation_this_month = db.query(HrTransaction).filter(
        HrTransaction.transaction_type == "resignation",
        HrTransaction.transaction_date >= this_month_start,
        HrTransaction.status.in_(["approved", "completed"])
    ).count()

    # 待处理事务
    pending_transactions = db.query(HrTransaction).filter(
        HrTransaction.status == "pending"
    ).count()

    # 即将到期合同（60天内）
    expiring_contracts = db.query(EmployeeContract).filter(
        EmployeeContract.status == "active",
        EmployeeContract.end_date <= today + timedelta(days=60),
        EmployeeContract.end_date >= today
    ).count()

    # 待处理合同提醒
    pending_reminders = db.query(ContractReminder).filter(
        ContractReminder.status == "pending"
    ).count()

    # 即将转正（30天内）
    confirmation_due = db.query(Employee).join(EmployeeHrProfile).filter(
        Employee.is_active == True,
        Employee.employment_type == "probation",
        EmployeeHrProfile.probation_end_date <= today + timedelta(days=30),
        EmployeeHrProfile.probation_end_date >= today
    ).count()

    # 按部门统计人数
    dept_stats = db.query(
        EmployeeHrProfile.dept_level1,
        func.count(EmployeeHrProfile.id)
    ).join(Employee).filter(
        Employee.is_active == True
    ).group_by(EmployeeHrProfile.dept_level1).all()

    return {
        "total_active": total_active,
        "probation_count": probation_count,
        "onboarding_this_month": onboarding_this_month,
        "resignation_this_month": resignation_this_month,
        "pending_transactions": pending_transactions,
        "expiring_contracts_60days": expiring_contracts,
        "pending_contract_reminders": pending_reminders,
        "confirmation_due_30days": confirmation_due,
        "by_department": [
            {"department": d[0] or "未分配", "count": d[1]}
            for d in dept_stats
        ],
        "alerts": {
            "total": pending_transactions + pending_reminders + confirmation_due,
            "transactions": pending_transactions,
            "contracts": pending_reminders,
            "confirmations": confirmation_due,
        }
    }


@router.get("/dashboard/pending-confirmations")
def get_pending_confirmations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> List[Dict[str, Any]]:
    """获取待转正员工列表"""
    today = date.today()

    employees = db.query(Employee).join(EmployeeHrProfile).filter(
        Employee.is_active == True,
        Employee.employment_type == "probation",
        EmployeeHrProfile.probation_end_date <= today + timedelta(days=60)
    ).order_by(EmployeeHrProfile.probation_end_date.asc()).limit(20).all()

    result = []
    for emp in employees:
        profile = emp.hr_profile
        days_until = (profile.probation_end_date - today).days if profile and profile.probation_end_date else 0
        result.append({
            "id": emp.id,
            "employee_code": emp.employee_code,
            "name": emp.name,
            "department": emp.department,
            "position": profile.position if profile else None,
            "hire_date": str(profile.hire_date) if profile and profile.hire_date else None,
            "probation_end_date": str(profile.probation_end_date) if profile and profile.probation_end_date else None,
            "days_until_confirmation": days_until,
            "status": "overdue" if days_until < 0 else ("urgent" if days_until <= 7 else "normal")
        })

    return result
