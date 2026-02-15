"""
AI需求理解Schema定义
用于API请求和响应的数据验证
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


# ========== 基础Schema ==========

class EquipmentItem(BaseModel):
    """设备清单项"""
    name: str = Field(..., description="设备名称")
    type: str = Field(..., description="设备类型")
    quantity: int = Field(1, ge=1, description="数量")
    specifications: Optional[Dict[str, Any]] = Field(None, description="规格要求")
    priority: str = Field("medium", description="优先级: high/medium/low")


class ProcessStep(BaseModel):
    """工艺流程步骤"""
    step_number: int = Field(..., ge=1, description="步骤序号")
    name: str = Field(..., description="步骤名称")
    description: str = Field(..., description="步骤描述")
    parameters: Optional[Dict[str, Any]] = Field(None, description="工艺参数")
    equipment_required: Optional[List[str]] = Field(None, description="所需设备")


class TechnicalParameter(BaseModel):
    """技术参数"""
    parameter_name: str = Field(..., description="参数名称")
    value: str = Field(..., description="参数值或范围")
    unit: Optional[str] = Field(None, description="单位")
    tolerance: Optional[str] = Field(None, description="公差")
    is_critical: bool = Field(False, description="是否关键参数")


class ClarificationQuestion(BaseModel):
    """澄清问题"""
    question_id: int = Field(..., ge=1, description="问题编号")
    category: str = Field(..., description="问题分类")
    question: str = Field(..., description="问题内容")
    importance: str = Field("medium", description="重要性: critical/high/medium/low")
    suggested_answer: Optional[str] = Field(None, description="建议回答")


class StructuredRequirement(BaseModel):
    """结构化需求"""
    project_type: str = Field(..., description="项目类型")
    industry: Optional[str] = Field(None, description="应用行业")
    core_objectives: List[str] = Field(..., description="核心目标")
    functional_requirements: List[str] = Field(..., description="功能性需求")
    non_functional_requirements: List[str] = Field(..., description="非功能性需求")
    constraints: Optional[List[str]] = Field(None, description="约束条件")
    assumptions: Optional[List[str]] = Field(None, description="假设条件")


class FeasibilityAnalysis(BaseModel):
    """技术可行性分析"""
    overall_feasibility: str = Field(..., description="总体可行性: high/medium/low/unknown")
    technical_risks: List[str] = Field(default_factory=list, description="技术风险")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="资源需求")
    estimated_complexity: str = Field(..., description="复杂度: simple/medium/complex/very_complex")
    development_challenges: List[str] = Field(default_factory=list, description="开发挑战")
    recommendations: List[str] = Field(default_factory=list, description="建议")


# ========== 请求Schema ==========

class RequirementAnalysisRequest(BaseModel):
    """需求分析请求"""
    presale_ticket_id: int = Field(..., ge=1, description="售前工单ID")
    raw_requirement: str = Field(..., min_length=10, description="原始需求描述")
    ai_model: Optional[str] = Field("gpt-4", description="使用的AI模型")
    analysis_depth: str = Field("standard", description="分析深度: quick/standard/deep")
    
    @validator('raw_requirement')
    def validate_requirement_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("需求描述至少10个字符")
        return v.strip()


class RequirementRefinementRequest(BaseModel):
    """需求精炼请求"""
    analysis_id: int = Field(..., ge=1, description="分析记录ID")
    additional_context: Optional[str] = Field(None, description="额外上下文")
    focus_areas: Optional[List[str]] = Field(None, description="重点关注领域")


class RequirementUpdateRequest(BaseModel):
    """更新结构化需求请求"""
    analysis_id: int = Field(..., ge=1, description="分析记录ID")
    structured_requirement: Optional[StructuredRequirement] = None
    equipment_list: Optional[List[EquipmentItem]] = None
    process_flow: Optional[List[ProcessStep]] = None
    technical_parameters: Optional[List[TechnicalParameter]] = None
    acceptance_criteria: Optional[List[str]] = None


# ========== 响应Schema ==========

class RequirementAnalysisResponse(BaseModel):
    """需求分析响应"""
    id: int
    presale_ticket_id: int
    raw_requirement: str
    structured_requirement: Optional[Dict[str, Any]]
    clarification_questions: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]
    feasibility_analysis: Optional[Dict[str, Any]]
    equipment_list: Optional[List[Dict[str, Any]]]
    process_flow: Optional[List[Dict[str, Any]]]
    technical_parameters: Optional[List[Dict[str, Any]]]
    acceptance_criteria: Optional[List[str]]
    ai_model_used: Optional[str]
    status: str
    is_refined: bool
    refinement_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ClarificationQuestionsResponse(BaseModel):
    """澄清问题响应"""
    analysis_id: int
    presale_ticket_id: int
    questions: List[ClarificationQuestion]
    total_count: int
    critical_count: int
    high_priority_count: int


class ConfidenceScoreResponse(BaseModel):
    """置信度评分响应"""
    analysis_id: int
    presale_ticket_id: int
    confidence_score: float
    score_breakdown: Dict[str, float]
    assessment: str
    recommendations: List[str]


class RequirementAnalysisSummary(BaseModel):
    """需求分析摘要"""
    total_analyses: int
    avg_confidence_score: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    most_common_equipment: List[str]
    most_common_challenges: List[str]
