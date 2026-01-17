# -*- coding: utf-8 -*-
"""
研发费用报表 - 自动生成
从 report_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.outsourcing import OutsourcingOrder, OutsourcingVendor
from app.models.project import Machine, Project, ProjectPaymentPlan
from app.models.rd_project import RdCost, RdCostType, RdProject
from app.models.report_center import (
    ReportDefinition,
    ReportGeneration,
    ReportSubscription,
    ReportTemplate,
)
from app.models.sales import Contract
from app.models.timesheet import Timesheet
from app.models.user import Role, User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.report_center import (
    ApplyTemplateRequest,
    ReportCompareRequest,
    ReportCompareResponse,
    ReportExportRequest,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportPreviewResponse,
    ReportRoleResponse,
    ReportTemplateListResponse,
    ReportTemplateResponse,
    ReportTypeResponse,
    RoleReportMatrixResponse,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/report-center/rd-expense",
    tags=["rd_expense"]
)

# 共 6 个路由

# ==================== 研发费用报表 ====================

@router.get("/rd-auxiliary-ledger", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_auxiliary_ledger(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    project_id: Optional[int] = Query(None, description="研发项目ID（不提供则查询所有项目）"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发费用辅助账
    税务要求的研发费用辅助账格式
    """
    query = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year
    )

    if project_id:
        query = query.filter(RdCost.rd_project_id == project_id)

    costs = query.order_by(RdCost.rd_project_id, RdCost.cost_date, RdCost.cost_type_id).all()

    # 按项目和费用类型汇总
    ledger_items = []
    current_project_id = None
    current_type_id = None
    project_total = Decimal("0")
    type_total = Decimal("0")

    for cost in costs:
        if current_project_id != cost.rd_project_id:
            if current_project_id:
                ledger_items.append({
                    "project_id": current_project_id,
                    "project_name": "",
                    "cost_type_id": current_type_id,
                    "cost_type_name": "",
                    "total_amount": float(type_total),
                    "items": []
                })
            current_project_id = cost.rd_project_id
            project = db.query(RdProject).filter(RdProject.id == cost.rd_project_id).first()
            project_total = Decimal("0")
            type_total = Decimal("0")
            current_type_id = cost.cost_type_id

        if current_type_id != cost.cost_type_id:
            if current_type_id:
                ledger_items.append({
                    "project_id": current_project_id,
                    "project_name": project.project_name if project else "",
                    "cost_type_id": current_type_id,
                    "cost_type_name": "",
                    "total_amount": float(type_total),
                    "items": []
                })
            current_type_id = cost.cost_type_id
            cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
            type_total = Decimal("0")

        type_total += cost.cost_amount or Decimal("0")
        project_total += cost.cost_amount or Decimal("0")

        ledger_items.append({
            "date": cost.cost_date.isoformat() if cost.cost_date else None,
            "cost_no": cost.cost_no,
            "description": cost.cost_description,
            "amount": float(cost.cost_amount or 0),
            "deductible_amount": float(cost.deductible_amount or 0)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "total_amount": float(project_total),
            "ledger": ledger_items
        }
    )


