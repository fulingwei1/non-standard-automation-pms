# -*- coding: utf-8 -*-
"""Path-parameter read-only route regressions."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalNodeDefinition,
    ApprovalTemplate,
)
from app.models.after_sales import AfterSalesFeedback
from app.models.issue import Issue
from app.models.material_progress_subscription import MaterialProgressSubscription
from app.models.material import Material, MaterialSupplier
from app.models.organization import Department
from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.performance import (
    MonthlyWorkSummary,
    PerformanceAdjustmentHistory,
    PerformancePeriod,
    PerformanceResult,
)
from app.models.presale_ai_emotion_analysis import PresaleAIEmotionAnalysis
from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
from app.models.presale_emotion_trend import PresaleEmotionTrend
from app.models.presale import PresaleSupportTicket
from app.models.presale.technical_parameter_template import TechnicalParameterTemplate
from app.models.project import Project, ProjectDocument, ProjectTemplate, ProjectTemplateVersion
from app.models.production import (
    ProductionProgressLog,
    WorkOrder,
    Workstation,
    WorkstationStatus,
    Workshop,
)
from app.models.purchase import GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem
from app.models.project_risk import ProjectRisk
from app.models.qualification import EmployeeQualification, QualificationLevel
from app.models.sales.presale_ai_cost import PresaleAICostEstimation
from app.models.sales import (
    Contract,
    ContractTemplate,
    ContractTemplateVersion,
    Invoice,
    Opportunity,
    Quote,
    QuoteVersion,
    TechnicalAssessment,
)
from app.models.shortage.smart_alert import ShortageAlert, ShortageHandlingPlan
from app.models.stage_instance import NodeTask, ProjectNodeInstance, ProjectStageInstance
from app.models.user import User
from app.models.vendor import Vendor
from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
    AcceptanceReport,
    AcceptanceSignature,
)
from app.models.assembly_kit import BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail
from app.models.bonus import BonusCalculation, BonusRule
from app.models.ecn import Ecn
from app.models.management_rhythm import MeetingActionItem, StrategicMeeting
from app.models.material import BomHeader, BomItem
from app.models.strategy import (
    AnnualKeyWork,
    CSF,
    KPI,
    PersonalKPI,
    Strategy,
    StrategyComparison,
)
from app.models.task_center import TaskComment, TaskUnified


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def _first_project(db: Session) -> Project:
    return db.query(Project).first()


def test_department_users_route_uses_current_user_roles_relationship(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    department = Department(
        dept_code=f"PP-D-{suffix}",
        dept_name=f"路径参数部门-{suffix}",
        is_active=True,
    )
    db_session.add(department)
    db_session.flush()
    admin.department = department.dept_name
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/org/departments/{department.id}/users",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert response.json()["total"] >= 1


def test_template_versions_route_uses_release_notes_for_description(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    template = ProjectTemplate(
        template_code=f"PP-TPL-{suffix}",
        template_name="Path Param Template",
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(template)
    db_session.flush()
    version = ProjectTemplateVersion(
        template_id=template.id,
        version_no="V1",
        release_notes="版本说明",
        status="DRAFT",
        created_by=admin.id,
    )
    db_session.add(version)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/templates/{template.id}/versions",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["description"] == "版本说明"


def test_project_detail_members_and_status_history_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            UPDATE projects
            SET progress_pct = NULL,
                contract_amount = NULL,
                budget_amount = NULL,
                actual_cost = NULL,
                is_active = NULL,
                erp_synced = NULL,
                erp_sync_status = NULL,
                invoice_issued = NULL,
                final_payment_completed = NULL
            WHERE id = :project_id
            """
        ),
        {"project_id": project.id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO project_members (
                project_id,
                user_id,
                role_code,
                allocation_pct,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                :user_id,
                :role_code,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": project.id,
            "user_id": admin.id,
            "role_code": f"PP_MEMBER_{suffix}",
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO project_status_logs (
                project_id,
                old_stage,
                new_stage,
                old_status,
                new_status,
                change_type,
                change_reason,
                changed_by,
                changed_at
            )
            VALUES (
                :project_id,
                'S1',
                'S2',
                'ST01',
                'ST02',
                'STAGE_CHANGE',
                '路径参数回归',
                :user_id,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_id": project.id, "user_id": admin.id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    detail = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}",
        headers=headers,
        follow_redirects=False,
    )
    members = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/members/",
        headers=headers,
        follow_redirects=False,
    )
    history = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/status-history",
        headers=headers,
        follow_redirects=False,
    )

    assert detail.status_code == 200, detail.text
    assert members.status_code == 200, members.text
    assert history.status_code == 200, history.text


