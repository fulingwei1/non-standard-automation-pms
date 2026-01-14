# -*- coding: utf-8 -*-
"""
ITR流程 API endpoints
提供端到端流程视图
"""

from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

from app.services.itr_service import (
    get_ticket_timeline,
    get_issue_related_data,
    get_itr_dashboard_data
)
from app.services.itr_analytics_service import (
    analyze_resolution_time,
    analyze_satisfaction_trend,
    identify_bottlenecks,
    analyze_sla_performance
)

router = APIRouter()


@router.get("/tickets/{ticket_id}/timeline", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_ticket_timeline_api(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单完整时间线
    整合工单、问题、验收、SLA监控等数据
    """
    timeline_data = get_ticket_timeline(db, ticket_id)
    
    if not timeline_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在"
        )
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=timeline_data
    )


@router.get("/issues/{issue_id}/related", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_issue_related_data_api(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题关联数据（工单、验收单等）
    """
    related_data = get_issue_related_data(db, issue_id)
    
    if not related_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问题不存在"
        )
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=related_data
    )


@router.get("/dashboard", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_itr_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ITR流程看板数据
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，应为 YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，应为 YYYY-MM-DD"
            )
    
    dashboard_data = get_itr_dashboard_data(
        db,
        project_id=project_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=dashboard_data
    )


@router.get("/analytics/efficiency", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_itr_efficiency_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ITR流程效率分析
    包含：问题解决时间分析、流程瓶颈识别
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，应为 YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，应为 YYYY-MM-DD"
            )
    
    resolution_analysis = analyze_resolution_time(db, start_dt, end_dt, project_id)
    bottlenecks = identify_bottlenecks(db, start_dt, end_dt)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "resolution_time": resolution_analysis,
            "bottlenecks": bottlenecks,
        }
    )


@router.get("/analytics/satisfaction", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_satisfaction_trend(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户满意度趋势分析
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，应为 YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，应为 YYYY-MM-DD"
            )
    
    satisfaction_trend = analyze_satisfaction_trend(db, start_dt, end_dt, project_id)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=satisfaction_trend
    )


@router.get("/analytics/bottlenecks", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_bottlenecks_analysis(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取流程瓶颈识别
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，应为 YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，应为 YYYY-MM-DD"
            )
    
    bottlenecks = identify_bottlenecks(db, start_dt, end_dt)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=bottlenecks
    )


@router.get("/analytics/sla", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_sla_performance_analysis(
    *,
    db: Session = Depends(deps.get_db),
    policy_id: Optional[int] = Query(None, description="策略ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取SLA达成率分析
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，应为 YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，应为 YYYY-MM-DD"
            )
    
    sla_performance = analyze_sla_performance(db, start_dt, end_dt, policy_id)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data=sla_performance
    )
