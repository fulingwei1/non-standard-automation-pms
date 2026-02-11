# -*- coding: utf-8 -*-
"""
员工档案 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.organization import Employee
from app.models.staff_matching import HrEmployeeProfile
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching import StaffMatchingService
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/", response_model=List[schemas.EmployeeProfileSummary])
def list_profiles(
    department: Optional[str] = Query(None, description="部门筛选"),
    employment_status: Optional[str] = Query(None, description="在职状态: active(在职), resigned(离职), all(全部)"),
    employment_type: Optional[str] = Query(None, description="员工类型: regular(正式), probation(试用期), intern(实习期)"),
    min_workload: Optional[float] = Query(None, description="最小工作负载"),
    max_workload: Optional[float] = Query(None, description="最大工作负载"),
    has_skill: Optional[int] = Query(None, description="包含技能ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工档案列表"""
    query = db.query(Employee, HrEmployeeProfile).outerjoin(
        HrEmployeeProfile, Employee.id == HrEmployeeProfile.employee_id
    )

    # 默认只显示在职员工，除非明确请求全部或离职
    if employment_status == 'all':
        pass  # 不过滤
    elif employment_status == 'resigned':
        query = query.filter(Employee.employment_status == 'resigned')
    else:
        # 默认显示在职员工
        query = query.filter(Employee.employment_status == 'active')

    # 员工类型筛选
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)

    query = apply_keyword_filter(query, Employee, department, "department")
    if min_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id == None,
                HrEmployeeProfile.current_workload_pct >= min_workload
            )
        )
    if max_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id == None,
                HrEmployeeProfile.current_workload_pct <= max_workload
            )
        )

    results = query.offset(pagination.offset).limit(pagination.limit).all()

    profiles = []
    for employee, profile in results:
        # 获取前3个技能
        top_skills = []
        if profile and profile.skill_tags:
            skill_tags = profile.skill_tags if isinstance(profile.skill_tags, list) else []
            top_skills = [s.get('tag_name', '') for s in skill_tags[:3]]

        profiles.append({
            'id': profile.id if profile else 0,
            'employee_id': employee.id,
            'employee_name': employee.name,
            'employee_code': employee.employee_code,
            'department': employee.department,
            'employment_status': getattr(employee, 'employment_status', 'active') or 'active',
            'employment_type': getattr(employee, 'employment_type', 'regular') or 'regular',
            'top_skills': top_skills,
            'attitude_score': profile.attitude_score if profile else None,
            'quality_score': profile.quality_score if profile else None,
            'current_workload_pct': profile.current_workload_pct if profile else 0,
            'available_hours': profile.available_hours if profile else 0,
            'total_projects': profile.total_projects if profile else 0,
            'avg_performance_score': profile.avg_performance_score if profile else None
        })

    return profiles


@router.get("/{employee_id}", response_model=schemas.EmployeeProfileResponse)
def get_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工档案详情"""
    profile = db.query(HrEmployeeProfile).filter(
        HrEmployeeProfile.employee_id == employee_id
    ).first()

    if not profile:
        # 尝试创建档案
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")

        profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    return profile


@router.post("/{employee_id}/refresh")
def refresh_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """刷新员工档案聚合数据"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    # 更新标签聚合
    profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    # 更新工作负载
    StaffMatchingService.update_employee_workload(db, employee_id)

    return {"message": "档案已刷新", "profile_id": profile.id}
