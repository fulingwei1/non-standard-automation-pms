# -*- coding: utf-8 -*-
"""
工作台统计 Schema
"""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class BusinessSupportDashboardResponse(BaseModel):
    """商务支持工作台统计响应"""

    active_contracts_count: int = Field(description="进行中合同数")
    pending_amount: Decimal = Field(description="待回款金额")
    overdue_amount: Decimal = Field(description="逾期款项")
    invoice_rate: Decimal = Field(description="本月开票率")
    active_bidding_count: int = Field(description="进行中投标数")
    acceptance_rate: Decimal = Field(description="验收按期率")
    urgent_tasks: List[dict] = Field(default_factory=list, description="紧急任务列表")
    today_todos: List[dict] = Field(default_factory=list, description="今日待办列表")


class PerformanceMetricsResponse(BaseModel):
    """本月绩效指标响应"""

    new_contracts_count: int = Field(description="新签合同数（本月签订的合同）")
    payment_completion_rate: Decimal = Field(description="回款完成率（本月实际回款/计划回款）")
    invoice_timeliness_rate: Decimal = Field(description="开票及时率（按时开票数/应开票数）")
    document_flow_count: int = Field(description="文件流转数（本月处理的文件数）")
    month: str = Field(description="统计月份（YYYY-MM格式）")
