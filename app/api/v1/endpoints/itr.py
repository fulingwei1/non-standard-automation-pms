# -*- coding: utf-8 -*-
"""
ITR 流程 API endpoints
提供端到端流程视图
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.itr_analytics_service import (
    analyze_resolution_time,
    analyze_satisfaction_trend,
    analyze_sla_performance,
    identify_bottlenecks,
)
from app.services.itr_service import (
    get_issue_related_data,
    get_itr_dashboard_data,
    get_ticket_timeline,
)

router = APIRouter()


# ==================== 写操作 API ====================

@router.post("/tickets", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    customer_id: int,
    problem_desc: str,
    problem_type: str = "GENERAL",
    urgency: str = "NORMAL",
    reported_by: str = "admin",
    assigned_to_id: Optional[int] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建售后服务工单
    
    - **project_id**: 项目 ID
    - **customer_id**: 客户 ID
    - **problem_desc**: 问题描述
    - **problem_type**: 问题类型（GENERAL/QUALITY/DELIVERY/OTHER）
    - **urgency**: 紧急程度（NORMAL/HIGH/CRITICAL）
    - **reported_by**: 报告人
    - **assigned_to_id**: 处理人 ID（可选）
    """
    from app.models.project import Project, Customer
    from app.models.service.ticket import ServiceTicket
    
    # 验证项目和客户
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    # 生成工单号
    now = datetime.now()
    ticket_no = f"ITR-{now.strftime('%Y%m%d%H%M%S')}-{project_id}"
    
    # 创建工单（使用模型实际字段）
    ticket = ServiceTicket(
        ticket_no=ticket_no,
        project_id=project_id,
        customer_id=customer_id,
        problem_type=problem_type,
        problem_desc=problem_desc,
        urgency=urgency,
        reported_by=reported_by,
        reported_time=now,
        status="PENDING",
    )
    
    if assigned_to_id:
        ticket.assigned_to_id = assigned_to_id
        ticket.assigned_time = now
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return ResponseModel(
        code=201,
        message="工单创建成功",
        data={"id": ticket.id, "ticket_no": ticket_no}
    )


@router.put("/tickets/{ticket_id}", response_model=ResponseModel)
def update_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    problem_desc: Optional[str] = None,
    urgency: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工单信息
    
    - **ticket_id**: 工单 ID
    - **problem_desc**: 问题描述（可选）
    - **urgency**: 紧急程度（可选）
    - **status**: 状态（可选）
    - **assigned_to_id**: 处理人 ID（可选）
    """
    from app.models.service.ticket import ServiceTicket
    
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 更新字段（使用模型实际字段名）
    if problem_desc is not None:
        ticket.problem_desc = problem_desc
    if urgency is not None:
        ticket.urgency = urgency
    if status is not None:
        ticket.status = status
    if assigned_to_id is not None:
        ticket.assigned_to_id = assigned_to_id
        ticket.assigned_time = datetime.now()
    
    db.commit()
    db.refresh(ticket)
    
    return ResponseModel(
        code=200,
        message="工单更新成功",
        data={"id": ticket.id, "ticket_no": ticket.ticket_no, "status": ticket.status}
    )


@router.put("/tickets/{ticket_id}/close", response_model=ResponseModel)
def close_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    solution: str,
    root_cause: Optional[str] = None,
    preventive_action: Optional[str] = None,
    satisfaction: Optional[int] = None,
    feedback: Optional[str] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭工单
    
    - **ticket_id**: 工单 ID
    - **solution**: 解决方案（必填）
    - **root_cause**: 根本原因（可选）
    - **preventive_action**: 预防措施（可选）
    - **satisfaction**: 满意度 1-5（可选）
    - **feedback**: 客户反馈（可选）
    """
    from app.models.service.ticket import ServiceTicket
    
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if ticket.status == "CLOSED":
        raise HTTPException(status_code=400, detail="工单已关闭，不能重复关闭")
    
    # 更新工单（使用模型实际字段名）
    ticket.status = "CLOSED"
    ticket.solution = solution
    ticket.root_cause = root_cause
    ticket.preventive_action = preventive_action
    ticket.satisfaction = satisfaction
    ticket.feedback = feedback
    ticket.resolved_time = datetime.now()
    
    db.commit()
    db.refresh(ticket)
    
    return ResponseModel(
        code=200,
        message="工单关闭成功",
        data={
            "id": ticket.id,
            "ticket_no": ticket.ticket_no,
            "status": ticket.status,
            "resolved_time": ticket.resolved_time.isoformat() if ticket.resolved_time else None
        }
    )


# ==================== 查询 API ====================

@router.get(
    "/tickets/{ticket_id}/timeline", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_ticket_timeline_api(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单完整时间线
    整合工单、问题、验收、SLA 监控等数据
    """
    timeline_data = get_ticket_timeline(db, ticket_id)

    if not timeline_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    return ResponseModel(code=200, message="获取成功", data=timeline_data)


@router.get(
    "/issues/{issue_id}/related", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="问题不存在")

    return ResponseModel(code=200, message="获取成功", data=related_data)


@router.get("/dashboard", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_itr_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目 ID 筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取 ITR 流程看板数据
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    dashboard_data = get_itr_dashboard_data(db, project_id, start_dt, end_dt)

    return ResponseModel(code=200, message="获取成功", data=dashboard_data)


@router.get("/analytics/efficiency", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_efficiency_analysis(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    project_id: Optional[int] = Query(None, description="项目 ID 筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取效率分析数据（平均响应时间、平均解决时间等）
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    efficiency_data = analyze_resolution_time(db, start_dt, end_dt, project_id)

    return ResponseModel(code=200, message="获取成功", data=efficiency_data)


@router.get(
    "/analytics/satisfaction", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_satisfaction_trend(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    project_id: Optional[int] = Query(None, description="项目 ID 筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度趋势数据
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    satisfaction_data = analyze_satisfaction_trend(db, start_dt, end_dt, project_id)

    return ResponseModel(code=200, message="获取成功", data=satisfaction_data)


@router.get(
    "/analytics/bottlenecks", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_bottlenecks(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    project_id: Optional[int] = Query(None, description="项目 ID 筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    识别瓶颈（响应超时、解决超时、满意度低等）
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    bottlenecks_data = identify_bottlenecks(db, start_dt, end_dt, project_id)

    return ResponseModel(code=200, message="获取成功", data=bottlenecks_data)


@router.get("/analytics/sla", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_sla_performance(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    project_id: Optional[int] = Query(None, description="项目 ID 筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取 SLA 达成率数据
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    sla_data = analyze_sla_performance(db, start_dt, end_dt, project_id)

    return ResponseModel(code=200, message="获取成功", data=sla_data)
