"""
知识库同步Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class KnowledgeSyncRequest(BaseModel):
    """知识库同步请求"""
    review_id: int = Field(..., description="复盘报告ID")
    auto_publish: bool = Field(default=True, description="是否自动发布")
    include_lessons: bool = Field(default=True, description="是否包含经验教训")


class KnowledgeSyncResponse(BaseModel):
    """知识库同步响应"""
    success: bool
    review_id: int
    knowledge_case_id: int
    case_name: str
    quality_score: float
    tags: List[str]
    sync_time: datetime
    is_new_case: bool
    updated_fields: List[str]


class KnowledgeImpactResponse(BaseModel):
    """知识库影响响应"""
    success: bool
    review_id: int
    synced: bool
    case_id: Optional[int] = None
    case_name: Optional[str] = None
    quality_score: Optional[float] = None
    tags: Optional[List[str]] = None
    last_updated: Optional[datetime] = None
    potential_reuse_scenarios: Optional[List[str]] = None
    similar_cases_count: Optional[int] = None
