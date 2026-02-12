# -*- coding: utf-8 -*-
"""
报表生成 - 导出功能
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.report_center import ReportGeneration
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.report_center import ReportExportRequest

router = APIRouter()


@router.post("/export", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_report(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ReportExportRequest,
    current_user: User = Depends(security.require_permission("report:export")),
) -> Any:
    """
    导出报表（xlsx/pdf/csv）（使用统一报表框架）
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework.engine import ReportEngine

    generation = db.query(ReportGeneration).filter(ReportGeneration.id == export_in.report_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 准备导出数据
    report_data = generation.report_data or {}
    report_title = generation.report_title or f"{generation.report_type}报表"
    filename = f"report_{generation.id}"

    try:
        export_format = export_in.export_format.upper().lower()  # 转换为小写以匹配统一框架

        # 如果报表有对应的报表代码，使用统一报表框架导出
        # 否则使用旧服务（向后兼容）
        report_code = getattr(generation, 'report_code', None)
        
        if report_code:
            # 使用统一报表框架导出
            engine = ReportEngine(db)
            result = engine.generate(
                report_code=report_code,
                params=report_data.get("params", {}),
                format=export_format,
                user=current_user,
                skip_cache=True,
            )
            
            # 获取文件流
            file_stream = result.data.get("file_stream")
            if file_stream:
                # 返回文件流
                return StreamingResponse(
                    file_stream,
                    media_type=result.content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}.{export_format}"
                    }
                )
        
        # 如果没有报表代码或统一框架导出失败，使用统一报表框架的渲染器
        try:
            if export_format == 'xlsx':
                from app.services.report_framework.renderers.excel_renderer import ExcelRenderer
                renderer = ExcelRenderer()
                # 将report_data转换为sections格式
                sections = []
                if isinstance(report_data, dict):
                    if 'summary' in report_data:
                        sections.append({
                            "id": "summary",
                            "title": "汇总",
                            "type": "metrics",
                            "items": [{"label": k, "value": v} for k, v in report_data['summary'].items()]
                        })
                    if 'details' in report_data:
                        sections.append({
                            "id": "details",
                            "title": "明细",
                            "type": "table",
                            "source": report_data['details']
                        })
                else:
                    sections = [{"id": "data", "title": report_title, "type": "table", "source": report_data}]
                metadata = {"code": f"REPORT_{generation.id}", "name": report_title}
                result = renderer.render(sections, metadata)
                filepath = result.file_path or ""
            elif export_format == 'pdf':
                from app.services.report_framework.renderers.pdf_renderer import PdfRenderer
                renderer = PdfRenderer()
                sections = []
                if isinstance(report_data, dict):
                    if 'summary' in report_data:
                        sections.append({
                            "id": "summary",
                            "title": "汇总",
                            "type": "metrics",
                            "items": [{"label": k, "value": v} for k, v in report_data['summary'].items()]
                        })
                    if 'details' in report_data:
                        sections.append({
                            "id": "details",
                            "title": "明细",
                            "type": "table",
                            "source": report_data['details']
                        })
                else:
                    sections = [{"id": "data", "title": report_title, "type": "table", "source": report_data}]
                metadata = {"code": f"REPORT_{generation.id}", "name": report_title}
                result = renderer.render(sections, metadata)
                filepath = result.file_path or ""
            elif export_format == 'csv':
                # CSV导出暂时使用简单实现
                import csv
                import os
                from datetime import datetime
                csv_dir = os.path.join(settings.UPLOAD_DIR, "exports")
                os.makedirs(csv_dir, exist_ok=True)
                csv_filename = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                csv_path = os.path.join(csv_dir, csv_filename)
                
                # 写入CSV
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    if isinstance(report_data, dict) and 'details' in report_data:
                        if report_data['details']:
                            writer = csv.DictWriter(f, fieldnames=report_data['details'][0].keys())
                            writer.writeheader()
                            writer.writerows(report_data['details'])
                    else:
                        writer = csv.writer(f)
                        writer.writerow([report_title])
                        writer.writerow([str(report_data)])
                
                filepath = os.path.join("exports", csv_filename)
            else:
                raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

        # 更新导出记录
        generation.export_format = export_format.upper()
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
                "format": export_format.upper(),
                "file_path": filepath,
                "download_url": f"/api/v1/reports/download/{generation.id}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


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
    直接导出报表（不需要先生成报表记录）（使用统一报表框架）
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework.engine import ReportEngine

    # 根据报表类型映射到报表代码
    report_code_map = {
        'PROJECT_LIST': 'PROJECT_LIST',
        'HEALTH_DISTRIBUTION': 'PROJECT_HEALTH_DISTRIBUTION',
        'UTILIZATION': 'TIMESHEET_UTILIZATION',
    }

    report_code = report_code_map.get(report_type)
    if not report_code:
        raise HTTPException(status_code=400, detail=f"不支持的报表类型: {report_type}")

    try:
        # 使用统一报表框架生成和导出
        engine = ReportEngine(db)
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if project_id:
            params['project_id'] = project_id
        if department_id:
            params['department_id'] = department_id

        result = engine.generate(
            report_code=report_code,
            params=params,
            format=export_format.lower(),
            user=current_user,
            skip_cache=True,
        )

        # 如果返回文件流，直接返回
        if result.data.get("file_stream"):
            filename = f"{report_type.lower()}_{datetime.now().strftime('%Y%m%d')}.{export_format.lower()}"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type=result.content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        # 否则返回文件路径
        filepath = result.data.get("file_path", "")
        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "file_path": filepath,
                "report_type": report_type,
                "format": export_format.upper()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
