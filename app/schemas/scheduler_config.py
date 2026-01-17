# -*- coding: utf-8 -*-
"""
定时服务配置管理 Schema
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class SchedulerTaskConfigBase(BaseModel):
    """定时任务配置基础Schema"""
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    module: str = Field(..., description="模块路径")
    callable_name: str = Field(..., description="函数名")
    owner: Optional[str] = Field(None, description="负责人")
    category: Optional[str] = Field(None, description="分类")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: bool = Field(True, description="是否启用")
    cron_config: Dict[str, Any] = Field(..., description="Cron配置")
    dependencies_tables: Optional[list] = Field(None, description="依赖的数据库表列表")
    risk_level: Optional[str] = Field(None, description="风险级别")
    sla_config: Optional[Dict[str, Any]] = Field(None, description="SLA配置")


class SchedulerTaskConfigCreate(SchedulerTaskConfigBase):
    """创建定时任务配置"""
    pass


class SchedulerTaskConfigUpdate(BaseModel):
    """更新定时任务配置"""
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    cron_config: Optional[Dict[str, Any]] = Field(None, description="Cron配置")

    @validator('cron_config')
    def validate_cron_config(cls, v):
        """验证Cron配置格式"""
        if v is None:
            return v

        # 验证Cron配置字段
        valid_fields = {'year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second'}
        for key in v.keys():
            if key not in valid_fields:
                raise ValueError(f"无效的Cron字段: {key}")

        return v


class SchedulerTaskConfigResponse(SchedulerTaskConfigBase):
    """定时任务配置响应"""
    id: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchedulerTaskConfigListResponse(BaseModel):
    """定时任务配置列表响应"""
    total: int
    items: list[SchedulerTaskConfigResponse]


class SchedulerTaskConfigSyncRequest(BaseModel):
    """同步任务配置请求（从scheduler_config.py同步到数据库）"""
    force: bool = Field(False, description="是否强制同步（覆盖已有配置）")
