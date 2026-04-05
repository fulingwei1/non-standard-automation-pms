# -*- coding: utf-8 -*-
"""
售后服务模块 API 权限与数据范围回归测试
"""

from datetime import date, datetime
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Customer, Project, ProjectMember
from app.models.service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    ServiceRecord,
    ServiceTicket,
)
from app.models.service.enums import (
    KnowledgeBaseStatusEnum,
    ServiceRecordStatusEnum,
    ServiceTicketStatusEnum,
    SurveyStatusEnum,
)
from app.models.user import ApiPermission, RoleApiPermission, User
from tests.conftest import ENGINEER_CREDENTIALS


SERVICE_PERMISSION_SPECS = (
    ("service:read", "售后服务查看"),
    ("service:create", "售后服务创建"),
    ("service:update", "售后服务更新"),
    ("service:delete", "售后服务删除"),
)


def _suffix() -> str:
    return uuid.uuid4().hex[:8]


def _auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _invalidate_permission_cache() -> None:
    try:
        from app.services.permission_cache_service import get_permission_cache_service

        get_permission_cache_service().invalidate_all()
    except Exception:
        pass


def _grant_service_permissions(db: Session, user: User) -> None:
    permissions: list[ApiPermission] = []
    for code, name in SERVICE_PERMISSION_SPECS:
        permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
        if not permission:
            permission = ApiPermission(
                perm_code=code,
                perm_name=name,
                module="service",
                action=code.split(":", 1)[1].upper(),
                description=f"测试自动创建 - {name}",
                is_active=True,
                is_system=True,
            )
            db.add(permission)
            db.flush()
        permissions.append(permission)

    roles = list(user.roles.all()) if hasattr(user.roles, "all") else list(user.roles)
    assert roles, "测试用户缺少角色，无法挂载售后权限"

    changed = False
    for user_role in roles:
        role = user_role.role if hasattr(user_role, "role") else user_role
        for permission in permissions:
            exists = (
                db.query(RoleApiPermission)
                .filter(
                    RoleApiPermission.role_id == role.id,
                    RoleApiPermission.permission_id == permission.id,
                )
                .first()
            )
            if not exists:
                db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
                changed = True

    if changed:
        db.commit()

    _invalidate_permission_cache()


