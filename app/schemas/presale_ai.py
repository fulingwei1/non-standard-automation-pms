"""
售前AI系统集成 - Pydantic Schemas
Team 10: 售前AI系统集成与前端UI
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class AIUsageStatsBase(BaseModel):
    """AI使用统计基础schema"""
    user_id: int
    ai_function: str
    usage_count: int = 0
    success_count: int = 0
    avg_response_time: Optional[int] = None
    date: date


class AIUsageStatsCreate(AIUsageStatsBase):
    """创建AI使用统计"""
    pass


class AIUsageStatsUpdate(BaseModel):
    """更新AI使用统计"""
    usage_count: Optional[int] = None
    success_count: Optional[int] = None
    avg_response_time: Optional[int] = None


class AIUsageStatsResponse(AIUsageStatsBase):
    """AI使用统计响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AIFeedbackBase(BaseModel):
    """AI反馈基础schema"""
    ai_function: str
    presale_ticket_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5, description="评分1-5星")
    feedback_text: Optional[str] = None


class AIFeedbackCreate(AIFeedbackBase):
    """创建AI反馈"""
    pass


class AIFeedbackResponse(AIFeedbackBase):
    """AI反馈响应"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AIConfigBase(BaseModel):
    """AI配置基础schema"""
    ai_function: str
    enabled: bool = True
    model_name: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=8000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    config_json: Optional[Dict[str, Any]] = None


class AIConfigCreate(AIConfigBase):
    """创建AI配置"""
    pass


class AIConfigUpdate(BaseModel):
    """更新AI配置"""
    enabled: Optional[bool] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8000)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    config_json: Optional[Dict[str, Any]] = None


class AIConfigResponse(AIConfigBase):
    """AI配置响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AIWorkflowLogBase(BaseModel):
    """AI工作流日志基础schema"""
    presale_ticket_id: int
    workflow_step: str
    status: str = "pending"
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AIWorkflowLogCreate(AIWorkflowLogBase):
    """创建AI工作流日志"""
    pass


class AIWorkflowLogResponse(AIWorkflowLogBase):
    """AI工作流日志响应"""
    id: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AIAuditLogBase(BaseModel):
    """AI审计日志基础schema"""
    action: str
    ai_function: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AIAuditLogCreate(AIAuditLogBase):
    """创建AI审计日志"""
    user_id: int


class AIAuditLogResponse(AIAuditLogBase):
    """AI审计日志响应"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 业务逻辑相关 Schemas ============

class DashboardStatsResponse(BaseModel):
    """仪表盘统计响应"""
    total_usage: int
    total_success: int
    success_rate: float
    avg_response_time: float
    top_functions: List[Dict[str, Any]]
    usage_trend: List[Dict[str, Any]]
    user_stats: Dict[str, Any]


class WorkflowStartRequest(BaseModel):
    """启动工作流请求"""
    presale_ticket_id: int
    initial_data: Optional[Dict[str, Any]] = None
    auto_run: bool = True  # 是否自动运行所有步骤


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    presale_ticket_id: int
    current_step: str
    overall_status: str
    steps: List[AIWorkflowLogResponse]
    progress: float  # 0-100
    estimated_completion: Optional[datetime]


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    ticket_ids: List[int]
    ai_function: str
    options: Optional[Dict[str, Any]] = None


class BatchProcessResponse(BaseModel):
    """批量处理响应"""
    job_id: str
    total_count: int
    status: str
    started_at: datetime


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str  # healthy, degraded, unhealthy
    services: Dict[str, Dict[str, Any]]
    timestamp: datetime


class ExportReportRequest(BaseModel):
    """导出报告请求"""
    start_date: date
    end_date: date
    ai_functions: Optional[List[str]] = None
    user_ids: Optional[List[int]] = None
    format: str = "excel"  # excel, pdf, csv


class ExportReportResponse(BaseModel):
    """导出报告响应"""
    file_url: str
    file_name: str
    file_size: int
    generated_at: datetime


class AIUsageStatsQuery(BaseModel):
    """AI使用统计查询"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    ai_functions: Optional[List[str]] = None
    user_ids: Optional[List[int]] = None
    group_by: str = "date"  # date, function, user


class AIFeedbackQuery(BaseModel):
    """AI反馈查询"""
    ai_function: Optional[str] = None
    min_rating: Optional[int] = Field(None, ge=1, le=5)
    max_rating: Optional[int] = Field(None, ge=1, le=5)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
