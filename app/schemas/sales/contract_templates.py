# -*- coding: utf-8 -*-
"""
合同模板 Schema

定义合同模板和版本的请求/响应模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 合同模板版本 ====================


class ContractTemplateVersionBase(BaseModel):
    """合同模板版本基础模型"""

    version_no: str = Field(..., description="版本号")
    clause_sections: Optional[Dict[str, Any]] = Field(None, description="条款结构")
    clause_library: Optional[Dict[str, Any]] = Field(None, description="条款库引用")
    attachment_refs: Optional[List[str]] = Field(None, description="附件引用")
    approval_flow: Optional[Dict[str, Any]] = Field(None, description="审批流配置")
    release_notes: Optional[str] = Field(None, description="版本说明")


class ContractTemplateVersionCreate(ContractTemplateVersionBase):
    """创建合同模板版本"""

    pass


class ContractTemplateVersionResponse(ContractTemplateVersionBase):
    """合同模板版本响应"""

    id: int
    template_id: int
    status: str = Field("DRAFT", description="状态: DRAFT/PUBLISHED/ARCHIVED")
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    published_by: Optional[int] = None
    publisher_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 合同模板 ====================


class ContractTemplateBase(BaseModel):
    """合同模板基础模型"""

    template_code: str = Field(..., max_length=50, description="模板编码")
    template_name: str = Field(..., max_length=200, description="模板名称")
    contract_type: Optional[str] = Field(None, max_length=50, description="合同类型")
    description: Optional[str] = Field(None, description="描述")
    visibility_scope: str = Field("TEAM", description="可见范围: PERSONAL/TEAM/DEPARTMENT/COMPANY")
    is_default: bool = Field(False, description="是否默认模板")


class ContractTemplateCreate(ContractTemplateBase):
    """创建合同模板"""

    initial_version: Optional[ContractTemplateVersionCreate] = Field(
        None, description="初始版本（可选）"
    )


class ContractTemplateUpdate(BaseModel):
    """更新合同模板"""

    template_name: Optional[str] = Field(None, max_length=200, description="模板名称")
    contract_type: Optional[str] = Field(None, max_length=50, description="合同类型")
    description: Optional[str] = Field(None, description="描述")
    visibility_scope: Optional[str] = Field(None, description="可见范围")
    is_default: Optional[bool] = Field(None, description="是否默认模板")
    status: Optional[str] = Field(None, description="状态")


class ContractTemplateResponse(ContractTemplateBase):
    """合同模板响应"""

    id: int
    status: str = Field("DRAFT", description="状态: DRAFT/ACTIVE/ARCHIVED")
    current_version_id: Optional[int] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    current_version: Optional[ContractTemplateVersionResponse] = None
    version_count: int = Field(0, description="版本数量")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 合同模板应用 ====================


class ContractTemplateApplyRequest(BaseModel):
    """应用合同模板请求"""

    template_id: int = Field(..., description="模板ID")
    version_id: Optional[int] = Field(None, description="版本ID（不指定则使用当前版本）")
    contract_id: Optional[int] = Field(None, description="目标合同ID（如已有合同）")
    opportunity_id: Optional[int] = Field(None, description="商机ID（创建新合同时）")
    customizations: Optional[Dict[str, Any]] = Field(None, description="自定义参数")


class ContractTemplateApplyResponse(BaseModel):
    """应用合同模板响应"""

    success: bool = Field(..., description="是否成功")
    contract_id: Optional[int] = Field(None, description="合同ID")
    contract_code: Optional[str] = Field(None, description="合同编码")
    template_id: int = Field(..., description="模板ID")
    version_id: int = Field(..., description="使用的版本ID")
    applied_sections: Optional[List[str]] = Field(None, description="已应用的条款段落")
    message: Optional[str] = Field(None, description="消息")


# ==================== 版本比较 ====================


class VersionDiffItem(BaseModel):
    """版本差异项"""

    section: str = Field(..., description="段落标识")
    field: str = Field(..., description="字段名")
    old_value: Optional[Any] = Field(None, description="旧值")
    new_value: Optional[Any] = Field(None, description="新值")
    change_type: str = Field(..., description="变更类型: ADD/MODIFY/DELETE")


class ContractTemplateVersionDiffResponse(BaseModel):
    """版本差异响应"""

    template_id: int
    from_version_id: int
    from_version_no: str
    to_version_id: int
    to_version_no: str
    diff_items: List[VersionDiffItem] = Field(default_factory=list)
    summary: str = Field("", description="差异摘要")


# ==================== 版本历史 ====================


class VersionHistoryItem(BaseModel):
    """版本历史项"""

    version_id: int
    version_no: str
    status: str
    release_notes: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ContractTemplateHistoryResponse(BaseModel):
    """模板版本历史响应"""

    template_id: int
    template_code: str
    template_name: str
    current_version_id: Optional[int] = None
    versions: List[VersionHistoryItem] = Field(default_factory=list)
