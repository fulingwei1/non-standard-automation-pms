"""
AI客户情绪分析API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db
from app.services.ai_emotion_service import AIEmotionService
from app.schemas.presale_ai_emotion import (
    EmotionAnalysisRequest,
    EmotionAnalysisResponse,
    ChurnRiskPredictionRequest,
    ChurnRiskPredictionResponse,
    FollowUpRecommendationRequest,
    FollowUpRecommendationResponse,
    FollowUpReminderListResponse,
    DismissReminderRequest,
    EmotionTrendResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/v1/presale/ai", tags=["AI情绪分析"])


@router.post("/analyze-emotion", response_model=EmotionAnalysisResponse, summary="分析客户情绪")
async def analyze_emotion(
    request: EmotionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析客户沟通内容的情绪、购买意向和流失风险
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_id**: 客户ID
    - **communication_content**: 沟通内容
    
    返回情绪分析结果，包括：
    - 情绪类型 (positive/neutral/negative)
    - 购买意向评分 (0-100)
    - 流失风险等级 (high/medium/low)
    - 情绪影响因素
    """
    try:
        service = AIEmotionService(db)
        result = await service.analyze_emotion(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            communication_content=request.communication_content
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"情绪分析失败: {str(e)}")


@router.get("/emotion-analysis/{ticket_id}", response_model=EmotionAnalysisResponse, summary="获取情绪分析")
async def get_emotion_analysis(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定工单的最新情绪分析结果
    
    - **ticket_id**: 售前工单ID
    """
    try:
        from app.models.presale_ai_emotion_analysis import PresaleAIEmotionAnalysis
        from sqlalchemy import desc
        
        analysis = db.query(PresaleAIEmotionAnalysis).filter(
            PresaleAIEmotionAnalysis.presale_ticket_id == ticket_id
        ).order_by(desc(PresaleAIEmotionAnalysis.created_at)).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="未找到情绪分析记录")
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取情绪分析失败: {str(e)}")


@router.post("/predict-churn-risk", response_model=ChurnRiskPredictionResponse, summary="预测流失风险")
async def predict_churn_risk(
    request: ChurnRiskPredictionRequest,
    db: Session = Depends(get_db)
):
    """
    基于客户沟通历史预测流失风险
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_id**: 客户ID
    - **recent_communications**: 最近的沟通记录列表
    - **days_since_last_contact**: 距离上次联系的天数(可选)
    - **response_time_trend**: 回复时间趋势(可选)
    
    返回流失风险预测，包括：
    - 流失风险等级
    - 风险评分
    - 风险因素
    - 挽回策略建议
    """
    try:
        service = AIEmotionService(db)
        result = await service.predict_churn_risk(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            recent_communications=request.recent_communications,
            days_since_last_contact=request.days_since_last_contact,
            response_time_trend=request.response_time_trend
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流失风险预测失败: {str(e)}")


@router.post("/recommend-follow-up", response_model=FollowUpRecommendationResponse, summary="推荐跟进时机")
async def recommend_follow_up(
    request: FollowUpRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    基于客户情绪分析推荐最佳跟进时机和内容
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_id**: 客户ID
    - **latest_emotion_analysis_id**: 最新情绪分析ID(可选)
    
    返回跟进建议，包括：
    - 推荐跟进时间
    - 优先级
    - 跟进内容建议
    - 最佳时机理由
    """
    try:
        service = AIEmotionService(db)
        result = await service.recommend_follow_up(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            latest_emotion_analysis_id=request.latest_emotion_analysis_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"跟进推荐失败: {str(e)}")


@router.get("/follow-up-reminders", response_model=FollowUpReminderListResponse, summary="获取跟进提醒列表")
async def get_follow_up_reminders(
    status: Optional[str] = Query(None, description="状态筛选: pending/completed/dismissed"),
    priority: Optional[str] = Query(None, description="优先级筛选: high/medium/low"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取跟进提醒列表
    
    - **status**: 状态筛选(可选)
    - **priority**: 优先级筛选(可选)
    - **limit**: 返回数量限制，默认50
    """
    try:
        service = AIEmotionService(db)
        reminders = service.get_follow_up_reminders(
            status=status,
            priority=priority,
            limit=limit
        )
        
        return {
            "total": len(reminders),
            "reminders": reminders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提醒列表失败: {str(e)}")


@router.get("/emotion-trend/{ticket_id}", response_model=EmotionTrendResponse, summary="获取情绪趋势")
async def get_emotion_trend(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定工单的客户情绪趋势
    
    - **ticket_id**: 售前工单ID
    
    返回情绪趋势数据，包括：
    - 趋势数据点列表
    - 关键转折点
    """
    try:
        service = AIEmotionService(db)
        trend = service.get_emotion_trend(ticket_id)
        
        if not trend:
            raise HTTPException(status_code=404, detail="未找到情绪趋势数据")
        
        return trend
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取情绪趋势失败: {str(e)}")


@router.post("/dismiss-reminder/{reminder_id}", response_model=MessageResponse, summary="忽略提醒")
async def dismiss_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    """
    忽略指定的跟进提醒
    
    - **reminder_id**: 提醒ID
    """
    try:
        service = AIEmotionService(db)
        success = service.dismiss_reminder(reminder_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="未找到指定提醒")
        
        return MessageResponse(message="提醒已忽略", success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"忽略提醒失败: {str(e)}")


@router.post("/batch-analyze-customers", response_model=BatchAnalysisResponse, summary="批量分析客户")
async def batch_analyze_customers(
    request: BatchAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    批量分析多个客户的情绪和流失风险
    
    - **customer_ids**: 客户ID列表(1-100个)
    - **analysis_type**: 分析类型(full/emotion/churn)，默认full
    
    返回批量分析摘要，包括：
    - 分析成功/失败数量
    - 每个客户的分析摘要
    - 是否需要关注标记
    - 推荐行动建议
    """
    try:
        service = AIEmotionService(db)
        result = await service.batch_analyze_customers(
            customer_ids=request.customer_ids,
            analysis_type=request.analysis_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")
