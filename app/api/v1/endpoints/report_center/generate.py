# -*- coding: utf-8 -*-
"""
报表生成 - 自动生成
从 report_center.py 拆分
"""

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



from fastapi import APIRouter

router = APIRouter(
    prefix="/report-center/generate",
    tags=["generate"]
)

# 共 7 个路由

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

    if not generation.export_path:
        raise HTTPException(status_code=404, detail="报表文件不存在，请先导出")

    # 安全检查：验证文件路径在允许的目录内
    export_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "reports"))
    file_path = os.path.abspath(generation.export_path)

    if not file_path.startswith(export_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="报表文件不存在，请先导出")

    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)

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
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.get("/download-file")
def download_file(
    *,
    path: str = Query(..., description="文件路径（相对于报表目录）"),
    current_user: User = Depends(security.require_permission("report:read")),
):
    """
    直接下载文件（仅限报表目录内的文件）

    安全限制：只允许下载 UPLOAD_DIR/reports 目录下的文件
    """
    # 安全检查：只允许访问报表目录
    export_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "reports"))
    os.makedirs(export_dir, exist_ok=True)

    # 将用户输入视为相对路径，拼接到报表目录
    file_path = os.path.abspath(os.path.join(export_dir, path))

    # 验证解析后的路径仍在报表目录内
    if not file_path.startswith(export_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)

    # 设置 MIME 类型
    media_type_map = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')

    # 生成下载文件名
    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
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



