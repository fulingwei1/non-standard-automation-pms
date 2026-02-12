# -*- coding: utf-8 -*-
"""
dimension_config Schemas

包含dimension_config相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 五维配置 Schemas ====================

class DimensionConfigBase(BaseModel):
    """五维权重配置基础"""
    job_type: str = Field(..., description="岗位类型")
    job_level: Optional[str] = Field(None, description="职级")
    department_id: Optional[int] = Field(None, description="部门ID（为空表示全局配置）")
    technical_weight: int = Field(30, ge=0, le=100, description="技术能力权重")
    execution_weight: int = Field(25, ge=0, le=100, description="项目执行权重")
    cost_quality_weight: int = Field(20, ge=0, le=100, description="成本质量权重")
    knowledge_weight: int = Field(15, ge=0, le=100, description="知识沉淀权重")
    collaboration_weight: int = Field(10, ge=0, le=100, description="团队协作权重")
    effective_date: date = Field(..., description="生效日期")
    config_name: Optional[str] = Field(None, description="配置名称")
    description: Optional[str] = Field(None, description="描述")


class DimensionConfigCreate(DimensionConfigBase):
    """创建五维配置"""
    pass


class DimensionConfigUpdate(BaseModel):
    """更新五维配置"""
    technical_weight: Optional[int] = Field(None, ge=0, le=100)
    execution_weight: Optional[int] = Field(None, ge=0, le=100)
    cost_quality_weight: Optional[int] = Field(None, ge=0, le=100)
    knowledge_weight: Optional[int] = Field(None, ge=0, le=100)
    collaboration_weight: Optional[int] = Field(None, ge=0, le=100)
    expired_date: Optional[date] = None
    description: Optional[str] = None


class DimensionConfigResponse(DimensionConfigBase):
    """五维配置响应"""
    id: int
    is_global: bool = Field(..., description="是否全局配置")
    expired_date: Optional[date] = None
    operator_id: Optional[int] = None
    approval_status: Optional[str] = Field(None, description="审批状态")
    affected_count: Optional[int] = Field(None, description="受影响人数")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


