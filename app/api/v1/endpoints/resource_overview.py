# -*- coding: utf-8 -*-
"""
跨项目资源全景视图 API
- 人员跨项目分配时间线
- 冲突检测（总分配>100%）
- 部门/时间范围筛选
"""

from datetime import date, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ProjectAllocation(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    stage: Optional[str] = None
    role: Optional[str] = None
    allocation_pct: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    source: str  # "member" or "resource_plan"


class ConflictPeriod(BaseModel):
    start_date: date
    end_date: date
    total_allocation: float
    projects: List[str]


class EmployeeResourceProfile(BaseModel):
    user_id: int
    real_name: str
    department: Optional[str] = None
    total_projects: int
    current_allocation: float  # sum of active allocations
    max_allocation: float  # peak allocation
    allocations: List[ProjectAllocation]
    conflicts: List[ConflictPeriod]
    has_conflict: bool


class ResourceOverviewResponse(BaseModel):
    total_employees: int
    employees_with_conflicts: int
    total_conflicts: int
    avg_utilization: float
    employees: List[EmployeeResourceProfile]


class DepartmentSummary(BaseModel):
    department: str
    total_members: int
    assigned_members: int
    avg_utilization: float
    conflict_count: int


# ============================================================================
# Helper functions
# ============================================================================

def _detect_conflicts(allocations: List[ProjectAllocation], today: date) -> List[ConflictPeriod]:
    """Detect time periods where total allocation > 100%."""
    if not allocations:
        return []

    # Collect all date boundaries
    dates = set()
    for a in allocations:
        if a.start_date and a.end_date:
            dates.add(a.start_date)
            dates.add(a.end_date)

    if len(dates) < 2:
        return []

    sorted_dates = sorted(dates)
    conflicts = []

    for i in range(len(sorted_dates) - 1):
        period_start = sorted_dates[i]
        period_end = sorted_dates[i + 1]

        # Sum allocations active during this period
        total = 0.0
        project_names = []
        for a in allocations:
            if a.start_date and a.end_date:
                if a.start_date <= period_start and a.end_date >= period_end:
                    total += a.allocation_pct
                    project_names.append(a.project_name)

        if total > 100:
            # Merge with previous conflict if contiguous
            if conflicts and conflicts[-1].end_date == period_start and conflicts[-1].total_allocation == total:
                conflicts[-1].end_date = period_end
            else:
                conflicts.append(ConflictPeriod(
                    start_date=period_start,
                    end_date=period_end,
                    total_allocation=total,
                    projects=project_names,
                ))

    return conflicts


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/", response_model=ResourceOverviewResponse, summary="跨项目资源全景视图")
def get_resource_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    department: Optional[str] = Query(None, description="按部门筛选"),
    start_date: Optional[date] = Query(None, description="时间范围开始"),
    end_date: Optional[date] = Query(None, description="时间范围结束"),
    only_conflicts: bool = Query(False, description="仅显示有冲突的人员"),
    only_assigned: bool = Query(True, description="仅显示有分配的人员"),
) -> Any:
    """
    获取所有人员的跨项目资源分配全景视图。
    
    数据来源：
    1. project_members — 项目成员分配
    2. project_stage_resource_plan — 阶段资源计划
    """
    today = date.today()
    if not start_date:
        start_date = today - timedelta(days=30)
    if not end_date:
        end_date = today + timedelta(days=180)

    # Query 1: project_members allocations
    member_sql = text("""
        SELECT 
            pm.user_id,
            u.real_name,
            u.department,
            pm.project_id,
            p.project_name,
            p.project_code,
            p.stage,
            pm.role_code as role,
            COALESCE(pm.allocation_pct, 100) as allocation_pct,
            COALESCE(pm.start_date, p.planned_start_date) as start_date,
            COALESCE(pm.end_date, p.planned_end_date) as end_date
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        JOIN projects p ON pm.project_id = p.id
        WHERE pm.is_active = 1
          AND p.is_active = 1
          AND (:dept IS NULL OR u.department = :dept)
    """)

    member_rows = db.execute(member_sql, {"dept": department}).fetchall()

    # Query 2: project_stage_resource_plan allocations
    plan_sql = text("""
        SELECT 
            rp.assigned_employee_id as user_id,
            u.real_name,
            u.department,
            rp.project_id,
            p.project_name,
            p.project_code,
            rp.stage_code as stage,
            rp.role_name as role,
            COALESCE(rp.allocation_pct, 100) as allocation_pct,
            COALESCE(rp.planned_start, p.planned_start_date) as start_date,
            COALESCE(rp.planned_end, p.planned_end_date) as end_date
        FROM project_stage_resource_plan rp
        JOIN users u ON rp.assigned_employee_id = u.id
        JOIN projects p ON rp.project_id = p.id
        WHERE rp.assigned_employee_id IS NOT NULL
          AND p.is_active = 1
          AND (:dept IS NULL OR u.department = :dept)
    """)

    plan_rows = db.execute(plan_sql, {"dept": department}).fetchall()

    # Build employee profiles
    employee_map: dict[int, EmployeeResourceProfile] = {}

    def ensure_employee(user_id, real_name, department):
        if user_id not in employee_map:
            employee_map[user_id] = EmployeeResourceProfile(
                user_id=user_id,
                real_name=real_name or f"用户{user_id}",
                department=department,
                total_projects=0,
                current_allocation=0,
                max_allocation=0,
                allocations=[],
                conflicts=[],
                has_conflict=False,
            )
        return employee_map[user_id]

    for row in member_rows:
        emp = ensure_employee(row.user_id, row.real_name, row.department)
        emp.allocations.append(ProjectAllocation(
            project_id=row.project_id,
            project_name=row.project_name,
            project_code=row.project_code,
            stage=row.stage,
            role=row.role,
            allocation_pct=float(row.allocation_pct),
            start_date=row.start_date,
            end_date=row.end_date,
            source="member",
        ))

    for row in plan_rows:
        emp = ensure_employee(row.user_id, row.real_name, row.department)
        # Avoid duplicates (same project+user already from project_members)
        existing = {(a.project_id, a.source) for a in emp.allocations}
        if (row.project_id, "member") not in existing:
            emp.allocations.append(ProjectAllocation(
                project_id=row.project_id,
                project_name=row.project_name,
                project_code=row.project_code,
                stage=row.stage,
                role=row.role,
                allocation_pct=float(row.allocation_pct),
                start_date=row.start_date,
                end_date=row.end_date,
                source="resource_plan",
            ))

    # If only_assigned=False, also include unassigned employees
    if not only_assigned:
        all_users_sql = text("""
            SELECT id, real_name, department FROM users
            WHERE is_active = 1 AND (:dept IS NULL OR department = :dept)
        """)
        for row in db.execute(all_users_sql, {"dept": department}).fetchall():
            ensure_employee(row.id, row.real_name, row.department)

    # Calculate metrics for each employee
    total_conflicts = 0
    employees_with_conflicts = 0
    total_util = 0.0

    for emp in employee_map.values():
        project_ids = set(a.project_id for a in emp.allocations)
        emp.total_projects = len(project_ids)

        # Current allocation: sum of allocations active today
        emp.current_allocation = sum(
            a.allocation_pct for a in emp.allocations
            if a.start_date and a.end_date and a.start_date <= today <= a.end_date
        )

        # Detect conflicts
        emp.conflicts = _detect_conflicts(emp.allocations, today)
        emp.has_conflict = len(emp.conflicts) > 0
        if emp.has_conflict:
            employees_with_conflicts += 1
            total_conflicts += len(emp.conflicts)

        # Max allocation (peak)
        emp.max_allocation = max(
            [emp.current_allocation] + [c.total_allocation for c in emp.conflicts],
            default=0
        )

        total_util += emp.current_allocation

    employees = list(employee_map.values())

    # Filter
    if only_conflicts:
        employees = [e for e in employees if e.has_conflict]

    # Sort: conflicts first, then by current_allocation desc
    employees.sort(key=lambda e: (-int(e.has_conflict), -e.current_allocation))

    avg_util = total_util / len(employee_map) if employee_map else 0

    return ResourceOverviewResponse(
        total_employees=len(employee_map),
        employees_with_conflicts=employees_with_conflicts,
        total_conflicts=total_conflicts,
        avg_utilization=round(avg_util, 1),
        employees=employees,
    )


