# -*- coding: utf-8 -*-
"""
工时分析与预测 API
提供6种分析接口和4种预测接口
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_permission
from app.models.user import User
from app.services.timesheet_analytics_service import TimesheetAnalyticsService
from app.services.timesheet_forecast_service import TimesheetForecastService
from app.schemas.timesheet_analytics import (
    TimesheetAnalyticsQuery,
    ProjectForecastRequest,
    CompletionForecastQuery,
    WorkloadAlertQuery,
    TimesheetTrendResponse,
    WorkloadHeatmapResponse,
    EfficiencyComparisonResponse,
    OvertimeStatisticsResponse,
    DepartmentComparisonResponse,
    ProjectDistributionResponse,
    ProjectForecastResponse,
    CompletionForecastResponse,
    WorkloadAlertResponse,
    GapAnalysisResponse
)

router = APIRouter()


# ==================== 工时分析 API ====================

@router.get("/trend", response_model=TimesheetTrendResponse, summary="工时趋势分析")
@require_permission("timesheet:read")
def get_timesheet_trend(
    period_type: str = Query(..., description="周期类型:DAILY/WEEKLY/MONTHLY/QUARTERLY/YEARLY"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    dimension: Optional[str] = Query(None, description="分析维度:USER/PROJECT/DEPARTMENT"),
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    project_ids: Optional[str] = Query(None, description="项目ID列表(逗号分隔)"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    工时趋势分析（支持多维度）
    
    支持的周期类型：
    - DAILY: 日度
    - WEEKLY: 周度
    - MONTHLY: 月度
    - QUARTERLY: 季度
    - YEARLY: 年度
    
    支持的分析维度：
    - USER: 按人员
    - PROJECT: 按项目
    - DEPARTMENT: 按部门
    """
    # 解析ID列表
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    project_id_list = [int(x) for x in project_ids.split(',')] if project_ids else None
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_trend(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        dimension=dimension,
        user_ids=user_id_list,
        project_ids=project_id_list,
        department_ids=department_id_list
    )


