# -*- coding: utf-8 -*-
"""
工时报表 API 端点 - 薄控制器层
"""

import logging
import os
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User
from app.models.report import OutputFormatEnum, ArchiveStatusEnum
from app.schemas.common import ResponseModel
from app.services.report.report_service import ReportService
from app.services.report_excel_service import ReportExcelService

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 报表模板管理（6个端点） ====================

@router.post("/templates", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    name: str,
    report_type: str,
    description: Optional[str] = None,
    config: Optional[dict] = None,
    output_format: str = "EXCEL",
    frequency: str = "MONTHLY",
    enabled: bool = True,
):
    """创建报表模板 (权限: HR/Admin)"""
    service = ReportService(db)
    
    template = service.create_template(
        name=name,
        report_type=report_type,
        created_by=current_user.id,
        description=description,
        config=config,
        output_format=output_format,
        frequency=frequency,
        enabled=enabled,
    )
    
    logger.info(f"用户 {current_user.username} 创建了报表模板: {template.name}")
    
    return ResponseModel(
        code=0,
        message="报表模板创建成功",
        data={
            "id": template.id,
            "name": template.name,
            "report_type": template.report_type,
            "enabled": template.enabled,
        }
    )


@router.get("/templates", response_model=ResponseModel)
def list_templates(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    report_type: Optional[str] = Query(None, description="报表类型"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取报表模板列表 (权限: HR/Manager)"""
    service = ReportService(db)
    
    result = service.list_templates(
        report_type=report_type,
        enabled=enabled,
        page=page,
        page_size=page_size,
    )
    
    items = []
    for template in result['templates']:
        items.append({
            "id": template.id,
            "name": template.name,
            "report_type": template.report_type,
            "description": template.description,
            "output_format": template.output_format,
            "frequency": template.frequency,
            "enabled": template.enabled,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        })
    
    return ResponseModel(
        code=0,
        message="查询成功",
        data={
            "total": result['total'],
            "page": result['page'],
            "page_size": result['page_size'],
            "items": items,
        }
    )


@router.get("/templates/{template_id}", response_model=ResponseModel)
def get_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
):
    """获取报表模板详情"""
    service = ReportService(db)
    
    result = service.get_template_with_recipients(template_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表模板不存在"
        )
    
    template = result['template']
    recipients = result['recipients']
    
    return ResponseModel(
        code=0,
        message="查询成功",
        data={
            "id": template.id,
            "name": template.name,
            "report_type": template.report_type,
            "description": template.description,
            "config": template.config,
            "output_format": template.output_format,
            "frequency": template.frequency,
            "enabled": template.enabled,
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "recipients": [
                {
                    "id": r.id,
                    "recipient_type": r.recipient_type,
                    "recipient_id": r.recipient_id,
                    "recipient_email": r.recipient_email,
                    "delivery_method": r.delivery_method,
                    "enabled": r.enabled,
                }
                for r in recipients
            ],
        }
    )


@router.put("/templates/{template_id}", response_model=ResponseModel)
def update_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    config: Optional[dict] = None,
    output_format: Optional[str] = None,
    frequency: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """更新报表模板 (权限: HR/Admin)"""
    service = ReportService(db)
    
    template = service.update_template(
        template_id=template_id,
        name=name,
        description=description,
        config=config,
        output_format=output_format,
        frequency=frequency,
        enabled=enabled,
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表模板不存在"
        )
    
    logger.info(f"用户 {current_user.username} 更新了报表模板: {template.name}")
    
    return ResponseModel(
        code=0,
        message="报表模板更新成功",
        data={"id": template.id}
    )


@router.delete("/templates/{template_id}", response_model=ResponseModel)
def delete_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
):
    """删除报表模板 (权限: Admin only)"""
    service = ReportService(db)
    
    success = service.delete_template(template_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表模板不存在"
        )
    
    logger.info(f"用户 {current_user.username} 删除了报表模板 ID: {template_id}")
    
    return ResponseModel(
        code=0,
        message="报表模板删除成功"
    )


@router.post("/templates/{template_id}/toggle", response_model=ResponseModel)
def toggle_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
):
    """启用/禁用报表模板"""
    service = ReportService(db)
    
    result = service.toggle_template(template_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表模板不存在"
        )
    
    template = result['template']
    enabled = result['enabled']
    
    logger.info(
        f"用户 {current_user.username} {'启用' if enabled else '禁用'}了报表模板: {template.name}"
    )
    
    return ResponseModel(
        code=0,
        message=f"报表模板已{'启用' if enabled else '禁用'}",
        data={"enabled": enabled}
    )


# ==================== 报表生成（3个端点） ====================

@router.post("/generate", response_model=ResponseModel)
def generate_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
    period: str,
):
    """
    手动生成报表
    
    参数:
    - template_id: 模板ID
    - period: 报表周期（如：2026-01）
    """
    service = ReportService(db)
    
    try:
        # 生成报表数据
        data = service.generate_report_data(
            template_id=template_id,
            period=period,
            generated_by=f"USER_{current_user.id}"
        )
        
        # 导出为文件
        template = data['template']
        if template.output_format == OutputFormatEnum.EXCEL.value:
            file_path = ReportExcelService.export_to_excel(
                data=data,
                template_name=template.name
            )
            file_size = os.path.getsize(file_path)
            row_count = len(data['summary'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"暂不支持的输出格式: {template.output_format}"
            )
        
        # 归档
        archive = service.archive_report(
            template_id=template_id,
            period=period,
            file_path=file_path,
            file_size=file_size,
            row_count=row_count,
            generated_by=f"USER_{current_user.id}",
            status=ArchiveStatusEnum.SUCCESS.value
        )
        
        logger.info(f"用户 {current_user.username} 生成了报表: {template.name} - {period}")
        
        return ResponseModel(
            code=0,
            message="报表生成成功",
            data={
                "archive_id": archive.id,
                "file_path": file_path,
                "file_size": file_size,
                "row_count": row_count,
            }
        )
        
    except ValueError as e:
        logger.error(f"报表生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"报表生成失败: {str(e)}", exc_info=True)
        
        # 记录失败归档
        service.archive_report(
            template_id=template_id,
            period=period,
            file_path="",
            file_size=0,
            row_count=0,
            generated_by=f"USER_{current_user.id}",
            status=ArchiveStatusEnum.FAILED.value,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报表生成失败: {str(e)}"
        )


@router.get("/preview", response_model=ResponseModel)
def preview_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
    period: str,
    limit: int = Query(50, ge=1, le=1000),
):
    """预览报表数据（不导出文件）"""
    service = ReportService(db)
    
    try:
        data = service.generate_report_data(
            template_id=template_id,
            period=period,
            generated_by=f"USER_{current_user.id}"
        )
        
        # 限制返回的数据量
        summary = data['summary'][:limit]
        detail = data.get('detail', [])[:limit]
        
        return ResponseModel(
            code=0,
            message="预览成功",
            data={
                "summary": summary,
                "detail": detail,
                "total_summary_rows": len(data['summary']),
                "total_detail_rows": len(data.get('detail', [])),
                "period": period,
            }
        )
        
    except ValueError as e:
        logger.error(f"报表预览失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"报表预览失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报表预览失败: {str(e)}"
        )


@router.get("/export", response_model=ResponseModel)
def export_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
    period: str,
    format: str = Query("excel", description="导出格式: excel/pdf/csv"),
):
    """导出报表（已有功能，增强版本）"""
    # 复用 generate_report 功能
    return generate_report(
        db=db,
        current_user=current_user,
        template_id=template_id,
        period=period
    )


# ==================== 报表归档管理（4个端点） ====================

@router.get("/archives", response_model=ResponseModel)
def list_archives(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: Optional[int] = Query(None, description="模板ID"),
    report_type: Optional[str] = Query(None, description="报表类型"),
    period: Optional[str] = Query(None, description="报表周期"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取报表归档列表"""
    service = ReportService(db)
    
    result = service.list_archives(
        template_id=template_id,
        report_type=report_type,
        period=period,
        status=status,
        page=page,
        page_size=page_size,
    )
    
    items = []
    for archive in result['archives']:
        items.append({
            "id": archive.id,
            "template_id": archive.template_id,
            "report_type": archive.report_type,
            "period": archive.period,
            "file_path": archive.file_path,
            "file_size": archive.file_size,
            "row_count": archive.row_count,
            "generated_at": archive.generated_at.isoformat() if archive.generated_at else None,
            "generated_by": archive.generated_by,
            "status": archive.status,
            "download_count": archive.download_count,
        })
    
    return ResponseModel(
        code=0,
        message="查询成功",
        data={
            "total": result['total'],
            "page": result['page'],
            "page_size": result['page_size'],
            "items": items,
        }
    )


@router.get("/archives/{archive_id}", response_model=ResponseModel)
def get_archive(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    archive_id: int,
):
    """获取报表归档详情"""
    service = ReportService(db)
    
    result = service.get_archive_with_template(archive_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表归档不存在"
        )
    
    archive = result['archive']
    template = result['template']
    
    return ResponseModel(
        code=0,
        message="查询成功",
        data={
            "id": archive.id,
            "template_id": archive.template_id,
            "template_name": template.name if template else None,
            "report_type": archive.report_type,
            "period": archive.period,
            "file_path": archive.file_path,
            "file_size": archive.file_size,
            "row_count": archive.row_count,
            "generated_at": archive.generated_at.isoformat() if archive.generated_at else None,
            "generated_by": archive.generated_by,
            "status": archive.status,
            "error_message": archive.error_message,
            "download_count": archive.download_count,
        }
    )


@router.get("/archives/{archive_id}/download")
def download_archive(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    archive_id: int,
):
    """下载报表文件"""
    service = ReportService(db)
    
    archive = service.get_archive(archive_id)
    
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表归档不存在"
        )
    
    if archive.status != ArchiveStatusEnum.SUCCESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报表生成失败，无法下载"
        )
    
    file_path = Path(archive.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表文件不存在"
        )
    
    # 增加下载次数
    service.increment_download_count(archive_id)
    
    logger.info(f"用户 {current_user.username} 下载了报表: {archive.period}")
    
    # 返回文件
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/archives/batch-download", response_model=ResponseModel)
def batch_download_archives(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    archive_ids: List[int],
):
    """
    批量下载报表（返回ZIP文件）
    
    TODO: 实现 ZIP 打包功能
    """
    service = ReportService(db)
    
    archives = service.get_archives_by_ids(archive_ids)
    
    files = []
    for archive in archives:
        if archive.status == ArchiveStatusEnum.SUCCESS.value:
            files.append({
                "id": archive.id,
                "file_path": archive.file_path,
                "period": archive.period,
            })
    
    return ResponseModel(
        code=0,
        message="批量下载准备完成",
        data={"files": files}
    )


# ==================== 收件人管理（2个端点） ====================

@router.post("/templates/{template_id}/recipients", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_recipient(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template_id: int,
    recipient_type: str,
    recipient_id: Optional[int] = None,
    recipient_email: Optional[str] = None,
    delivery_method: str = "EMAIL",
    enabled: bool = True,
):
    """添加报表收件人"""
    service = ReportService(db)
    
    recipient = service.add_recipient(
        template_id=template_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        recipient_email=recipient_email,
        delivery_method=delivery_method,
        enabled=enabled,
    )
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报表模板不存在"
        )
    
    logger.info(f"用户 {current_user.username} 添加了收件人")
    
    return ResponseModel(
        code=0,
        message="收件人添加成功",
        data={"id": recipient.id}
    )


@router.delete("/recipients/{recipient_id}", response_model=ResponseModel)
def delete_recipient(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    recipient_id: int,
):
    """删除报表收件人"""
    service = ReportService(db)
    
    success = service.delete_recipient(recipient_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收件人不存在"
        )
    
    logger.info(f"用户 {current_user.username} 删除了收件人 ID: {recipient_id}")
    
    return ResponseModel(
        code=0,
        message="收件人删除成功"
    )
