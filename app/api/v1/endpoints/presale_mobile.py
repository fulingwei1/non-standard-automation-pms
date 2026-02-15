# -*- coding: utf-8 -*-
"""
移动端AI销售助手 - API路由
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.presale_mobile import (
    ChatRequest,
    ChatResponse,
    CreateVisitRecordRequest,
    CustomerSnapshotResponse,
    OfflineDataSyncRequest,
    OfflineDataSyncResponse,
    QuickEstimateRequest,
    QuickEstimateResponse,
    VisitHistoryResponse,
    VisitRecordResponse,
    VoiceQuestionRequest,
    VoiceQuestionResponse,
    VoiceToVisitRecordRequest,
)
from app.services.presale_mobile_service import PresaleMobileService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== AI问答 ====================


@router.post("/chat", response_model=ChatResponse, summary="实时AI问答")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    实时AI问答

    销售人员现场提问，AI实时回答，支持：
    - 技术参数查询
    - 竞品对比数据
    - 成功案例引用
    - 报价参考信息
    """
    service = PresaleMobileService(db)
    try:
        result = await service.chat(
            user_id=current_user.id,
            question=request.question,
            presale_ticket_id=request.presale_ticket_id,
            context=request.context,
        )
        return result
    except Exception as e:
        logger.error(f"AI问答失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI问答失败: {str(e)}",
        )


# ==================== 语音交互 ====================


@router.post(
    "/voice-question",
    response_model=VoiceQuestionResponse,
    summary="语音提问（STT+AI+TTS）",
)
async def voice_question(
    request: VoiceQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    语音提问

    支持：
    - 语音输入问题（STT）
    - AI实时回答
    - 语音播报答案（TTS）

    适合现场环境，解放双手
    """
    service = PresaleMobileService(db)
    try:
        result = await service.voice_question(
            user_id=current_user.id,
            audio_base64=request.audio_base64,
            audio_format=request.format,
            presale_ticket_id=request.presale_ticket_id,
        )
        return result
    except Exception as e:
        logger.error(f"语音提问失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音提问失败: {str(e)}",
        )


# ==================== 拜访准备 ====================


@router.get(
    "/visit-preparation/{ticket_id}",
    response_model=Dict[str, Any],
    summary="拜访准备清单",
)
def get_visit_preparation(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取拜访准备清单

    包含:
    - 客户背景自动展示
    - 话术推荐
    - 注意事项提醒
    - 技术资料
    - 竞品对比
    """
    service = PresaleMobileService(db)
    try:
        result = service.get_visit_preparation(ticket_id, current_user.id)
        return result
    except Exception as e:
        logger.error(f"获取拜访准备清单失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取拜访准备清单失败: {str(e)}",
        )


# ==================== 快速估价 ====================


@router.post(
    "/quick-estimate", response_model=QuickEstimateResponse, summary="现场快速估价"
)
async def quick_estimate(
    request: QuickEstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    现场快速估价

    支持:
    - 拍照识别设备（可选）
    - 快速BOM匹配
    - 成本预估
    - 报价范围建议
    """
    service = PresaleMobileService(db)
    try:
        result = await service.quick_estimate(
            user_id=current_user.id,
            equipment_description=request.equipment_description,
            equipment_photo_base64=request.equipment_photo_base64,
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
        )
        return result
    except Exception as e:
        logger.error(f"快速估价失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速估价失败: {str(e)}",
        )


# ==================== 拜访记录 ====================


@router.post(
    "/create-visit-record",
    response_model=VisitRecordResponse,
    summary="创建拜访记录",
)
def create_visit_record(
    request: CreateVisitRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    创建拜访记录

    手动创建拜访记录，记录：
    - 拜访日期和类型
    - 参会人员
    - 讨论要点
    - 客户反馈
    - 下一步行动
    """
    service = PresaleMobileService(db)
    try:
        result = service.create_visit_record(
            user_id=current_user.id,
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            visit_date=request.visit_date.isoformat(),
            visit_type=request.visit_type.value,
            attendees=request.attendees,
            discussion_points=request.discussion_points,
            customer_feedback=request.customer_feedback,
            next_steps=request.next_steps,
        )
        return result
    except Exception as e:
        logger.error(f"创建拜访记录失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建拜访记录失败: {str(e)}",
        )


@router.post(
    "/voice-to-visit-record",
    response_model=VisitRecordResponse,
    summary="语音转拜访记录",
)
async def voice_to_visit_record(
    request: VoiceToVisitRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    语音转拜访记录

    通过语音自动生成拜访记录：
    - 语音转文字
    - AI提取关键信息
    - 自动生成拜访报告
    - 一键同步到系统
    """
    service = PresaleMobileService(db)
    try:
        result = await service.voice_to_visit_record(
            user_id=current_user.id,
            audio_base64=request.audio_base64,
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            visit_date=request.visit_date.isoformat(),
            visit_type=request.visit_type.value,
        )
        return result
    except Exception as e:
        logger.error(f"语音转拜访记录失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音转拜访记录失败: {str(e)}",
        )


@router.get(
    "/visit-history/{customer_id}",
    response_model=VisitHistoryResponse,
    summary="拜访历史",
)
def get_visit_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取客户拜访历史

    查询指定客户的所有拜访记录
    """
    service = PresaleMobileService(db)
    try:
        result = service.get_visit_history(customer_id)
        return result
    except Exception as e:
        logger.error(f"获取拜访历史失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取拜访历史失败: {str(e)}",
        )


# ==================== 客户快照 ====================


@router.get(
    "/customer-snapshot/{customer_id}",
    response_model=CustomerSnapshotResponse,
    summary="客户快照（背景信息）",
)
def get_customer_snapshot(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取客户快照

    快速查看客户背景信息：
    - 公司基本信息
    - 历史订单和营收
    - 最近互动记录
    - 关键决策人
    - 主要关注点
    """
    service = PresaleMobileService(db)
    try:
        result = service.get_customer_snapshot(customer_id)
        return result
    except Exception as e:
        logger.error(f"获取客户快照失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户快照失败: {str(e)}",
        )


# ==================== 离线数据同步 ====================


@router.post(
    "/sync-offline-data",
    response_model=OfflineDataSyncResponse,
    summary="离线数据同步",
)
def sync_offline_data(
    request: OfflineDataSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    离线数据同步

    同步离线时产生的数据：
    - 对话记录
    - 拜访记录
    - 估价记录
    """
    service = PresaleMobileService(db)
    try:
        result = service.sync_offline_data(
            user_id=current_user.id,
            data_type=request.data_type,
            local_id=request.local_id,
            data_payload=request.data_payload,
        )
        return result
    except Exception as e:
        logger.error(f"离线数据同步失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"离线数据同步失败: {str(e)}",
        )
