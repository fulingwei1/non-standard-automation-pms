# -*- coding: utf-8 -*-
"""
方案版本 Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 请求模型 ====================


class SolutionVersionCreate(BaseModel):
    """创建方案版本请求"""

    model_config = ConfigDict(populate_by_name=True)

    # 方案内容
    generated_solution: Optional[Dict[str, Any]] = Field(None, description="生成的完整方案")
    architecture_diagram: Optional[str] = Field(None, description="系统架构图 Mermaid 代码")
    topology_diagram: Optional[str] = Field(None, description="设备拓扑图")
    signal_flow_diagram: Optional[str] = Field(None, description="信号流程图")
    bom_list: Optional[Dict[str, Any]] = Field(None, description="BOM清单")
    technical_parameters: Optional[Dict[str, Any]] = Field(None, description="技术参数表")
    process_flow: Optional[str] = Field(None, description="工艺流程说明")
    solution_description: Optional[str] = Field(None, description="方案描述")

    # 变更信息
    change_summary: Optional[str] = Field(None, description="变更摘要")
    change_reason: Optional[str] = Field(None, max_length=200, description="变更原因")

    # AI 元数据
    ai_model_used: Optional[str] = Field(None, description="使用的AI模型")
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1, description="置信度评分")
    quality_score: Optional[Decimal] = Field(None, ge=0, le=5, description="质量评分")


class SolutionVersionUpdate(BaseModel):
    """更新方案版本请求（仅 draft 状态可更新）"""

    generated_solution: Optional[Dict[str, Any]] = None
    architecture_diagram: Optional[str] = None
    topology_diagram: Optional[str] = None
    signal_flow_diagram: Optional[str] = None
    bom_list: Optional[Dict[str, Any]] = None
    technical_parameters: Optional[Dict[str, Any]] = None
    process_flow: Optional[str] = None
    solution_description: Optional[str] = None
    change_summary: Optional[str] = None


class ApprovalRequest(BaseModel):
    """审批请求"""

    action: str = Field(..., description="审批动作：approve / reject")
    comments: Optional[str] = Field(None, description="审批意见")


# ==================== 响应模型 ====================


class SolutionVersionResponse(BaseModel):
    """方案版本响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="版本ID")
    solution_id: int = Field(description="方案ID")
    version_no: str = Field(description="版本号")

    # 方案内容
    generated_solution: Optional[Dict[str, Any]] = Field(None, description="方案内容")
    architecture_diagram: Optional[str] = Field(None, description="架构图")
    bom_list: Optional[Dict[str, Any]] = Field(None, description="BOM清单")
    solution_description: Optional[str] = Field(None, description="方案描述")

    # 变更信息
    change_summary: Optional[str] = Field(None, description="变更摘要")
    change_reason: Optional[str] = Field(None, description="变更原因")
    parent_version_id: Optional[int] = Field(None, description="父版本ID")

    # 状态
    status: str = Field(description="状态：draft/pending_review/approved/rejected")
    approved_by: Optional[int] = Field(None, description="审批人ID")
    approved_at: Optional[datetime] = Field(None, description="审批时间")
    approval_comments: Optional[str] = Field(None, description="审批意见")

    # AI 元数据
    confidence_score: Optional[Decimal] = Field(None, description="置信度评分")
    quality_score: Optional[Decimal] = Field(None, description="质量评分")

    # 时间戳
    created_by: int = Field(description="创建人ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class SolutionVersionListResponse(BaseModel):
    """方案版本列表响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    solution_id: int
    version_no: str
    status: str
    change_summary: Optional[str] = None
    created_at: datetime
    created_by: int


class VersionCompareResponse(BaseModel):
    """版本对比响应"""

    version_1: Dict[str, Any] = Field(description="版本1信息")
    version_2: Dict[str, Any] = Field(description="版本2信息")
    differences: Dict[str, Any] = Field(description="差异详情")
    has_differences: bool = Field(description="是否有差异")


# ==================== 绑定验证模型 ====================


class BindingIssueResponse(BaseModel):
    """绑定问题响应"""

    level: str = Field(description="问题级别：error/warning/info")
    code: str = Field(description="问题代码")
    message: str = Field(description="问题描述")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class BindingValidationResponse(BaseModel):
    """绑定验证响应"""

    quote_version_id: int = Field(description="报价版本ID")
    status: str = Field(description="绑定状态：valid/outdated/invalid")
    issues: List[BindingIssueResponse] = Field(description="问题列表")
    validated_at: datetime = Field(description="验证时间")
    is_valid: bool = Field(description="是否有效")


class ImpactCheckResponse(BaseModel):
    """影响检查响应"""

    affected_items: List[Dict[str, Any]] = Field(description="受影响的实体列表")
    total_count: int = Field(description="受影响总数")


class CostSyncResponse(BaseModel):
    """成本同步响应"""

    quote_version_id: int = Field(description="报价版本ID")
    cost_total: Decimal = Field(description="同步后的成本总计")
    gross_margin: Optional[Decimal] = Field(None, description="重新计算的毛利率")
    binding_status: str = Field(description="绑定状态")
    synced_at: datetime = Field(description="同步时间")
