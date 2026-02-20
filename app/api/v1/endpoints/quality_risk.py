# -*- coding: utf-8 -*-
"""
质量风险识别系统 API端点
提供质量风险检测、测试推荐、质量报告等功能
"""

import logging
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.quality_risk import (
    QualityRiskDetectionUpdate,
    QualityRiskDetectionResponse,
    QualityTestRecommendationUpdate,
    QualityTestRecommendationResponse,
    WorkLogAnalysisRequest,
    QualityReportRequest,
    QualityReportResponse,
)
from app.services.quality_risk_management import QualityRiskManagementService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 质量风险检测端点 ====================

@router.post(
    "/detections/analyze",
    response_model=QualityRiskDetectionResponse,
    summary="分析工作日志并检测质量风险"
)
async def analyze_work_logs(
    request: WorkLogAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分析工作日志，自动检测质量风险
    
    - **project_id**: 项目ID（必填）
    - **start_date**: 开始日期（可选，默认最近7天）
    - **end_date**: 结束日期（可选，默认今天）
    - **module_name**: 模块名称（可选）
    - **user_ids**: 用户ID列表（可选）
    """
    try:
        service = QualityRiskManagementService(db)
        detection = service.analyze_work_logs(
            project_id=request.project_id,
            start_date=request.start_date,
            end_date=request.end_date,
            module_name=request.module_name,
            user_ids=request.user_ids,
            current_user_id=current_user.id
        )
        return detection
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"分析工作日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


@router.get(
    "/detections",
    response_model=List[QualityRiskDetectionResponse],
    summary="查询质量风险检测记录"
)
async def list_detections(
    project_id: Optional[int] = Query(None, description="项目ID"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    status: Optional[str] = Query(None, description="状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询质量风险检测记录列表"""
    service = QualityRiskManagementService(db)
    detections = service.list_detections(
        project_id=project_id,
        risk_level=risk_level,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return detections


@router.get(
    "/detections/{detection_id}",
    response_model=QualityRiskDetectionResponse,
    summary="获取质量风险检测详情"
)
async def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取质量风险检测详情"""
    service = QualityRiskManagementService(db)
    detection = service.get_detection(detection_id)
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    return detection


@router.patch(
    "/detections/{detection_id}",
    response_model=QualityRiskDetectionResponse,
    summary="更新质量风险检测状态"
)
async def update_detection(
    detection_id: int,
    update_data: QualityRiskDetectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新质量风险检测状态（确认/标记为误报/解决）"""
    service = QualityRiskManagementService(db)
    detection = service.update_detection(
        detection_id=detection_id,
        status=update_data.status,
        resolution_note=update_data.resolution_note,
        current_user_id=current_user.id
    )
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    return detection


# ==================== 测试推荐端点 ====================

@router.post(
    "/recommendations/generate",
    response_model=QualityTestRecommendationResponse,
    summary="生成测试推荐"
)
async def generate_test_recommendation(
    detection_id: int = Query(..., description="质量风险检测ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于质量风险检测结果，生成测试推荐"""
    service = QualityRiskManagementService(db)
    recommendation = service.generate_test_recommendation(
        detection_id=detection_id,
        current_user_id=current_user.id
    )
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="质量风险检测记录不存在"
        )
    
    return recommendation


@router.get(
    "/recommendations",
    response_model=List[QualityTestRecommendationResponse],
    summary="查询测试推荐列表"
)
async def list_recommendations(
    project_id: Optional[int] = Query(None, description="项目ID"),
    priority_level: Optional[str] = Query(None, description="优先级"),
    status: Optional[str] = Query(None, description="状态"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询测试推荐列表"""
    service = QualityRiskManagementService(db)
    recommendations = service.list_recommendations(
        project_id=project_id,
        priority_level=priority_level,
        status=status,
        skip=skip,
        limit=limit
    )
    return recommendations


@router.patch(
    "/recommendations/{recommendation_id}",
    response_model=QualityTestRecommendationResponse,
    summary="更新测试推荐"
)
async def update_recommendation(
    recommendation_id: int,
    update_data: QualityTestRecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试推荐（接受/拒绝/完成/评估效果）"""
    service = QualityRiskManagementService(db)
    recommendation = service.update_recommendation(
        recommendation_id=recommendation_id,
        update_data=update_data.model_dump(exclude_unset=True)
    )
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试推荐不存在"
        )
    
    return recommendation


# ==================== 质量报告端点 ====================

@router.post(
    "/reports/generate",
    response_model=QualityReportResponse,
    summary="生成质量分析报告"
)
async def generate_quality_report(
    request: QualityReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成项目质量分析报告（包含风险趋势、推荐建议等）"""
    try:
        service = QualityRiskManagementService(db)
        report = service.generate_quality_report(
            project_id=request.project_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_recommendations=request.include_recommendations
        )
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"生成质量报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


# ==================== 统计分析端点 ====================

@router.get("/statistics/summary", summary="质量风险统计摘要")
async def get_statistics_summary(
    project_id: Optional[int] = Query(None, description="项目ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取质量风险统计摘要"""
    service = QualityRiskManagementService(db)
    summary = service.get_statistics_summary(
        project_id=project_id,
        days=days
    )
    return summary
