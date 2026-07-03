# -*- coding: utf-8 -*-
"""Node task API regressions."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.project import Customer, Project
from app.models.stage_instance import NodeTask, ProjectNodeInstance, ProjectStageInstance
from app.models.user import User


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _create_project(db: Session, suffix: str, creator_id: int) -> Project:
    customer = Customer(
        customer_code=f"NT-CUST-{suffix}",
        customer_name=f"Node task customer {suffix}",
        contact_person="QA",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"NT-PJ-{suffix}",
        project_name=f"Node task project {suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        created_by=creator_id,
    )
    db.add(project)
    db.flush()
    return project


def _create_node(db: Session, project: Project, suffix: str) -> ProjectNodeInstance:
    stage = ProjectStageInstance(
        project_id=project.id,
        stage_code=f"NT-ST-{suffix[:6]}",
        stage_name="Node task self-service stage",
        sequence=1,
    )
    db.add(stage)
    db.flush()

    node = ProjectNodeInstance(
        project_id=project.id,
        stage_instance_id=stage.id,
        node_code=f"NTN{suffix[:6]}",
        node_name="Node task self-service node",
        sequence=1,
    )
    db.add(node)
    db.flush()
    return node


def test_regular_user_can_read_only_own_node_tasks(
    client: TestClient,
    db_session: Session,
):
    """A logged-in user should read their own node tasks without task_center:read."""
    suffix = uuid4().hex[:8]
    marker = f"NODE-TASK-SELF-{suffix}"

    actor = User(
        username=f"node_task_actor_{suffix}",
        password_hash=get_password_hash("password123"),
        real_name="Node task actor",
        department="QA",
        is_active=True,
        is_superuser=False,
    )
    other_user = User(
        username=f"node_task_other_{suffix}",
        password_hash=get_password_hash("password123"),
        real_name="Node task other",
        department="QA",
        is_active=True,
        is_superuser=False,
    )
    db_session.add_all([actor, other_user])
    db_session.flush()

    project = _create_project(db_session, suffix, actor.id)
    node = _create_node(db_session, project, suffix)

    own_task = NodeTask(
        node_instance_id=node.id,
        task_code=f"NT-T-{suffix}",
        task_name=f"{marker}-own",
        sequence=1,
        status="PENDING",
        priority="HIGH",
        assignee_id=actor.id,
    )
    other_task = NodeTask(
        node_instance_id=node.id,
        task_code=f"NT-O-{suffix}",
        task_name=f"{marker}-other",
        sequence=2,
        status="PENDING",
        priority="HIGH",
        assignee_id=other_user.id,
    )
    db_session.add_all([own_task, other_task])
    db_session.commit()

    headers = _auth_headers_for_user(actor)

    response = client.get(
        f"{settings.API_V1_PREFIX}/node-tasks/my-tasks",
        params={"status": "PENDING", "project_id": project.id},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    task_names = {item["task_name"] for item in response.json()}
    assert f"{marker}-own" in task_names
    assert f"{marker}-other" not in task_names

    cross_user_response = client.get(
        f"{settings.API_V1_PREFIX}/node-tasks/user/{other_user.id}",
        headers=headers,
    )
    assert cross_user_response.status_code == 403
