# -*- coding: utf-8 -*-
"""
部门维度 API 模块

提供部门管理者视角的数据访问：
- /departments/{dept_id}/projects    部门相关项目
- /departments/{dept_id}/workload    部门工作量
- /departments/{dept_id}/timesheet   部门工时统计
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import ProjectListResponse
from app.services.project import ProjectCoreService, ProjectResourceService

router = APIRouter()


@router.get(
    "/{dept_id}/projects",
    response_model=ResponseModel[PaginatedResponse[ProjectListResponse]],
    status_code=status.HTTP_200_OK,
)
def get_department_projects(
    dept_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查询部门相关项目"""
    service = ProjectCoreService(db)
    department = service.get_department(dept_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    data = service.list_department_projects(dept_id, current_user, page=page, page_size=page_size)
    return ResponseModel(
        data=data,
        message=f"{department.dept_name} 项目列表",
    )


@router.get(
    "/{dept_id}/workload",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_department_workload(
    dept_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """部门工作量汇总"""
    service = ProjectResourceService(db)
    try:
        data = service.get_department_workload_summary(dept_id, start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResponseModel(data=data)


@router.get(
    "/{dept_id}/timesheet",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_department_timesheet_summary(
    dept_id: int,
    year: int = Query(date.today().year, ge=2000, description="年份"),
    month: int = Query(date.today().month, ge=1, le=12, description="月份"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """部门工时汇总"""
    service = ProjectResourceService(db)
    try:
        data = service.get_department_timesheet_summary(dept_id, year, month)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResponseModel(data=data)
