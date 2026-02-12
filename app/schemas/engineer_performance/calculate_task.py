# -*- coding: utf-8 -*-
"""
calculate_task Schemas

包含calculate_task相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 计算任务 Schemas ====================

class CalculateTaskCreate(BaseModel):
    """创建计算任务"""
    period_id: int = Field(..., description="考核周期ID")
    job_types: Optional[List[str]] = Field(None, description="指定岗位类型")
    force_recalculate: bool = Field(False, description="是否强制重新计算")


class CalculateTaskStatus(BaseModel):
    """计算任务状态"""
    task_id: str
    status: str  # pending/running/completed/failed
    progress: int = Field(0, ge=0, le=100)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
