# -*- coding: utf-8 -*-
"""
合同相关 Schema - 审核和盖章
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class ContractReviewCreate(BaseModel):
    """创建合同审核"""

    contract_id: int = Field(description="合同ID")
    review_type: str = Field(max_length=20, description="审核类型")
    review_comment: Optional[str] = Field(default=None, description="审核意见")
    risk_items: Optional[dict] = Field(default=None, description="风险项列表")


class ContractReviewUpdate(BaseModel):
    """更新合同审核"""

    review_status: Optional[str] = None
    review_comment: Optional[str] = None
    risk_items: Optional[dict] = None


class ContractReviewResponse(TimestampSchema):
    """合同审核响应"""

    id: int
    contract_id: int
    review_type: Optional[str] = None
    review_status: Optional[str] = None
    reviewer_id: Optional[int] = None
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    risk_items: Optional[dict] = None


class ContractSealRecordCreate(BaseModel):
    """创建合同盖章记录"""

    contract_id: int = Field(description="合同ID")
    seal_date: Optional[date] = Field(default=None, description="盖章日期")
    send_date: Optional[date] = Field(default=None, description="邮寄日期")
    tracking_no: Optional[str] = Field(default=None, max_length=50, description="快递单号")
    courier_company: Optional[str] = Field(default=None, max_length=50, description="快递公司")
    remark: Optional[str] = Field(default=None, description="备注")


class ContractSealRecordUpdate(BaseModel):
    """更新合同盖章记录"""

    seal_status: Optional[str] = None
    seal_date: Optional[date] = None
    send_date: Optional[date] = None
    tracking_no: Optional[str] = None
    courier_company: Optional[str] = None
    receive_date: Optional[date] = None
    archive_date: Optional[date] = None
    archive_location: Optional[str] = None
    remark: Optional[str] = None


class ContractSealRecordResponse(TimestampSchema):
    """合同盖章记录响应"""

    id: int
    contract_id: int
    seal_status: Optional[str] = None
    seal_date: Optional[date] = None
    seal_operator_id: Optional[int] = None
    send_date: Optional[date] = None
    tracking_no: Optional[str] = None
    courier_company: Optional[str] = None
    receive_date: Optional[date] = None
    archive_date: Optional[date] = None
    archive_location: Optional[str] = None
    remark: Optional[str] = None
