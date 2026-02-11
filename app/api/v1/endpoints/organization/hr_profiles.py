# -*- coding: utf-8 -*-
"""
人事档案管理端点
"""

import io
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Employee, EmployeeHrProfile
from app.models.user import User
from app.schemas.organization import (
    EmployeeHrProfileResponse,
    EmployeeHrProfileUpdate,
    EmployeeWithHrProfileResponse,
)
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

router = APIRouter()


@router.get("/hr-profiles")
def get_hr_profiles(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="搜索关键词（姓名/工号/部门）"),
    dept_level1: Optional[str] = Query(None, description="一级部门筛选"),
    employment_status: Optional[str] = Query(None, description="在职状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """获取人事档案列表（分页）"""

    query = db.query(Employee).outerjoin(EmployeeHrProfile)

    query = apply_keyword_filter(query, Employee, keyword, ["name", "employee_code", "department"])

    if dept_level1:
        query = query.filter(EmployeeHrProfile.dept_level1 == dept_level1)

    if employment_status:
        query = query.filter(Employee.employment_status == employment_status)

    total = query.count()
    employees = query.order_by(Employee.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for emp in employees:
        profile = emp.hr_profile
        item = {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "name": emp.name,
            "department": emp.department,
            "role": emp.role,
            "phone": emp.phone,
            "is_active": emp.is_active,
            "employment_status": emp.employment_status,
            "employment_type": emp.employment_type,
            "id_card": emp.id_card,
            "hr_profile": None
        }
        if profile:
            item["hr_profile"] = {
                "id": profile.id,
                "dept_level1": profile.dept_level1,
                "dept_level2": profile.dept_level2,
                "dept_level3": profile.dept_level3,
                "position": profile.position,
                "job_level": profile.job_level,
                "hire_date": str(profile.hire_date) if profile.hire_date else None,
                "is_confirmed": profile.is_confirmed,
                "gender": profile.gender,
                "age": profile.age,
                "ethnicity": profile.ethnicity,
                "education_level": profile.education_level,
                "graduate_school": profile.graduate_school,
                "major": profile.major,
            }
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total)
    }


@router.get("/hr-profiles/{emp_id}", response_model=EmployeeWithHrProfileResponse)
def get_hr_profile(
    emp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定员工的人事档案详情"""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    return employee


@router.put("/hr-profiles/{emp_id}", response_model=EmployeeHrProfileResponse)
def update_hr_profile(
    emp_id: int,
    profile_in: EmployeeHrProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新员工人事档案"""
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    profile = db.query(EmployeeHrProfile).filter(EmployeeHrProfile.employee_id == emp_id).first()
    if not profile:
        profile = EmployeeHrProfile(employee_id=emp_id)
        db.add(profile)

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/hr-profiles/import")
async def import_hr_profiles(
    file: UploadFile = File(..., description="人事档案Excel文件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    批量导入人事档案数据

    从Excel文件导入完整的人事档案信息，包括：
    - 基本信息（姓名、部门、职务等）
    - 入职信息（入职时间、转正日期、合同期限等）
    - 个人信息（性别、年龄、民族、政治面貌等）
    - 联系信息（地址、紧急联系人等）
    - 教育背景（毕业院校、专业、学历等）
    - 财务社保（银行卡、社保号、公积金号等）

    系统会根据姓名匹配员工，已存在的员工会更新档案，不存在的会新建员工和档案。
    """
    from app.services.hr_profile_import_service import (
        import_hr_profiles_from_dataframe,
        validate_excel_file,
        validate_required_columns,
    )

    validate_excel_file(file.filename)

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")

    validate_required_columns(df)

    result = import_hr_profiles_from_dataframe(db, df)

    db.commit()

    return {
        "success": True,
        "message": f"导入完成：新增 {result['imported']} 人，更新 {result['updated']} 人，跳过 {result['skipped']} 条",
        "imported": result['imported'],
        "updated": result['updated'],
        "skipped": result['skipped'],
        "errors": result['errors']
    }


@router.get("/hr-profiles/statistics/overview")
def get_hr_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """获取人事统计概览"""
    total = db.query(Employee).filter(Employee.is_active == True).count()

    dept_stats = db.query(
        EmployeeHrProfile.dept_level1,
        func.count(EmployeeHrProfile.id)
    ).join(Employee).filter(Employee.is_active == True).group_by(
        EmployeeHrProfile.dept_level1
    ).all()

    status_stats = db.query(
        Employee.employment_status,
        func.count(Employee.id)
    ).group_by(Employee.employment_status).all()

    probation_count = db.query(Employee).filter(
        Employee.is_active == True,
        Employee.employment_type == 'probation'
    ).count()

    return {
        "total_active": total,
        "probation_count": probation_count,
        "by_department": [{"department": d[0] or "未分配", "count": d[1]} for d in dept_stats],
        "by_status": [{"status": s[0] or "未知", "count": s[1]} for s in status_stats],
    }