def test_project_payment_and_resource_plan_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO project_payment_plans (
                project_id,
                payment_no,
                payment_name,
                payment_type,
                planned_amount,
                planned_date,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                99,
                :payment_name,
                'ADVANCE',
                1000,
                CURRENT_DATE,
                'PENDING',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_id": project.id, "payment_name": f"路径参数收款-{suffix}"},
    )
    db_session.execute(
        text(
            """
            INSERT INTO project_stage_resource_plan (
                project_id,
                stage_code,
                role_code,
                role_name,
                headcount,
                allocation_pct,
                assignment_status,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                :stage_code,
                :role_code,
                'Legacy Role',
                NULL,
                NULL,
                NULL,
                :user_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": project.id,
            "stage_code": f"PROJ{suffix[:6].upper()}",
            "role_code": f"PP_ROLE_{suffix}",
            "user_id": admin.id,
        },
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    paths = [
        f"/projects/{project.id}/payment-plans",
        f"/projects/{project.id}/resource-plan/",
        f"/projects/{project.id}/resource-plan/utilization",
        f"/projects/{project.id}/resource-plan/summary",
    ]

    for path in paths:
        response = client.get(
            f"{settings.API_V1_PREFIX}{path}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_project_cost_and_evaluation_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO project_costs (
                project_id,
                cost_type,
                cost_category,
                amount,
                tax_amount,
                cost_date,
                description,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                NULL,
                NULL,
                100,
                NULL,
                NULL,
                :description,
                :user_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": project.id,
            "description": f"路径参数成本-{suffix}",
            "user_id": admin.id,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO project_evaluations (
                evaluation_code,
                project_id,
                novelty_score,
                new_tech_score,
                difficulty_score,
                workload_score,
                amount_score,
                total_score,
                evaluation_level,
                evaluator_id,
                evaluator_name,
                evaluation_date,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :code,
                :project_id,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                :user_id,
                '路径参数评价人',
                CURRENT_DATE,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "code": f"PP-EVAL-{suffix}",
            "project_id": project.id,
            "user_id": admin.id,
        },
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    costs = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/",
        headers=headers,
        follow_redirects=False,
    )
    evaluations = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/evaluations/",
        headers=headers,
        follow_redirects=False,
    )

    assert costs.status_code == 200, costs.text
    assert evaluations.status_code == 200, evaluations.text


def test_cost_prediction_detail_routes_tolerate_legacy_nulls_and_datetimes(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO cost_prediction (
                project_id,
                project_code,
                prediction_date,
                prediction_version,
                current_bac,
                current_ac,
                current_ev,
                predicted_eac,
                is_approved,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                NULL,
                CURRENT_DATE,
                :version,
                NULL,
                NULL,
                NULL,
                1000,
                NULL,
                :user_id,
                '2024-01-01 14:00:00',
                '2024-01-01 14:00:00'
            )
            """
        ),
        {
            "project_id": project.id,
            "version": f"PP-{suffix}",
            "user_id": admin.id,
        },
    )
    prediction_id = db_session.execute(
        text("SELECT id FROM cost_prediction WHERE prediction_version = :version"),
        {"version": f"PP-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO cost_optimization_suggestions (
                prediction_id,
                project_id,
                project_code,
                suggestion_code,
                suggestion_title,
                description,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                :prediction_id,
                :project_id,
                NULL,
                :code,
                '路径参数优化建议',
                '兼容历史日期',
                :user_id,
                '2024-01-01 14:00:00',
                '2024-01-01 14:00:00'
            )
            """
        ),
        {
            "prediction_id": prediction_id,
            "project_id": project.id,
            "code": f"PP-SUG-{suffix}",
            "user_id": admin.id,
        },
    )
    suggestion_id = db_session.execute(
        text("SELECT id FROM cost_optimization_suggestions WHERE suggestion_code = :code"),
        {"code": f"PP-SUG-{suffix}"},
    ).scalar_one()
    db_session.commit()

    headers = _auth_headers(admin_token)
    prediction = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/predictions/{prediction_id}",
        headers=headers,
        follow_redirects=False,
    )
    suggestion = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/suggestions/{suggestion_id}",
        headers=headers,
        follow_redirects=False,
    )

    assert prediction.status_code == 200, prediction.text
    assert suggestion.status_code == 200, suggestion.text


def test_cost_prediction_static_routes_are_not_shadowed_by_detail_route(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO cost_prediction (
                project_id,
                project_code,
                prediction_date,
                prediction_version,
                current_bac,
                current_ac,
                current_ev,
                predicted_eac,
                is_approved,
                created_by,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                NULL,
                CURRENT_DATE,
                :version,
                NULL,
                NULL,
                NULL,
                1000,
                NULL,
                :user_id,
                '2024-01-01 14:00:00',
                '2024-01-01 14:00:00'
            )
            """
        ),
        {
            "project_id": project.id,
            "version": f"PP-STATIC-{suffix}",
            "user_id": admin.id,
        },
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    latest = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/predictions/latest",
        headers=headers,
        follow_redirects=False,
    )
    history = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/predictions/history",
        headers=headers,
        follow_redirects=False,
    )

    assert latest.status_code == 200, latest.text
    assert history.status_code == 200, history.text
    assert isinstance(history.json(), list)


def test_project_overview_tolerates_missing_after_sales_tables(
    client: TestClient, admin_token: str, db_session: Session
):
    project = _first_project(db_session)
    bind = db_session.get_bind()

    AfterSalesFeedback.__table__.drop(bind=bind, checkfirst=True)
    db_session.commit()
    try:
        headers = _auth_headers(admin_token)
        overview = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project.id}/overview",
            headers=headers,
            follow_redirects=False,
        )
        after_sales = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project.id}/after-sales-status",
            headers=headers,
            follow_redirects=False,
        )
    finally:
        AfterSalesFeedback.__table__.create(bind=bind, checkfirst=True)
        db_session.commit()

    assert overview.status_code == 200, overview.text
    assert after_sales.status_code == 200, after_sales.text


def test_project_stage_routes_tolerate_legacy_null_defaults(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO project_stage_instances (
                project_id,
                stage_code,
                stage_name,
                sequence,
                status,
                category,
                is_milestone,
                is_parallel,
                progress,
                is_modified,
                review_required,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                :stage_code,
                :stage_name,
                99,
                'PENDING',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": project.id,
            "stage_code": f"PP-ST-{suffix}",
            "stage_name": "路径参数阶段",
        },
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/stages/",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    item = next(
        row for row in response.json() if row["stage_code"] == f"PP-ST-{suffix}"
    )
    assert item["category"] == "execution"
    assert item["is_milestone"] is False
    assert item["is_parallel"] is False
    assert item["progress"] == 0


def test_project_risk_and_material_subscription_routes_tolerate_missing_tables(
    client: TestClient, admin_token: str, db_session: Session
):
    project = _first_project(db_session)
    bind = db_session.get_bind()

    ProjectRisk.__table__.drop(bind=bind, checkfirst=True)
    MaterialProgressSubscription.__table__.drop(bind=bind, checkfirst=True)
    db_session.commit()
    try:
        headers = _auth_headers(admin_token)
        routes = [
            f"/projects/{project.id}/risks",
            f"/projects/{project.id}/risk-matrix",
            f"/projects/{project.id}/risk-summary",
            f"/projects/{project.id}/material-progress/subscribe",
        ]
        responses = [
            client.get(
                f"{settings.API_V1_PREFIX}{path}",
                headers=headers,
                follow_redirects=False,
            )
            for path in routes
        ]
        detail = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project.id}/risks/1",
            headers=headers,
            follow_redirects=False,
        )
    finally:
        ProjectRisk.__table__.create(bind=bind, checkfirst=True)
        MaterialProgressSubscription.__table__.create(bind=bind, checkfirst=True)
        db_session.commit()

    for response in responses:
        assert response.status_code == 200, response.text
    assert detail.status_code == 404, detail.text
    assert responses[-1].json()["data"]["subscribed"] is False


