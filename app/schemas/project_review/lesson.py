"""
项目经验教训Schema
"""
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ProjectLessonBase(BaseModel):
    """经验教训基础Schema"""
    lesson_type: str = Field(..., description="类型：SUCCESS/FAILURE")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: str = Field(..., description="问题/经验描述")
    root_cause: Optional[str] = Field(None, description="根本原因")
    impact: Optional[str] = Field(None, description="影响范围")
    improvement_action: Optional[str] = Field(None, description="改进措施")
    category: Optional[str] = Field(None, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    priority: str = Field(default="MEDIUM", description="优先级")


class ProjectLessonCreate(ProjectLessonBase):
    """创建经验教训"""
    review_id: int = Field(..., description="复盘报告ID")
    project_id: int = Field(..., description="项目ID")
    responsible_person: Optional[str] = None
    due_date: Optional[date] = None


class ProjectLessonUpdate(BaseModel):
    """更新经验教训"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    improvement_action: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    responsible_person: Optional[str] = None
    due_date: Optional[date] = None


class ProjectLessonResponse(BaseModel):
    """经验教训响应"""
    id: int
    review_id: int
    project_id: int
    lesson_type: str
    title: str
    description: str
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    improvement_action: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: str
    status: str
    responsible_person: Optional[str] = None
    due_date: Optional[date] = None
    resolved_date: Optional[date] = None
    ai_extracted: bool = False
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LessonExtractRequest(BaseModel):
    """提取经验教训请求"""
    review_id: int = Field(..., description="复盘报告ID")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="最小置信度")
    auto_save: bool = Field(default=True, description="是否自动保存")


class LessonExtractResponse(BaseModel):
    """提取经验教训响应"""
    success: bool
    review_id: int
    extracted_count: int
    saved_count: int
    lessons: List[ProjectLessonResponse]
    processing_time_ms: float
