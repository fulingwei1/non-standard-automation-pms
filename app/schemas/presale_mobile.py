# -*- coding: utf-8 -*-
"""
移动端AI销售助手 - Pydantic Schemas
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class QuestionType(str, Enum):
    """问题类型"""

    TECHNICAL = "technical"
    COMPETITOR = "competitor"
    CASE = "case"
    PRICING = "pricing"
    OTHER = "other"


class VisitType(str, Enum):
    """拜访类型"""

    FIRST_CONTACT = "first_contact"
    FOLLOW_UP = "follow_up"
    DEMO = "demo"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"


class SyncStatus(str, Enum):
    """同步状态"""

    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


# Chat Schemas
class ChatRequest(BaseModel):
    """AI问答请求"""

    question: str = Field(..., description="用户提问")
    presale_ticket_id: Optional[int] = Field(None, description="售前工单ID")
    context: Optional[Dict[str, Any]] = Field(None, description="对话上下文")


class ChatResponse(BaseModel):
    """AI问答响应"""

    id: int
    answer: str
    question_type: QuestionType
    response_time: int
    context: Optional[Dict[str, Any]]
    created_at: datetime


# Voice Schemas
class VoiceQuestionRequest(BaseModel):
    """语音提问请求"""

    audio_base64: str = Field(..., description="音频文件（base64编码）")
    presale_ticket_id: Optional[int] = Field(None, description="售前工单ID")
    format: str = Field("mp3", description="音频格式：mp3/wav/m4a")


class VoiceQuestionResponse(BaseModel):
    """语音提问响应"""

    transcription: str = Field(..., description="语音转文字")
    answer: str = Field(..., description="AI回答")
    audio_url: Optional[str] = Field(None, description="回答音频URL")
    response_time: int


# Visit Preparation Schemas
class VisitPreparationResponse(BaseModel):
    """拜访准备清单响应"""

    ticket_id: int
    customer_name: str
    customer_background: str
    previous_interactions: List[Dict[str, Any]]
    recommended_scripts: List[str]
    attention_points: List[str]
    technical_materials: List[Dict[str, str]]
    competitor_comparison: Optional[Dict[str, Any]]


# Quick Estimate Schemas
class QuickEstimateRequest(BaseModel):
    """快速估价请求"""

    equipment_photo_base64: Optional[str] = Field(None, description="设备照片（base64）")
    equipment_description: str = Field(..., description="设备描述")
    presale_ticket_id: Optional[int] = Field(None, description="售前工单ID")
    customer_id: Optional[int] = Field(None, description="客户ID")


class QuickEstimateResponse(BaseModel):
    """快速估价响应"""

    id: int
    recognized_equipment: str
    estimated_cost: int
    price_range_min: int
    price_range_max: int
    bom_items: List[Dict[str, Any]]
    confidence_score: int
    recommendation: str


# Visit Record Schemas
class CreateVisitRecordRequest(BaseModel):
    """创建拜访记录请求"""

    presale_ticket_id: int
    customer_id: int
    visit_date: date
    visit_type: VisitType
    attendees: List[Dict[str, str]] = Field(
        ..., description="参会人员：[{name, title, company}]"
    )
    discussion_points: str
    customer_feedback: Optional[str] = None
    next_steps: Optional[str] = None


class VoiceToVisitRecordRequest(BaseModel):
    """语音转拜访记录请求"""

    audio_base64: str = Field(..., description="拜访录音（base64编码）")
    presale_ticket_id: int
    customer_id: int
    visit_date: date
    visit_type: VisitType


class VisitRecordResponse(BaseModel):
    """拜访记录响应"""

    id: int
    presale_ticket_id: int
    customer_id: int
    visit_date: date
    visit_type: VisitType
    attendees: List[Dict[str, str]]
    discussion_points: str
    customer_feedback: Optional[str]
    next_steps: Optional[str]
    ai_generated_summary: Optional[str]
    created_at: datetime


# Customer Snapshot Schema
class CustomerSnapshotResponse(BaseModel):
    """客户快照响应"""

    customer_id: int
    customer_name: str
    industry: str
    company_size: Optional[str]
    contact_person: str
    contact_phone: str
    recent_tickets: List[Dict[str, Any]]
    total_orders: int
    total_revenue: float
    last_interaction: Optional[datetime]
    key_concerns: List[str]
    decision_makers: List[Dict[str, str]]


# Visit History Schema
class VisitHistoryResponse(BaseModel):
    """拜访历史响应"""

    visits: List[VisitRecordResponse]
    total_visits: int
    latest_visit: Optional[VisitRecordResponse]


# Offline Sync Schemas
class OfflineDataSyncRequest(BaseModel):
    """离线数据同步请求"""

    data_type: str = Field(..., description="数据类型：chat/visit/estimate")
    local_id: str = Field(..., description="本地临时ID")
    data_payload: Dict[str, Any] = Field(..., description="数据内容")


class OfflineDataSyncResponse(BaseModel):
    """离线数据同步响应"""

    success: bool
    synced_id: Optional[int]
    message: str


# Equipment Recognition Schema
class EquipmentRecognitionRequest(BaseModel):
    """设备识别请求"""

    image_base64: str = Field(..., description="设备图片（base64编码）")


class EquipmentRecognitionResponse(BaseModel):
    """设备识别响应"""

    equipment_name: str
    equipment_category: str
    specifications: Dict[str, Any]
    confidence: int
    similar_products: List[Dict[str, str]]
