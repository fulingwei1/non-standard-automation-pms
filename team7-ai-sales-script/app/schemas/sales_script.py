from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SalesScriptRequest(BaseModel):
    presale_ticket_id: int = Field(..., description="售前工单ID")
    scenario: str = Field(..., description="场景类型")
    customer_profile_id: Optional[int] = Field(None, description="客户画像ID")
    context: Optional[str] = Field(None, description="当前上下文")


class SalesScriptResponse(BaseModel):
    id: int
    presale_ticket_id: int
    scenario: str
    recommended_scripts: Optional[List[str]]
    response_strategy: Optional[str]
    success_case_references: Optional[List[Dict[str, Any]]]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ObjectionHandlingRequest(BaseModel):
    presale_ticket_id: int = Field(..., description="售前工单ID")
    objection_type: str = Field(..., description="异议类型")
    customer_profile_id: Optional[int] = Field(None, description="客户画像ID")
    context: Optional[str] = Field(None, description="详细异议内容")


class ObjectionHandlingResponse(BaseModel):
    id: int
    objection_type: str
    response_strategy: str
    recommended_scripts: Optional[List[str]]
    success_case_references: Optional[List[Dict[str, Any]]]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class SalesProgressRequest(BaseModel):
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_profile_id: Optional[int] = Field(None, description="客户画像ID")
    current_situation: str = Field(..., description="当前销售情况描述")


class SalesProgressResponse(BaseModel):
    current_stage: str
    next_actions: List[str]
    key_milestones: List[str]
    recommendations: str

    class Config:
        from_attributes = True


class ScriptFeedbackRequest(BaseModel):
    script_id: int = Field(..., description="话术记录ID")
    is_effective: bool = Field(..., description="是否有效")
    feedback_notes: Optional[str] = Field(None, description="反馈备注")


class ScriptTemplateRequest(BaseModel):
    scenario: str = Field(..., description="场景类型")
    customer_type: Optional[str] = Field(None, description="客户类型")
    script_content: str = Field(..., description="话术内容")
    tags: Optional[List[str]] = Field(None, description="标签")
    success_rate: Optional[float] = Field(None, description="成功率")
