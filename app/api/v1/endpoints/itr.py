# -*- coding: utf-8 -*-
"""
ITR流程 API endpoints
提供端到端流程视图
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.customer import Customer
from app.models.project import Project
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.service import (
    ServiceTicketClose,
    ServiceTicketCreate,
    ServiceTicketUpdate,
)
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


@router.post(
    "/tickets", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: ServiceTicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建服务工单
    - **project_id**: 项目 ID（主项目）
    - **customer_id**: 客户 ID
    - **problem_type**: 问题类型
    - **problem_desc**: 问题描述
    - **urgency**: 紧急程度
    - **reported_by**: 报告人
    - **reported_time**: 报告时间
    - **assignee_id**: 处理人 ID（可选）
    - **cc_user_ids**: 抄送人员 ID 列表（可选）
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == ticket_in.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在 (ID: {ticket_in.project_id})",
        )

    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == ticket_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"客户不存在 (ID: {ticket_in.customer_id})",
        )

    # 验证处理人存在（如果提供）
    assigned_to_name = None
    if ticket_in.assignee_id:
        assignee = db.query(User).filter(User.id == ticket_in.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"处理人不存在 (ID: {ticket_in.assignee_id})",
            )
        assigned_to_name = assignee.nickname or assignee.full_name

    # 生成工单号
    import uuid
    ticket_no = f"ITR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # 创建工单
    ticket = ServiceTicket(
        ticket_no=ticket_no,
        project_id=ticket_in.project_id,
        customer_id=ticket_in.customer_id,
        problem_type=ticket_in.problem_type,
        problem_desc=ticket_in.problem_desc,
        urgency=ticket_in.urgency,
        reported_by=ticket_in.reported_by,
        reported_time=ticket_in.reported_time,
        assigned_to_id=ticket_in.assignee_id,
        assigned_to_name=assigned_to_name,
        assigned_time=datetime.now() if ticket_in.assignee_id else None,
        status="PENDING",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 处理抄送人员
    if ticket_in.cc_user_ids:
        from app.models.service import ServiceTicketCcUser
        for user_id in ticket_in.cc_user_ids:
            cc_user = ServiceTicketCcUser(
                ticket_id=ticket.id,
                user_id=user_id,
            )
            db.add(cc_user)

    # 处理多项目关联
    if ticket_in.project_ids and len(ticket_in.project_ids) > 1:
        from app.models.service import ServiceTicketProject
        for pid in ticket_in.project_ids:
            if pid != ticket_in.project_id:  # 跳过主项目
                related_project = ServiceTicketProject(
                    ticket_id=ticket.id,
                    project_id=pid,
                    is_primary=False,
                )
                db.add(related_project)

    db.commit()
    db.refresh(ticket)

    return ResponseModel(
        code=201,
        message="工单创建成功",
        data={
            "id": ticket.id,
            "ticket_no": ticket.ticket_no,
        },
    )


@router.put(
    "/tickets/{ticket_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def update_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    ticket_in: ServiceTicketUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新服务工单
    - **ticket_id**: 工单 ID
    - **problem_desc**: 问题描述（可选）
    - **urgency**: 紧急程度（可选）
    - **status**: 状态（可选）
    """
    # 查找工单
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工单不存在 (ID: {ticket_id})",
        )

    # 更新字段
    update_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    return ResponseModel(
        code=200,
        message="工单更新成功",
        data={
            "id": ticket.id,
            "ticket_no": ticket.ticket_no,
            "status": ticket.status,
        },
    )


@router.put(
    "/tickets/{ticket_id}/close", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def close_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    ticket_in: ServiceTicketClose,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭服务工单
    - **ticket_id**: 工单 ID
    - **solution**: 解决方案（必填）
    - **root_cause**: 根本原因（可选）
    - **preventive_action**: 预防措施（可选）
    - **satisfaction**: 满意度 1-5（可选）
    - **feedback**: 客户反馈（可选）
    """
    # 查找工单
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工单不存在 (ID: {ticket_id})",
        )

    # 检查工单状态
    if ticket.status == "CLOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工单已关闭，无法重复关闭",
        )

    # 更新工单信息
    ticket.solution = ticket_in.solution
    ticket.root_cause = ticket_in.root_cause
    ticket.preventive_action = ticket_in.preventive_action
    ticket.satisfaction = ticket_in.satisfaction
    ticket.feedback = ticket_in.feedback
    ticket.status = "CLOSED"
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
            "resolved_time": ticket.resolved_time.isoformat() if ticket.resolved_time else None,
        },
    )


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
    整合工单、问题、验收、SLA监控等数据
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
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    dashboard_data = get_itr_dashboard_data(
        db, project_id=project_id, start_date=start_dt, end_date=end_dt
    )

    return ResponseModel(code=200, message="获取成功", data=dashboard_data)


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
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    resolution_analysis = analyze_resolution_time(db, start_dt, end_dt, project_id)
    bottlenecks = identify_bottlenecks(db, start_dt, end_dt)

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "resolution_time": resolution_analysis,
            "bottlenecks": bottlenecks,
        },
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
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    satisfaction_trend = analyze_satisfaction_trend(db, start_dt, end_dt, project_id)

    return ResponseModel(code=200, message="获取成功", data=satisfaction_trend)


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
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    bottlenecks = identify_bottlenecks(db, start_dt, end_dt)

    return ResponseModel(code=200, message="获取成功", data=bottlenecks)


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
                status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期格式错误，应为 YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期格式错误，应为 YYYY-MM-DD"
            )

    sla_performance = analyze_sla_performance(db, start_dt, end_dt, policy_id)

    return ResponseModel(code=200, message="获取成功", data=sla_performance)
