# -*- coding: utf-8 -*-
"""
数据完整性保障 API 端点
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.performance import PerformancePeriod
from app.services.data_integrity_service import DataIntegrityService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/data-integrity", tags=["数据完整性"])


@router.get("/check/{engineer_id}", summary="检查数据完整性")
async def check_data_completeness(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查工程师的数据完整性"""
    service = DataIntegrityService(db)

    report = service.check_data_completeness(engineer_id, period_id)

    return ResponseModel(
        code=200,
        message="数据完整性检查完成",
        data=report
    )


@router.get("/report", summary="生成数据质量报告")
async def generate_data_quality_report(
    period_id: int,
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成数据质量报告"""
    service = DataIntegrityService(db)

    report = service.generate_data_quality_report(period_id, department_id)

    return ResponseModel(
        code=200,
        message="数据质量报告生成成功",
        data=report
    )


@router.get("/reminders", summary="获取数据缺失提醒")
async def get_missing_data_reminders(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据缺失提醒列表"""
    service = DataIntegrityService(db)

    reminders = service.get_missing_data_reminders(period_id)

    return ResponseModel(
        code=200,
        message="获取数据缺失提醒成功",
        data=reminders
    )


@router.get("/suggest-fixes/{engineer_id}", summary="获取自动修复建议")
async def get_auto_fix_suggestions(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取自动修复建议"""
    service = DataIntegrityService(db)

    suggestions = service.suggest_auto_fixes(engineer_id, period_id)

    return ResponseModel(
        code=200,
        message="获取自动修复建议成功",
        data=suggestions
    )


class AutoFixRequest(BaseModel):
    """自动修复请求"""
    engineer_id: int = Field(..., description="工程师ID")
    period_id: int = Field(..., description="考核周期ID")
    fix_types: Optional[List[str]] = Field(None, description="要修复的问题类型列表")


@router.post("/auto-fix", summary="自动修复数据问题")
async def auto_fix_data_issues(
    request: AutoFixRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动修复数据问题"""
    service = DataIntegrityService(db)

    try:
        result = service.auto_fix_data_issues(
            engineer_id=request.engineer_id,
            period_id=request.period_id,
            fix_types=request.fix_types
        )
        return ResponseModel(
            code=200,
            message="自动修复完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-reminders", summary="发送数据缺失提醒")
async def send_data_missing_reminders(
    period_id: int = Body(..., description="考核周期ID"),
    reminder_types: Optional[List[str]] = Body(None, description="提醒类型列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送数据缺失提醒（批量）"""
    service = DataIntegrityService(db)

    try:
        result = service.send_data_missing_reminders(
            period_id=period_id,
            reminder_types=reminder_types
        )
        return ResponseModel(
            code=200,
            message=f"已发送{result['sent_count']}个提醒",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-report", summary="导出数据质量报告")
async def export_data_quality_report(
    period_id: int,
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    format: str = Query('json', description="导出格式（json/excel/pdf）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出数据质量报告"""
    service = DataIntegrityService(db)

    try:
        report = service.export_data_quality_report(
            period_id=period_id,
            department_id=department_id,
            format=format
        )
        return ResponseModel(
            code=200,
            message="报告导出成功",
            data=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
