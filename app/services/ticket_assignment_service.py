# -*- coding: utf-8 -*-
"""
工单智能分配服务
根据项目自动获取相关人员，支持多项目合并
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMember
from app.models.user import User


def get_project_members_for_ticket(
    db: Session,
    project_ids: List[int],
    include_roles: Optional[List[str]] = None,
    exclude_user_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取项目相关人员（去重）

    根据项目ID列表获取所有相关人员，按用户ID去重，
    合并该用户在多个项目中的角色信息。

    Args:
        db: 数据库会话
        project_ids: 项目ID列表
        include_roles: 包含的角色（可选，如：['PM', 'ME', 'EE']）
        exclude_user_id: 排除的用户ID（如当前用户）

    Returns:
        去重后的人员列表，每个人员包含：
        - user_id: 用户ID
        - username: 用户名
        - real_name: 真实姓名
        - role_code: 主要角色编码
        - role_name: 角色名称
        - projects: 该人员在哪些项目中（列表）
        - is_lead: 是否负责人
    """
    if not project_ids:
        return []

    # 查询项目成员
    query = db.query(ProjectMember).filter(
        ProjectMember.project_id.in_(project_ids),
        ProjectMember.is_active == True
    )

    if include_roles:
        query = query.filter(ProjectMember.role_code.in_(include_roles))

    if exclude_user_id:
        query = query.filter(ProjectMember.user_id != exclude_user_id)

    members = query.all()

    if not members:
        return []

    # 按用户ID去重，合并项目列表
    user_members = {}
    for member in members:
        user_id = member.user_id
        user = member.user

        if user_id not in user_members:
            user_members[user_id] = {
                "user_id": user_id,
                "username": user.username if user else "Unknown",
                "real_name": (user.real_name or user.username) if user else "Unknown",
                "email": user.email if user else None,
                "phone": user.phone if user else None,
                "department": user.department if user else None,
                "position": user.position if user else None,
                "role_code": member.role_code,
                "role_name": member.role_type.role_name if member.role_type else member.role_code,
                "projects": [],
                "is_lead": member.is_lead,
                "allocation_pct": float(member.allocation_pct or 100)
            }

        # 添加项目信息
        project = member.project
        project_info = {
            "project_id": member.project_id,
            "project_code": project.project_code if project else None,
            "project_name": project.project_name if project else None,
            "role_code": member.role_code,
            "is_lead": member.is_lead
        }

        # 避免重复添加同一项目
        if not any(p["project_id"] == member.project_id for p in user_members[user_id]["projects"]):
            user_members[user_id]["projects"].append(project_info)

    # 按角色优先级和姓名排序
    role_priority = {
        "PM": 1, "PMC": 2, "ME": 3, "EE": 4,
        "SW": 5, "DEBUG": 6, "QA": 7, "SALES": 8
    }

    sorted_members = sorted(
        user_members.values(),
        key=lambda x: (
            role_priority.get(x["role_code"], 99),
            x["real_name"]
        )
    )

    return sorted_members


def get_ticket_related_projects(
    db: Session,
    ticket_id: int
) -> Dict[str, Any]:
    """
    获取工单关联的所有项目

    Args:
        db: 数据库会话
        ticket_id: 工单ID

    Returns:
        包含主项目和关联项目的字典
    """
    from app.models.service import ServiceTicket, ServiceTicketProject

    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        return {
            "primary_project": None,
            "related_projects": []
        }

    # 获取主项目
    primary_project = None
    if ticket.project_id:
        project = db.query(Project).filter(Project.id == ticket.project_id).first()
        if project:
            primary_project = {
                "id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name
            }

    # 获取关联项目
    ticket_projects = db.query(ServiceTicketProject).filter(
        ServiceTicketProject.ticket_id == ticket_id
    ).all()

    related_projects = []
    for tp in ticket_projects:
        if tp.project_id != ticket.project_id:  # 排除主项目
            project = db.query(Project).filter(Project.id == tp.project_id).first()
            if project:
                related_projects.append({
                    "id": project.id,
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "is_primary": tp.is_primary
                })

    return {
        "primary_project": primary_project,
        "related_projects": related_projects
    }
