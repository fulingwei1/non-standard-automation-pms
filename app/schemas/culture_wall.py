# -*- coding: utf-8 -*-
"""
文化墙 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== 文化墙内容 ====================

class CultureWallContentCreate(BaseModel):
    """创建文化墙内容"""
    content_type: str = Field(..., description="内容类型:STRATEGY/CULTURE/IMPORTANT/NOTICE/REWARD")
    title: str = Field(..., description="标题")
    content: Optional[str] = Field(None, description="内容")
    summary: Optional[str] = Field(None, description="摘要")
    images: Optional[List[Dict[str, Any]]] = Field(None, description="图片列表")
    videos: Optional[List[Dict[str, Any]]] = Field(None, description="视频列表")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")
    is_published: Optional[bool] = Field(False, description="是否发布")
    publish_date: Optional[date] = Field(None, description="发布日期")
    expire_date: Optional[date] = Field(None, description="过期日期")
    priority: Optional[int] = Field(0, description="优先级")
    display_order: Optional[int] = Field(0, description="显示顺序")
    related_project_id: Optional[int] = Field(None, description="关联项目ID")
    related_department_id: Optional[int] = Field(None, description="关联部门ID")


class CultureWallContentUpdate(BaseModel):
    """更新文化墙内容"""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
    videos: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_published: Optional[bool] = None
    publish_date: Optional[date] = None
    expire_date: Optional[date] = None
    priority: Optional[int] = None
    display_order: Optional[int] = None
    related_project_id: Optional[int] = None
    related_department_id: Optional[int] = None


class CultureWallContentResponse(BaseModel):
    """文化墙内容响应"""
    id: int
    content_type: str
    title: str
    content: Optional[str]
    summary: Optional[str]
    images: Optional[List[Dict[str, Any]]]
    videos: Optional[List[Dict[str, Any]]]
    attachments: Optional[List[Dict[str, Any]]]
    is_published: bool
    publish_date: Optional[date]
    expire_date: Optional[date]
    priority: int
    display_order: int
    view_count: int
    related_project_id: Optional[int]
    related_department_id: Optional[int]
    published_by: Optional[int]
    published_by_name: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_read: Optional[bool] = False  # 是否已读（需要查询时填充）

    class Config:
        from_attributes = True


# ==================== 个人目标 ====================

class PersonalGoalCreate(BaseModel):
    """创建个人目标"""
    goal_type: str = Field(..., description="目标类型:MONTHLY/QUARTERLY/YEARLY")
    period: str = Field(..., description="目标周期")
    title: str = Field(..., description="目标标题")
    description: Optional[str] = Field(None, description="目标描述")
    target_value: Optional[str] = Field(None, description="目标值")
    unit: Optional[str] = Field(None, description="单位")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    notes: Optional[str] = Field(None, description="备注")


class PersonalGoalUpdate(BaseModel):
    """更新个人目标"""
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[str] = None
    current_value: Optional[str] = None
    unit: Optional[str] = None
    progress: Optional[int] = None
    status: Optional[str] = None
    end_date: Optional[date] = None
    completed_date: Optional[date] = None
    notes: Optional[str] = None


class PersonalGoalResponse(BaseModel):
    """个人目标响应"""
    id: int
    user_id: int
    goal_type: str
    period: str
    title: str
    description: Optional[str]
    target_value: Optional[str]
    current_value: Optional[str]
    unit: Optional[str]
    progress: int
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    completed_date: Optional[date]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 文化墙汇总 ====================

class CultureWallSummary(BaseModel):
    """文化墙汇总响应"""
    strategies: List[CultureWallContentResponse] = Field(default=[], description="战略规划")
    cultures: List[CultureWallContentResponse] = Field(default=[], description="企业文化")
    important_items: List[CultureWallContentResponse] = Field(default=[], description="重要事项")
    notices: List[CultureWallContentResponse] = Field(default=[], description="通知公告")
    rewards: List[CultureWallContentResponse] = Field(default=[], description="奖励通报")
    personal_goals: List[PersonalGoalResponse] = Field(default=[], description="个人目标")
    notifications: List[Dict[str, Any]] = Field(default=[], description="系统通知（从通知系统获取）")