@router.get("/workload", response_model=WorkloadHeatmapResponse, summary="人员负荷热力图")
@require_permission("timesheet:read")
def get_workload_heatmap(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    人员负荷分析（工时饱和度、负荷热力图）
    
    返回：
    - 热力图数据（人员×日期）
    - 超负荷人员列表
    - 统计信息
    """
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_workload(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        user_ids=user_id_list,
        department_ids=department_id_list
    )


@router.get("/efficiency", response_model=EfficiencyComparisonResponse, summary="工时效率对比")
@require_permission("timesheet:read")
def get_efficiency_comparison(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    project_ids: Optional[str] = Query(None, description="项目ID列表(逗号分隔)"),
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    工时效率对比（计划vs实际）
    
    返回：
    - 计划工时与实际工时对比
    - 工时偏差分析
    - 效率率
    - 洞察建议
    """
    project_id_list = [int(x) for x in project_ids.split(',')] if project_ids else None
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_efficiency(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        project_ids=project_id_list,
        user_ids=user_id_list
    )


@router.get("/overtime", response_model=OvertimeStatisticsResponse, summary="加班统计分析")
@require_permission("timesheet:read")
def get_overtime_statistics(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    加班统计分析
    
    返回：
    - 总加班时长
    - 周末加班/节假日加班
    - 加班率
    - 人均加班
    - 加班趋势
    - TOP加班人员
    """
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_overtime(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        user_ids=user_id_list,
        department_ids=department_id_list
    )


@router.get("/department-comparison", response_model=DepartmentComparisonResponse, summary="部门工时对比")
@require_permission("timesheet:read")
def get_department_comparison(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    部门工时对比
    
    返回：
    - 各部门工时统计
    - 部门排名
    - 人均工时
    - 加班率对比
    - 可视化图表数据
    """
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_department_comparison(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        department_ids=department_id_list
    )


@router.get("/project-distribution", response_model=ProjectDistributionResponse, summary="项目工时分布")
@require_permission("timesheet:read")
def get_project_distribution(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    project_ids: Optional[str] = Query(None, description="项目ID列表(逗号分隔)"),
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    项目工时分布
    
    返回：
    - 项目工时占比
    - 饼图数据
    - 集中度指数
    - 项目详细信息
    """
    project_id_list = [int(x) for x in project_ids.split(',')] if project_ids else None
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    
    service = TimesheetAnalyticsService(db)
    return service.analyze_project_distribution(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        project_ids=project_id_list,
        user_ids=user_id_list
    )


# ==================== 工时预测 API ====================

@router.post("/forecast/project", response_model=ProjectForecastResponse, summary="预测项目工时")
@require_permission("timesheet:read")
def forecast_project_hours(
    request: ProjectForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预测项目需要工时
    
    支持3种预测方法：
    1. HISTORICAL_AVERAGE - 历史平均法（基于相似项目平均工时）
    2. LINEAR_REGRESSION - 线性回归（基于项目特征：团队规模、周期、复杂度）
    3. TREND_FORECAST - 趋势预测（基于当前工时消耗趋势）
    
    请求参数：
    - project_id: 项目ID（已存在项目）
    - project_name: 项目名称（新项目预测）
    - project_type: 项目类型
    - complexity: 复杂度（LOW/MEDIUM/HIGH）
    - team_size: 团队规模
    - duration_days: 计划周期（天）
    - forecast_method: 预测方法
    - similar_project_ids: 相似项目ID列表（可选，用于历史平均法）
    
    返回：
    - 预测工时（含最小值、最大值）
    - 置信度
    - 相似项目列表
    - 算法参数
    - 建议措施
    """
    service = TimesheetForecastService(db)
    return service.forecast_project_hours(
        project_id=request.project_id,
        project_name=request.project_name,
        project_type=request.project_type,
        complexity=request.complexity,
        team_size=request.team_size,
        duration_days=request.duration_days,
        forecast_method=request.forecast_method,
        similar_project_ids=request.similar_project_ids
    )


@router.get("/forecast/completion", response_model=CompletionForecastResponse, summary="预测完工时间")
@require_permission("timesheet:read")
def forecast_completion_time(
    project_id: int = Query(..., description="项目ID"),
    forecast_method: str = Query('TREND_FORECAST', description="预测方法"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预测项目完工时间
    
    基于：
    - 当前进度
    - 已消耗工时
    - 工时消耗速度（最近14天）
    
    返回：
    - 预测完工日期
    - 预测剩余天数
    - 剩余工时
    - 预测曲线
    - 风险因素
    """
    service = TimesheetForecastService(db)
    return service.forecast_completion(
        project_id=project_id,
        forecast_method=forecast_method
    )


@router.get("/forecast/workload-alert", response_model=List[WorkloadAlertResponse], summary="人员负荷预警")
@require_permission("timesheet:read")
def get_workload_alerts(
    user_ids: Optional[str] = Query(None, description="用户ID列表(逗号分隔)"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    alert_level: Optional[str] = Query(None, description="预警级别:LOW/MEDIUM/HIGH/CRITICAL"),
    forecast_days: int = Query(30, description="预测天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    人员工时饱和度预警
    
    预警级别：
    - CRITICAL: 严重超负荷（饱和度≥120%）
    - HIGH: 高负荷（饱和度≥100%）
    - MEDIUM: 中等负荷（饱和度≥85%）
    - LOW: 低负荷（饱和度<60%）
    
    返回：
    - 人员饱和度
    - 预警级别
    - 可用工时
    - 缺口工时
    - 建议措施
    """
    user_id_list = [int(x) for x in user_ids.split(',')] if user_ids else None
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    
    service = TimesheetForecastService(db)
    return service.forecast_workload_alert(
        user_ids=user_id_list,
        department_ids=department_id_list,
        alert_level=alert_level,
        forecast_days=forecast_days
    )


@router.get("/forecast/gap-analysis", response_model=GapAnalysisResponse, summary="工时缺口分析")
@require_permission("timesheet:read")
def get_gap_analysis(
    period_type: str = Query('MONTHLY', description="周期类型"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    department_ids: Optional[str] = Query(None, description="部门ID列表(逗号分隔)"),
    project_ids: Optional[str] = Query(None, description="项目ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    工时缺口分析
    
    分析：
    - 需求工时 vs 可用工时
    - 部门缺口
    - 项目缺口
    
    返回：
    - 总缺口工时
    - 缺口率
    - 部门缺口明细
    - 项目缺口明细
    - 建议措施
    - 可视化图表
    """
    department_id_list = [int(x) for x in department_ids.split(',')] if department_ids else None
    project_id_list = [int(x) for x in project_ids.split(',')] if project_ids else None
    
    service = TimesheetForecastService(db)
    return service.analyze_gap(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        department_ids=department_id_list,
        project_ids=project_id_list
    )
