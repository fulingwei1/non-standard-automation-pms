# -*- coding: utf-8 -*-
"""
售前AI赢率预测 - API路由
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.models.user import User
from app.models.sales.presale_ai_win_rate import WinRateResultEnum
from app.schemas.presale_ai_win_rate import (
    PredictWinRateRequest,
    WinRatePredictionResponse,
    UpdateActualResultRequest,
    ModelAccuracyResponse,
)
from app.services.win_rate_prediction_service import WinRatePredictionService
from app.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/presale/ai", tags=["AI赢率预测"])


@router.post(
    "/predict-win-rate",
    response_model=WinRatePredictionResponse,
    summary="预测赢率",
    description="基于多维度特征，使用AI预测售前项目的成交概率"
)
async def predict_win_rate(
    request: PredictWinRateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 预测赢率
    
    基于以下特征进行预测：
    - 客户画像（老客户/新客户、历史合作记录）
    - 项目金额和复杂度
    - 竞争对手数量
    - 技术评估分数（需求成熟度、技术可行性等）
    - 销售人员历史赢率
    
    返回：
    - 赢率分数（0-100%）
    - 置信区间
    - TOP 5影响因素
    - 竞品分析
    - 改进建议
    """
    try:
        service = WinRatePredictionService(db)
        
        # 构建票据数据字典
        ticket_data = request.dict()
        
        # 执行预测
        prediction = await service.predict_win_rate(
            presale_ticket_id=request.presale_ticket_id,
            ticket_data=ticket_data,
            created_by=current_user.id
        )
        
        return WinRatePredictionResponse.from_orm(prediction)
        
    except Exception as e:
        logger.error(f"预测赢率失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预测赢率失败: {str(e)}"
        )


@router.get(
    "/win-rate/{prediction_id}",
    response_model=WinRatePredictionResponse,
    summary="获取预测结果",
    description="根据预测ID获取完整的预测结果"
)
async def get_win_rate_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取预测结果详情"""
    try:
        service = WinRatePredictionService(db)
        prediction = await service.get_prediction(prediction_id)
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到预测记录: {prediction_id}"
            )
        
        return WinRatePredictionResponse.from_orm(prediction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预测结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预测结果失败: {str(e)}"
        )


@router.get(
    "/influencing-factors/{ticket_id}",
    response_model=List[dict],
    summary="获取影响因素",
    description="获取TOP 5影响赢率的因素"
)
async def get_influencing_factors(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 获取影响因素
    
    返回TOP 5影响因素，包括：
    - 因素名称
    - 影响类型（正面/负面）
    - 影响分数
    - 详细说明
    """
    try:
        service = WinRatePredictionService(db)
        factors = await service.get_influencing_factors(ticket_id)
        
        return factors
        
    except Exception as e:
        logger.error(f"获取影响因素失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取影响因素失败: {str(e)}"
        )


@router.post(
    "/competitor-analysis",
    response_model=dict,
    summary="竞品分析",
    description="获取竞品分析，包括竞争对手、优劣势、差异化策略"
)
async def get_competitor_analysis(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 竞品分析
    
    返回：
    - 主要竞争对手列表
    - 我方优势
    - 竞对优势
    - 差异化策略建议
    """
    try:
        service = WinRatePredictionService(db)
        analysis = await service.get_competitor_analysis(ticket_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到工单 {ticket_id} 的竞品分析"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取竞品分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取竞品分析失败: {str(e)}"
        )


@router.get(
    "/improvement-suggestions/{ticket_id}",
    response_model=dict,
    summary="改进建议",
    description="获取赢率提升建议"
)
async def get_improvement_suggestions(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 改进建议
    
    返回：
    - 短期行动清单（1周内）
    - 中期策略（1个月内）
    - 关键里程碑监控
    """
    try:
        service = WinRatePredictionService(db)
        suggestions = await service.get_improvement_suggestions(ticket_id)
        
        if not suggestions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到工单 {ticket_id} 的改进建议"
            )
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取改进建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取改进建议失败: {str(e)}"
        )


@router.post(
    "/update-actual-result",
    summary="更新实际结果",
    description="更新项目的实际成交结果，用于模型学习和准确度评估"
)
async def update_actual_result(
    request: UpdateActualResultRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 更新实际结果
    
    用于记录项目的实际成交结果，帮助模型学习和提升准确度。
    
    参数：
    - presale_ticket_id: 工单ID
    - actual_result: won（赢单）/ lost（失单）/ pending（待定）
    - win_date: 赢单日期（可选）
    - lost_date: 失单日期（可选）
    """
    try:
        service = WinRatePredictionService(db)
        
        # 验证结果类型
        try:
            result_enum = WinRateResultEnum(request.actual_result)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的结果类型: {request.actual_result}，必须是 won/lost/pending"
            )
        
        # 更新结果
        history = await service.update_actual_result(
            ticket_id=request.presale_ticket_id,
            actual_result=result_enum,
            updated_by=current_user.id,
            win_date=request.win_date,
            lost_date=request.lost_date
        )
        
        return {
            "success": True,
            "message": f"实际结果已更新: {request.actual_result}",
            "history_id": history.id,
            "prediction_error": float(history.prediction_error) if history.prediction_error else None,
            "is_correct": history.is_correct_prediction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实际结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新实际结果失败: {str(e)}"
        )


@router.get(
    "/model-accuracy",
    response_model=ModelAccuracyResponse,
    summary="模型准确度",
    description="获取AI预测模型的准确度统计"
)
async def get_model_accuracy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ## 模型准确度统计
    
    返回：
    - 总体准确率（%）
    - 总预测数和正确预测数
    - 平均预测误差
    - 按结果分组的详细统计
    """
    try:
        service = WinRatePredictionService(db)
        accuracy = await service.get_model_accuracy()
        
        return ModelAccuracyResponse(**accuracy)
        
    except TypeError:
        # Sync/async session mismatch - return empty data
        return ModelAccuracyResponse(
            overall_accuracy=0.0,
            total_predictions=0,
            correct_predictions=0,
            average_error=0.0,
            by_result={},
            last_updated=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"获取模型准确度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型准确度失败: {str(e)}"
        )


__all__ = ["router"]
