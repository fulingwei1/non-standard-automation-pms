# -*- coding: utf-8 -*-
"""
绩效管理 Schema
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema, PaginatedResponse


# ==================== 个人绩效 ====================

class PersonalPerformanceResponse(BaseModel):
    """个人绩效响应"""
    user_id: int
    user_name: str
    period_id: int
    period_name: str
    period_type: str
    start_date: date
    end_date: date
    total_score: Decimal
    level: str
    rank: Optional[int] = None
    indicators: List[Dict[str, Any]] = Field(default=[], description="指标明细")
    project_contributions: List[Dict[str, Any]] = Field(default=[], description="项目贡献")


class PerformanceTrendResponse(BaseModel):
    """绩效趋势分析响应"""
    user_id: int
    user_name: str
    periods: List[Dict[str, Any]] = Field(description="各期绩效数据")
    trend_direction: str = Field(description="趋势方向：UP/DOWN/STABLE")
    avg_score: Decimal
    max_score: Decimal
    min_score: Decimal


# ==================== 团队/部门绩效 ====================

class TeamPerformanceResponse(BaseModel):
    """团队绩效汇总响应"""
    team_id: int
    team_name: str
    period_id: int
    period_name: str
    member_count: int
    avg_score: Decimal
    max_score: Decimal
    min_score: Decimal
    level_distribution: Dict[str, int] = Field(description="等级分布")
    members: List[Dict[str, Any]] = Field(description="成员绩效列表")


class PerformanceResultResponse(PersonalPerformanceResponse):
    """兼容历史命名的个人绩效响应"""
    pass

class DepartmentPerformanceResponse(BaseModel):
    """部门绩效汇总响应"""
    department_id: int
    department_name: str
    period_id: int
    period_name: str
    member_count: int
    avg_score: Decimal
    level_distribution: Dict[str, int]
    teams: List[Dict[str, Any]] = Field(description="团队绩效列表")


class PerformanceRankingResponse(BaseModel):
    """绩效排行榜响应"""
    ranking_type: str = Field(description="排行榜类型：TEAM/DEPARTMENT/COMPANY")
    period_id: int
    period_name: str
    rankings: List[Dict[str, Any]] = Field(description="排名列表")


# ==================== 项目绩效 ====================

class ProjectPerformanceResponse(BaseModel):
    """项目成员绩效响应"""
    project_id: int
    project_name: str
    period_id: int
    period_name: str
    member_count: int
    total_contribution_score: Decimal
    members: List[Dict[str, Any]] = Field(description="成员贡献列表")


class ProjectProgressReportResponse(BaseModel):
    """项目进展报告响应"""
    project_id: int
    project_name: str
    report_type: str = Field(description="报告类型：WEEKLY/MONTHLY")
    report_date: date
    progress_summary: Dict[str, Any]
    member_contributions: List[Dict[str, Any]]
    key_achievements: List[str]
    risks_and_issues: List[str]


class PerformanceCompareResponse(BaseModel):
    """绩效对比响应"""
    user_ids: List[int]
    period_id: int
    period_name: str
    comparison_data: List[Dict[str, Any]] = Field(description="对比数据")
