# -*- coding: utf-8 -*-
"""
售前集成数据模式
用于售前评估系统与项目管理系统的数据对接
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== 五维评估数据 ====================

class DimensionScore(BaseModel):
    """五维评估分数"""
    requirement_maturity: int = Field(..., ge=0, le=100, description="需求成熟度")
    technical_feasibility: int = Field(..., ge=0, le=100, description="技术可行性")
    business_feasibility: int = Field(..., ge=0, le=100, description="商务可行性")
    delivery_risk: int = Field(..., ge=0, le=100, description="交付风险(越高风险越低)")
    customer_relationship: int = Field(..., ge=0, le=100, description="客户关系")

    @property
    def total_score(self) -> float:
        """计算总分（加权平均）"""
        weights = {
            'requirement_maturity': 0.20,
            'technical_feasibility': 0.25,
            'business_feasibility': 0.20,
            'delivery_risk': 0.15,
            'customer_relationship': 0.20
        }
        return (
            self.requirement_maturity * weights['requirement_maturity'] +
            self.technical_feasibility * weights['technical_feasibility'] +
            self.business_feasibility * weights['business_feasibility'] +
            self.delivery_risk * weights['delivery_risk'] +
            self.customer_relationship * weights['customer_relationship']
        )


class VetoRule(BaseModel):
    """一票否决规则"""
    rule_id: str
    rule_name: str
    is_triggered: bool = False
    description: Optional[str] = None


# ==================== 线索转项目请求 ====================

class LeadConversionRequest(BaseModel):
    """销售线索转项目请求（从presales-system回调）"""
    lead_id: str = Field(..., description="线索编号，如 XS2501001")
    lead_name: str = Field(..., description="线索名称/项目名称")

    # 客户信息
    customer_name: str = Field(..., description="客户名称")
    customer_industry: Optional[str] = Field(None, description="客户行业")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_phone: Optional[str] = Field(None, description="联系电话")

    # 销售信息
    salesperson_id: int = Field(..., description="销售人员ID")
    salesperson_name: str = Field(..., description="销售人员姓名")

    # 评估信息
    decision: str = Field(..., description="评估决策: approved/rejected/deferred")
    evaluation_score: float = Field(..., ge=0, le=100, description="评估总分")
    dimension_scores: DimensionScore = Field(..., description="五维评估分数")
    veto_rules: Optional[List[VetoRule]] = Field(None, description="一票否决规则")
    evaluation_comment: Optional[str] = Field(None, description="评估意见")
    evaluator_id: Optional[int] = Field(None, description="评估人ID")
    evaluator_name: Optional[str] = Field(None, description="评估人姓名")
    evaluation_time: Optional[datetime] = Field(None, description="评估时间")

    # 项目预估信息
    estimated_amount: Optional[Decimal] = Field(None, description="预估金额")
    expected_contract_date: Optional[date] = Field(None, description="预计签约日期")
    expected_delivery_date: Optional[date] = Field(None, description="预计交付日期")
    machine_count: int = Field(1, ge=1, description="预计设备数量")

    # 技术需求摘要
    requirement_summary: Optional[str] = Field(None, description="需求摘要")
    technical_challenges: Optional[List[str]] = Field(None, description="技术难点")

    # 预测中标率
    predicted_win_rate: Optional[float] = Field(None, ge=0, le=1, description="预测中标率")

    class Config:
        from_attributes = True


class LeadConversionResponse(BaseModel):
    """线索转项目响应"""
    success: bool
    project_id: Optional[int] = None
    project_code: Optional[str] = Field(None, description="项目编号，如 PJ2501001")
    lead_id: str
    message: str


# ==================== 中标预测相关 ====================

class WinRatePredictionRequest(BaseModel):
    """中标率预测请求"""
    lead_id: Optional[str] = None
    dimension_scores: DimensionScore
    salesperson_id: int
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    estimated_amount: Optional[Decimal] = None
    competitor_count: Optional[int] = Field(None, description="竞争对手数量")
    is_repeat_customer: bool = Field(False, description="是否老客户")


class WinRatePredictionResponse(BaseModel):
    """中标率预测响应"""
    predicted_win_rate: float = Field(..., ge=0, le=1, description="预测中标率(0-1)")
    probability_level: str = Field(..., description="概率等级: VERY_HIGH/HIGH/MEDIUM/LOW/VERY_LOW")
    confidence: float = Field(..., ge=0, le=1, description="预测置信度")

    # 影响因素分析
    factors: Dict[str, Any] = Field(default_factory=dict, description="影响因素")
    recommendations: List[str] = Field(default_factory=list, description="提升中标率建议")

    # 参考数据
    similar_leads_count: int = Field(0, description="相似线索数量")
    similar_leads_win_rate: Optional[float] = Field(None, description="相似线索历史中标率")


# ==================== 资源投入分析 ====================

class ResourceInvestmentSummary(BaseModel):
    """资源投入汇总"""
    lead_id: str
    lead_name: Optional[str] = None

    # 工时投入
    total_hours: float = Field(0, description="总投入工时")
    engineer_hours: float = Field(0, description="工程师工时")
    presales_hours: float = Field(0, description="售前工时")
    design_hours: float = Field(0, description="方案设计工时")

    # 人员统计
    engineer_count: int = Field(0, description="参与工程师数")
    engineers: List[Dict[str, Any]] = Field(default_factory=list, description="工程师详情")

    # 成本估算
    estimated_cost: Decimal = Field(Decimal('0'), description="估算成本")
    hourly_rate: Decimal = Field(Decimal('300'), description="时薪标准")

    # 时间分布
    investment_by_stage: Dict[str, float] = Field(default_factory=dict, description="各阶段投入")
    investment_by_month: Dict[str, float] = Field(default_factory=dict, description="各月投入")


class ResourceWasteAnalysis(BaseModel):
    """资源浪费分析"""
    analysis_period: str = Field(..., description="分析周期，如 2025-01")

    # 整体统计
    total_leads: int = Field(0, description="总线索数")
    won_leads: int = Field(0, description="中标数")
    lost_leads: int = Field(0, description="丢标数")
    abandoned_leads: int = Field(0, description="放弃数")
    pending_leads: int = Field(0, description="进行中数")

    # 中标率
    overall_win_rate: float = Field(0, description="整体中标率")

    # 资源浪费
    total_investment_hours: float = Field(0, description="总投入工时")
    wasted_hours: float = Field(0, description="浪费工时（失败线索）")
    wasted_cost: Decimal = Field(Decimal('0'), description="浪费成本")
    waste_rate: float = Field(0, description="浪费率")

    # 失败原因分布
    loss_reasons: Dict[str, int] = Field(default_factory=dict, description="丢标原因分布")


# ==================== 销售人员绩效分析 ====================

class SalespersonPerformance(BaseModel):
    """销售人员绩效"""
    salesperson_id: int
    salesperson_name: str
    department: Optional[str] = None

    # 线索统计
    total_leads: int = Field(0, description="总线索数")
    won_leads: int = Field(0, description="中标数")
    lost_leads: int = Field(0, description="丢标数")
    win_rate: float = Field(0, description="中标率")

    # 金额统计
    total_estimated_amount: Decimal = Field(Decimal('0'), description="总预估金额")
    won_amount: Decimal = Field(Decimal('0'), description="中标金额")

    # 资源效率
    total_resource_hours: float = Field(0, description="消耗资源工时")
    wasted_hours: float = Field(0, description="浪费工时")
    resource_efficiency: float = Field(0, description="资源效率（中标金额/消耗工时）")

    # 主要丢标原因
    top_loss_reasons: List[Dict[str, Any]] = Field(default_factory=list, description="主要丢标原因")

    # 趋势（近6个月）
    monthly_trend: List[Dict[str, Any]] = Field(default_factory=list, description="月度趋势")


class SalespersonRanking(BaseModel):
    """销售人员排行榜"""
    ranking_type: str = Field(..., description="排行类型: win_rate/efficiency/amount")
    period: str = Field(..., description="统计周期")
    rankings: List[SalespersonPerformance] = Field(default_factory=list)


# ==================== 失败案例分析 ====================

class FailureCaseAnalysis(BaseModel):
    """失败案例分析"""
    lead_id: str
    lead_name: str
    customer_name: str
    salesperson_name: str

    # 失败信息
    loss_reason: str
    loss_reason_detail: Optional[str] = None
    competitor_who_won: Optional[str] = None

    # 投入分析
    total_investment_hours: float
    investment_cost: Decimal

    # 评估分数回顾
    original_scores: Optional[DimensionScore] = None
    predicted_win_rate: Optional[float] = None

    # 教训总结
    lessons_learned: Optional[str] = None
    early_warning_signals: Optional[List[str]] = None


class FailurePatternAnalysis(BaseModel):
    """失败模式分析"""
    analysis_period: str

    # 模式统计
    patterns: List[Dict[str, Any]] = Field(default_factory=list, description="失败模式")

    # 高风险特征
    high_risk_indicators: List[str] = Field(default_factory=list, description="高风险指标")

    # 建议
    recommendations: List[str] = Field(default_factory=list, description="改进建议")


# ==================== 仪表板数据 ====================

class PresalesDashboardData(BaseModel):
    """售前分析仪表板数据"""
    # 概览指标
    total_leads_ytd: int = Field(0, description="年度总线索数")
    won_leads_ytd: int = Field(0, description="年度中标数")
    overall_win_rate: float = Field(0, description="整体中标率")
    avg_investment_per_lead: float = Field(0, description="平均每线索投入工时")

    # 资源浪费
    total_wasted_hours: float = Field(0, description="总浪费工时")
    total_wasted_cost: Decimal = Field(Decimal('0'), description="总浪费成本")
    waste_rate: float = Field(0, description="浪费率")

    # 近期趋势
    monthly_stats: List[Dict[str, Any]] = Field(default_factory=list, description="月度统计")

    # 销售排行
    top_performers: List[Dict[str, Any]] = Field(default_factory=list, description="绩优销售")
    bottom_performers: List[Dict[str, Any]] = Field(default_factory=list, description="待改进销售")

    # 失败原因分布
    loss_reason_distribution: Dict[str, int] = Field(default_factory=dict, description="丢标原因分布")

    # 预警信息
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="预警信息")
