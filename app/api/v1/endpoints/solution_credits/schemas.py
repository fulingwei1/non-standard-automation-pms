# -*- coding: utf-8 -*-
"""
方案生成积分管理 - Schema定义
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreditInfoResponse(BaseModel):
    """用户积分信息响应"""
    user_id: int
    balance: int = Field(..., description="当前积分余额")
    generate_cost: int = Field(..., description="每次生成消耗积分")
    can_generate: bool = Field(..., description="是否可以生成方案")
    remaining_generations: int = Field(..., description="剩余可生成次数")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")


class TransactionResponse(BaseModel):
    """交易记录响应"""
    id: int
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    related_type: Optional[str]
    related_id: Optional[int]
    remark: Optional[str]
    operator_id: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """交易记录列表响应"""
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int


class AdminAddCreditsRequest(BaseModel):
    """管理员充值请求"""
    user_id: int = Field(..., description="目标用户ID")
    amount: int = Field(..., ge=1, le=1000, description="充值数量（1-1000）")
    remark: Optional[str] = Field(None, max_length=200, description="充值备注")


class BatchAddCreditsRequest(BaseModel):
    """批量���值请求"""
    user_ids: List[int] = Field(..., min_length=1, max_length=100, description="用户ID列表")
    amount: int = Field(..., ge=1, le=1000, description="每人充值数量（1-1000）")
    remark: Optional[str] = Field(None, max_length=200, description="充值备注")


class AdminDeductCreditsRequest(BaseModel):
    """管理员扣除请求"""
    user_id: int = Field(..., description="目标用户ID")
    amount: int = Field(..., ge=1, le=1000, description="扣除数量（1-1000）")
    remark: str = Field(..., min_length=2, max_length=200, description="扣除原因（必填）")


class UserCreditItem(BaseModel):
    """用户积分项"""
    user_id: int
    username: str
    real_name: Optional[str]
    employee_no: Optional[str]
    department: Optional[str]
    balance: int
    remaining_generations: int
    last_updated: Optional[datetime]


class UserCreditListResponse(BaseModel):
    """用户积分列表响应"""
    items: List[UserCreditItem]
    total: int
    page: int
    page_size: int


class CreditConfigItem(BaseModel):
    """积分配置项"""
    key: str
    value: str
    description: Optional[str]
    is_active: bool


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置说明")


class OperationResponse(BaseModel):
    """操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None