@router.get("/departments", response_model=List[DepartmentSummary], summary="部门资源汇总")
def get_department_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """按部门汇总资源分配情况。"""
    today = date.today()

    sql = text("""
        SELECT 
            u.department,
            COUNT(DISTINCT u.id) as total_members,
            COUNT(DISTINCT pm.user_id) as assigned_members,
            AVG(COALESCE(pm.allocation_pct, 0)) as avg_allocation
        FROM users u
        LEFT JOIN project_members pm ON u.id = pm.user_id AND pm.is_active = 1
        WHERE u.is_active = 1 AND u.department IS NOT NULL AND u.department != ''
        GROUP BY u.department
        ORDER BY assigned_members DESC
    """)

    rows = db.execute(sql).fetchall()
    results = []
    for row in rows:
        results.append(DepartmentSummary(
            department=row.department,
            total_members=row.total_members,
            assigned_members=row.assigned_members or 0,
            avg_utilization=round(float(row.avg_allocation or 0), 1),
            conflict_count=0,  # TODO: calculate per-dept conflicts
        ))

    return results


@router.get("/timeline", summary="资源时间线数据（甘特图用）")
def get_resource_timeline(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_id: Optional[int] = Query(None, description="指定用户"),
    department: Optional[str] = Query(None, description="按部门筛选"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
) -> Any:
    """返回适合甘特图/时间线渲染的资源分配数据。"""
    today = date.today()
    if not start_date:
        start_date = today - timedelta(days=30)
    if not end_date:
        end_date = today + timedelta(days=180)

    sql = text("""
        SELECT 
            pm.user_id,
            u.real_name,
            u.department,
            pm.project_id,
            p.project_name,
            p.project_code,
            p.stage,
            pm.role_code,
            COALESCE(pm.allocation_pct, 100) as allocation_pct,
            COALESCE(pm.start_date, p.planned_start_date) as start_date,
            COALESCE(pm.end_date, p.planned_end_date) as end_date
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        JOIN projects p ON pm.project_id = p.id
        WHERE pm.is_active = 1 AND p.is_active = 1
          AND (:uid IS NULL OR pm.user_id = :uid)
          AND (:dept IS NULL OR u.department = :dept)
          AND COALESCE(pm.end_date, p.planned_end_date) >= :start
          AND COALESCE(pm.start_date, p.planned_start_date) <= :end
        ORDER BY u.real_name, pm.start_date
    """)

    rows = db.execute(sql, {
        "uid": user_id,
        "dept": department,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
    }).fetchall()

    timeline = []
    for row in rows:
        timeline.append({
            "user_id": row.user_id,
            "real_name": row.real_name,
            "department": row.department,
            "project_id": row.project_id,
            "project_name": row.project_name,
            "project_code": row.project_code,
            "stage": row.stage,
            "role": row.role_code,
            "allocation_pct": float(row.allocation_pct),
            "start_date": str(row.start_date) if row.start_date else None,
            "end_date": str(row.end_date) if row.end_date else None,
        })

    return {"items": timeline, "total": len(timeline)}
