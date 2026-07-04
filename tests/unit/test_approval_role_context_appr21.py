# -*- coding: utf-8 -*-
"""APPR-21: ROLE approvers should prefer the business/project context."""

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMember
from app.models.user import Role, User, UserRole
from app.services.approval_engine.router import ApprovalRouterService


def _user(db: Session, username: str) -> User:
    user = User(
        username=username,
        password_hash="x",
        real_name=username,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_role_approver_prefers_project_member_over_global_first_user(db_session: Session):
    role_code = "APPR21_PM"
    role = Role(role_code=role_code, role_name="APPR21 项目经理", is_active=True)
    db_session.add(role)
    db_session.flush()

    global_first = _user(db_session, "appr21_global_first")
    project_pm = _user(db_session, "appr21_project_pm")
    db_session.add_all(
        [
            UserRole(user_id=global_first.id, role_id=role.id),
            UserRole(user_id=project_pm.id, role_id=role.id),
        ]
    )

    project = Project(
        project_code="APPR21-PROJ",
        project_name="APPR21 项目",
        stage="S1",
        status="ST01",
        health="H1",
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(
        ProjectMember(
            project_id=project.id,
            user_id=project_pm.id,
            role_code=role_code,
            is_active=True,
            is_lead=True,
        )
    )
    db_session.commit()

    approver_ids = ApprovalRouterService(db_session)._resolve_role_approvers(
        {"role_codes": [role_code]},
        {"form_data": {"project_id": project.id}},
    )

    assert approver_ids == [project_pm.id]


def test_role_approver_falls_back_to_global_role_without_project_context(
    db_session: Session,
):
    role_code = "APPR21_GLOBAL"
    role = Role(role_code=role_code, role_name="APPR21 全局角色", is_active=True)
    db_session.add(role)
    db_session.flush()

    first_user = _user(db_session, "appr21_global_a")
    second_user = _user(db_session, "appr21_global_b")
    db_session.add_all(
        [
            UserRole(user_id=first_user.id, role_id=role.id),
            UserRole(user_id=second_user.id, role_id=role.id),
        ]
    )
    db_session.commit()

    approver_ids = ApprovalRouterService(db_session)._resolve_role_approvers(
        {"role_codes": [role_code]},
        {},
    )

    assert approver_ids == [first_user.id, second_user.id]
