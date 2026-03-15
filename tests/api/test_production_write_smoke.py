import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.project import Customer, Project
from app.models.user import User


pytestmark = [pytest.mark.api]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db):
    return db.query(User).filter(User.username == "admin").first()


def _create_project(db, suffix: str) -> Project:
    admin = _admin_user(db)

    customer = Customer(
        customer_code=f"CUST-SMOKE-{suffix}",
        customer_name=f"生产冒烟客户-{suffix}",
        contact_person="张三",
        contact_phone="13800000000",
        status="ACTIVE",
        created_by=admin.id if admin else None,
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PRJ-SMOKE-{suffix}",
        project_name=f"生产写操作冒烟项目-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        created_by=admin.id if admin else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestProductionWriteSmoke:
    def test_production_write_flow_smoke(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]
        project = _create_project(db, suffix)

        workshop_create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/workshops",
            json={
                "workshop_code": f"WS-SMOKE-{suffix}",
                "workshop_name": f"冒烟车间-{suffix}",
                "workshop_type": "ASSEMBLY",
                "location": "A1",
                "capacity_hours": 16,
                "description": "生产写操作冒烟",
            },
            headers=headers,
        )
        assert workshop_create_resp.status_code == 200, workshop_create_resp.text
        workshop = workshop_create_resp.json()
        assert workshop["workshop_code"] == f"WS-SMOKE-{suffix}"
        assert workshop["workshop_name"] == f"冒烟车间-{suffix}"
        assert float(workshop["capacity_hours"]) == 16.0

        workshop_update_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/workshops/{workshop['id']}",
            json={
                "location": "B2",
                "capacity_hours": 18,
                "description": "生产写操作冒烟-已更新",
            },
            headers=headers,
        )
        assert workshop_update_resp.status_code == 200, workshop_update_resp.text
        updated_workshop = workshop_update_resp.json()
        assert updated_workshop["location"] == "B2"
        assert float(updated_workshop["capacity_hours"]) == 18.0
        assert updated_workshop["description"] == "生产写操作冒烟-已更新"

        worker_create_resp = client.post(
            f"{settings.API_V1_PREFIX}/workers",
            json={
                "worker_code": f"WK-SMOKE-{suffix}",
                "worker_name": "冒烟工人",
                "workshop_id": workshop["id"],
                "position": "装配工",
                "skill_level": "SENIOR",
                "phone": "13800001111",
                "hire_date": "2026-03-01",
                "is_active": True,
            },
            headers=headers,
        )
        assert worker_create_resp.status_code == 200, worker_create_resp.text
        worker = worker_create_resp.json()
        assert worker["worker_code"] == f"WK-SMOKE-{suffix}"
        assert worker["workshop_id"] == workshop["id"]
        assert worker["workshop_name"] == workshop["workshop_name"]
        assert worker["hire_date"] == "2026-03-01"

        work_order_create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/work-orders",
            json={
                "task_name": f"生产写操作冒烟工单-{suffix}",
                "task_type": "ASSEMBLY",
                "project_id": project.id,
                "workshop_id": workshop["id"],
                "plan_qty": 10,
                "plan_start_date": str(date.today()),
                "plan_end_date": str(date.today() + timedelta(days=1)),
                "priority": "NORMAL",
                "work_content": "装配+报工链路冒烟",
            },
            headers=headers,
        )
        assert work_order_create_resp.status_code == 200, work_order_create_resp.text
        work_order = work_order_create_resp.json()
        assert work_order["status"] == "PENDING"
        assert work_order["project_id"] == project.id
        assert work_order["workshop_id"] == workshop["id"]
        assert work_order["plan_qty"] == 10

        assign_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/work-orders/{work_order['id']}/assign",
            json={
                # 故意走兼容字段，验证 worker_id -> assigned_to 兼容
                "worker_id": worker["id"],
            },
            headers=headers,
        )
        assert assign_resp.status_code == 200, assign_resp.text
        assigned_order = assign_resp.json()
        assert assigned_order["assigned_to"] == worker["id"]
        assert assigned_order["assigned_worker_name"] == worker["worker_name"]
        assert assigned_order["status"] == "ASSIGNED"

        start_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/work-reports/start",
            json={
                "work_order_id": work_order["id"],
                # 故意走兼容字段，验证 assigned_to -> worker_id 兼容
                "assigned_to": worker["id"],
                "report_note": "开工",
            },
            headers=headers,
        )
        assert start_resp.status_code == 200, start_resp.text
        start_report = start_resp.json()
        assert start_report["report_type"] == "START"
        assert start_report["worker_id"] == worker["id"]
        assert start_report["report_note"] == "开工"

        progress_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/work-reports/progress",
            json={
                "work_order_id": work_order["id"],
                "assigned_to": worker["id"],
                "progress_percent": 60,
                "work_hours": 2.5,
                "report_note": "进行中",
            },
            headers=headers,
        )
        assert progress_resp.status_code == 200, progress_resp.text
        progress_report = progress_resp.json()
        assert progress_report["report_type"] == "PROGRESS"
        assert progress_report["worker_id"] == worker["id"]
        assert progress_report["progress_percent"] == 60
        assert float(progress_report["work_hours"]) == 2.5

        complete_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/work-reports/complete",
            json={
                "work_order_id": work_order["id"],
                "assigned_to": worker["id"],
                "completed_qty": 10,
                "qualified_qty": 9,
                "defect_qty": 1,
                "work_hours": 3.0,
                "report_note": "完工",
            },
            headers=headers,
        )
        assert complete_resp.status_code == 200, complete_resp.text
        complete_report = complete_resp.json()
        assert complete_report["report_type"] == "COMPLETE"
        assert complete_report["worker_id"] == worker["id"]
        assert complete_report["completed_qty"] == 10
        assert complete_report["qualified_qty"] == 9
        assert complete_report["defect_qty"] == 1
        assert float(complete_report["work_hours"]) == 3.0

        work_order_detail_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/work-orders/{work_order['id']}",
            headers=headers,
        )
        assert work_order_detail_resp.status_code == 200, work_order_detail_resp.text
        completed_order = work_order_detail_resp.json()
        assert completed_order["status"] == "COMPLETED"
        assert completed_order["progress"] == 100
        assert completed_order["completed_qty"] == 10
        assert completed_order["qualified_qty"] == 9
        assert completed_order["defect_qty"] == 1
        assert float(completed_order["actual_hours"]) == 5.5

        work_reports_list_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/work-reports",
            params={"work_order_id": work_order["id"], "page": 1, "page_size": 10},
            headers=headers,
        )
        assert work_reports_list_resp.status_code == 200, work_reports_list_resp.text
        work_reports_data = work_reports_list_resp.json()
        assert work_reports_data["total"] >= 3
        assert {item["report_type"] for item in work_reports_data["items"]} >= {
            "START",
            "PROGRESS",
            "COMPLETE",
        }

        exception_create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production-exceptions",
            json={
                "exception_type": "QUALITY",
                "exception_level": "MAJOR",
                "title": f"生产写操作冒烟异常-{suffix}",
                "description": "报工后发现轻微质量异常",
                "project_id": project.id,
                "workshop_id": workshop["id"],
                "work_order_id": work_order["id"],
                "impact_hours": 1.5,
                "impact_cost": 200,
            },
            headers=headers,
        )
        assert exception_create_resp.status_code == 200, exception_create_resp.text
        exception = exception_create_resp.json()
        assert exception["status"] == "REPORTED"
        assert exception["project_name"] == project.project_name
        assert exception["workshop_name"] == workshop["workshop_name"]
        assert exception["work_order_id"] == work_order["id"]