def test_project_change_routes_tolerate_legacy_nulls_and_old_decisions(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    db_session.execute(
        text(
            """
            INSERT INTO change_requests (
                change_code,
                project_id,
                title,
                change_type,
                change_source,
                submitter_id,
                submitter_name,
                status,
                approval_decision,
                notify_customer,
                notify_team,
                created_at,
                updated_at
            )
            VALUES (
                :code,
                :project_id,
                '路径参数变更',
                'REQUIREMENT',
                'CUSTOMER',
                :user_id,
                '系统管理员',
                'SUBMITTED',
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"code": f"PP-CHG-{suffix}", "project_id": project.id, "user_id": admin.id},
    )
    change_id = db_session.execute(
        text("SELECT id FROM change_requests WHERE change_code = :code"),
        {"code": f"PP-CHG-{suffix}"},
    ).scalar_one()
    template_flow = db_session.execute(
        text(
            """
            SELECT t.id AS template_id, f.id AS flow_id
            FROM approval_templates t
            JOIN approval_flow_definitions f ON f.template_id = t.id
            WHERE t.template_code = 'TPL_PROJECT'
            ORDER BY COALESCE(f.is_default, 0) DESC, f.id
            LIMIT 1
            """
        )
    ).mappings().one()
    db_session.execute(
        text(
            """
            INSERT INTO approval_instances (
                instance_no,
                template_id,
                flow_id,
                entity_type,
                entity_id,
                initiator_id,
                initiator_name,
                form_data,
                status,
                title,
                submitted_at,
                created_at,
                updated_at
            )
            VALUES (
                :instance_no,
                :template_id,
                :flow_id,
                'PROJECT_CHANGE_REQUEST',
                :change_id,
                :user_id,
                '系统管理员',
                '{"source":"path_param_contract_test"}',
                'PENDING',
                '路径参数变更审批',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "instance_no": f"PP-CHG-AP-{suffix}",
            "template_id": template_flow["template_id"],
            "flow_id": template_flow["flow_id"],
            "change_id": change_id,
            "user_id": admin.id,
        },
    )
    instance_id = db_session.execute(
        text("SELECT id FROM approval_instances WHERE instance_no = :instance_no"),
        {"instance_no": f"PP-CHG-AP-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO approval_action_logs (
                instance_id,
                operator_id,
                operator_name,
                action,
                action_detail,
                action_at,
                created_at,
                updated_at
            )
            VALUES (
                :instance_id,
                :user_id,
                '系统管理员',
                'COMMENT',
                '{"source":"path_param_contract_test","decision":"ch230356"}',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"instance_id": instance_id, "user_id": admin.id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    detail = client.get(
        f"{settings.API_V1_PREFIX}/projects/changes/{change_id}",
        headers=headers,
        follow_redirects=False,
    )
    approvals = client.get(
        f"{settings.API_V1_PREFIX}/projects/changes/{change_id}/approvals",
        headers=headers,
        follow_redirects=False,
    )

    assert detail.status_code == 200, detail.text
    assert approvals.status_code == 200, approvals.text


def test_production_progress_routes_tolerate_legacy_nulls_and_overflow_progress(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)

    workshop = Workshop(
        workshop_code=f"PP-WSH-{suffix}",
        workshop_name="路径参数车间",
        workshop_type="ASSEMBLY",
        is_active=True,
    )
    db_session.add(workshop)
    db_session.flush()
    workstation = Workstation(
        workstation_code=f"PP-WST-{suffix}",
        workstation_name="路径参数工位",
        workshop_id=workshop.id,
        status="IDLE",
        is_active=True,
    )
    db_session.add(workstation)
    db_session.flush()
    work_order = WorkOrder(
        work_order_no=f"PP-WO-{suffix}",
        task_name="路径参数工单",
        task_type="OTHER",
        workshop_id=workshop.id,
        workstation_id=workstation.id,
        status="IN_PROGRESS",
        priority="NORMAL",
        progress=None,
    )
    db_session.add(work_order)
    db_session.flush()
    log = ProductionProgressLog(
        work_order_id=work_order.id,
        workstation_id=workstation.id,
        current_progress=135,
        status="IN_PROGRESS",
        logged_at=datetime.utcnow(),
        logged_by=admin.id,
    )
    db_session.add(log)
    db_session.flush()
    db_session.execute(
        text(
            """
            INSERT INTO workstation_status (
                workstation_id,
                current_state,
                current_progress,
                completed_qty_today,
                target_qty_today,
                capacity_utilization,
                work_hours_today,
                idle_hours_today,
                planned_hours_today,
                quality_rate,
                is_bottleneck,
                bottleneck_level,
                alert_count,
                status_updated_at,
                created_at,
                updated_at
            )
            VALUES (
                :workstation_id,
                'IDLE',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"workstation_id": workstation.id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    timeline = client.get(
        f"{settings.API_V1_PREFIX}/production/progress/work-orders/{work_order.id}/timeline",
        headers=headers,
        follow_redirects=False,
    )
    realtime = client.get(
        f"{settings.API_V1_PREFIX}/production/progress/workstations/{workstation.id}/realtime",
        headers=headers,
        follow_redirects=False,
    )

    assert timeline.status_code == 200, timeline.text
    assert realtime.status_code == 200, realtime.text
    assert timeline.json()["current_progress"] == 0
    assert timeline.json()["timeline"][0]["current_progress"] == 100


def test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)

    opportunity = Opportunity(
        opp_code=f"PP-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="路径参数商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()
    contract = Contract(
        contract_code=f"PP-CON-{suffix}",
        contract_name="路径参数合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=Decimal("1000"),
        received_amount=None,
        status="draft",
    )
    db_session.add(contract)
    db_session.flush()
    invoice = Invoice(
        invoice_code=f"PP-INV-{suffix}",
        contract_id=contract.id,
        amount=Decimal("1000"),
        status="DRAFT",
    )
    db_session.add(invoice)
    quote = Quote(
        quote_code=f"PP-Q-{suffix[:6]}",
        opportunity_id=opportunity.id,
        customer_id=project.customer_id,
        owner_id=admin.id,
    )
    db_session.add(quote)
    db_session.flush()
    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("1000"),
        cost_total=Decimal("600"),
        gross_margin=Decimal("40"),
        created_by=admin.id,
    )
    db_session.add(version)
    db_session.flush()
    quote.current_version_id = version.id
    assessment = TechnicalAssessment(
        source_type="OPPORTUNITY",
        source_id=opportunity.id,
        evaluator_id=admin.id,
        status=None,
        veto_triggered=None,
    )
    db_session.add(assessment)
    db_session.commit()

    headers = _auth_headers(admin_token)
    contract_response = client.get(
        f"{settings.API_V1_PREFIX}/sales/enhanced/{contract.id}",
        headers=headers,
        follow_redirects=False,
    )
    invoice_status = client.get(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval-status",
        headers=headers,
        follow_redirects=False,
    )
    invoice_history = client.get(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval-history",
        headers=headers,
        follow_redirects=False,
    )
    assessment_response = client.get(
        f"{settings.API_V1_PREFIX}/sales/assessments/{assessment.id}",
        headers=headers,
        follow_redirects=False,
    )
    export_response = client.get(
        f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/export/excel",
        headers=headers,
        follow_redirects=False,
    )

    assert contract_response.status_code == 200, contract_response.text
    assert Decimal(str(contract_response.json()["received_amount"])) == Decimal("0")
    assert invoice_status.status_code == 200, invoice_status.text
    assert invoice_history.status_code == 200, invoice_history.text
    assert assessment_response.status_code == 200, assessment_response.text
    assert assessment_response.json()["status"] == "PENDING"
    assert assessment_response.json()["veto_triggered"] is False
    assert export_response.status_code == 200, export_response.text
    assert "filename*" in export_response.headers["content-disposition"]


def test_sales_template_flow_and_contract_template_apply_routes_match_response_models(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)

    approval_template = ApprovalTemplate(
        template_code=f"PP-AP-TPL-{suffix}",
        template_name="路径参数审批模板",
        category="SALES",
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(approval_template)
    db_session.flush()
    flow = ApprovalFlowDefinition(
        template_id=approval_template.id,
        flow_name="路径参数审批流",
        is_default=True,
        version=1,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()
    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_name="路径参数节点",
        node_order=1,
        node_type="APPROVAL",
        can_delegate=None,
        is_active=True,
    )
    db_session.add(node)

    contract_template = ContractTemplate(
        template_code=f"PP-CT-{suffix}",
        template_name="路径参数合同模板",
        contract_type="sales",
        status="ACTIVE",
        visibility_scope="TEAM",
        owner_id=admin.id,
    )
    db_session.add(contract_template)
    db_session.flush()
    template_version = ContractTemplateVersion(
        template_id=contract_template.id,
        version_no="V1",
        status="PUBLISHED",
        clause_sections={"sections": []},
        created_by=admin.id,
    )
    db_session.add(template_version)
    db_session.flush()
    contract_template.current_version_id = template_version.id
    db_session.commit()

    headers = _auth_headers(admin_token)
    flows = client.get(
        f"{settings.API_V1_PREFIX}/sales/templates/{approval_template.id}/flows",
        headers=headers,
        follow_redirects=False,
    )
    apply_template = client.get(
        f"{settings.API_V1_PREFIX}/sales/contract-templates/{contract_template.id}/apply",
        headers=headers,
        follow_redirects=False,
    )

    assert flows.status_code == 200, flows.text
    assert flows.json()[0]["nodes"][0]["can_delegate"] is True
    assert apply_template.status_code == 200, apply_template.text
    payload = apply_template.json()
    assert payload["success"] is True
    assert payload["template_id"] == contract_template.id
    assert payload["version_id"] == template_version.id


def test_supplier_materials_route_serializes_material_rows(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    supplier = Vendor(
        supplier_code=f"PP-V-{suffix}",
        supplier_name="路径参数供应商",
        vendor_type="MATERIAL",
        created_by=admin.id,
    )
    material = Material(
        material_code=f"PP-M-{suffix}",
        material_name="路径参数物料",
        created_by=admin.id,
    )
    db_session.add_all([supplier, material])
    db_session.flush()
    db_session.add(MaterialSupplier(material_id=material.id, supplier_id=supplier.id))
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/suppliers/{supplier.id}/materials",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["items"][0]["id"] == material.id
    assert payload["items"][0]["material_code"] == material.material_code


def test_shortage_handling_solutions_tolerate_legacy_null_scores(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)
    material = Material(
        material_code=f"PP-SHORT-{suffix}",
        material_name="路径参数缺料物料",
        created_by=admin.id,
    )
    db_session.add(material)
    db_session.flush()
    alert = ShortageAlert(
        alert_no=f"PP-ALERT-{suffix}",
        project_id=project.id,
        material_id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        required_qty=Decimal("10"),
        available_qty=Decimal("0"),
        shortage_qty=Decimal("10"),
        alert_level="CRITICAL",
        alert_date=date.today(),
        created_by=admin.id,
    )
    db_session.add(alert)
    db_session.flush()
    plan = ShortageHandlingPlan(
        plan_no=f"PP-PLAN-{suffix}",
        alert_id=alert.id,
        solution_type="URGENT_PURCHASE",
        solution_name="紧急采购",
        ai_score=None,
        feasibility_score=None,
        cost_score=None,
        time_score=None,
        risk_score=None,
        is_recommended=None,
        recommendation_rank=None,
        status=None,
        created_by=admin.id,
    )
    db_session.add(plan)
    db_session.commit()

    headers = _auth_headers(admin_token)
    for prefix in ("shortage/smart", "shortage/smart-alerts"):
        response = client.get(
            f"{settings.API_V1_PREFIX}/{prefix}/alerts/{alert.id}/solutions",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text
        item = response.json()["items"][0]
        assert Decimal(str(item["ai_score"])) == Decimal("0")
        assert item["is_recommended"] is False
        assert item["recommendation_rank"] == 999
        assert item["status"] == "PENDING"


def test_presale_templates_and_ai_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    ticket = PresaleSupportTicket(
        ticket_no=f"PP-TICKET-{suffix}",
        title="路径参数售前工单",
        ticket_type="TECH_SUPPORT",
        applicant_id=admin.id,
        applicant_name=admin.username,
    )
    template = TechnicalParameterTemplate(
        name="路径参数技术参数模板",
        code=f"PP-TP-{suffix}",
        industry="ATE",
        test_type="FAT",
        reference_docs=[{"name": "客户需求澄清", "type": "checklist"}],
        sample_images=[{"name": "FAT/SAT 验收", "type": "acceptance"}],
        created_by=admin.id,
    )
    cost = PresaleAICostEstimation(
        presale_ticket_id=1,
        hardware_cost=None,
        software_cost=None,
        installation_cost=None,
        service_cost=None,
        risk_reserve=None,
        total_cost=Decimal("0"),
        created_by=admin.id,
    )
    # 2026-07-03 去重：老AI方案栈 /presale/ai/solution/{id} 已下线（方案统一走 /presale/proposals）
    db_session.add_all([ticket, template, cost])
    db_session.flush()
    analysis = PresaleAIEmotionAnalysis(
        presale_ticket_id=ticket.id,
        customer_id=1,
        sentiment=None,
        purchase_intent_score=None,
        churn_risk=None,
        emotion_factors=None,
        analysis_result=None,
    )
    trend = PresaleEmotionTrend(
        presale_ticket_id=ticket.id,
        customer_id=1,
        trend_data=None,
        key_turning_points=None,
    )
    db_session.add_all([analysis, trend])
    db_session.commit()

    headers = _auth_headers(admin_token)
    template_response = client.get(
        f"{settings.API_V1_PREFIX}/presale/technical-parameters/templates/{template.id}",
        headers=headers,
        follow_redirects=False,
    )
    cost_response = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/cost-estimation/{cost.id}",
        headers=headers,
        follow_redirects=False,
    )
    emotion_response = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/emotion-analysis/{ticket.id}",
        headers=headers,
        follow_redirects=False,
    )
    trend_response = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/emotion-trend/{ticket.id}",
        headers=headers,
        follow_redirects=False,
    )

    assert template_response.status_code == 200, template_response.text
    assert template_response.json()["reference_docs"][0]["type"] == "checklist"
    assert cost_response.status_code == 200, cost_response.text
    assert cost_response.json()["cost_breakdown"]["hardware_cost"] == "0"
    assert emotion_response.status_code == 200, emotion_response.text
    assert emotion_response.json()["sentiment"] == "neutral"
    assert trend_response.status_code == 200, trend_response.text
    assert trend_response.json()["trend_data"] == []


def test_presale_quotation_and_win_rate_routes_handle_legacy_records(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    db_session.execute(
        text(
            """
            INSERT INTO presale_ai_quotation (
                presale_ticket_id,
                quotation_number,
                quotation_type,
                items,
                subtotal,
                tax,
                discount,
                total,
                validity_days,
                status,
                version,
                created_by,
                created_at
            )
            VALUES (
                :ticket_id,
                :quotation_number,
                'NORMAL',
                '{"table":"presale_ai_quotation","column":"items"}',
                0,
                0,
                0,
                0,
                30,
                'DRAFT',
                1,
                :created_by,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "ticket_id": 991001,
            "quotation_number": f"PP-QT-{suffix}",
            "created_by": admin.id,
        },
    )
    quotation_id = db_session.execute(text("SELECT last_insert_rowid()")).scalar_one()
    db_session.commit()

    # 2026-07-03 去重：/presale/ai/win-rate|influencing-factors|improvement-suggestions
    # 随异步老栈 presale_ai_win_rate.py 下线，赢率统一走 /presales/predict-win-rate
    headers = _auth_headers(admin_token)
    quotation = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/quotation/{quotation_id}",
        headers=headers,
        follow_redirects=False,
    )
    empty_history = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/quotation-history/991003",
        headers=headers,
        follow_redirects=False,
    )

    assert quotation.status_code == 200, quotation.text
    assert quotation.json()["quotation_type"] == "standard"
    assert quotation.json()["items"] == []
    assert empty_history.status_code == 200, empty_history.text
    assert empty_history.json()["quotation_id"] is None


def test_acceptance_and_node_task_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)
    order = AcceptanceOrder(
        order_no=f"PP-ACC-{suffix}",
        project_id=project.id,
        acceptance_type="FAT",
        status="COMPLETED",
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()
    item = AcceptanceOrderItem(
        order_id=order.id,
        category_code="CAT",
        category_name="分类",
        item_code="ITEM",
        item_name="检查项",
        is_required=None,
        is_key_item=None,
        result_status=None,
    )
    issue = AcceptanceIssue(
        issue_no=f"PP-ISSUE-{suffix}",
        order_id=order.id,
        issue_type="DEFECT",
        severity="MAJOR",
        title="问题",
        description="描述",
        status=None,
        is_blocking=None,
    )
    signature = AcceptanceSignature(
        order_id=order.id,
        signer_type="QA",
        signer_name="QA",
        signed_at=None,
    )
    report = AcceptanceReport(
        order_id=order.id,
        report_no=f"PP-RPT-{suffix}",
        report_type="FAT",
        version=None,
        generated_by=admin.id,
    )
    stage = ProjectStageInstance(
        project_id=project.id,
        stage_code=f"PP-ST-{suffix[:6]}",
        stage_name="路径参数阶段",
        sequence=1,
    )
    db_session.add(stage)
    db_session.flush()
    node = ProjectNodeInstance(
        project_id=project.id,
        stage_instance_id=stage.id,
        node_code=f"N{suffix[:6]}",
        node_name="路径参数节点",
        sequence=1,
    )
    db_session.add(node)
    db_session.flush()
    task = NodeTask(
        node_instance_id=node.id,
        task_code=f"T{suffix[:6]}",
        task_name="路径参数任务",
        sequence=1,
        status="PENDING",
        priority=None,
    )
    db_session.add_all([item, issue, signature, report, task])
    db_session.flush()
    db_session.execute(
        text("UPDATE acceptance_reports SET version = NULL WHERE id = :report_id"),
        {"report_id": report.id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    items = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-orders/{order.id}/items",
        headers=headers,
        follow_redirects=False,
    )
    issue_detail = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-issues/{issue.id}",
        headers=headers,
        follow_redirects=False,
    )
    issue_list = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-orders/{order.id}/issues",
        headers=headers,
        follow_redirects=False,
    )
    signatures = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-orders/{order.id}/signatures",
        headers=headers,
        follow_redirects=False,
    )
    reports = client.get(
        f"{settings.API_V1_PREFIX}/acceptance-orders/{order.id}/report",
        headers=headers,
        follow_redirects=False,
    )
    task_response = client.get(
        f"{settings.API_V1_PREFIX}/node-tasks/{task.id}",
        headers=headers,
        follow_redirects=False,
    )

    assert items.status_code == 200, items.text
    assert items.json()[0]["is_required"] is True
    assert issue_detail.status_code == 200, issue_detail.text
    assert issue_detail.json()["status"] == "OPEN"
    assert issue_detail.json()["is_blocking"] is False
    assert issue_list.status_code == 200, issue_list.text
    assert signatures.status_code == 200, signatures.text
    assert signatures.json()[0]["signed_at"] is not None
    assert reports.status_code == 200, reports.text
    assert reports.json()[0]["version"] == 1
    assert task_response.status_code == 200, task_response.text
    assert task_response.json()["priority"] == "NORMAL"


def test_authenticated_path_param_routes_tolerate_legacy_aliases_and_json_text(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    project = _first_project(db_session)
    admin = _admin_user(db_session)
    department = Department(
        dept_code=f"PP-B4-D-{suffix}",
        dept_name="第4批兼容部门",
        is_active=True,
    )
    db_session.add(department)
    db_session.flush()
    db_session.add(
        Issue(
            issue_no=f"PP-B4-I-{suffix}",
            category="PROJECT",
            project_id=project.id,
            issue_type="QUALITY",
            severity="HIGH",
            priority="HIGH",
            title="路径参数问题",
            description="兼容 JSON 字符串标签",
            reporter_id=admin.id,
            reporter_name=admin.display_name,
            report_date=datetime.now(),
            status="OPEN",
            tags='["legacy-tag","capacity_shortage"]',
            attachments=None,
        )
    )
    project.progress_pct = Decimal("42")
    db_session.commit()

    headers = _auth_headers(admin_token)
    project_issues = client.get(
        f"{settings.API_V1_PREFIX}/issues/projects/{project.id}/issues",
        headers=headers,
        follow_redirects=False,
    )
    team = client.get(
        f"{settings.API_V1_PREFIX}/performance/team/team/{department.id}",
        headers=headers,
        follow_redirects=False,
    )
    department_perf = client.get(
        f"{settings.API_V1_PREFIX}/performance/team/department/{department.id}",
        headers=headers,
        follow_redirects=False,
    )
    project_progress = client.get(
        f"{settings.API_V1_PREFIX}/performance/project/project/{project.id}/progress",
        headers=headers,
        follow_redirects=False,
    )

    assert project_issues.status_code == 200, project_issues.text
    assert project_issues.json()["items"][0]["tags"] == ["legacy-tag", "capacity_shortage"]
    assert team.status_code == 200, team.text
    assert department_perf.status_code == 200, department_perf.text
    assert project_progress.status_code == 200, project_progress.text


def test_engineer_performance_path_routes_tolerate_missing_optional_data(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    period = PerformancePeriod(
        period_code=f"PP-B4-P-{suffix}",
        period_name="第4批绩效周期",
        period_type="MONTHLY",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status="FINALIZED",
        is_active=True,
    )
    db_session.add(period)
    db_session.flush()
    result = PerformanceResult(
        period_id=period.id,
        user_id=admin.id,
        user_name=admin.display_name,
        total_score=Decimal("80"),
        level="A",
    )
    db_session.add(result)
    db_session.flush()
    db_session.add(
        PerformanceAdjustmentHistory(
            result_id=result.id,
            original_total_score=Decimal("75"),
            adjusted_total_score=Decimal("80"),
            adjustment_reason="路径参数回归调整",
            adjusted_by=admin.id,
            adjusted_by_name=None,
        )
    )
    summary = MonthlyWorkSummary(
        employee_id=admin.id,
        period="2026-01",
        work_content="本月完成路径参数回归",
        self_evaluation="自评正常",
        status="SUBMITTED",
    )
    db_session.add(summary)
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/engineer-performance/manager-evaluation/adjustment-history/{result.id}",
        f"/engineer-performance/data-integrity/suggest-fixes/{admin.id}?period_id={period.id}",
        f"/engineer-performance/feedback/message/{admin.id}?period_id={period.id}",
        f"/engineer-performance/solution/{admin.id}/score?period_id={period.id}",
        f"/performance/new/manager/evaluation/{summary.id}",
    ]

    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_strategy_path_routes_tolerate_legacy_model_field_drift(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    project = _first_project(db_session)
    strategy = Strategy(
        code=f"PP-B4-S-{suffix}",
        name="第4批战略",
        year=2026,
        status="ACTIVE",
        created_by=admin.id,
        is_active=True,
    )
    db_session.add(strategy)
    db_session.flush()
    csf = CSF(
        strategy_id=strategy.id,
        dimension="FINANCIAL",
        code=f"PP-B4-CSF-{suffix}",
        name="第4批关键成功要素",
        owner_dept_id=admin.department_id,
        owner_user_id=admin.id,
        is_active=True,
    )
    db_session.add(csf)
    db_session.flush()
    kpi = KPI(
        csf_id=csf.id,
        code=f"PP-B4-KPI-{suffix}",
        name="第4批 KPI",
        ipooc_type="OUTPUT",
        target_value=Decimal("100"),
        current_value=Decimal("50"),
        weight=Decimal("20"),
        owner_user_id=admin.id,
        is_active=True,
    )
    work = AnnualKeyWork(
        csf_id=csf.id,
        code=f"PP-B4-WORK-{suffix}",
        name="第4批年度重点工作",
        year=2026,
        owner_user_id=admin.id,
        progress_percent=20,
        is_active=True,
    )
    personal = PersonalKPI(
        employee_id=admin.id,
        year=2026,
        source_type="CSF_KPI",
        source_id=kpi.id,
        kpi_name="第4批个人 KPI",
        status="PENDING",
    )
    comparison = StrategyComparison(
        current_strategy_id=strategy.id,
        current_year=2026,
        generated_date=date.today(),
        generated_by=admin.id,
        is_active=True,
    )
    db_session.add_all([kpi, work, personal, comparison])
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/strategy/csfs/{csf.id}",
        f"/strategy/kpis/{kpi.id}",
        f"/strategy/kpis/{kpi.id}/with-history",
        f"/strategy/annual-works/{work.id}",
        f"/strategy/annual-works/{work.id}/linked-projects",
        f"/strategy/decomposition/trace/{personal.id}",
        f"/strategy/health/{strategy.id}",
        f"/strategy/routine/{strategy.id}",
        f"/strategy/comparisons/{comparison.id}",
        f"/strategy/dashboard/overview/{strategy.id}",
        f"/strategy/dashboard/execution-status/{strategy.id}",
    ]
    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_outsourcing_task_qualification_and_document_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    project = _first_project(db_session)
    vendor = Vendor(
        supplier_code=f"PP-B4-OSV-{suffix}",
        supplier_name="第4批外协商",
        vendor_type="OUTSOURCING",
        created_by=admin.id,
    )
    db_session.add(vendor)
    db_session.flush()
    order = OutsourcingOrder(
        order_no=f"PP-B4-OS-{suffix}",
        vendor_id=vendor.id,
        project_id=project.id,
        order_type="MACHINING",
        order_title="第4批外协订单",
        total_amount=Decimal("0"),
        amount_with_tax=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(order)
    db_session.flush()
    item = OutsourcingOrderItem(
        order_id=order.id,
        item_no=1,
        material_code="PP-B4-MAT",
        material_name="第4批物料",
        unit=None,
        quantity=Decimal("1"),
        unit_price=None,
        amount=None,
        material_provided=None,
        status=None,
    )
    task = TaskUnified(
        task_code=f"PP-B4-TASK-{suffix}",
        title="第4批任务",
        task_type="PERSONAL",
        assignee_id=admin.id,
        status="PENDING",
        priority="MEDIUM",
    )
    db_session.add_all([item, task])
    db_session.flush()
    comment = TaskComment(
        task_id=task.id,
        content="第4批评论",
        comment_type=None,
        commenter_id=None,
        commenter_name=None,
        mentioned_users=None,
        created_at=None,
    )
    level = QualificationLevel(
        level_code=f"PPB4{suffix[:6].upper()}",
        level_name="第4批等级",
        level_order=99,
        is_active=None,
    )
    db_session.add(level)
    db_session.flush()
    qualification = EmployeeQualification(
        employee_id=admin.employee_id,
        position_type="ENGINEER",
        current_level_id=level.id,
        status=None,
    )
    document = ProjectDocument(
        project_id=project.id,
        doc_type="TECH",
        doc_name=f"第4批文档-{suffix}",
        doc_no=f"PP-B4-DOC-{suffix}",
        version=None,
        file_path="legacy/null-version.txt",
        file_name="legacy/null-version.txt",
        uploaded_by=admin.id,
    )
    db_session.add_all([comment, qualification, document])
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/outsourcing-orders/{order.id}",
        f"/outsourcing-orders/{order.id}/items",
        f"/outsourcing-orders/{order.id}/print",
        f"/task-center/tasks/{task.id}/comments",
        f"/qualifications/employees/{admin.employee_id}",
        f"/documents/{document.id}/versions",
    ]
    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_ecn_state_machine_routes_tolerate_null_legacy_status(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    project = _first_project(db_session)
    ecn = Ecn(
        ecn_no=f"PP-B5-ECN-{suffix}",
        ecn_title="第5批 ECN",
        ecn_type="DESIGN",
        source_type="PROJECT",
        source_id=project.id,
        project_id=project.id,
        change_reason="路径参数回归",
        change_description="兼容旧库空状态",
        status=None,
        applicant_id=admin.id,
    )
    db_session.add(ecn)
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/ecn/state-machine/{ecn.id}/state",
        f"/ecn/state-machine/{ecn.id}/allowed-transitions",
        f"/ecn/state-machine/{ecn.id}/health",
    ]
    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_assembly_kit_path_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    project = _first_project(db_session)
    bom = BomHeader(
        bom_no=f"PP-B5-BOM-{suffix}",
        bom_name="第5批 BOM",
        project_id=project.id,
        status="DRAFT",
        created_by=admin.id,
    )
    db_session.add(bom)
    db_session.flush()
    bom_item = BomItem(
        bom_id=bom.id,
        item_no=1,
        material_code=f"PP-B5-MAT-{suffix}",
        material_name="第5批物料",
        quantity=Decimal("1"),
    )
    db_session.add(bom_item)
    db_session.flush()
    attrs = BomItemAssemblyAttrs(
        bom_item_id=bom_item.id,
        bom_id=bom.id,
        assembly_stage="S1",
        importance_level=None,
        is_blocking=None,
        can_postpone=None,
        has_substitute=None,
        stage_order=None,
        created_by=admin.id,
    )
    readiness = MaterialReadiness(
        readiness_no=f"PP-B5-RD-{suffix}",
        project_id=project.id,
        bom_id=None,
        overall_kit_rate=None,
        blocking_kit_rate=None,
        can_start=None,
        analysis_time=datetime.now(),
        analyzed_by=admin.id,
    )
    db_session.add_all([attrs, readiness])
    db_session.flush()
    shortage = ShortageDetail(
        readiness_id=readiness.id,
        bom_item_id=bom_item.id,
        material_id=None,
        material_code=bom_item.material_code,
        material_name=bom_item.material_name,
        assembly_stage="S1",
        is_blocking=None,
        required_qty=Decimal("1"),
        stock_qty=None,
        allocated_qty=None,
        in_transit_qty=None,
        available_qty=None,
        shortage_qty=None,
        shortage_rate=None,
        alert_level=None,
    )
    db_session.add(shortage)
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/assembly-kit/bom-attributes/bom/{bom.id}/assembly-attrs",
        f"/assembly-kit/analysis/{readiness.id}",
    ]
    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_management_rhythm_routes_tolerate_legacy_action_item_values(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    meeting = StrategicMeeting(
        rhythm_level="STRATEGIC",
        cycle_type="MONTHLY",
        meeting_name="第5批战略会议",
        meeting_type="经营分析会",
        meeting_date=date(2026, 1, 1),
        organizer_id=admin.id,
        organizer_name=admin.display_name,
        attendees=[],
        strategic_context={},
        strategic_structure={},
        status="SCHEDULED",
        created_by=admin.id,
    )
    db_session.add(meeting)
    db_session.flush()
    action_item = MeetingActionItem(
        meeting_id=meeting.id,
        action_description="第5批行动项",
        owner_id=admin.id,
        owner_name=admin.display_name,
        due_date=date(2026, 1, 31),
        status=None,
        priority=None,
        created_by=admin.id,
    )
    db_session.add(action_item)
    db_session.commit()

    headers = _auth_headers(admin_token)
    routes = [
        f"/management-rhythm/meetings/strategic-meetings/{meeting.id}",
        f"/management-rhythm/action-items/strategic-meetings/{meeting.id}/action-items",
    ]
    for route in routes:
        response = client.get(
            f"{settings.API_V1_PREFIX}{route}",
            headers=headers,
            follow_redirects=False,
        )
        assert response.status_code == 200, response.text


def test_material_demand_lead_time_forecast_uses_current_purchase_order_fields(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    vendor = Vendor(
        supplier_code=f"PP-B6-V-{suffix}",
        supplier_name="第6批供应商",
        vendor_type="MATERIAL",
    )
    material = Material(
        material_code=f"PP-B6-MAT-{suffix}",
        material_name="第6批预测物料",
        lead_time_days=12,
    )
    db_session.add_all([vendor, material])
    db_session.flush()
    purchase_order = PurchaseOrder(
        order_no=f"PP-B6-PO-{suffix}",
        supplier_id=vendor.id,
        status="APPROVED",
        created_at=datetime(2026, 1, 1),
    )
    db_session.add(purchase_order)
    db_session.flush()
    order_item = PurchaseOrderItem(
        order_id=purchase_order.id,
        item_no=1,
        material_id=material.id,
        material_code=material.material_code,
        material_name=material.material_name,
        quantity=Decimal("1"),
    )
    db_session.add(order_item)
    db_session.flush()
    receipt = GoodsReceipt(
        receipt_no=f"PP-B6-GR-{suffix}",
        order_id=purchase_order.id,
        supplier_id=vendor.id,
        receipt_date=date(2026, 1, 10),
        status="APPROVED",
    )
    db_session.add(receipt)
    db_session.flush()
    receipt_item = GoodsReceiptItem(
        receipt_id=receipt.id,
        order_item_id=order_item.id,
        material_code=material.material_code,
        material_name=material.material_name,
        delivery_qty=Decimal("1"),
        received_qty=Decimal("1"),
    )
    db_session.add(receipt_item)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/material-demands/materials/{material.id}/lead-time-forecast?days=365",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["historical_count"] == 1
    assert data["forecast_avg_lead_time"] == 9


def test_presale_ai_analysis_route_tolerates_legacy_null_status_fields(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    ticket = PresaleSupportTicket(
        ticket_no=f"PP-B6-T-{suffix}",
        title="第6批售前需求",
        ticket_type="TECHNICAL",
        applicant_id=admin.id,
        applicant_name=admin.display_name,
    )
    db_session.add(ticket)
    db_session.flush()
    analysis = PresaleAIRequirementAnalysis(
        presale_ticket_id=ticket.id,
        raw_requirement="需要自动化产线方案",
        status=None,
        is_refined=None,
        refinement_count=None,
    )
    db_session.add(analysis)
    db_session.flush()
    analysis_id = analysis.id
    db_session.commit()
    db_session.execute(
        text(
            """
            UPDATE presale_ai_requirement_analysis
            SET status = NULL, is_refined = NULL, refinement_count = NULL
            WHERE id = :analysis_id
            """
        ),
        {"analysis_id": analysis_id},
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/analysis/{analysis_id}",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "draft"
    assert data["is_refined"] is False
    assert data["refinement_count"] == 0


def test_project_workspace_bonus_route_uses_current_distribution_date_field(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    project = _first_project(db_session)
    rule = BonusRule(
        rule_code=f"PP-B6-R-{suffix}",
        rule_name="第6批奖金规则",
        bonus_type="PROJECT",
    )
    db_session.add(rule)
    db_session.flush()
    calculation = BonusCalculation(
        calculation_code=f"PP-B6-C-{suffix}",
        rule_id=rule.id,
        project_id=project.id,
        user_id=admin.id,
        calculated_amount=Decimal("1000"),
        status="CALCULATED",
    )
    db_session.add(calculation)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/project-workspace/projects/{project.id}/bonuses",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["statistics"]["calculation_count"] >= 1


def test_sales_region_attachment_download_placeholder_is_not_a_server_error(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales-regions/enhanced/attachments/999999/download",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 404, response.text


def test_cost_dashboard_path_route_accepts_string_month_trend(
    client: TestClient, admin_token: str, db_session: Session
):
    project = _first_project(db_session)

    response = client.get(
        f"{settings.API_V1_PREFIX}/dashboard/cost/{project.id}",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    trend = response.json()["data"]["cost_trend"]
    assert trend
    assert isinstance(trend[0]["month"], str)


def test_evm_metrics_route_resolves_project_path_and_permission_dependency(
    client: TestClient, admin_token: str, db_session: Session
):
    project = _first_project(db_session)

    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/evm/metrics",
        params={"pv": 100, "ev": 80, "ac": 90, "bac": 120},
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["sv"] == -20.0
    assert data["cv"] == -10.0
    assert data["spi"] == 0.8
    assert data["cpi"] == 0.888889
