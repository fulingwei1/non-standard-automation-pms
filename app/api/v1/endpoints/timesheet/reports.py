# -*- coding: utf-8 -*-
"""
工时汇总与报表 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, extract, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.organization import Department, Employee
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import (
    OvertimeApplication,
    Timesheet,
    TimesheetApprovalLog,
    TimesheetBatch,
    TimesheetRule,
    TimesheetSummary,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.timesheet import (
    MonthSummaryResponse,
    TimesheetBatchCreate,
    TimesheetCreate,
    TimesheetListResponse,
    TimesheetResponse,
    TimesheetStatisticsResponse,
    TimesheetUpdate,
    WeekTimesheetResponse,
)

router = APIRouter()


def check_timesheet_approval_permission(
    db: Session,
    timesheet: Timesheet,
    current_user: User
) -> bool:
    """
    检查用户是否有权审批指定的工时记录

    审批权限规则：
    1. 超级管理员可以审批所有工时
    2. 项目经理可以审批其项目的工时
    3. 研发项目负责人可以审批其研发项目的工时
    4. 部门经理可以审批其部门成员的工时

    Args:
        db: 数据库会话
        timesheet: 工时记录
        current_user: 当前用户

    Returns:
        bool: 是否有审批权限
    """
    # 1. 超级管理员可以审批所有工时
    if hasattr(current_user, 'is_superuser') and current_user.is_superuser:
        return True

    # 2. 检查是否是项目经理（非标项目）
    if timesheet.project_id:
        project = db.query(Project).filter(Project.id == timesheet.project_id).first()
        if project and project.pm_id == current_user.id:
            return True

    # 3. 检查是否是研发项目负责人
    if timesheet.rd_project_id:
        rd_project = db.query(RdProject).filter(RdProject.id == timesheet.rd_project_id).first()
        if rd_project and rd_project.project_manager_id == current_user.id:
            return True

    # 4. 检查是否是部门经理
    if timesheet.department_id:
        department = db.query(Department).filter(Department.id == timesheet.department_id).first()
        if department and department.manager_id:
            # 需要通过 employee_id 关联到 user
            # 查找当前用户对应的 employee
            if hasattr(current_user, 'employee_id') and current_user.employee_id:
                if department.manager_id == current_user.employee_id:
                    return True

    # 5. 如果工时记录有提交人的部门信息，检查当前用户是否是该部门经理
    if timesheet.user_id:
        # 获取工时提交人
        timesheet_user = db.query(User).filter(User.id == timesheet.user_id).first()
        if timesheet_user and hasattr(timesheet_user, 'employee_id') and timesheet_user.employee_id:
            # 获取提交人的员工信息
            employee = db.query(Employee).filter(Employee.id == timesheet_user.employee_id).first()
            if employee and employee.department:
                # 查找该部门
                dept = db.query(Department).filter(Department.dept_name == employee.department).first()
                if dept and dept.manager_id:
                    # 检查当前用户是否是该部门经理
                    if hasattr(current_user, 'employee_id') and current_user.employee_id == dept.manager_id:
                        return True

    return False



from fastapi import APIRouter

router = APIRouter(
    prefix="/timesheet/reports",
    tags=["reports"]
)

# 共 7 个路由

# ==================== 工时汇总与报表 ====================

@router.post("/aggregate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def aggregate_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    user_id: Optional[int] = Query(None, description="用户ID（可选）"),
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    current_user: User = Depends(security.require_permission("timesheet:manage")),
) -> Any:
    """
    手动触发工时汇总
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService

    try:
        service = TimesheetAggregationService(db)
        result = service.aggregate_monthly_timesheet(year, month, user_id, department_id, project_id)

        return ResponseModel(
            code=200,
            message="工时汇总完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工时汇总失败: {str(e)}")


@router.get("/reports/hr", response_model=ResponseModel)
def get_hr_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取HR加班工资报表
    """
    from fastapi.responses import StreamingResponse

    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService

    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_hr_report_excel(year, month, department_id)

            filename = f"HR加班工资表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_hr_report(year, month, department_id)

            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成HR报表失败: {str(e)}")


@router.get("/reports/finance", response_model=ResponseModel)
def get_finance_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取财务报表（项目成本核算表）
    """
    from fastapi.responses import StreamingResponse

    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService

    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_finance_report_excel(year, month, project_id)

            filename = f"项目成本核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_finance_report(year, month, project_id)

            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成财务报表失败: {str(e)}")


