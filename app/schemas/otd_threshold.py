# -*- coding: utf-8 -*-
"""
OTD 阈值配置 pydantic schema

- OtdThresholdConfigResponse：GET 返回用，所有字段必返
- OtdThresholdConfigUpdate：PUT 更新用，所有字段 Optional，支持部分更新
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OtdThresholdConfigBase(BaseModel):
    """阈值配置公共字段。"""

    model_config = ConfigDict(from_attributes=True)

    # 扫描范围
    scan_limit: Optional[int] = None
    stages_in_delivery: Optional[List[str]] = None

    # 维度1 采购延期
    procurement_overdue_medium_days: Optional[int] = None
    procurement_overdue_high_days: Optional[int] = None
    procurement_overdue_critical_days: Optional[int] = None

    # 维度2 图纸未冻结
    design_freeze_check_from_stage: Optional[str] = None
    design_freeze_high_stage: Optional[str] = None
    design_freeze_critical_stage: Optional[str] = None
    design_review_pass_conclusions: Optional[List[str]] = None

    # 维度3 客户变更
    change_window_short_days: Optional[int] = None
    change_window_long_days: Optional[int] = None
    change_critical_count: Optional[int] = None
    change_high_count: Optional[int] = None

    # 维度5 调试反复
    debug_window_days: Optional[int] = None
    debug_high_count: Optional[int] = None
    debug_medium_count: Optional[int] = None
    debug_categories: Optional[List[str]] = None

    # 维度6 验收资料
    acceptance_near_window_days: Optional[int] = None
    acceptance_high_window_days: Optional[int] = None
    acceptance_check_from_stage: Optional[str] = None
    acceptance_doc_keywords: Optional[List[str]] = None

    # 维度7 回款
    payment_upcoming_days: Optional[int] = None

    # 维度8 关键节点
    key_milestone_critical_days: Optional[int] = None
    key_milestone_critical_count: Optional[int] = None

    # 维度9 进度滞后
    progress_medium_threshold: Optional[float] = None
    progress_high_threshold: Optional[float] = None

    # 维度10 毛利偏差
    margin_medium_threshold: Optional[float] = None
    margin_high_threshold: Optional[float] = None
    margin_critical_threshold: Optional[float] = None

    # 维度11 未关闭事项
    open_items_high_count: Optional[int] = None
    open_items_medium_count: Optional[int] = None

    # 状态集合
    status_sets: Optional[dict] = None


class OtdThresholdConfigResponse(OtdThresholdConfigBase):
    """GET 返回结构。"""

    id: Optional[int] = None
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    is_default: bool
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OtdThresholdConfigUpdate(OtdThresholdConfigBase):
    """PUT 更新结构。所有业务字段 Optional，name/description 也允许改。"""

    name: Optional[str] = None
    description: Optional[str] = None
