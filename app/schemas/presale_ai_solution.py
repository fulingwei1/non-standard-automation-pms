"""
售前AI方案生成 - Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ==================== 请求模型 ====================

class TemplateMatchRequest(BaseModel):
    """模板匹配请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    requirement_analysis_id: Optional[int] = Field(None, description="需求分析ID")
    industry: Optional[str] = Field(None, description="行业")
    equipment_type: Optional[str] = Field(None, description="设备类型")
    keywords: Optional[str] = Field(None, description="关键词")
    top_k: int = Field(3, ge=1, le=10, description="返回TOP K个模板")


class SolutionGenerationRequest(BaseModel):
    """方案生成请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    requirement_analysis_id: Optional[int] = Field(None, description="需求分析ID")
    template_id: Optional[int] = Field(None, description="参考模板ID")
    requirements: Dict[str, Any] = Field(..., description="需求详情")
    generate_architecture: bool = Field(True, description="是否生成架构图")
    generate_bom: bool = Field(True, description="是否生成BOM")
    ai_model: Optional[str] = Field("gpt-4", description="AI模型选择")


class ArchitectureGenerationRequest(BaseModel):
    """架构图生成请求"""
    solution_id: Optional[int] = Field(None, description="方案ID")
    requirements: Dict[str, Any] = Field(..., description="需求详情")
    diagram_type: str = Field("architecture", description="图表类型: architecture/topology/signal_flow")
    format: str = Field("mermaid", description="输出格式: mermaid/plantuml")


class BOMGenerationRequest(BaseModel):
    """BOM生成请求"""
    solution_id: Optional[int] = Field(None, description="方案ID")
    equipment_list: List[Dict[str, Any]] = Field(..., description="设备清单")
    include_cost: bool = Field(True, description="是否包含成本估算")
    include_suppliers: bool = Field(True, description="是否推荐供应商")


class SolutionUpdateRequest(BaseModel):
    """方案更新请求"""
    generated_solution: Optional[Dict[str, Any]] = Field(None, description="方案内容")
    architecture_diagram: Optional[str] = Field(None, description="架构图")
    bom_list: Optional[Dict[str, Any]] = Field(None, description="BOM清单")
    solution_description: Optional[str] = Field(None, description="方案描述")
    status: Optional[str] = Field(None, description="状态")


class SolutionReviewRequest(BaseModel):
    """方案审核请求"""
    status: str = Field(..., description="审核状态: approved/rejected")
    review_comments: Optional[str] = Field(None, description="审核意见")


class PDFExportRequest(BaseModel):
    """PDF导出请求"""
    solution_id: int = Field(..., description="方案ID")
    include_diagrams: bool = Field(True, description="包含架构图")
    include_bom: bool = Field(True, description="包含BOM")
    template_style: str = Field("standard", description="模板样式")


# ==================== 响应模型 ====================

class TemplateMatchItem(BaseModel):
    """模板匹配项"""
    template_id: int
    template_name: str
    similarity_score: float = Field(..., ge=0, le=1, description="相似度评分")
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    usage_count: int = 0
    avg_quality_score: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class TemplateMatchResponse(BaseModel):
    """模板匹配响应"""
    matched_templates: List[TemplateMatchItem]
    total_templates: int
    search_time_ms: int


class BOMItem(BaseModel):
    """BOM项"""
    item_name: str = Field(..., description="项目名称")
    model: str = Field(..., description="型号")
    quantity: int = Field(..., description="数量")
    unit: str = Field(..., description="单位")
    unit_price: Optional[Decimal] = Field(None, description="单价")
    total_price: Optional[Decimal] = Field(None, description="总价")
    supplier: Optional[str] = Field(None, description="供应商")
    lead_time_days: Optional[int] = Field(None, description="交付周期(天)")
    notes: Optional[str] = Field(None, description="备注")


class SolutionResponse(BaseModel):
    """方案响应"""
    id: int
    presale_ticket_id: int
    requirement_analysis_id: Optional[int] = None
    matched_template_ids: Optional[List[int]] = None
    generated_solution: Optional[Dict[str, Any]] = None
    architecture_diagram: Optional[str] = None
    topology_diagram: Optional[str] = None
    signal_flow_diagram: Optional[str] = None
    bom_list: Optional[Dict[str, Any]] = None
    solution_description: Optional[str] = None
    technical_parameters: Optional[Dict[str, Any]] = None
    process_flow: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None
    estimated_cost: Optional[Decimal] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    ai_model_used: Optional[str] = None
    generation_time_seconds: Optional[Decimal] = None
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SolutionGenerationResponse(BaseModel):
    """方案生成响应"""
    solution: SolutionResponse
    generation_time_seconds: float
    ai_model_used: str
    tokens_used: int


class ArchitectureGenerationResponse(BaseModel):
    """架构图生成响应"""
    diagram_code: str = Field(..., description="Mermaid/PlantUML代码")
    diagram_type: str
    format: str
    preview_url: Optional[str] = Field(None, description="预览URL")


class BOMGenerationResponse(BaseModel):
    """BOM生成响应"""
    bom_items: List[BOMItem]
    total_cost: Optional[Decimal] = None
    item_count: int
    generation_time_seconds: float


# ==================== 模板相关模型 ====================

class SolutionTemplateCreate(BaseModel):
    """创建方案模板"""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    equipment_type: Optional[str] = Field(None, max_length=100)
    complexity_level: Optional[str] = Field(None, max_length=50)
    solution_content: Dict[str, Any]
    architecture_diagram: Optional[str] = None
    bom_template: Optional[Dict[str, Any]] = None
    technical_specs: Optional[Dict[str, Any]] = None
    equipment_list: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    keywords: Optional[str] = None
    typical_cost_range_min: Optional[Decimal] = None
    typical_cost_range_max: Optional[Decimal] = None


class SolutionTemplateUpdate(BaseModel):
    """更新方案模板"""
    name: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    complexity_level: Optional[str] = None
    solution_content: Optional[Dict[str, Any]] = None
    architecture_diagram: Optional[str] = None
    bom_template: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SolutionTemplateResponse(BaseModel):
    """方案模板响应"""
    id: int
    name: str
    code: Optional[str] = None
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    complexity_level: Optional[str] = None
    solution_content: Optional[Dict[str, Any]] = None
    architecture_diagram: Optional[str] = None
    bom_template: Optional[Dict[str, Any]] = None
    technical_specs: Optional[Dict[str, Any]] = None
    usage_count: int
    success_rate: Optional[Decimal] = None
    avg_quality_score: Optional[Decimal] = None
    typical_cost_range_min: Optional[Decimal] = None
    typical_cost_range_max: Optional[Decimal] = None
    tags: Optional[List[str]] = None
    is_active: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== 统计分析模型 ====================

class SolutionStatistics(BaseModel):
    """方案统计"""
    total_solutions: int
    solutions_by_status: Dict[str, int]
    avg_generation_time: float
    avg_quality_score: float
    total_cost_estimated: Decimal
    most_used_templates: List[Dict[str, Any]]