@router.get("/reports/rd", response_model=ResponseModel)
def get_rd_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取研发报表（研发费用核算表）
    """
    from fastapi.responses import StreamingResponse

    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService

    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_rd_report_excel(year, month, rd_project_id)

            filename = f"研发费用核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_rd_report(year, month, rd_project_id)

            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发报表失败: {str(e)}")


@router.get("/reports/project", response_model=ResponseModel)
def get_project_report(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Query(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期（可选）"),
    end_date: Optional[date] = Query(None, description="结束日期（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取项目报表（项目工时统计）
    """
    from fastapi.responses import StreamingResponse

    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService

    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_project_report_excel(project_id, start_date, end_date)

            project = db.query(Project).filter(Project.id == project_id).first()
            project_name = project.project_name if project else f"项目{project_id}"
            filename = f"{project_name}_工时报表.xlsx"

            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_project_report(project_id, start_date, end_date)

            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成项目报表失败: {str(e)}")


@router.post("/sync", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: Optional[int] = Query(None, description="工时记录ID（可选）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选，用于批量同步）"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID（可选，用于批量同步）"),
    year: Optional[int] = Query(None, description="年份（用于批量同步）"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份（用于批量同步）"),
    sync_target: str = Query("all", description="同步目标：all/finance/rd/project/hr"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    手动触发数据同步
    """
    from app.services.timesheet_sync_service import TimesheetSyncService

    try:
        service = TimesheetSyncService(db)
        results = {}

        if timesheet_id:
            # 同步单个工时记录
            if sync_target in ["all", "finance"]:
                results['finance'] = service.sync_to_finance(timesheet_id=timesheet_id)
            if sync_target in ["all", "rd"]:
                results['rd'] = service.sync_to_rd(timesheet_id=timesheet_id)
            if sync_target in ["all", "project"]:
                results['project'] = service.sync_to_project(timesheet_id=timesheet_id)
        elif project_id and year and month:
            # 批量同步项目
            if sync_target in ["all", "finance"]:
                results['finance'] = service.sync_to_finance(project_id=project_id, year=year, month=month)
            if sync_target in ["all", "project"]:
                results['project'] = service.sync_to_project(project_id=project_id)
        elif rd_project_id and year and month:
            # 批量同步研发项目
            if sync_target in ["all", "rd"]:
                results['rd'] = service.sync_to_rd(rd_project_id=rd_project_id, year=year, month=month)
        elif year and month:
            # 同步所有数据
            if sync_target in ["all", "hr"]:
                results['hr'] = service.sync_to_hr(year=year, month=month)
        else:
            raise HTTPException(status_code=400, detail="参数不完整")

        return ResponseModel(
            code=200,
            message="数据同步完成",
            data=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据同步失败: {str(e)}")


@router.get("/sync-status/{timesheet_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_sync_status(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时记录的同步状态
    """
    from app.models.finance import FinancialProjectCost
    from app.models.project import ProjectCost
    from app.models.rd_project import RdCost

    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 检查同步状态
    sync_status = {
        'finance': {'status': 'not_synced', 'message': '未同步'},
        'rd': {'status': 'not_synced', 'message': '未同步'},
        'project': {'status': 'not_synced', 'message': '未同步'},
        'hr': {'status': 'not_synced', 'message': '未同步'},
    }

    # 检查财务同步状态
    if timesheet.project_id and timesheet.status == 'APPROVED':
        finance_cost = db.query(FinancialProjectCost).filter(
            FinancialProjectCost.source_type == 'TIMESHEET',
            FinancialProjectCost.source_id == timesheet_id
        ).first()
        if finance_cost:
            sync_status['finance'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': finance_cost.id,
                'sync_time': finance_cost.created_at.isoformat() if finance_cost.created_at else None
            }

    # 检查研发同步状态
    if timesheet.rd_project_id and timesheet.status == 'APPROVED':
        rd_cost = db.query(RdCost).filter(
            RdCost.source_type == 'CALCULATED',
            RdCost.source_id == timesheet_id
        ).first()
        if rd_cost:
            sync_status['rd'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': rd_cost.id,
                'sync_time': rd_cost.created_at.isoformat() if rd_cost.created_at else None
            }

    # 检查项目同步状态（通过ProjectCost）
    if timesheet.project_id and timesheet.status == 'APPROVED':
        # 项目成本通过LaborCostService更新，这里检查是否有对应的成本记录
        project_cost = db.query(ProjectCost).filter(
            ProjectCost.project_id == timesheet.project_id,
            ProjectCost.cost_type == 'LABOR'
        ).first()
        if project_cost:
            sync_status['project'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': project_cost.id,
                'sync_time': project_cost.updated_at.isoformat() if project_cost.updated_at else None
            }

    # HR同步状态（审批通过即视为已同步到HR）
    if timesheet.status == 'APPROVED':
        sync_status['hr'] = {
            'status': 'synced',
            'message': '已同步',
            'sync_time': timesheet.approve_time.isoformat() if timesheet.approve_time else None
        }

    return ResponseModel(
        code=200,
        message="success",
        data=sync_status
    )

