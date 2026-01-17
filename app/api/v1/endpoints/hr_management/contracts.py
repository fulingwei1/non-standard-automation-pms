# -*- coding: utf-8 -*-
"""
合同管理端点
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.organization import (
    Employee,
    EmployeeContract,
)
from app.models.user import User
from app.schemas.organization import (
    EmployeeContractCreate,
    EmployeeContractResponse,
    EmployeeContractUpdate,
)

router = APIRouter()


@router.get("/contracts")
def get_contracts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    status: Optional[str] = Query(None, description="合同状态"),
    expiring_in_days: Optional[int] = Query(None, description="即将到期天数内"),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取合同列表"""
    query = db.query(EmployeeContract).join(Employee)

    if employee_id:
        query = query.filter(EmployeeContract.employee_id == employee_id)
    if status:
        query = query.filter(EmployeeContract.status == status)
    if expiring_in_days:
        expiry_date = date.today() + timedelta(days=expiring_in_days)
        query = query.filter(
            EmployeeContract.status == "active",
            EmployeeContract.end_date <= expiry_date,
            EmployeeContract.end_date >= date.today()
        )

    total = query.count()
    offset = (page - 1) * page_size
    contracts = query.order_by(EmployeeContract.end_date.asc()).offset(offset).limit(page_size).all()

    items = []
    for c in contracts:
        days_until_expiry = None
        if c.end_date:
            days_until_expiry = (c.end_date - date.today()).days

        items.append({
            "id": c.id,
            "employee_id": c.employee_id,
            "employee_name": c.employee.name if c.employee else None,
            "employee_code": c.employee.employee_code if c.employee else None,
            "contract_no": c.contract_no,
            "contract_type": c.contract_type,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "duration_months": c.duration_months,
            "position": c.position,
            "department": c.department,
            "status": c.status,
            "sign_date": str(c.sign_date) if c.sign_date else None,
            "is_renewed": c.is_renewed,
            "renewal_count": c.renewal_count,
            "days_until_expiry": days_until_expiry,
            "reminder_sent": c.reminder_sent,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.post("/contracts", response_model=EmployeeContractResponse)
def create_contract(
    contract_in: EmployeeContractCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """创建员工合同"""
    # 验证员工存在
    employee = db.query(Employee).filter(Employee.id == contract_in.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    # 生成合同编号
    if not contract_in.contract_no:
        count = db.query(EmployeeContract).filter(
            EmployeeContract.employee_id == contract_in.employee_id
        ).count()
        contract_in.contract_no = f"HT-{employee.employee_code}-{count + 1:02d}"

    contract = EmployeeContract(**contract_in.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.put("/contracts/{contract_id}", response_model=EmployeeContractResponse)
def update_contract(
    contract_id: int,
    contract_in: EmployeeContractUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """更新员工合同"""
    contract = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    update_data = contract_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    db.commit()
    db.refresh(contract)
    return contract


@router.post("/contracts/{contract_id}/renew")
def renew_contract(
    contract_id: int,
    new_end_date: date,
    duration_months: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """续签合同"""
    old_contract = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not old_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 标记旧合同为已续签
    old_contract.status = "renewed"
    old_contract.is_renewed = True

    # 创建新合同
    new_contract = EmployeeContract(
        employee_id=old_contract.employee_id,
        contract_type=old_contract.contract_type,
        start_date=old_contract.end_date + timedelta(days=1) if old_contract.end_date else date.today(),
        end_date=new_end_date,
        duration_months=duration_months,
        position=old_contract.position,
        department=old_contract.department,
        work_location=old_contract.work_location,
        base_salary=old_contract.base_salary,
        status="active",
        sign_date=date.today(),
        renewal_count=old_contract.renewal_count + 1,
    )

    # 生成新合同编号
    employee = old_contract.employee
    new_contract.contract_no = f"HT-{employee.employee_code}-{old_contract.renewal_count + 2:02d}"

    # 关联旧合同
    old_contract.renewed_contract_id = None  # 稍后更新

    db.add(new_contract)
    db.commit()

    # 更新关联
    old_contract.renewed_contract_id = new_contract.id
    db.commit()

    return {
        "success": True,
        "message": "合同续签成功",
        "new_contract_id": new_contract.id,
        "new_contract_no": new_contract.contract_no
    }


@router.get("/contracts/expiring")
def get_expiring_contracts(
    db: Session = Depends(deps.get_db),
    days: int = Query(60, description="未来多少天内到期"),
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Dict[str, Any]:
    """获取即将到期的合同（用于提醒）"""
    expiry_date = date.today() + timedelta(days=days)

    contracts = db.query(EmployeeContract).join(Employee).filter(
        EmployeeContract.status == "active",
        EmployeeContract.end_date <= expiry_date,
        EmployeeContract.end_date >= date.today(),
        Employee.is_active == True
    ).order_by(EmployeeContract.end_date.asc()).all()

    # 分组：两个月内、一个月内、两周内
    two_months = []
    one_month = []
    two_weeks = []

    today = date.today()
    for c in contracts:
        days_until = (c.end_date - today).days if c.end_date else 0
        item = {
            "id": c.id,
            "employee_id": c.employee_id,
            "employee_name": c.employee.name if c.employee else None,
            "employee_code": c.employee.employee_code if c.employee else None,
            "department": c.department,
            "position": c.position,
            "contract_no": c.contract_no,
            "end_date": str(c.end_date) if c.end_date else None,
            "days_until_expiry": days_until,
            "reminder_sent": c.reminder_sent,
        }

        if days_until <= 14:
            two_weeks.append(item)
        elif days_until <= 30:
            one_month.append(item)
        elif days_until <= 60:
            two_months.append(item)

    return {
        "two_weeks": two_weeks,
        "one_month": one_month,
        "two_months": two_months,
        "total_expiring": len(contracts),
        "summary": {
            "two_weeks_count": len(two_weeks),
            "one_month_count": len(one_month),
            "two_months_count": len(two_months),
        }
    }
