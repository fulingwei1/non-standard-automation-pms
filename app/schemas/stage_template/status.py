# -*- coding: utf-8 -*-
"""
状态更新 Schemas

包含状态更新和评审相关的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 状态更新 Schemas ====================

class UpdateStageStatusRequest(BaseModel):
    """更新阶段状态请求"""
    status: str = Field(..., description="新状态: PENDING/IN_PROGRESS/COMPLETED/DELAYED/BLOCKED/SKIPPED")
    remark: Optional[str] = Field(default=None, description="备注说明")


class StageReviewRequest(BaseModel):
    """阶段评审请求"""
    review_result: str = Field(..., description="评审结果: PASSED/CONDITIONAL/FAILED")
    review_notes: Optional[str] = Field(default=None, description="评审记录")

