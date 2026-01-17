# -*- coding: utf-8 -*-
"""
客户供应商入驻 Schema
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class CustomerSupplierRegistrationCreate(BaseModel):
    """创建客户供应商入驻申请"""

    customer_id: int = Field(description="客户ID")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    platform_name: str = Field(max_length=100, description="平台名称")
    platform_url: Optional[str] = Field(default=None, description="平台链接")
    application_date: Optional[date] = Field(default=None, description="申请日期")
    contact_person: Optional[str] = Field(default=None, description="联系人")
    contact_phone: Optional[str] = Field(default=None, description="联系电话")
    contact_email: Optional[str] = Field(default=None, description="联系邮箱")
    required_docs: Optional[List[str]] = Field(default=None, description="提交资料")
    remark: Optional[str] = Field(default=None, description="备注")


class CustomerSupplierRegistrationUpdate(BaseModel):
    """更新入驻记录"""

    platform_name: Optional[str] = None
    platform_url: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    application_date: Optional[date] = None
    expire_date: Optional[date] = None
    required_docs: Optional[List[str]] = None
    registration_status: Optional[str] = None
    remark: Optional[str] = None


class CustomerSupplierRegistrationResponse(TimestampSchema):
    """入驻记录响应"""

    id: int
    registration_no: str
    customer_id: int
    customer_name: Optional[str] = None
    platform_name: str
    platform_url: Optional[str] = None
    registration_status: str
    application_date: Optional[date] = None
    approved_date: Optional[date] = None
    expire_date: Optional[date] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    required_docs: Optional[List[str]] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_comment: Optional[str] = None
    external_sync_status: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    remark: Optional[str] = None


class SupplierRegistrationReviewRequest(BaseModel):
    """入驻审核请求"""

    review_comment: Optional[str] = Field(default=None, description="审核意见")
