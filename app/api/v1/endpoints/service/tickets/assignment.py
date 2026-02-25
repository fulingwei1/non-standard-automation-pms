# -*- coding: utf-8 -*-
"""
服务工单管理 - 分配相关
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import ServiceTicket, ServiceTicketCcUser
from app.models.user import User
from app.schemas.service import ServiceTicketAssign, ServiceTicketResponse
from app.utils.db_helpers import get_or_404

from fastapi import APIRouter

router = APIRouter()


@router.get("/project-members", response_model=dict, status_code=status.HTTP_200_OK)
def get_project_members_for_ticket(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: str = Query(..., description="项目ID列表，逗号分隔（如：1,2,3）"),
    include_roles: Optional[str] = Query(None, description="包含的角色，逗号分隔（可选）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目相关人员（用于工单分配）
    根据项目ID列表获取所有相关人员，自动去重
    """
    from app.services.ticket_assignment_service import get_project_members_for_ticket

    # 解析项目ID列表
    try:
        project_id_list = [int(pid.strip()) for pid in project_ids.split(",") if pid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误，应为逗号分隔的数字")

    if not project_id_list:
        raise HTTPException(status_code=400, detail="至少需要一个项目ID")

    # 解析角色列表（可选）
    role_list = None
    if include_roles:
        try:
            role_list = [role.strip() for role in include_roles.split(",") if role.strip()]
        except (ValueError, AttributeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"解析角色列表失败: {e}, include_roles: {include_roles}")
            role_list = None

    # 获取项目成员
    members = get_project_members_for_ticket(
        db=db,
        project_ids=project_id_list,
        include_roles=role_list,
        exclude_user_id=current_user.id  # 排除当前用户
    )

    return {
        "members": members,
        "total": len(members)
    }


@router.get("/{ticket_id}/projects", response_model=dict, status_code=status.HTTP_200_OK)
def get_ticket_related_projects(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单关联的所有项目
    """
    from app.services.ticket_assignment_service import get_ticket_related_projects

    projects_data = get_ticket_related_projects(db, ticket_id)

    return projects_data


@router.put("/{ticket_id}/assign", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def assign_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    assign_in: ServiceTicketAssign,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分配服务工单（支持抄送人员）
    """
    ticket = get_or_404(db, ServiceTicket, ticket_id, "服务工单不存在")

    assignee = db.query(User).filter(User.id == assign_in.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    # 验证抄送人员（如果提供了）
    if assign_in.cc_user_ids:
        for user_id in assign_in.cc_user_ids:
            if not db.query(User).filter(User.id == user_id).first():
                raise HTTPException(status_code=404, detail=f"抄送人员不存在 (ID: {user_id})")

    ticket.assigned_to_id = assign_in.assignee_id
    ticket.assigned_to_name = assignee.name or assignee.username
    ticket.assigned_time = datetime.now()
    ticket.status = "IN_PROGRESS"

    # 记录响应时间（首次分配时）
    if not ticket.response_time:
        ticket.response_time = datetime.now()

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "ASSIGNED",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": f"工单已分配给 {assignee.name or assignee.username}",
    })

    # 更新抄送人员
    if assign_in.cc_user_ids is not None:
        # 删除旧的抄送人员
        db.query(ServiceTicketCcUser).filter(
            ServiceTicketCcUser.ticket_id == ticket_id
        ).delete()

        # 添加新的抄送人员（排除处理人）
        for user_id in assign_in.cc_user_ids:
            if user_id != assign_in.assignee_id:
                cc_user = ServiceTicketCcUser(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    notified_at=datetime.now()
                )
                db.add(cc_user)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    return ticket
