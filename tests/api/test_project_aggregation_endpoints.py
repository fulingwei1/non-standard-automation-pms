import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Department
from app.models.project import Project


def test_my_projects_endpoint_returns_memberships(
    client: TestClient,
    auth_headers,
    mock_project: Project,
) -> None:
    response = client.get(
        f"{settings.API_V1_PREFIX}/my/projects?page=1&page_size=10",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] >= 1
    first_item = payload["items"][0]
    assert "project_code" in first_item
    assert "task_stats" in first_item


def test_my_workload_endpoint_returns_summary(
    client: TestClient,
    auth_headers,
    create_test_task,
) -> None:
    start = datetime.date.today().replace(day=1)
    end = start + datetime.timedelta(days=7)
    create_test_task(plan_start_date=start, plan_end_date=end)

    response = client.get(
        f"{settings.API_V1_PREFIX}/my/workload",
        headers=auth_headers,
    )
    assert response.status_code == 200
    summary = response.json()["data"]["summary"]
    assert "total_assigned_hours" in summary
    assert "allocation_rate" in summary


def test_department_projects_and_workload_endpoints(
    client: TestClient,
    admin_auth_headers,
    db_session: Session,
    mock_project: Project,
) -> None:
    department = Department(
        dept_code="DPT-TEST",
        dept_name="测试部门",
        is_active=True,
    )
    db_session.add(department)
    db_session.commit()
    mock_project.dept_id = department.id
    db_session.add(mock_project)
    db_session.commit()

    project_resp = client.get(
        f"{settings.API_V1_PREFIX}/departments/{department.id}/projects",
        headers=admin_auth_headers,
    )
    assert project_resp.status_code == 200
    project_data = project_resp.json()["data"]
    assert project_data["total"] >= 1

    workload_resp = client.get(
        f"{settings.API_V1_PREFIX}/departments/{department.id}/workload",
        headers=admin_auth_headers,
    )
    assert workload_resp.status_code == 200
    workload_data = workload_resp.json()["data"]
    assert workload_data["department"]["name"] == "测试部门"


def test_analytics_projects_health_endpoint(
    client: TestClient,
    admin_auth_headers,
) -> None:
    response = client.get(
        f"{settings.API_V1_PREFIX}/analytics/projects/health",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "by_health" in data
    assert "total_projects" in data
