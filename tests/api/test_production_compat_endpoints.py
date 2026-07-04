import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.material import Material
from app.models.production import (
    MaterialRequisition,
    ProductionDailyReport,
    WorkOrder,
    WorkReport,
    Worker,
    Workshop,
    Workstation,
)
from app.models.project import Project
from app.models.user import User


pytestmark = [pytest.mark.api]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db):
    return db.query(User).filter(User.username == "admin").first()


class TestProductionCompatibilityEndpoints:
    def test_workers_compatibility_routes(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-COMP-{suffix}",
            workshop_name=f"兼容车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        db.add(workshop)
        db.commit()
        db.refresh(workshop)

        create_payload = {
            "worker_code": f"WK-{suffix}",
            "worker_name": "兼容工人",
            "workshop_id": workshop.id,
            "phone": "13800001111",
            "skill_level": "SENIOR",
            "hire_date": "2026-03-01",
            "is_active": True,
        }
        create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/workers",
            json=create_payload,
            headers=headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        created = create_resp.json()
        assert created["worker_code"] == create_payload["worker_code"]
        assert created["skill_level"] == "SENIOR"
        assert created["hire_date"] == "2026-03-01"
        assert created["workshop_name"] == workshop.workshop_name

        worker_id = created["id"]

        list_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/workers",
            params={"page": 1, "page_size": 10, "search": suffix},
            headers=headers,
        )
        assert list_resp.status_code == 200, list_resp.text
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert any(item["id"] == worker_id for item in list_data["items"])

        detail_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/workers/{worker_id}",
            headers=headers,
        )
        assert detail_resp.status_code == 200, detail_resp.text
        assert detail_resp.json()["worker_name"] == "兼容工人"

        update_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/workers/{worker_id}",
            json={"phone": "13900002222", "skill_level": "EXPERT", "is_active": False},
            headers=headers,
        )
        assert update_resp.status_code == 200, update_resp.text
        updated = update_resp.json()
        assert updated["phone"] == "13900002222"
        assert updated["skill_level"] == "EXPERT"
        assert updated["is_active"] is False

        work_order = WorkOrder(
            work_order_no=f"WO-{suffix}",
            task_name="兼容派工任务",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            assigned_to=worker_id,
            status="COMPLETED",
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        report = WorkReport(
            report_no=f"WR-{suffix}",
            work_order_id=work_order.id,
            worker_id=worker_id,
            report_type="COMPLETE",
            report_time=datetime.now(),
            work_hours=Decimal("6.50"),
            completed_qty=12,
            qualified_qty=11,
            defect_qty=1,
            status="APPROVED",
        )
        db.add(report)
        db.commit()

        performance_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/workers/{worker_id}/performance",
            headers=headers,
        )
        assert performance_resp.status_code == 200, performance_resp.text
        performance = performance_resp.json()
        assert performance["worker_id"] == worker_id
        assert performance["total_reports"] == 1
        assert performance["total_completed_qty"] == 12
        assert performance["total_qualified_qty"] == 11

    def test_material_requisition_create_issue_deducts_inventory(
        self, client: TestClient, admin_token: str, db
    ):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]
        admin = _admin_user(db)

        material = Material(
            material_code=f"MR-MAT-{suffix}",
            material_name=f"领料物料-{suffix}",
            unit="件",
            current_stock=Decimal("5.0000"),
            standard_price=Decimal("10"),
            created_by=admin.id if admin else None,
        )
        work_order = WorkOrder(
            work_order_no=f"MR-WO-{suffix}",
            task_name="领料扣库测试工单",
            task_type="ASSEMBLY",
            status="IN_PROGRESS",
            created_by=admin.id if admin else None,
        )
        db.add(material)
        db.add(work_order)
        db.commit()
        db.refresh(material)
        db.refresh(work_order)

        stock = MaterialStock(
            tenant_id=1,
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            location="默认仓库",
            batch_number="",
            quantity=Decimal("5.0000"),
            available_quantity=Decimal("5.0000"),
            reserved_quantity=Decimal("0"),
            unit=material.unit,
            unit_price=Decimal("10"),
            total_value=Decimal("50.00"),
        )
        db.add(stock)
        db.commit()

        create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/material-requisitions",
            json={
                "work_order_id": work_order.id,
                "apply_reason": "生产领料扣库回归",
                "items": [{"material_id": material.id, "request_qty": 3}],
            },
            headers=headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        created = create_resp.json()["data"]
        requisition_id = created["id"]
        item_id = created["items"][0]["id"]
        assert created["status"] == "DRAFT"
        assert created["items"][0]["request_qty"] == 3.0

        approve_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/material-requisitions/{requisition_id}/approve",
            json={"approved_qty": {str(item_id): 3}},
            headers=headers,
        )
        assert approve_resp.status_code == 200, approve_resp.text

        issue_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/material-requisitions/{requisition_id}/issue",
            json={"issued_qty": {str(item_id): 3}, "location": "默认仓库"},
            headers=headers,
        )
        assert issue_resp.status_code == 200, issue_resp.text

        db.expire_all()
        requisition = db.get(MaterialRequisition, requisition_id)
        assert requisition.status == "ISSUED"
        assert requisition.items[0].issued_qty == Decimal("3.0000")

        stock = (
            db.query(MaterialStock)
            .filter(MaterialStock.material_id == material.id, MaterialStock.location == "默认仓库")
            .one()
        )
        assert stock.quantity == Decimal("2.0000")
        assert stock.available_quantity == Decimal("2.0000")
        db.refresh(material)
        assert material.current_stock == Decimal("2.0000")

        transaction = (
            db.query(MaterialTransaction)
            .filter(
                MaterialTransaction.material_id == material.id,
                MaterialTransaction.transaction_type == "ISSUE",
                MaterialTransaction.related_order_id == work_order.id,
            )
            .one_or_none()
        )
        assert transaction is not None
        assert transaction.quantity == Decimal("3.0000")
        assert transaction.related_order_type == "WORK_ORDER"

    def test_production_exception_compatibility_routes(
        self, client: TestClient, admin_token: str, db
    ):
        headers = _auth_headers(admin_token)
        admin = _admin_user(db)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-EXC-{suffix}",
            workshop_name=f"异常车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        project = Project(
            project_code=f"PRJ-{suffix}",
            project_name=f"异常项目-{suffix}",
            created_by=admin.id if admin else None,
        )
        db.add(workshop)
        db.add(project)
        db.commit()
        db.refresh(workshop)
        db.refresh(project)

        create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/exceptions",
            json={
                "exception_type": "MATERIAL",
                "exception_level": "MAJOR",
                "title": f"异常兼容测试-{suffix}",
                "description": "领料延迟导致停线",
                "project_id": project.id,
                "workshop_id": workshop.id,
                "impact_hours": 2.5,
                "impact_cost": 800,
            },
            headers=headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        created = create_resp.json()
        assert created["status"] == "REPORTED"
        assert created["project_name"] == project.project_name
        assert created["workshop_name"] == workshop.workshop_name

        exception_id = created["id"]

        list_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/exceptions",
            params={"page": 1, "page_size": 10, "search": suffix},
            headers=headers,
        )
        assert list_resp.status_code == 200, list_resp.text
        assert any(item["id"] == exception_id for item in list_resp.json()["items"])

        handle_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/exceptions/{exception_id}/handle",
            json={"handle_plan": "紧急协调替代料", "handle_result": "已恢复生产"},
            headers=headers,
        )
        assert handle_resp.status_code == 200, handle_resp.text
        handled = handle_resp.json()
        assert handled["status"] == "RESOLVED"
        assert handled["handle_result"] == "已恢复生产"

        detail_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/exceptions/{exception_id}",
            headers=headers,
        )
        assert detail_resp.status_code == 200, detail_resp.text
        assert detail_resp.json()["status"] == "RESOLVED"

        close_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/exceptions/{exception_id}/close",
            headers=headers,
        )
        assert close_resp.status_code == 200, close_resp.text
        assert close_resp.json()["status"] == "CLOSED"

    def test_work_order_update_compatibility_route(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-UPD-{suffix}",
            workshop_name=f"更新车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        db.add(workshop)
        db.commit()
        db.refresh(workshop)

        work_order = WorkOrder(
            work_order_no=f"WO-UPD-{suffix}",
            task_name="旧任务名",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            plan_qty=5,
            priority="NORMAL",
            status="PENDING",
            remark="old",
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        update_resp = client.put(
            f"{settings.API_V1_PREFIX}/production/work-orders/{work_order.id}",
            json={
                "task_name": "新任务名",
                "plan_qty": 8,
                "priority": "HIGH",
                "remark": "updated",
            },
            headers=headers,
        )
        assert update_resp.status_code == 200, update_resp.text
        updated = update_resp.json()
        assert updated["task_name"] == "新任务名"
        assert updated["plan_qty"] == 8
        assert updated["priority"] == "HIGH"
        assert updated["remark"] == "updated"

    def test_work_report_generic_create_route(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-REP-{suffix}",
            workshop_name=f"报工车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        db.add(workshop)
        db.commit()
        db.refresh(workshop)

        worker = Worker(
            worker_no=f"WK-REP-{suffix}",
            worker_name="报工工人",
            workshop_id=workshop.id,
            skill_level="SENIOR",
            status="ACTIVE",
            is_active=True,
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        work_order = WorkOrder(
            work_order_no=f"WO-REP-{suffix}",
            task_name="兼容报工任务",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            assigned_to=worker.id,
            status="ASSIGNED",
            plan_qty=10,
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        create_resp = client.post(
            f"{settings.API_V1_PREFIX}/production/work-reports",
            json={
                "work_order_id": work_order.id,
                "report_note": "扫码开工",
            },
            headers=headers,
        )
        assert create_resp.status_code == 200, create_resp.text
        created = create_resp.json()
        assert created["report_type"] == "START"
        assert created["work_order_id"] == work_order.id
        assert created["worker_id"] == worker.id
        db.refresh(work_order)
        assert work_order.status == "STARTED"

    def test_workshop_task_board_compatibility_route(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-BOARD-{suffix}",
            workshop_name=f"看板车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        worker = Worker(
            worker_no=f"WK-BOARD-{suffix}",
            worker_name="看板工人",
            skill_level="SENIOR",
            status="ACTIVE",
            is_active=True,
        )
        db.add(workshop)
        db.add(worker)
        db.commit()
        worker.workshop_id = workshop.id
        db.add(worker)
        db.commit()
        db.refresh(workshop)
        db.refresh(worker)

        work_order = WorkOrder(
            work_order_no=f"WO-BOARD-{suffix}",
            task_name="看板任务",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            assigned_to=worker.id,
            status="STARTED",
            plan_qty=20,
            completed_qty=8,
            progress=40,
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        workstation = Workstation(
            workstation_code=f"ST-{suffix}",
            workstation_name="装配工位A",
            workshop_id=workshop.id,
            status="WORKING",
            current_worker_id=worker.id,
            current_work_order_id=work_order.id,
            is_active=True,
        )
        db.add(workstation)
        db.commit()

        board_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/workshops/{workshop.id}/task-board",
            headers=headers,
        )
        assert board_resp.status_code == 200, board_resp.text
        board = board_resp.json()
        assert board["workshop_name"] == workshop.workshop_name
        assert any(item["work_order_no"] == work_order.work_order_no for item in board["work_orders"])
        assert any(item["current_worker_name"] == worker.worker_name for item in board["workstations"])

    def test_daily_report_compatibility_routes(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]
        report_day = date(2026, 3, 15)

        workshop = Workshop(
            workshop_code=f"WS-DR-{suffix}",
            workshop_name=f"日报车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        db.add(workshop)
        db.commit()
        db.refresh(workshop)

        report = ProductionDailyReport(
            report_date=report_day,
            workshop_id=workshop.id,
            plan_qty=20,
            completed_qty=16,
            plan_hours=Decimal("18.00"),
            actual_hours=Decimal("15.50"),
            overtime_hours=Decimal("1.00"),
            should_attend=10,
            actual_attend=9,
            leave_count=1,
            total_qty=16,
            qualified_qty=15,
            new_exception_count=2,
            resolved_exception_count=1,
            summary="日报兼容测试",
        )
        db.add(report)
        db.commit()

        list_resp = client.get(
            f"{settings.API_V1_PREFIX}/production-daily-reports",
            params={"report_date": report_day.isoformat(), "page": 1, "page_size": 10},
            headers=headers,
        )
        assert list_resp.status_code == 200, list_resp.text
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert list_data["items"][0]["workshop_name"] == workshop.workshop_name
        assert list_data["items"][0]["completion_rate"] == 80.0
        assert list_data["items"][0]["pass_rate"] == 93.75

        latest_resp = client.get(
            f"{settings.API_V1_PREFIX}/production-daily-reports/latest",
            params={"workshop_id": workshop.id},
            headers=headers,
        )
        assert latest_resp.status_code == 200, latest_resp.text
        latest = latest_resp.json()
        assert latest["report_date"] == report_day.isoformat()
        assert latest["workshop_name"] == workshop.workshop_name
        assert latest["summary"] == "日报兼容测试"

    def test_worker_report_compatibility_routes(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)
        suffix = uuid.uuid4().hex[:8]

        workshop = Workshop(
            workshop_code=f"WS-RPT-{suffix}",
            workshop_name=f"报表车间-{suffix}",
            workshop_type="ASSEMBLY",
            is_active=True,
        )
        db.add(workshop)
        db.commit()
        db.refresh(workshop)

        worker_a = Worker(
            worker_no=f"WK-RPT-A-{suffix}",
            worker_name="报表工人A",
            workshop_id=workshop.id,
            skill_level="SENIOR",
            status="ACTIVE",
            is_active=True,
        )
        worker_b = Worker(
            worker_no=f"WK-RPT-B-{suffix}",
            worker_name="报表工人B",
            workshop_id=workshop.id,
            skill_level="INTERMEDIATE",
            status="ACTIVE",
            is_active=True,
        )
        db.add(worker_a)
        db.add(worker_b)
        db.commit()
        db.refresh(worker_a)
        db.refresh(worker_b)

        work_order_a = WorkOrder(
            work_order_no=f"WO-RPT-A-{suffix}",
            task_name="绩效任务A",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            assigned_to=worker_a.id,
            status="COMPLETED",
            plan_qty=20,
        )
        work_order_b = WorkOrder(
            work_order_no=f"WO-RPT-B-{suffix}",
            task_name="绩效任务B",
            task_type="ASSEMBLY",
            workshop_id=workshop.id,
            assigned_to=worker_b.id,
            status="COMPLETED",
            plan_qty=20,
        )
        db.add(work_order_a)
        db.add(work_order_b)
        db.commit()
        db.refresh(work_order_a)
        db.refresh(work_order_b)

        db.add_all(
            [
                WorkReport(
                    report_no=f"WR-RPT-A1-{suffix}",
                    work_order_id=work_order_a.id,
                    worker_id=worker_a.id,
                    report_type="PROGRESS",
                    report_time=datetime(2026, 3, 10, 9, 0, 0),
                    work_hours=Decimal("4.00"),
                    completed_qty=8,
                    qualified_qty=7,
                    defect_qty=1,
                    status="APPROVED",
                ),
                WorkReport(
                    report_no=f"WR-RPT-A2-{suffix}",
                    work_order_id=work_order_a.id,
                    worker_id=worker_a.id,
                    report_type="COMPLETE",
                    report_time=datetime(2026, 3, 11, 18, 0, 0),
                    work_hours=Decimal("2.00"),
                    completed_qty=4,
                    qualified_qty=4,
                    defect_qty=0,
                    status="APPROVED",
                ),
                WorkReport(
                    report_no=f"WR-RPT-B1-{suffix}",
                    work_order_id=work_order_b.id,
                    worker_id=worker_b.id,
                    report_type="COMPLETE",
                    report_time=datetime(2026, 3, 11, 18, 30, 0),
                    work_hours=Decimal("3.00"),
                    completed_qty=6,
                    qualified_qty=6,
                    defect_qty=0,
                    status="APPROVED",
                ),
            ]
        )
        db.commit()

        performance_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/reports/worker-performance",
            params={
                "workshop_id": workshop.id,
                "period_start": "2026-03-01",
                "period_end": "2026-03-31",
            },
            headers=headers,
        )
        assert performance_resp.status_code == 200, performance_resp.text
        performance = performance_resp.json()
        assert len(performance) == 2
        worker_a_report = next(item for item in performance if item["worker_id"] == worker_a.id)
        assert worker_a_report["total_reports"] == 2
        assert worker_a_report["total_completed_qty"] == 12
        assert worker_a_report["total_qualified_qty"] == 11
        assert worker_a_report["average_efficiency"] == 1.83

        ranking_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/reports/worker-ranking",
            params={
                "workshop_id": workshop.id,
                "ranking_type": "output",
                "period_start": "2026-03-01",
                "period_end": "2026-03-31",
            },
            headers=headers,
        )
        assert ranking_resp.status_code == 200, ranking_resp.text
        ranking = ranking_resp.json()
        assert ranking[0]["worker_id"] == worker_a.id
        assert ranking[0]["rank"] == 1
        assert ranking[0]["output"] == 12
        assert ranking[0]["quality_rate"] == 91.67

    def test_material_requisitions_data_scope_own_vs_all(
        self, client: TestClient, admin_token: str, normal_user_token: str, db
    ):
        """PERM-17: 领料单列表按数据权限过滤（OWN 只见自己申请的，ALL/超管全见）。"""
        if not admin_token or not normal_user_token:
            pytest.skip("Auth tokens not available")

        admin = _admin_user(db)
        normal_user = db.query(User).filter(User.username == "user").first()
        assert normal_user is not None and admin is not None
        suffix = uuid.uuid4().hex[:8]
        scope_marker = f"ST{suffix}"

        own_requisition = MaterialRequisition(
            requisition_no=f"MR-OWN-{suffix}",
            applicant_id=normal_user.id,
            apply_time=datetime.now(),
            status=scope_marker,
        )
        other_requisition = MaterialRequisition(
            requisition_no=f"MR-OTH-{suffix}",
            applicant_id=admin.id,
            apply_time=datetime.now(),
            status=scope_marker,
        )
        db.add_all([own_requisition, other_requisition])
        db.commit()
        db.refresh(own_requisition)
        db.refresh(other_requisition)

        # OWN 数据权限的普通用户（无角色，默认降级为 OWN）只能看到自己申请的领料单
        own_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/material-requisitions",
            params={"page": 1, "page_size": 50, "status": scope_marker},
            headers=_auth_headers(normal_user_token),
        )
        assert own_resp.status_code == 200, own_resp.text
        own_ids = {item["id"] for item in own_resp.json()["items"]}
        assert own_ids == {own_requisition.id}

        # 超管 / ALL 数据权限用户可以看到全部领料单
        admin_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/material-requisitions",
            params={"page": 1, "page_size": 50, "status": scope_marker},
            headers=_auth_headers(admin_token),
        )
        assert admin_resp.status_code == 200, admin_resp.text
        admin_ids = {item["id"] for item in admin_resp.json()["items"]}
        assert admin_ids == {own_requisition.id, other_requisition.id}

    def test_work_reports_data_scope_own_vs_all(
        self, client: TestClient, admin_token: str, normal_user_token: str, db
    ):
        """PERM-17: 报工记录列表按数据权限过滤（OWN 只见自己审核的，ALL/超管全见）。

        WorkReport.worker_id 关联的是工人档案（Worker.id），无法直接与
        current_user.id 比较，因此过滤配置以 approved_by（审核人）作为所有者字段。
        """
        if not admin_token or not normal_user_token:
            pytest.skip("Auth tokens not available")

        admin = _admin_user(db)
        normal_user = db.query(User).filter(User.username == "user").first()
        assert normal_user is not None and admin is not None
        suffix = uuid.uuid4().hex[:8]
        scope_marker = f"ST{suffix}"

        work_order = WorkOrder(
            work_order_no=f"WR-SCOPE-WO-{suffix}",
            task_name="数据权限测试工单",
            task_type="ASSEMBLY",
        )
        worker = Worker(
            worker_no=f"WR-SCOPE-WK-{suffix}",
            worker_name="数据权限测试工人",
        )
        db.add_all([work_order, worker])
        db.commit()
        db.refresh(work_order)
        db.refresh(worker)

        own_report = WorkReport(
            report_no=f"WR-OWN-{suffix}",
            work_order_id=work_order.id,
            worker_id=worker.id,
            report_type=scope_marker,
            report_time=datetime.now(),
            status="APPROVED",
            approved_by=normal_user.id,
        )
        other_report = WorkReport(
            report_no=f"WR-OTH-{suffix}",
            work_order_id=work_order.id,
            worker_id=worker.id,
            report_type=scope_marker,
            report_time=datetime.now(),
            status="APPROVED",
            approved_by=admin.id,
        )
        db.add_all([own_report, other_report])
        db.commit()
        db.refresh(own_report)
        db.refresh(other_report)

        own_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/work-reports",
            params={"page": 1, "page_size": 50, "report_type": scope_marker},
            headers=_auth_headers(normal_user_token),
        )
        assert own_resp.status_code == 200, own_resp.text
        own_ids = {item["id"] for item in own_resp.json()["items"]}
        assert own_ids == {own_report.id}

        admin_resp = client.get(
            f"{settings.API_V1_PREFIX}/production/work-reports",
            params={"page": 1, "page_size": 50, "report_type": scope_marker},
            headers=_auth_headers(admin_token),
        )
        assert admin_resp.status_code == 200, admin_resp.text
        admin_ids = {item["id"] for item in admin_resp.json()["items"]}
        assert admin_ids == {own_report.id, other_report.id}
