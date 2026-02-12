# -*- coding: utf-8 -*-
"""
plc_program Schemas

包含plc_program相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== PLC程序 Schemas ====================

class PlcProgramVersionBase(BaseModel):
    """PLC程序版本基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    program_name: str = Field(..., max_length=200, description="程序名称")
    plc_brand: Optional[str] = Field(None, description="PLC品牌")
    plc_model: Optional[str] = Field(None, description="PLC型号")
    version: Optional[str] = Field(None, description="版本")


class PlcProgramVersionCreate(PlcProgramVersionBase):
    """创建PLC程序版本"""
    programmer_id: int = Field(..., description="程序员ID")


class PlcProgramVersionUpdate(BaseModel):
    """更新PLC程序版本（调试结果）"""
    first_debug_date: Optional[date] = None
    is_first_pass: Optional[bool] = None
    debug_issues: Optional[int] = None
    debug_hours: Optional[Decimal] = None
    remarks: Optional[str] = None


class PlcProgramVersionResponse(PlcProgramVersionBase):
    """PLC程序版本响应"""
    id: int
    program_code: Optional[str] = None
    programmer_id: int
    programmer_name: Optional[str] = None
    first_debug_date: Optional[date] = None
    is_first_pass: Optional[bool] = None
    debug_issues: int = 0
    debug_hours: Optional[Decimal] = None
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


