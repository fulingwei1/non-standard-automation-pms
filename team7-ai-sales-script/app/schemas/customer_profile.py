from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CustomerProfileAnalysisRequest(BaseModel):
    customer_id: int = Field(..., description="客户ID")
    presale_ticket_id: Optional[int] = Field(None, description="售前工单ID")
    communication_notes: str = Field(..., description="沟通记录文本")


class CustomerProfileResponse(BaseModel):
    id: int
    customer_id: int
    presale_ticket_id: Optional[int]
    customer_type: str
    focus_points: Optional[List[str]]
    decision_style: str
    communication_notes: Optional[str]
    ai_analysis: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True
