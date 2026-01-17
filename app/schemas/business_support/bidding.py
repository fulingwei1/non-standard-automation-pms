# -*- coding: utf-8 -*-
"""
投标管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class BiddingProjectCreate(BaseModel):
    """创建投标项目"""

    bidding_no: str = Field(max_length=50, description="投标编号")
    project_name: str = Field(max_length=500, description="项目名称")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    customer_name: Optional[str] = Field(default=None, max_length=200, description="客户名称")
    tender_no: Optional[str] = Field(default=None, max_length=100, description="招标编号")
    tender_type: Optional[str] = Field(default=None, max_length=20, description="招标类型")
    tender_platform: Optional[str] = Field(default=None, max_length=200, description="招标平台")
    tender_url: Optional[str] = Field(default=None, max_length=500, description="招标链接")
    publish_date: Optional[date] = Field(default=None, description="发布日期")
    deadline_date: Optional[datetime] = Field(default=None, description="投标截止时间")
    bid_opening_date: Optional[datetime] = Field(default=None, description="开标时间")
    bid_bond: Optional[Decimal] = Field(default=None, description="投标保证金")
    bid_bond_status: Optional[str] = Field(default="not_required", max_length=20, description="保证金状态")
    estimated_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    submission_method: Optional[str] = Field(default=None, max_length=20, description="投递方式")
    submission_address: Optional[str] = Field(default=None, max_length=500, description="投递地址")
    sales_person_id: Optional[int] = Field(default=None, description="业务员ID")
    sales_person_name: Optional[str] = Field(default=None, max_length=50, description="业务员")
    support_person_id: Optional[int] = Field(default=None, description="商务支持ID")
    support_person_name: Optional[str] = Field(default=None, max_length=50, description="商务支持")
    remark: Optional[str] = Field(default=None, description="备注")


class BiddingProjectUpdate(BaseModel):
    """更新投标项目"""

    project_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    tender_no: Optional[str] = None
    tender_type: Optional[str] = None
    tender_platform: Optional[str] = None
    tender_url: Optional[str] = None
    publish_date: Optional[date] = None
    deadline_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    bid_bond: Optional[Decimal] = None
    bid_bond_status: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    bid_document_status: Optional[str] = None
    technical_doc_ready: Optional[bool] = None
    commercial_doc_ready: Optional[bool] = None
    qualification_doc_ready: Optional[bool] = None
    submission_method: Optional[str] = None
    submission_address: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    support_person_name: Optional[str] = None
    bid_result: Optional[str] = None
    bid_price: Optional[Decimal] = None
    win_price: Optional[Decimal] = None
    result_date: Optional[date] = None
    result_remark: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class BiddingProjectResponse(TimestampSchema):
    """投标项目响应"""

    id: int
    bidding_no: str
    project_name: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    tender_no: Optional[str] = None
    tender_type: Optional[str] = None
    tender_platform: Optional[str] = None
    tender_url: Optional[str] = None
    publish_date: Optional[date] = None
    deadline_date: Optional[datetime] = None
    bid_opening_date: Optional[datetime] = None
    bid_bond: Optional[Decimal] = None
    bid_bond_status: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    bid_document_status: Optional[str] = None
    technical_doc_ready: Optional[bool] = None
    commercial_doc_ready: Optional[bool] = None
    qualification_doc_ready: Optional[bool] = None
    submission_method: Optional[str] = None
    submission_address: Optional[str] = None
    sales_person_id: Optional[int] = None
    sales_person_name: Optional[str] = None
    support_person_id: Optional[int] = None
    support_person_name: Optional[str] = None
    bid_result: Optional[str] = None
    bid_price: Optional[Decimal] = None
    win_price: Optional[Decimal] = None
    result_date: Optional[date] = None
    result_remark: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class BiddingDocumentCreate(BaseModel):
    """创建投标文件"""

    bidding_project_id: int = Field(description="投标项目ID")
    document_type: str = Field(max_length=50, description="文件类型")
    document_name: str = Field(max_length=200, description="文件名称")
    file_path: str = Field(max_length=500, description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    version: Optional[str] = Field(default=None, max_length=20, description="版本号")
    remark: Optional[str] = Field(default=None, description="备注")


class BiddingDocumentResponse(TimestampSchema):
    """投标文件响应"""

    id: int
    bidding_project_id: int
    document_type: Optional[str] = None
    document_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    version: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    remark: Optional[str] = None