@router.get("/rd-deduction-detail", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_deduction_detail(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    project_id: Optional[int] = Query(None, description="研发项目ID"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发费用加计扣除明细
    """
    query = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year,
        RdCost.deductible_amount > 0
    )

    if project_id:
        query = query.filter(RdCost.rd_project_id == project_id)

    costs = query.order_by(RdCost.rd_project_id, RdCost.cost_type_id).all()

    # 按费用类型汇总
    by_type = {}
    total_deductible = Decimal("0")

    for cost in costs:
        type_id = cost.cost_type_id
        if type_id not in by_type:
            cost_type = db.query(RdCostType).filter(RdCostType.id == type_id).first()
            by_type[type_id] = {
                "cost_type_id": type_id,
                "cost_type_name": cost_type.type_name if cost_type else "",
                "total_amount": Decimal("0"),
                "deductible_amount": Decimal("0"),
                "items": []
            }

        deductible = cost.deductible_amount or Decimal("0")
        by_type[type_id]["total_amount"] += cost.cost_amount or Decimal("0")
        by_type[type_id]["deductible_amount"] += deductible
        total_deductible += deductible

        by_type[type_id]["items"].append({
            "cost_no": cost.cost_no,
            "date": cost.cost_date.isoformat() if cost.cost_date else None,
            "description": cost.cost_description,
            "amount": float(cost.cost_amount or 0),
            "deductible_amount": float(deductible)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "total_deductible": float(total_deductible),
            "by_type": [
                {
                    "cost_type_id": v["cost_type_id"],
                    "cost_type_name": v["cost_type_name"],
                    "total_amount": float(v["total_amount"]),
                    "deductible_amount": float(v["deductible_amount"]),
                    "items": v["items"]
                }
                for v in by_type.values()
            ]
        }
    )


@router.get("/rd-high-tech", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_high_tech_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    高新企业研发费用表
    用于高新技术企业认定
    """
    # 获取研发费用
    costs = db.query(RdCost).join(RdProject).filter(
        func.extract('year', RdCost.cost_date) == year
    ).all()

    # 按费用类型汇总（六大费用类型）
    by_type = {}
    total_cost = Decimal("0")

    for cost in costs:
        cost_type = db.query(RdCostType).filter(RdCostType.id == cost.cost_type_id).first()
        type_code = cost_type.type_code if cost_type else "OTHER"

        if type_code not in by_type:
            by_type[type_code] = {
                "type_code": type_code,
                "type_name": cost_type.type_name if cost_type else "其他",
                "amount": Decimal("0")
            }

        by_type[type_code]["amount"] += cost.cost_amount or Decimal("0")
        total_cost += cost.cost_amount or Decimal("0")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "total_cost": float(total_cost),
            "by_type": [
                {
                    "type_code": v["type_code"],
                    "type_name": v["type_name"],
                    "amount": float(v["amount"])
                }
                for v in by_type.values()
            ]
        }
    )


@router.get("/rd-intensity", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_intensity_report(
    *,
    db: Session = Depends(deps.get_db),
    start_year: int = Query(..., description="开始年度"),
    end_year: int = Query(..., description="结束年度"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发投入强度报表
    研发费用/营业收入
    """
    intensity_data = []

    for year in range(start_year, end_year + 1):
        # 计算研发费用
        rd_costs = db.query(func.sum(RdCost.cost_amount)).filter(
            func.extract('year', RdCost.cost_date) == year
        ).scalar() or Decimal("0")

        # 从项目收款计划获取营业收入（按实际收款日期统计）
        revenue = db.query(func.sum(ProjectPaymentPlan.actual_amount)).filter(
            func.extract('year', ProjectPaymentPlan.actual_date) == year,
            ProjectPaymentPlan.status.in_(['COMPLETED', 'PARTIAL']),
            ProjectPaymentPlan.actual_amount.isnot(None)
        ).scalar() or Decimal("0")

        intensity = (float(rd_costs) / float(revenue) * 100) if revenue > 0 else 0.0

        intensity_data.append({
            "year": year,
            "rd_cost": float(rd_costs),
            "revenue": float(revenue),
            "intensity": round(intensity, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": start_year, "end": end_year},
            "intensity_data": intensity_data,
            "avg_intensity": round(sum(d["intensity"] for d in intensity_data) / len(intensity_data), 2) if intensity_data else 0.0
        }
    )


@router.get("/rd-personnel", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_personnel_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发人员统计
    研发人员占比统计
    """
    # 获取参与研发项目的用户
    rd_projects = db.query(RdProject).filter(
        func.extract('year', RdProject.start_date) <= year,
        func.extract('year', RdProject.end_date) >= year
    ).all()

    # 通过工时记录统计研发人员
    rd_user_ids = set()
    for project in rd_projects:
        if project.linked_project_id:
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.linked_project_id,
                func.extract('year', Timesheet.work_date) == year,
                Timesheet.status == 'APPROVED'
            ).all()
            rd_user_ids.update([ts.user_id for ts in timesheets])

    # 获取所有用户
    all_users = db.query(User).filter(User.is_active == True).all()
    total_users = len(all_users)
    rd_users_count = len(rd_user_ids)

    rd_personnel_list = []
    for user_id in rd_user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            rd_personnel_list.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "department": user.department
            })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "year": year,
            "total_users": total_users,
            "rd_users_count": rd_users_count,
            "rd_ratio": round(rd_users_count / total_users * 100, 2) if total_users > 0 else 0.0,
            "rd_personnel": rd_personnel_list
        }
    )


@router.get("/rd-export", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_rd_report(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str = Query(..., description="报表类型：auxiliary-ledger/deduction-detail/high-tech/intensity/personnel"),
    year: int = Query(..., description="年度"),
    format: str = Query("xlsx", description="导出格式：xlsx/pdf"),
    project_id: Optional[int] = Query(None, description="研发项目ID"),
    current_user: User = Depends(security.require_permission("report:export")),
) -> Any:
    """
    导出研发费用报表
    """
    from app.services.rd_report_data_service import get_rd_report_data
    from app.services.report_export_service import report_export_service

    # 获取报表数据
    try:
        report_result = get_rd_report_data(db, report_type, year, project_id)
        report_data = {k: v for k, v in report_result.items() if k != 'title'}
        report_title = report_result.get('title', f"{year}年研发费用报表")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 导出文件
    try:
        filename = f"rd-{report_type}-{year}"
        export_fmt = format.upper()

        if export_fmt == 'XLSX':
            filepath = report_export_service.export_to_excel(report_data, filename, report_title)
        elif export_fmt == 'PDF':
            filepath = report_export_service.export_to_pdf(report_data, filename, report_title)
        elif export_fmt == 'CSV':
            filepath = report_export_service.export_to_csv(report_data, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "report_type": report_type,
                "year": year,
                "format": export_fmt,
                "file_path": filepath,
                "download_url": f"/api/v1/reports/download-file?path={filepath}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")



