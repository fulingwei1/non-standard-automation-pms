# -*- coding: utf-8 -*-
"""
联系人管理 Schema
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..common import TimestampSchema


class ContactCreate(BaseModel):
    """创建联系人"""

    model_config = ConfigDict(populate_by_name=True)

    customer_id: int = Field(description="所属客户ID")
    name: str = Field(max_length=100, description="姓名")
    position: Optional[str] = Field(default=None, max_length=100, description="职位")
    department: Optional[str] = Field(default=None, max_length=100, description="部门")
    
    # 联系方式
    mobile: Optional[str] = Field(default=None, max_length=20, description="手机号码")
    phone: Optional[str] = Field(default=None, max_length=20, description="座机")
    email: Optional[EmailStr] = Field(default=None, description="电子邮箱")
    wechat: Optional[str] = Field(default=None, max_length=100, description="微信号")
    
    # 其他信息
    birthday: Optional[date] = Field(default=None, description="生日")
    hobbies: Optional[str] = Field(default=None, description="兴趣爱好")
    notes: Optional[str] = Field(default=None, description="备注")
    is_primary: Optional[bool] = Field(default=False, description="是否为主要联系人")


class ContactUpdate(BaseModel):
    """更新联系人"""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=100, description="姓名")
    position: Optional[str] = Field(default=None, max_length=100, description="职位")
    department: Optional[str] = Field(default=None, max_length=100, description="部门")
    mobile: Optional[str] = Field(default=None, max_length=20, description="手机号码")
    phone: Optional[str] = Field(default=None, max_length=20, description="座机")
    email: Optional[EmailStr] = Field(default=None, description="电子邮箱")
    wechat: Optional[str] = Field(default=None, max_length=100, description="微信号")
    birthday: Optional[date] = Field(default=None, description="生日")
    hobbies: Optional[str] = Field(default=None, description="兴趣爱好")
    notes: Optional[str] = Field(default=None, description="备注")
    is_primary: Optional[bool] = Field(default=None, description="是否为主要联系人")


class ContactResponse(TimestampSchema):
    """联系人响应"""

    id: int = Field(description="联系人ID")
    customer_id: int = Field(description="所属客户ID")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    name: str = Field(description="姓名")
    position: Optional[str] = Field(default=None, description="职位")
    department: Optional[str] = Field(default=None, description="部门")
    mobile: Optional[str] = Field(default=None, description="手机号码")
    phone: Optional[str] = Field(default=None, description="座机")
    email: Optional[str] = Field(default=None, description="电子邮箱")
    wechat: Optional[str] = Field(default=None, description="微信号")
    birthday: Optional[date] = Field(default=None, description="生日")
    hobbies: Optional[str] = Field(default=None, description="兴趣爱好")
    notes: Optional[str] = Field(default=None, description="备注")
    is_primary: bool = Field(description="是否为主要联系人")


class ContactListResponse(BaseModel):
    """联系人列表响应"""

    total: int = Field(description="总数")
    items: List[ContactResponse] = Field(description="联系人列表")


class SetPrimaryRequest(BaseModel):
    """设置主要联系人请求"""

    contact_id: int = Field(description="要设置为主要联系人的ID")
