# -*- coding: utf-8 -*-
"""
绩效管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


# ==================== 新绩效系统 - 月度工作总结 ====================

class MonthlyWorkSummaryCreate(BaseModel):
    """创建月度工作总结"""
    period: str = Field(..., description="评价周期 (格式: YYYY-MM)", min_length=7, max_length=7)
    work_content: str = Field(..., description="本月工作内容", min_length=10)
    self_evaluation: str = Field(..., description="自我评价", min_length=10)
    highlights: Optional[str] = Field(None, description="工作亮点")
    problems: Optional[str] = Field(None, description="遇到的问题")
    next_month_plan: Optional[str] = Field(None, description="下月计划")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "2026-01",
                "work_content": "完成项目A的机械设计评审...",
                "self_evaluation": "本月工作饱和，按时完成任务...",
                "highlights": "提前完成关键里程碑",
                "problems": "部分供应商交期延误",
                "next_month_plan": "完成电气设计和采购"
            }
        }


class MonthlyWorkSummaryUpdate(BaseModel):
    """更新月度工作总结（草稿）"""
    work_content: Optional[str] = Field(None, description="本月工作内容")
    self_evaluation: Optional[str] = Field(None, description="自我评价")
    highlights: Optional[str] = Field(None, description="工作亮点")
    problems: Optional[str] = Field(None, description="遇到的问题")
    next_month_plan: Optional[str] = Field(None, description="下月计划")


class MonthlyWorkSummaryResponse(BaseModel):
    """月度工作总结响应"""
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    period: str
    work_content: str
    self_evaluation: str
    highlights: Optional[str] = None
    problems: Optional[str] = None
    next_month_plan: Optional[str] = None
    status: str
    submit_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MonthlyWorkSummaryListItem(BaseModel):
    """月度工作总结列表项"""
    id: int
    period: str
    status: str
    submit_date: Optional[datetime] = None
    evaluation_count: int = Field(default=0, description="已收到的评价数量")
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 新绩效系统 - 绩效评价 ====================

class PerformanceEvaluationRecordCreate(BaseModel):
    """创建绩效评价"""
    score: int = Field(..., ge=60, le=100, description="评分 (60-100)")
    comment: str = Field(..., min_length=10, description="评价意见")
    project_id: Optional[int] = Field(None, description="项目ID (项目经理评价时必填)")
    project_weight: Optional[int] = Field(None, ge=0, le=100, description="项目权重")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 92,
                "comment": "工作认真负责，按时完成任务，技术能力强...",
                "project_id": 123,
                "project_weight": 60
            }
        }


class PerformanceEvaluationRecordUpdate(BaseModel):
    """更新绩效评价（草稿）"""
    score: Optional[int] = Field(None, ge=60, le=100, description="评分 (60-100)")
    comment: Optional[str] = Field(None, description="评价意见")


class PerformanceEvaluationRecordResponse(BaseModel):
    """绩效评价记录响应"""
    id: int
    summary_id: int
    evaluator_id: int
    evaluator_name: Optional[str] = None
    evaluator_type: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    project_weight: Optional[int] = None
    score: int
    comment: str
    status: str
    evaluated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluationTaskItem(BaseModel):
    """待评价任务项"""
    task_id: int = Field(..., description="任务ID (即 summary_id)")
    employee_id: int
    employee_name: str
    employee_department: Optional[str] = None
    period: str
    evaluation_type: str = Field(..., description="评价类型: dept/project")
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    status: str
    deadline: Optional[date] = None
    submit_date: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 123,
                "employee_id": 10,
                "employee_name": "王工程师",
                "employee_department": "技术开发部",
                "period": "2026-01",
                "evaluation_type": "dept",
                "project_id": None,
                "project_name": None,
                "status": "SUBMITTED",
                "deadline": "2026-02-05",
                "submit_date": "2026-02-01T10:30:00"
            }
        }


class EvaluationTaskListResponse(BaseModel):
    """待评价任务列表响应"""
    total: int
    pending_count: int
    completed_count: int
    tasks: List[EvaluationTaskItem]


class EvaluationDetailResponse(BaseModel):
    """评价详情响应（包含工作总结）"""
    summary: MonthlyWorkSummaryResponse
    employee_info: Dict[str, Any]
    historical_performance: List[Dict[str, Any]] = Field(default=[], description="历史绩效参考")
    my_evaluation: Optional[PerformanceEvaluationRecordResponse] = None

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "id": 123,
                    "employee_id": 10,
                    "period": "2026-01",
                    "work_content": "...",
                    "self_evaluation": "...",
                    "status": "SUBMITTED"
                },
                "employee_info": {
                    "id": 10,
                    "name": "王工程师",
                    "department": "技术开发部",
                    "position": "工程师"
                },
                "historical_performance": [],
                "my_evaluation": None
            }
        }


# ==================== 新绩效系统 - 个人绩效查看 ====================

class MyPerformanceCurrentStatus(BaseModel):
    """当前评价状态"""
    period: str
    summary_status: str
    dept_evaluation: Dict[str, Any] = Field(description="部门经理评价状态")
    project_evaluations: List[Dict[str, Any]] = Field(default=[], description="项目经理评价状态")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "2026-01",
                "summary_status": "SUBMITTED",
                "dept_evaluation": {
                    "status": "PENDING",
                    "evaluator": "李经理",
                    "score": None
                },
                "project_evaluations": [
                    {
                        "project_name": "项目A",
                        "status": "COMPLETED",
                        "evaluator": "张经理",
                        "score": 92,
                        "weight": 60
                    }
                ]
            }
        }


class MyPerformanceResult(BaseModel):
    """我的绩效结果"""
    period: str
    final_score: Optional[float] = None
    level: Optional[str] = None
    rank: Optional[int] = None
    dept_score: Optional[int] = None
    project_score: Optional[float] = None
    score_breakdown: Dict[str, Any] = Field(default={}, description="得分构成")


class MyPerformanceHistoryItem(BaseModel):
    """历史绩效记录项"""
    period: str
    final_score: Optional[float] = None
    level: Optional[str] = None
    rank: Optional[int] = None
    dept_evaluation: Optional[Dict[str, Any]] = None
    project_evaluations: List[Dict[str, Any]] = Field(default=[])


class MyPerformanceResponse(BaseModel):
    """我的绩效响应"""
    current_status: MyPerformanceCurrentStatus
    latest_result: Optional[MyPerformanceResult] = None
    quarterly_trend: List[Dict[str, Any]] = Field(default=[], description="季度趋势")
    history: List[MyPerformanceHistoryItem] = Field(default=[], description="历史记录")


# ==================== 新绩效系统 - 权重配置 ====================

class EvaluationWeightConfigCreate(BaseModel):
    """创建权重配置"""
    dept_manager_weight: int = Field(..., ge=0, le=100, description="部门经理权重 (%)")
    project_manager_weight: int = Field(..., ge=0, le=100, description="项目经理权重 (%)")
    effective_date: date = Field(..., description="生效日期")
    reason: Optional[str] = Field(None, description="调整原因")

    class Config:
        json_schema_extra = {
            "example": {
                "dept_manager_weight": 60,
                "project_manager_weight": 40,
                "effective_date": "2026-02-01",
                "reason": "根据公司项目型组织调整"
            }
        }


class EvaluationWeightConfigResponse(BaseModel):
    """权重配置响应"""
    id: int
    dept_manager_weight: int
    project_manager_weight: int
    effective_date: date
    operator_id: int
    operator_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationWeightConfigListResponse(BaseModel):
    """权重配置列表响应"""
    current: EvaluationWeightConfigResponse
    history: List[EvaluationWeightConfigResponse] = Field(default=[])
