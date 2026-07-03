# -*- coding: utf-8 -*-
"""
员工档案 API端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.organization import Employee
from app.models.staff_matching import HrEmployeeProfile
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching import StaffMatchingService
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _as_json_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _normalize_profile_object(profile: HrEmployeeProfile) -> HrEmployeeProfile:
    if profile.total_projects is None:
        profile.total_projects = 0
    if profile.current_workload_pct is None:
        profile.current_workload_pct = 0
    if profile.available_hours is None:
        profile.available_hours = 0
    for field in (
        "skill_tags",
        "domain_tags",
        "attitude_tags",
        "character_tags",
        "special_tags",
    ):
        if getattr(profile, field, None) is not None and not isinstance(getattr(profile, field), list):
            setattr(profile, field, [])
    return profile


def _build_profile_summary(employee: Employee, profile: Optional[HrEmployeeProfile]) -> dict:
    top_skills = []
    if profile:
        skill_tags = _as_json_list(profile.skill_tags)
        top_skills = [
            skill.get("tag_name", "")
            for skill in skill_tags[:3]
            if isinstance(skill, dict)
        ]

    return {
        "id": profile.id if profile else 0,
        "employee_id": employee.id,
        "employee_name": employee.name,
        "employee_code": employee.employee_code,
        "department": employee.department,
        "employment_status": getattr(employee, "employment_status", "active") or "active",
        "employment_type": getattr(employee, "employment_type", "regular") or "regular",
        "top_skills": top_skills,
        "attitude_score": profile.attitude_score if profile else None,
        "quality_score": profile.quality_score if profile else None,
        "current_workload_pct": profile.current_workload_pct if profile and profile.current_workload_pct is not None else 0,
        "available_hours": profile.available_hours if profile and profile.available_hours is not None else 0,
        "total_projects": profile.total_projects if profile and profile.total_projects is not None else 0,
        "avg_performance_score": profile.avg_performance_score if profile else None,
    }


@router.get("/", response_model=List[schemas.EmployeeProfileSummary])
def list_profiles(
    department: Optional[str] = Query(None, description="部门筛选"),
    employment_status: Optional[str] = Query(
        None, description="在职状态: active(在职), resigned(离职), all(全部)"
    ),
    employment_type: Optional[str] = Query(
        None, description="员工类型: regular(正式), probation(试用期), intern(实习期)"
    ),
    min_workload: Optional[float] = Query(None, description="最小工作负载"),
    max_workload: Optional[float] = Query(None, description="最大工作负载"),
    has_skill: Optional[int] = Query(None, description="包含技能ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read")),
):
    """获取员工档案列表"""
    query = db.query(Employee, HrEmployeeProfile).outerjoin(
        HrEmployeeProfile, Employee.id == HrEmployeeProfile.employee_id
    )

    # 默认只显示在职员工，除非明确请求全部或离职
    if employment_status == "all":
        pass  # 不过滤
    elif employment_status == "resigned":
        query = query.filter(Employee.employment_status == "resigned")
    else:
        # 默认显示在职员工
        query = query.filter(Employee.employment_status == "active")

    # 员工类型筛选
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)

    query = apply_keyword_filter(query, Employee, department, "department")
    if min_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id.is_(None),
                HrEmployeeProfile.current_workload_pct >= min_workload,
            )
        )
    if max_workload is not None:
        query = query.filter(
            or_(
                HrEmployeeProfile.id.is_(None),
                HrEmployeeProfile.current_workload_pct <= max_workload,
            )
        )

    results = apply_pagination(query, pagination.offset, pagination.limit).all()

    profiles = []
    for employee, profile in results:
        profiles.append(_build_profile_summary(employee, profile))

    return profiles


@router.get("/{employee_id}", response_model=schemas.EmployeeProfileResponse)
def get_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read")),
):
    """获取员工档案详情"""
    profile = (
        db.query(HrEmployeeProfile).filter(HrEmployeeProfile.employee_id == employee_id).first()
    )

    if not profile:
        # 尝试创建档案
        get_or_404(db, Employee, employee_id, "员工不存在")

        profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    return _normalize_profile_object(profile)


@router.post("/{employee_id}/refresh")
def refresh_profile(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read")),
):
    """刷新员工档案聚合数据"""
    get_or_404(db, Employee, employee_id, "员工不存在")

    # 更新标签聚合
    profile = StaffMatchingService.aggregate_employee_profile(db, employee_id)

    # 更新工作负载
    StaffMatchingService.update_employee_workload(db, employee_id)

    return {"message": "档案已刷新", "profile_id": profile.id}
