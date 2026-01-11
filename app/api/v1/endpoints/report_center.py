# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from sqlalchemy import desc, func, and_, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User, Role
from app.models.project import Project, Machine, ProjectPaymentPlan
from app.models.rd_project import RdProject, RdCost, RdCostType
from app.models.timesheet import Timesheet
from app.models.sales import Contract
from app.models.outsourcing import OutsourcingVendor, OutsourcingOrder
from app.models.report_center import (
    ReportTemplate, ReportDefinition, ReportGeneration,
    ReportSubscription
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.report_center import (
    ReportRoleResponse, ReportTypeResponse, RoleReportMatrixResponse,
    ReportGenerateRequest, ReportGenerateResponse, ReportPreviewResponse,
    ReportCompareRequest, ReportCompareResponse, ReportExportRequest,
    ReportTemplateResponse, ReportTemplateListResponse, ApplyTemplateRequest
)

router = APIRouter()


# ==================== 报表配置 ====================

@router.get("/roles", response_model=ReportRoleResponse, status_code=status.HTTP_200_OK)
def get_report_roles(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取支持角色列表（角色配置）
    """
    roles = db.query(Role).filter(Role.is_active == True).all()
    
    role_list = []
    for role in roles:
        role_list.append({
            "role_id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "description": role.description
        })
    
    return ReportRoleResponse(roles=role_list)


@router.get("/types", response_model=ReportTypeResponse, status_code=status.HTTP_200_OK)
def get_report_types(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取报表类型列表（周报/月报/成本等）
    """
    types = [
        {"type": "PROJECT_WEEKLY", "name": "项目周报", "description": "项目每周进展报告"},
        {"type": "PROJECT_MONTHLY", "name": "项目月报", "description": "项目每月进展报告"},
        {"type": "DEPT_WEEKLY", "name": "部门周报", "description": "部门每周工作汇总"},
        {"type": "DEPT_MONTHLY", "name": "部门月报", "description": "部门每月工作汇总"},
        {"type": "COMPANY_MONTHLY", "name": "公司月报", "description": "公司每月经营报告"},
        {"type": "COST_ANALYSIS", "name": "成本分析", "description": "项目成本分析报告"},
        {"type": "WORKLOAD_ANALYSIS", "name": "负荷分析", "description": "人员负荷分析报告"},
        {"type": "RISK_REPORT", "name": "风险报告", "description": "项目风险分析报告"},
        {"type": "CUSTOM", "name": "自定义报表", "description": "用户自定义报表"}
    ]
    
    return ReportTypeResponse(types=types)


@router.get("/role-report-matrix", response_model=RoleReportMatrixResponse, status_code=status.HTTP_200_OK)
def get_role_report_matrix(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    角色-报表权限矩阵（权限配置）
    """
    from app.services.report_data_generation_service import report_data_service

    matrix = report_data_service.ROLE_REPORT_MATRIX

    return RoleReportMatrixResponse(matrix=matrix)


# ==================== 报表生成 ====================

@router.post("/generate", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    *,
    db: Session = Depends(deps.get_db),
    generate_in: ReportGenerateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    生成报表（按角色/类型）
    """
    from app.services.report_data_generation_service import report_data_service

    # 检查权限
    if not report_data_service.check_permission(db, current_user, generate_in.report_type, generate_in.role):
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限生成 {generate_in.report_type} 类型的报表"
        )

    # 生成报表编码
    report_code = f"RPT-{datetime.now().strftime('%y%m%d%H%M%S')}"

    # 根据报表类型和角色生成数据
    report_data = report_data_service.generate_report_by_type(
        db,
        generate_in.report_type,
        generate_in.project_id,
        generate_in.department_id,
        generate_in.start_date,
        generate_in.end_date
    )

    # 如果有错误，返回错误信息
    if "error" in report_data:
        raise HTTPException(status_code=400, detail=report_data["error"])

    # 创建报表生成记录
    generation = ReportGeneration(
        report_type=generate_in.report_type,
        report_title=f"{generate_in.report_type}报表",
        viewer_role=generate_in.role,
        scope_type="PROJECT" if generate_in.project_id else ("DEPARTMENT" if generate_in.department_id else None),
        scope_id=generate_in.project_id or generate_in.department_id,
        period_start=generate_in.start_date,
        period_end=generate_in.end_date,
        report_data=report_data,
        status="GENERATED",
        generated_by=current_user.id
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    return ReportGenerateResponse(
        report_id=generation.id,
        report_code=report_code,
        report_name=generation.report_title or f"{generate_in.report_type}报表",
        report_type=generation.report_type,
        generated_at=generation.generated_at or datetime.now(),
        data=generation.report_data or {}
    )


@router.get("/preview/{report_type}", response_model=ReportPreviewResponse, status_code=status.HTTP_200_OK)
def preview_report(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str,
    project_id: Optional[int] = Query(None, description="项目ID"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    预览报表（简化版预览）
    """
    from app.services.report_data_generation_service import report_data_service

    # 生成预览数据（使用默认时间范围）
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    preview_data = report_data_service.generate_report_by_type(
        db,
        report_type,
        project_id,
        None,  # department_id
        start_date,
        end_date
    )

    # 添加可用的字段列表
    preview_data["available_fields"] = list(preview_data.get("summary", {}).keys())
    preview_data["sections"] = [k for k in preview_data.keys() if k not in ["summary", "available_fields", "error"]]

    return ReportPreviewResponse(
        report_type=report_type,
        preview_data=preview_data
    )


@router.post("/compare-roles", response_model=ReportCompareResponse, status_code=status.HTTP_200_OK)
def compare_role_perspectives(
    *,
    db: Session = Depends(deps.get_db),
    compare_in: ReportCompareRequest,
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    比较角色视角（多角色对比）
    """
    from app.services.report_data_generation_service import report_data_service

    # 为每个角色生成报表数据
    role_data = {}
    for role in compare_in.roles:
        report_data = report_data_service.generate_report_by_type(
            db,
            compare_in.report_type,
            compare_in.project_id,
            compare_in.department_id,
            compare_in.start_date,
            compare_in.end_date
        )
        role_data[role] = report_data

    # 分析差异
    differences = []
    common_points = []

    # 比较摘要数据
    if role_data:
        first_role = compare_in.roles[0]
        first_summary = role_data.get(first_role, {}).get("summary", {})

        for key, value in first_summary.items():
            is_common = True
            values_by_role = {}

            for role in compare_in.roles:
                role_summary = role_data.get(role, {}).get("summary", {})
                role_value = role_summary.get(key)

                if role != first_role:
                    if role_value != value:
                        is_common = False

                values_by_role[role] = role_value

            if is_common and value is not None:
                common_points.append({
                    "field": key,
                    "value": value,
                    "description": f"所有角色在此项上一致"
                })
            elif values_by_role:
                differences.append({
                    "field": key,
                    "values": values_by_role,
                    "description": f"各角色在此项上存在差异"
                })

    comparison_data = {
        "roles": compare_in.roles,
        "role_data": role_data,
        "differences": differences,
        "common_points": common_points
    }

    return ReportCompareResponse(
        report_type=compare_in.report_type,
        comparison_data=comparison_data
    )


@router.post("/export", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_report(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ReportExportRequest,
    current_user: User = Depends(security.require_permission("report:export")),
) -> Any:
    """
    导出报表（xlsx/pdf/csv）
    """
    from app.services.report_export_service import report_export_service

    generation = db.query(ReportGeneration).filter(ReportGeneration.id == export_in.report_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 准备导出数据
    report_data = generation.report_data or {}
    report_title = generation.report_title or f"{generation.report_type}报表"
    filename = f"report_{generation.id}"

    try:
        export_format = export_in.export_format.upper()

        if export_format == 'XLSX':
            filepath = report_export_service.export_to_excel(
                data=report_data,
                filename=filename,
                title=report_title
            )
        elif export_format == 'PDF':
            filepath = report_export_service.export_to_pdf(
                data=report_data,
                filename=filename,
                title=report_title
            )
        elif export_format == 'CSV':
            filepath = report_export_service.export_to_csv(
                data=report_data,
                filename=filename
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")

        # 更新导出记录
        generation.export_format = export_format
        generation.export_path = filepath
        generation.exported_at = datetime.now()
        db.add(generation)
        db.commit()

        # 返回下载链接
        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "report_id": generation.id,
                "format": export_format,
                "file_path": filepath,
                "download_url": f"/api/v1/reports/download/{generation.id}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/download/{report_id}")
def download_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("report:read")),
):
    """
    下载已导出的报表文件
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == report_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="报表不存在")

    if not generation.export_path or not os.path.exists(generation.export_path):
        raise HTTPException(status_code=404, detail="报表文件不存在，请先导出")

    # 获取文件扩展名
    _, ext = os.path.splitext(generation.export_path)

    # 设置 MIME 类型
    media_type_map = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')

    # 生成下载文件名
    filename = f"{generation.report_title or 'report'}_{generation.id}{ext}"

    return FileResponse(
        path=generation.export_path,
        media_type=media_type,
        filename=filename
    )


@router.get("/download-file")
def download_file(
    *,
    path: str = Query(..., description="文件路径"),
    current_user: User = Depends(security.require_permission("report:read")),
):
    """
    直接下载文件（通过路径）
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 获取文件扩展名
    _, ext = os.path.splitext(path)

    # 设置 MIME 类型
    media_type_map = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')

    # 生成下载文件名
    filename = os.path.basename(path)

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=filename
    )


@router.post("/export-direct", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_direct(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str = Query(..., description="报表类型"),
    export_format: str = Query("xlsx", description="导出格式: xlsx/pdf/csv"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    直接导出报表（不需要先生成报表记录）
    """
    from app.services.report_export_service import report_export_service, ReportGenerator

    # 根据报表类型生成数据
    report_data = {}
    report_title = ""

    if report_type == 'PROJECT_LIST':
        # 项目列表报表
        query = db.query(Project)
        if project_id:
            query = query.filter(Project.id == project_id)
        projects = query.all()

        project_list = []
        for p in projects:
            project_list.append({
                "项目编码": p.project_code,
                "项目名称": p.project_name,
                "客户": p.customer_name if hasattr(p, 'customer_name') else '',
                "阶段": p.stage,
                "健康度": p.health,
                "状态": p.status,
                "计划开始": str(p.planned_start_date) if p.planned_start_date else '',
                "计划结束": str(p.planned_end_date) if p.planned_end_date else '',
            })

        report_data = ReportGenerator.generate_project_report(project_list)
        report_title = "项目列表报表"

    elif report_type == 'HEALTH_DISTRIBUTION':
        # 健康度分布报表
        health_stats = db.query(
            Project.health,
            func.count(Project.id).label('count')
        ).filter(Project.status != "CANCELLED").group_by(Project.health).all()

        health_list = []
        for stat in health_stats:
            health_list.append({
                "健康度": stat.health or "H4",
                "项目数量": stat.count
            })

        report_data = {"details": health_list}
        report_title = "项目健康度分布报表"

    elif report_type == 'UTILIZATION':
        # 人员利用率报表
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        timesheets = db.query(Timesheet).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status == "APPROVED"
        ).all()

        user_hours = {}
        for ts in timesheets:
            if ts.user_id not in user_hours:
                user_hours[ts.user_id] = 0
            user_hours[ts.user_id] += float(ts.hours or 0)

        work_days = sum(1 for d in range((end_date - start_date).days + 1)
                       if (start_date + timedelta(days=d)).weekday() < 5)
        standard_hours = work_days * 8

        util_list = []
        for user_id, hours in user_hours.items():
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                rate = (hours / standard_hours * 100) if standard_hours > 0 else 0
                util_list.append({
                    "姓名": user.real_name or user.username,
                    "部门": user.department or '',
                    "工时(小时)": round(hours, 1),
                    "标准工时": standard_hours,
                    "利用率": f"{rate:.1f}%"
                })

        report_data = ReportGenerator.generate_utilization_report(util_list)
        report_title = f"人员利用率报表 ({start_date} ~ {end_date})"

    else:
        raise HTTPException(status_code=400, detail=f"不支持的报表类型: {report_type}")

    # 导出文件
    try:
        filename = f"{report_type.lower()}_{datetime.now().strftime('%Y%m%d')}"
        export_fmt = export_format.upper()

        if export_fmt == 'XLSX':
            filepath = report_export_service.export_to_excel(report_data, filename, report_title)
        elif export_fmt == 'PDF':
            filepath = report_export_service.export_to_pdf(report_data, filename, report_title)
        elif export_fmt == 'CSV':
            filepath = report_export_service.export_to_csv(report_data, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")

        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "file_path": filepath,
                "report_type": report_type,
                "format": export_fmt
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 报表模板 ====================

@router.get("/templates", response_model=ReportTemplateListResponse, status_code=status.HTTP_200_OK)
def get_report_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报表类型筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取报表模板列表
    """
    query = db.query(ReportTemplate).filter(ReportTemplate.is_active == True)
    
    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(desc(ReportTemplate.use_count), desc(ReportTemplate.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for template in templates:
        items.append(ReportTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            report_type=template.report_type,
            description=template.description,
            is_system=template.is_system or False,
            is_active=template.is_active or True,
            use_count=template.use_count or 0,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))
    
    return ReportTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/templates/apply", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
def apply_report_template(
    *,
    db: Session = Depends(deps.get_db),
    apply_in: ApplyTemplateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    应用报表模板（套用模板）
    """
    from app.services.template_report_service import template_report_service

    template = db.query(ReportTemplate).filter(ReportTemplate.id == apply_in.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已停用")

    # 更新使用次数
    template.use_count = (template.use_count or 0) + 1
    db.add(template)

    # 生成报表编码
    report_code = f"RPT-{datetime.now().strftime('%y%m%d%H%M%S')}"

    # 根据模板配置生成报表数据
    report_data = template_report_service.generate_from_template(
        db,
        template,
        apply_in.project_id,
        apply_in.department_id,
        apply_in.start_date,
        apply_in.end_date,
        apply_in.filters
    )

    # 如果有错误，返回错误信息
    if "error" in report_data:
        raise HTTPException(status_code=400, detail=report_data["error"])

    generation = ReportGeneration(
        template_id=template.id,
        report_type=template.report_type,
        report_title=apply_in.report_name,
        scope_type="PROJECT" if apply_in.project_id else ("DEPARTMENT" if apply_in.department_id else None),
        scope_id=apply_in.project_id or apply_in.department_id,
        period_start=apply_in.start_date,
        period_end=apply_in.end_date,
        report_data=report_data,
        status="GENERATED",
        generated_by=current_user.id
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    return ReportGenerateResponse(
        report_id=generation.id,
        report_code=report_code,
        report_name=generation.report_title or f"{template.template_name}报表",
        report_type=generation.report_type,
        generated_at=generation.generated_at or datetime.now(),
        data=generation.report_data or {}
    )


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
    from app.services.report_export_service import report_export_service
    from app.services.rd_report_data_service import get_rd_report_data

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


# ==================== BI 报表 ====================

@router.get("/delivery-rate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_delivery_rate(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    交付准时率
    统计项目按计划交付的准时率
    """
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()
    
    # 获取在时间范围内的项目
    projects = db.query(Project).filter(
        Project.planned_end_date >= start_date,
        Project.planned_end_date <= end_date,
        Project.status.in_(["COMPLETED", "EXECUTING"])
    ).all()
    
    total_projects = len(projects)
    on_time_projects = 0
    delayed_projects = 0
    
    for project in projects:
        if project.actual_end_date and project.planned_end_date:
            if project.actual_end_date <= project.planned_end_date:
                on_time_projects += 1
            else:
                delayed_projects += 1
    
    on_time_rate = (on_time_projects / total_projects * 100) if total_projects > 0 else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_projects": total_projects,
            "on_time_projects": on_time_projects,
            "delayed_projects": delayed_projects,
            "on_time_rate": round(on_time_rate, 2)
        }
    )


@router.get("/health-distribution", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_health_distribution(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    项目健康度分布
    统计各健康度等级的项目数量
    """
    health_stats = db.query(
        Project.health,
        func.count(Project.id).label('count')
    ).filter(
        Project.status != "CANCELLED"
    ).group_by(Project.health).all()
    
    distribution = {}
    total = 0
    for stat in health_stats:
        health = stat.health or "H4"
        count = stat.count or 0
        distribution[health] = count
        total += count
    
    # 计算百分比
    distribution_pct = {}
    for health, count in distribution.items():
        distribution_pct[health] = round(count / total * 100, 2) if total > 0 else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_projects": total,
            "distribution": distribution,
            "distribution_percentage": distribution_pct
        }
    )


@router.get("/utilization", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_utilization(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    人员利用率
    统计人员的工时利用情况
    """
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # 查询工时记录
    query = db.query(Timesheet).filter(
        Timesheet.work_date >= start_date,
        Timesheet.work_date <= end_date,
        Timesheet.status == "APPROVED"
    )
    
    if department_id:
        # 通过用户关联部门
        query = query.join(User).filter(User.department_id == department_id)
    
    timesheets = query.all()
    
    # 按用户统计
    user_hours = {}
    for ts in timesheets:
        user_id = ts.user_id
        if user_id not in user_hours:
            user_hours[user_id] = 0
        user_hours[user_id] += float(ts.hours or 0)
    
    # 计算标准工时（假设每天8小时，工作日）
    work_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 周一到周五
            work_days += 1
        current += timedelta(days=1)
    
    standard_hours = work_days * 8
    
    utilization_data = []
    for user_id, hours in user_hours.items():
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            utilization_rate = (hours / standard_hours * 100) if standard_hours > 0 else 0
            utilization_data.append({
                "user_id": user_id,
                "user_name": user.real_name or user.username,
                "department": user.department,
                "total_hours": round(hours, 2),
                "standard_hours": standard_hours,
                "utilization_rate": round(utilization_rate, 2)
            })
    
    # 按利用率排序
    utilization_data.sort(key=lambda x: x["utilization_rate"], reverse=True)
    
    avg_utilization = sum([u["utilization_rate"] for u in utilization_data]) / len(utilization_data) if utilization_data else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_users": len(utilization_data),
            "avg_utilization_rate": round(avg_utilization, 2),
            "utilization_list": utilization_data
        }
    )


@router.get("/supplier-performance", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_supplier_performance(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    供应商绩效
    统计供应商的交期、质量、价格等绩效指标
    """
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()
    
    # 查询外协订单
    orders = db.query(OutsourcingOrder).filter(
        OutsourcingOrder.order_date >= start_date,
        OutsourcingOrder.order_date <= end_date
    ).all()
    
    # 按供应商统计
    vendor_stats = {}
    for order in orders:
        vendor_id = order.vendor_id
        if vendor_id not in vendor_stats:
            vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
            vendor_stats[vendor_id] = {
                "vendor_id": vendor_id,
                "vendor_name": vendor.vendor_name if vendor else None,
                "vendor_code": vendor.vendor_code if vendor else None,
                "total_orders": 0,
                "total_amount": Decimal("0"),
                "on_time_deliveries": 0,
                "delayed_deliveries": 0,
                "quality_pass_rate": 0.0
            }
        
        stats = vendor_stats[vendor_id]
        stats["total_orders"] += 1
        stats["total_amount"] += order.order_amount or Decimal("0")
        
        # 检查交付情况
        from app.models.outsourcing import OutsourcingDelivery
        deliveries = db.query(OutsourcingDelivery).filter(
            OutsourcingDelivery.order_id == order.id
        ).all()
        
        for delivery in deliveries:
            if delivery.delivery_date and order.expected_delivery_date:
                if delivery.delivery_date <= order.expected_delivery_date:
                    stats["on_time_deliveries"] += 1
                else:
                    stats["delayed_deliveries"] += 1
        
        # 检查质检情况
        from app.models.outsourcing import OutsourcingInspection
        inspections = db.query(OutsourcingInspection).filter(
            OutsourcingInspection.order_id == order.id
        ).all()
        
        if inspections:
            pass_count = sum([1 for ins in inspections if ins.inspection_result == "PASS"])
            stats["quality_pass_rate"] = (pass_count / len(inspections) * 100) if inspections else 0
    
    # 计算准时率
    performance_list = []
    for vendor_id, stats in vendor_stats.items():
        total_deliveries = stats["on_time_deliveries"] + stats["delayed_deliveries"]
        on_time_rate = (stats["on_time_deliveries"] / total_deliveries * 100) if total_deliveries > 0 else 0
        
        performance_list.append({
            "vendor_id": stats["vendor_id"],
            "vendor_name": stats["vendor_name"],
            "vendor_code": stats["vendor_code"],
            "total_orders": stats["total_orders"],
            "total_amount": float(stats["total_amount"]),
            "on_time_rate": round(on_time_rate, 2),
            "quality_pass_rate": round(stats["quality_pass_rate"], 2),
            "performance_score": round((on_time_rate + stats["quality_pass_rate"]) / 2, 2)
        })
    
    # 按绩效得分排序
    performance_list.sort(key=lambda x: x["performance_score"], reverse=True)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_vendors": len(performance_list),
            "performance_list": performance_list
        }
    )


@router.get("/dashboard/executive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_executive_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    决策驾驶舱数据
    综合看板数据，包括项目、销售、成本、进度等关键指标
    """
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # 项目统计
    total_projects = db.query(Project).filter(Project.status != "CANCELLED").count()
    active_projects = db.query(Project).filter(Project.status == "EXECUTING").count()
    completed_projects = db.query(Project).filter(Project.status == "COMPLETED").count()
    
    # 健康度分布
    health_dist = db.query(
        Project.health,
        func.count(Project.id).label('count')
    ).filter(Project.status != "CANCELLED").group_by(Project.health).all()
    health_distribution = {stat.health or "H4": stat.count for stat in health_dist}
    
    # 销售统计（本月）
    month_contracts = db.query(Contract).filter(
        func.date(Contract.signed_date) >= month_start,
        Contract.status.in_(["SIGNED", "EXECUTING"])
    ).all()
    month_contract_amount = sum([float(c.contract_amount or 0) for c in month_contracts])
    
    # 成本统计
    total_budget = db.query(func.sum(Project.budget_amount)).scalar() or 0
    total_actual = db.query(func.sum(Project.actual_cost)).scalar() or 0
    
    # 合同统计
    total_contracts = db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count()
    total_contract_amount = db.query(func.sum(Contract.contract_amount)).filter(
        Contract.status.in_(["SIGNED", "EXECUTING"])
    ).scalar() or 0
    
    # 回款统计（从项目收款计划）
    from app.models.project import ProjectPaymentPlan
    total_received = db.query(func.sum(ProjectPaymentPlan.actual_amount)).filter(
        ProjectPaymentPlan.status == "PAID"
    ).scalar() or 0
    
    # 人员统计
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # 工时统计（本月）
    month_timesheets = db.query(Timesheet).filter(
        Timesheet.work_date >= month_start,
        Timesheet.status == "APPROVED"
    ).all()
    month_total_hours = sum([float(ts.hours or 0) for ts in month_timesheets])
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "completed_projects": completed_projects,
                "total_contracts": total_contracts,
                "total_contract_amount": round(float(total_contract_amount), 2),
                "total_received": round(float(total_received), 2),
                "total_budget": round(float(total_budget), 2),
                "total_actual_cost": round(float(total_actual), 2),
                "total_users": total_users
            },
            "monthly": {
                "month": today.strftime("%Y-%m"),
                "new_contracts": len(month_contracts),
                "contract_amount": round(month_contract_amount, 2),
                "total_hours": round(month_total_hours, 2)
            },
            "health_distribution": health_distribution,
            "updated_at": datetime.now().isoformat()
        }
    )