def _create_foreign_project(db: Session, template_project: Project, pm_user: User) -> Project:
    project = Project(
        project_code=f"PJT-SVC-{_suffix().upper()}",
        project_name=f"售后外部项目-{_suffix()}",
        customer_id=template_project.customer_id,
        customer_name=template_project.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        pm_id=pm_user.id,
        pm_name=pm_user.real_name or pm_user.username,
        priority="NORMAL",
        created_by=pm_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _ensure_customer(db: Session) -> Customer:
    customer = db.query(Customer).filter(Customer.customer_code == "CUST-SERVICE-SCOPE").first()
    if customer:
        return customer

    customer = Customer(
        customer_code="CUST-SERVICE-SCOPE",
        customer_name="售后权限测试客户",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def _create_accessible_project(db: Session, engineer_user: User, pm_user: User) -> Project:
    customer = _ensure_customer(db)
    project = Project(
        project_code=f"PJT-SVC-ACCESS-{_suffix().upper()}",
        project_name=f"售后可见项目-{_suffix()}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        pm_id=pm_user.id,
        pm_name=pm_user.real_name or pm_user.username,
        priority="NORMAL",
        created_by=pm_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    members = [
        ProjectMember(
            project_id=project.id,
            user_id=pm_user.id,
            role_code="PM",
            is_lead=True,
            allocation_pct=100,
            created_by=pm_user.id,
        ),
        ProjectMember(
            project_id=project.id,
            user_id=engineer_user.id,
            role_code="ENGINEER",
            allocation_pct=100,
            created_by=pm_user.id,
        ),
    ]
    db.add_all(members)
    db.commit()
    return project


def _create_ticket(
    db: Session,
    *,
    project_id: int,
    customer_id: int,
    suffix: str,
) -> ServiceTicket:
    ticket = ServiceTicket(
        ticket_no=f"TK-{suffix.upper()}-{uuid.uuid4().hex[:4].upper()}",
        project_id=project_id,
        customer_id=customer_id,
        problem_type="INSTALLATION",
        problem_desc=f"ticket-scope-{suffix}",
        urgency="HIGH",
        reported_by="scope-test",
        reported_time=datetime(2026, 3, 16, 10, 0, 0),
        status=ServiceTicketStatusEnum.PENDING.value,
        timeline=[],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _create_record(
    db: Session,
    *,
    project_id: int,
    customer_id: int,
    engineer_id: int,
    engineer_name: str,
    suffix: str,
) -> ServiceRecord:
    record = ServiceRecord(
        record_no=f"SR-{suffix.upper()}-{uuid.uuid4().hex[:4].upper()}",
        service_type="INSTALLATION",
        project_id=project_id,
        customer_id=customer_id,
        location=f"service-scope-{suffix}",
        service_date=date(2026, 3, 16),
        service_engineer_id=engineer_id,
        service_engineer_name=engineer_name,
        service_content=f"record-scope-{suffix}",
        status=ServiceRecordStatusEnum.IN_PROGRESS.value,
        photos=[],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _create_survey(
    db: Session,
    *,
    creator: User,
    suffix: str,
    label: str,
) -> CustomerSatisfaction:
    survey = CustomerSatisfaction(
        survey_no=f"SV-{suffix.upper()}-{label.upper()}",
        survey_type="AFTER_SERVICE",
        customer_name=f"survey-customer-{suffix}",
        project_name=f"survey-project-{suffix}",
        survey_date=date(2026, 3, 16),
        send_method="EMAIL",
        status=SurveyStatusEnum.DRAFT.value,
        created_by=creator.id,
        created_by_name=creator.real_name or creator.username,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


def _create_communication(
    db: Session,
    *,
    creator: User,
    suffix: str,
    label: str,
) -> CustomerCommunication:
    communication = CustomerCommunication(
        communication_no=f"CM-{suffix.upper()}-{label.upper()}",
        communication_type="PHONE",
        customer_name=f"comm-customer-{suffix}",
        communication_date=date(2026, 3, 16),
        topic="FOLLOW_UP",
        subject=f"comm-subject-{suffix}",
        content=f"comm-content-{suffix}",
        created_by=creator.id,
        created_by_name=creator.real_name or creator.username,
    )
    db.add(communication)
    db.commit()
    db.refresh(communication)
    return communication


def _create_article(db: Session, *, author: User) -> KnowledgeBase:
    suffix = _suffix()
    article = KnowledgeBase(
        article_no=f"KB-{suffix.upper()}",
        title=f"knowledge-{suffix}",
        category="FAQ",
        content="scope test article",
        tags=["scope"],
        is_faq=True,
        is_featured=False,
        status=KnowledgeBaseStatusEnum.DRAFT.value,
        author_id=author.id,
        author_name=author.real_name or author.username,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def test_service_ticket_list_requires_service_read(
    client: TestClient,
    regular_user_token: str,
):
    response = client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {regular_user_token}"},
    )

    assert response.status_code == 403
    assert "service:read" in response.json()["detail"]


def test_service_tickets_are_filtered_by_project_scope(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    mock_project = _create_accessible_project(db_session, engineer_user, pm_user)
    foreign_project = _create_foreign_project(db_session, mock_project, pm_user)
    suffix = _suffix()

    visible_ticket = _create_ticket(
        db_session,
        project_id=mock_project.id,
        customer_id=mock_project.customer_id,
        suffix=suffix,
    )
    hidden_ticket = _create_ticket(
        db_session,
        project_id=foreign_project.id,
        customer_id=foreign_project.customer_id,
        suffix=suffix,
    )

    response = client.get("/api/v1/tickets", params={"keyword": suffix}, headers=headers)

    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["items"]}
    assert visible_ticket.id in ids
    assert hidden_ticket.id not in ids


def test_service_ticket_detail_for_foreign_project_is_forbidden(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    mock_project = _create_accessible_project(db_session, engineer_user, pm_user)
    foreign_project = _create_foreign_project(db_session, mock_project, pm_user)
    hidden_ticket = _create_ticket(
        db_session,
        project_id=foreign_project.id,
        customer_id=foreign_project.customer_id,
        suffix=_suffix(),
    )

    response = client.get(f"/api/v1/tickets/{hidden_ticket.id}", headers=headers)

    assert response.status_code == 403
    assert "服务工单" in response.json()["detail"]


def test_service_records_are_filtered_by_project_scope(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    mock_project = _create_accessible_project(db_session, engineer_user, pm_user)
    foreign_project = _create_foreign_project(db_session, mock_project, pm_user)
    suffix = _suffix()

    visible_record = _create_record(
        db_session,
        project_id=mock_project.id,
        customer_id=mock_project.customer_id,
        engineer_id=engineer_user.id,
        engineer_name=engineer_user.real_name or engineer_user.username,
        suffix=suffix,
    )
    hidden_record = _create_record(
        db_session,
        project_id=foreign_project.id,
        customer_id=foreign_project.customer_id,
        engineer_id=engineer_user.id,
        engineer_name=engineer_user.real_name or engineer_user.username,
        suffix=suffix,
    )

    response = client.get("/api/v1/records", params={"keyword": suffix}, headers=headers)

    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["items"]}
    assert visible_record.id in ids
    assert hidden_record.id not in ids


def test_surveys_only_return_current_users_owned_data(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    suffix = _suffix()

    own_survey = _create_survey(db_session, creator=engineer_user, suffix=suffix, label="own")
    other_survey = _create_survey(db_session, creator=pm_user, suffix=suffix, label="other")

    response = client.get("/api/v1/surveys", params={"keyword": suffix}, headers=headers)

    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["items"]}
    assert own_survey.id in ids
    assert other_survey.id not in ids


def test_communications_only_return_current_users_owned_data(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    suffix = _suffix()

    own_comm = _create_communication(db_session, creator=engineer_user, suffix=suffix, label="own")
    other_comm = _create_communication(db_session, creator=pm_user, suffix=suffix, label="other")

    response = client.get("/api/v1/communications", params={"keyword": suffix}, headers=headers)

    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["items"]}
    assert own_comm.id in ids
    assert other_comm.id not in ids


def test_knowledge_update_requires_author_or_superuser(
    client: TestClient,
    db_session: Session,
    engineer_user: User,
    pm_user: User,
):
    _grant_service_permissions(db_session, engineer_user)
    headers = _auth_headers(
        client, ENGINEER_CREDENTIALS["username"], ENGINEER_CREDENTIALS["password"]
    )
    article = _create_article(db_session, author=pm_user)

    response = client.put(
        f"/api/v1/knowledge-base/{article.id}",
        json={"title": "attempted-overwrite"},
        headers=headers,
    )

    assert response.status_code == 403
    assert "知识库文章" in response.json()["detail"]

    db_session.refresh(article)
    assert article.title != "attempted-overwrite"
