# -*- coding: utf-8 -*-
"""
summary Schemas

包含summary相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 绩效汇总 Schemas ====================

class EngineerDimensionScore(BaseModel):
    """工程师五维得分（或方案工程师六维得分）"""
    technical_score: Decimal = Field(..., description="技术能力得分")
    execution_score: Decimal = Field(..., description="项目执行得分")
    cost_quality_score: Decimal = Field(..., description="成本质量得分")
    knowledge_score: Decimal = Field(..., description="知识沉淀得分")
    collaboration_score: Decimal = Field(..., description="团队协作得分")
    solution_success_score: Optional[Decimal] = Field(None, description="方案成功率得分（仅方案工程师）")


class EngineerPerformanceSummary(BaseModel):
    """工程师绩效汇总"""
    engineer_id: int
    engineer_name: str
    job_type: str
    job_level: str
    department_name: Optional[str] = None
    period_id: int
    period_name: str

    # 得分
    total_score: Decimal
    level: str  # S/A/B/C/D
    dimension_scores: EngineerDimensionScore

    # 排名
    dept_rank: Optional[int] = None
    job_type_rank: Optional[int] = None
    company_rank: Optional[int] = None

    # 环比
    score_change: Optional[Decimal] = None
    rank_change: Optional[int] = None


class CompanySummaryResponse(BaseModel):
    """公司整体概况响应"""
    period_id: int
    period_name: str
    total_engineers: int

    # 按岗位统计
    by_job_type: Dict[str, Dict[str, Any]]

    # 等级分布
    level_distribution: Dict[str, int]

    # 平均分
    avg_score: Decimal
    max_score: Decimal
    min_score: Decimal

    # Top 工程师
    top_engineers: List[EngineerPerformanceSummary]


class RankingQueryParams(BaseModel):
    """排名查询参数"""
    period_id: Optional[int] = Field(None, description="考核周期ID")
    job_type: Optional[str] = Field(None, description="岗位类型")
    job_level: Optional[str] = Field(None, description="职级")
    department_id: Optional[int] = Field(None, description="部门ID")
    limit: int = Field(20, ge=1, le=100, description="返回数量")
    offset: int = Field(0, ge=0, description="偏移量")


class RankingResponse(BaseModel):
    """排名响应"""
    total: int
    items: List[EngineerPerformanceSummary]
    period_id: int
    period_name: str


class EngineerTrendResponse(BaseModel):
    """工程师趋势响应"""
    engineer_id: int
    engineer_name: str
    trends: List[Dict[str, Any]] = Field(..., description="历史趋势数据")


class EngineerComparisonResponse(BaseModel):
    """工程师对比响应"""
    engineer_id: int
    engineer_name: str
    job_type: str
    job_level: str

    # 个人得分
    scores: EngineerDimensionScore
    total_score: Decimal

    # 同岗位平均
    job_type_avg: EngineerDimensionScore
    job_type_avg_total: Decimal

    # 同级别平均
    job_level_avg: EngineerDimensionScore
    job_level_avg_total: Decimal


