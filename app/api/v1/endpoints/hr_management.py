# -*- coding: utf-8 -*-
"""
人事管理API端点
包含：人事事务（入职、离职、转正、调岗、晋升、调薪）、合同管理、合同到期提醒
"""

from typing import Any, List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.organization import (
    Employee, EmployeeHrProfile, HrTransaction,
    EmployeeContract, ContractReminder, SalaryRecord
)
from app.schemas.organization import (
    HrTransactionCreate, HrTransactionResponse,
    EmployeeContractCreate, EmployeeContractUpdate, EmployeeContractResponse,
    ContractReminderResponse
)

router = APIRouter()


# ==================== 人事事务 API ====================


@router.get("/transactions")
def get_hr_transactions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    transaction_type: Optional[str] = Query(None, description="事务类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """获取人事事务列表"""
    query = db.query(HrTransaction).join(Employee, HrTransaction.employee_id == Employee.id)

    if transaction_type:
        query = query.filter(HrTransaction.transaction_type == transaction_type)
    if status:
        query = query.filter(HrTransaction.status == status)
    if employee_id:
        query = query.filter(HrTransaction.employee_id == employee_id)
    if start_date:
        query = query.filter(HrTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(HrTransaction.transaction_date <= end_date)

    total = query.count()
    offset = (page - 1) * page_size
    transactions = query.order_by(HrTransaction.created_at.desc()).offset(offset).limit(page_size).all()

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
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.post("/transactions", response_model=HrTransactionResponse)
def create_hr_transaction(
    transaction_in: HrTransactionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """获取人事事务统计"""
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

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


# ==================== 合同管理 API ====================


@router.get("/contracts")
def get_contracts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    status: Optional[str] = Query(None, description="合同状态"),
    expiring_in_days: Optional[int] = Query(None, description="即将到期天数内"),
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    expired_soon = []

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


# ==================== 合同到期提醒 API ====================


@router.get("/contract-reminders")
def get_contract_reminders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """获取合同到期提醒列表"""
    query = db.query(ContractReminder).join(Employee)

    if status:
        query = query.filter(ContractReminder.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    reminders = query.order_by(ContractReminder.contract_end_date.asc()).offset(offset).limit(page_size).all()

    items = []
    for r in reminders:
        items.append({
            "id": r.id,
            "contract_id": r.contract_id,
            "employee_id": r.employee_id,
            "employee_name": r.employee.name if r.employee else None,
            "reminder_type": r.reminder_type,
            "reminder_date": str(r.reminder_date) if r.reminder_date else None,
            "contract_end_date": str(r.contract_end_date) if r.contract_end_date else None,
            "days_until_expiry": r.days_until_expiry,
            "status": r.status,
            "handle_action": r.handle_action,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.put("/contract-reminders/{reminder_id}/handle")
def handle_contract_reminder(
    reminder_id: int,
    action: str = Query(..., description="处理动作: renew, terminate, extend, ignore"),
    remark: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """处理合同到期提醒"""
    reminder = db.query(ContractReminder).filter(ContractReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒记录不存在")

    reminder.status = "handled"
    reminder.handled_at = datetime.now()
    reminder.handled_by = current_user.id
    reminder.handle_action = action
    reminder.handle_remark = remark

    db.commit()

    return {"success": True, "message": "提醒已处理"}


@router.post("/contract-reminders/generate")
def generate_contract_reminders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    生成合同到期提醒（手动触发，也可由定时任务调用）
    提前两个月、一个月、两周发送提醒
    """
    today = date.today()
    two_months_later = today + timedelta(days=60)
    one_month_later = today + timedelta(days=30)
    two_weeks_later = today + timedelta(days=14)

    # 查找需要提醒的合同
    contracts = db.query(EmployeeContract).join(Employee).filter(
        EmployeeContract.status == "active",
        EmployeeContract.end_date <= two_months_later,
        EmployeeContract.end_date >= today,
        Employee.is_active == True
    ).all()

    created_count = 0

    for contract in contracts:
        days_until = (contract.end_date - today).days if contract.end_date else 0

        # 确定提醒类型
        if days_until <= 14:
            reminder_type = "two_weeks"
        elif days_until <= 30:
            reminder_type = "one_month"
        else:
            reminder_type = "two_months"

        # 检查是否已有相同类型的提醒
        existing = db.query(ContractReminder).filter(
            ContractReminder.contract_id == contract.id,
            ContractReminder.reminder_type == reminder_type
        ).first()

        if not existing:
            reminder = ContractReminder(
                contract_id=contract.id,
                employee_id=contract.employee_id,
                reminder_type=reminder_type,
                reminder_date=today,
                contract_end_date=contract.end_date,
                days_until_expiry=days_until,
                status="pending"
            )
            db.add(reminder)
            created_count += 1

            # 更新合同的提醒状态
            contract.reminder_sent = True
            contract.reminder_sent_at = datetime.now()

    db.commit()

    return {
        "success": True,
        "message": f"已生成 {created_count} 条合同到期提醒",
        "created_count": created_count
    }


# ==================== 人事仪表板统计 ====================


@router.get("/dashboard/overview")
def get_hr_dashboard_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
