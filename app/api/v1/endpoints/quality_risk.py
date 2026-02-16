# -*- coding: utf-8 -*-
"""
质量风险识别系统 API端点
提供质量风险检测、测试推荐、质量报告等功能
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.quality_risk_detection import (
    QualityRiskDetection,
    QualityTestRecommendation,
    RiskLevelEnum,
    RiskStatusEnum,
    TestRecommendationStatusEnum,
)
from app.models.timesheet import Timesheet
from app.models.progress import Task
from app.schemas.quality_risk import (
    QualityRiskDetectionCreate,
    QualityRiskDetectionUpdate,
    QualityRiskDetectionResponse,
    QualityTestRecommendationCreate,
    QualityTestRecommendationUpdate,
    QualityTestRecommendationResponse,
    WorkLogAnalysisRequest,
    QualityReportRequest,
    QualityReportResponse,
)
from app.services.quality_risk_ai import (
    QualityRiskAnalyzer,
    TestRecommendationEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 质量风险检测端点 ====================

@router.post("/detections/analyze", response_model=QualityRiskDetectionResponse, summary="分析工作日志并检测质量风险")
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
        # 设置默认日期范围
        end_date = request.end_date or date.today()
        start_date = request.start_date or (end_date - timedelta(days=7))
        
        # 查询工作日志
        query = db.query(Timesheet).filter(
            Timesheet.project_id == request.project_id,
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )
        
        if request.module_name:
            query = query.filter(Timesheet.task_name.contains(request.module_name))
        
        if request.user_ids:
            query = query.filter(Timesheet.user_id.in_(request.user_ids))
        
        work_logs = query.all()
        
        if not work_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到符合条件的工作日志"
            )
        
        # 转换为字典格式
        log_dicts = [
            {
                'work_date': str(log.work_date),
                'user_name': log.user_name,
                'task_name': log.task_name,
                'work_content': log.work_content or '',
                'work_result': log.work_result or '',
                'hours': float(log.hours) if log.hours else 0
            }
            for log in work_logs
        ]
        
        # AI分析
        analyzer = QualityRiskAnalyzer(db)
        analysis_result = analyzer.analyze_work_logs(log_dicts)
        
        # 创建检测记录
        detection = QualityRiskDetection(
            project_id=request.project_id,
            module_name=request.module_name,
            detection_date=end_date,
            source_type='WORK_LOG',
            risk_signals=analysis_result.get('risk_signals', []),
            risk_keywords=analysis_result.get('risk_keywords', {}),
            abnormal_patterns=analysis_result.get('abnormal_patterns', []),
            risk_level=analysis_result.get('risk_level'),
            risk_score=analysis_result.get('risk_score'),
            risk_category=analysis_result.get('risk_category'),
            predicted_issues=analysis_result.get('predicted_issues', []),
            rework_probability=analysis_result.get('rework_probability'),
            estimated_impact_days=analysis_result.get('estimated_impact_days'),
            ai_analysis=analysis_result.get('ai_analysis'),
            ai_confidence=analysis_result.get('ai_confidence'),
            analysis_model=analysis_result.get('analysis_model'),
            status='DETECTED',
            created_by=current_user.id
        )
        
        db.add(detection)
        db.commit()
        db.refresh(detection)
        
        logger.info(f"创建质量风险检测记录 ID={detection.id}, 项目={request.project_id}, 风险等级={detection.risk_level}")
        
        return detection
        
    except Exception as e:
        db.rollback()
        logger.error(f"分析工作日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


@router.get("/detections", response_model=List[QualityRiskDetectionResponse], summary="查询质量风险检测记录")
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
    
    query = db.query(QualityRiskDetection)
    
    if project_id:
        query = query.filter(QualityRiskDetection.project_id == project_id)
    
    if risk_level:
        query = query.filter(QualityRiskDetection.risk_level == risk_level)
    
    if status:
        query = query.filter(QualityRiskDetection.status == status)
    
    if start_date:
        query = query.filter(QualityRiskDetection.detection_date >= start_date)
    
    if end_date:
        query = query.filter(QualityRiskDetection.detection_date <= end_date)
    
    query = query.order_by(desc(QualityRiskDetection.detection_date))
    
    detections = query.offset(skip).limit(limit).all()
    
    return detections


@router.get("/detections/{detection_id}", response_model=QualityRiskDetectionResponse, summary="获取质量风险检测详情")
async def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取质量风险检测详情"""
    
    detection = db.query(QualityRiskDetection).filter(
        QualityRiskDetection.id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    return detection


@router.patch("/detections/{detection_id}", response_model=QualityRiskDetectionResponse, summary="更新质量风险检测状态")
async def update_detection(
    detection_id: int,
    update_data: QualityRiskDetectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新质量风险检测状态（确认/标记为误报/解决）"""
    
    detection = db.query(QualityRiskDetection).filter(
        QualityRiskDetection.id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    # 更新字段
    if update_data.status:
        detection.status = update_data.status
        if update_data.status in ['CONFIRMED', 'FALSE_POSITIVE', 'RESOLVED']:
            detection.confirmed_by = current_user.id
            detection.confirmed_at = datetime.now()
    
    if update_data.resolution_note:
        detection.resolution_note = update_data.resolution_note
    
    db.commit()
    db.refresh(detection)
    
    logger.info(f"更新质量风险检测 ID={detection_id}, 状态={detection.status}")
    
    return detection


# ==================== 测试推荐端点 ====================

@router.post("/recommendations/generate", response_model=QualityTestRecommendationResponse, summary="生成测试推荐")
async def generate_test_recommendation(
    detection_id: int = Query(..., description="质量风险检测ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于质量风险检测结果，生成测试推荐"""
    
    # 查询检测记录
    detection = db.query(QualityRiskDetection).filter(
        QualityRiskDetection.id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="质量风险检测记录不存在"
        )
    
    # 构建风险分析结果
    risk_analysis = {
        'risk_level': detection.risk_level,
        'risk_score': float(detection.risk_score),
        'risk_category': detection.risk_category,
        'risk_signals': detection.risk_signals or [],
        'risk_keywords': detection.risk_keywords or {},
        'abnormal_patterns': detection.abnormal_patterns or [],
        'predicted_issues': detection.predicted_issues or [],
        'rework_probability': float(detection.rework_probability) if detection.rework_probability else 0,
        'estimated_impact_days': detection.estimated_impact_days or 0
    }
    
    # 项目信息（简化版）
    project_info = {
        'project_id': detection.project_id
    }
    
    # 生成推荐
    engine = TestRecommendationEngine()
    recommendation_data = engine.generate_recommendations(risk_analysis, project_info)
    
    # 创建推荐记录
    recommendation = QualityTestRecommendation(
        project_id=detection.project_id,
        detection_id=detection.id,
        recommendation_date=date.today(),
        focus_areas=recommendation_data['focus_areas'],
        priority_modules=recommendation_data.get('priority_modules'),
        risk_modules=recommendation_data.get('risk_modules'),
        test_types=recommendation_data.get('test_types'),
        test_scenarios=recommendation_data.get('test_scenarios'),
        test_coverage_target=recommendation_data.get('test_coverage_target'),
        recommended_testers=recommendation_data.get('recommended_testers'),
        recommended_days=recommendation_data.get('recommended_days'),
        priority_level=recommendation_data['priority_level'],
        ai_reasoning=recommendation_data.get('ai_reasoning'),
        risk_summary=recommendation_data.get('risk_summary'),
        status='PENDING',
        created_by=current_user.id
    )
    
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    
    logger.info(f"生成测试推荐 ID={recommendation.id}, 检测={detection_id}, 优先级={recommendation.priority_level}")
    
    return recommendation


@router.get("/recommendations", response_model=List[QualityTestRecommendationResponse], summary="查询测试推荐列表")
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
    
    query = db.query(QualityTestRecommendation)
    
    if project_id:
        query = query.filter(QualityTestRecommendation.project_id == project_id)
    
    if priority_level:
        query = query.filter(QualityTestRecommendation.priority_level == priority_level)
    
    if status:
        query = query.filter(QualityTestRecommendation.status == status)
    
    query = query.order_by(desc(QualityTestRecommendation.recommendation_date))
    
    recommendations = query.offset(skip).limit(limit).all()
    
    return recommendations


@router.patch("/recommendations/{recommendation_id}", response_model=QualityTestRecommendationResponse, summary="更新测试推荐")
async def update_recommendation(
    recommendation_id: int,
    update_data: QualityTestRecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试推荐（接受/拒绝/完成/评估效果）"""
    
    recommendation = db.query(QualityTestRecommendation).filter(
        QualityTestRecommendation.id == recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试推荐不存在"
        )
    
    # 更新字段
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(recommendation, field, value)
    
    db.commit()
    db.refresh(recommendation)
    
    logger.info(f"更新测试推荐 ID={recommendation_id}, 状态={recommendation.status}")
    
    return recommendation


# ==================== 质量报告端点 ====================

@router.post("/reports/generate", response_model=QualityReportResponse, summary="生成质量分析报告")
async def generate_quality_report(
    request: QualityReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成项目质量分析报告（包含风险趋势、推荐建议等）"""
    
    # 查询检测记录
    detections = db.query(QualityRiskDetection).filter(
        QualityRiskDetection.project_id == request.project_id,
        QualityRiskDetection.detection_date >= request.start_date,
        QualityRiskDetection.detection_date <= request.end_date
    ).all()
    
    if not detections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定时间段内没有质量风险检测数据"
        )
    
    # 统计风险分布
    risk_distribution = {}
    for detection in detections:
        level = detection.risk_level
        risk_distribution[level] = risk_distribution.get(level, 0) + 1
    
    # 确定总体风险等级
    if risk_distribution.get('CRITICAL', 0) > 0:
        overall_risk = 'CRITICAL'
    elif risk_distribution.get('HIGH', 0) >= 3:
        overall_risk = 'HIGH'
    elif risk_distribution.get('MEDIUM', 0) >= 5:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'
    
    # 提取高风险模块
    top_risk_modules = []
    for detection in sorted(detections, key=lambda x: x.risk_score, reverse=True)[:5]:
        top_risk_modules.append({
            'module': detection.module_name or '未知模块',
            'risk_score': float(detection.risk_score),
            'risk_level': detection.risk_level,
            'detection_date': str(detection.detection_date)
        })
    
    # 趋势分析
    trend_data = {}
    for detection in detections:
        date_key = str(detection.detection_date)
        if date_key not in trend_data:
            trend_data[date_key] = {'count': 0, 'avg_score': 0, 'scores': []}
        trend_data[date_key]['count'] += 1
        trend_data[date_key]['scores'].append(float(detection.risk_score))
    
    for date_key in trend_data:
        scores = trend_data[date_key]['scores']
        trend_data[date_key]['avg_score'] = sum(scores) / len(scores)
    
    # 查询推荐（如果需要）
    recommendations_data = None
    if request.include_recommendations:
        recommendations = db.query(QualityTestRecommendation).filter(
            QualityTestRecommendation.project_id == request.project_id,
            QualityTestRecommendation.recommendation_date >= request.start_date,
            QualityTestRecommendation.recommendation_date <= request.end_date
        ).all()
        
        recommendations_data = [
            {
                'id': rec.id,
                'priority': rec.priority_level,
                'status': rec.status,
                'recommended_days': rec.recommended_days,
                'ai_reasoning': rec.ai_reasoning
            }
            for rec in recommendations
        ]
    
    # 生成报告摘要
    summary = f"在{request.start_date}至{request.end_date}期间，共检测到{len(detections)}个质量风险，"
    summary += f"总体风险等级为{overall_risk}。"
    if risk_distribution.get('CRITICAL', 0) > 0:
        summary += f"其中包含{risk_distribution['CRITICAL']}个严重风险，需立即关注。"
    
    report = {
        'project_id': request.project_id,
        'project_name': f"项目 {request.project_id}",  # TODO: 从Project表查询
        'report_period': f"{request.start_date} 至 {request.end_date}",
        'overall_risk_level': overall_risk,
        'total_detections': len(detections),
        'risk_distribution': risk_distribution,
        'top_risk_modules': top_risk_modules,
        'trend_analysis': trend_data,
        'recommendations': recommendations_data,
        'summary': summary,
        'generated_at': datetime.now()
    }
    
    logger.info(f"生成质量报告: 项目={request.project_id}, 检测数={len(detections)}, 风险等级={overall_risk}")
    
    return report


# ==================== 统计分析端点 ====================

@router.get("/statistics/summary", summary="质量风险统计摘要")
async def get_statistics_summary(
    project_id: Optional[int] = Query(None, description="项目ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取质量风险统计摘要"""
    
    start_date = date.today() - timedelta(days=days)
    
    query = db.query(QualityRiskDetection).filter(
        QualityRiskDetection.detection_date >= start_date
    )
    
    if project_id:
        query = query.filter(QualityRiskDetection.project_id == project_id)
    
    detections = query.all()
    
    # 统计
    total = len(detections)
    by_level = {}
    by_status = {}
    avg_score = 0
    
    for detection in detections:
        by_level[detection.risk_level] = by_level.get(detection.risk_level, 0) + 1
        by_status[detection.status] = by_status.get(detection.status, 0) + 1
        avg_score += float(detection.risk_score)
    
    avg_score = avg_score / total if total > 0 else 0
    
    return {
        'total_detections': total,
        'average_risk_score': round(avg_score, 2),
        'by_risk_level': by_level,
        'by_status': by_status,
        'period_days': days,
        'start_date': str(start_date),
        'end_date': str(date.today())
    }
