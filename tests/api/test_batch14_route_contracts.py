# -*- coding: utf-8 -*-
"""Batch 14 read-only route-order regressions."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.production import Worker, Workshop
from app.models.sales import QuoteTemplate, QuoteTemplateVersion
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def _parse_route_segment(segment: str) -> dict:
    if segment.startswith("{") and segment.endswith("}"):
        inner = segment[1:-1]
        name, _, converter = inner.partition(":")
        return {"dynamic": True, "name": name, "converter": converter or "str"}
    return {"dynamic": False, "literal": segment}


def _segment_accepts_literal(dynamic_segment: dict, literal: str) -> bool:
    converter = dynamic_segment["converter"]
    if converter == "int":
        return literal.isdigit()
    if converter == "float":
        try:
            float(literal)
            return True
        except ValueError:
            return False
    return literal != ""


def _dynamic_route_captures_static(dynamic_path: str, static_path: str) -> bool:
    dynamic_segments = [
        _parse_route_segment(segment)
        for segment in dynamic_path.strip("/").split("/")
        if segment
    ]
    static_segments = [
        _parse_route_segment(segment)
        for segment in static_path.strip("/").split("/")
        if segment
    ]
    if len(dynamic_segments) != len(static_segments):
        return False

    has_dynamic_segment = False
    for dynamic_segment, static_segment in zip(dynamic_segments, static_segments):
        if static_segment["dynamic"]:
            return False
        if dynamic_segment["dynamic"]:
            has_dynamic_segment = True
            if not _segment_accepts_literal(dynamic_segment, static_segment["literal"]):
                return False
            continue
        if dynamic_segment["literal"] != static_segment["literal"]:
            return False
    return has_dynamic_segment


def test_production_my_work_reports_route_is_not_captured_by_detail_route(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    suffix = uuid4().hex[:8]
    workshop = Workshop(
        workshop_code=f"B14-WS-{suffix}",
        workshop_name="Batch 14 Workshop",
        workshop_type="MACHINING",
        capacity_hours=Decimal("8.00"),
        is_active=True,
    )
    db_session.add(workshop)
    db_session.flush()
    worker = Worker(
        worker_no=f"B14-WK-{suffix}",
        user_id=admin.id,
        worker_name=admin.real_name or admin.username,
        workshop_id=workshop.id,
        position="OPERATOR",
        skill_level="INTERMEDIATE",
        entry_date=date.today(),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(worker)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/production/work-reports/my",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert "items" in payload
    assert "total" in payload


def test_sales_leads_export_route_is_not_captured_by_detail_route(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/leads/export",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert "spreadsheet" in response.headers["content-type"]


def test_legacy_sales_quote_templates_route_uses_current_template_model(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    suffix = uuid4().hex[:8]
    template = QuoteTemplate(
        template_code=f"B14-QT-{suffix}",
        template_name="Batch 14 Quote Template",
        description="legacy route regression",
        status="DRAFT",
        visibility_scope="PUBLIC",
        owner_id=admin.id,
    )
    db_session.add(template)
    db_session.flush()
    version = QuoteTemplateVersion(
        template_id=template.id,
        version_no="V1",
        status="DRAFT",
        sections={"items": []},
        created_by=admin.id,
    )
    db_session.add(version)
    db_session.flush()
    template.current_version_id = version.id
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/quotes/templates",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    item = next(item for item in payload["data"]["items"] if item["id"] == template.id)
    assert item["owner_id"] == admin.id
    assert item["created_by"] == admin.id


def test_sales_contract_pending_approval_route_accepts_engine_result_dict(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/contracts/approval/pending",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["data"]["items"] == []
    assert payload["data"]["total"] == 0


def test_sales_templates_route_tolerates_legacy_invalid_json(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    code = f"B14-AP-TPL-{suffix}"
    db_session.execute(
        text(
            """
            INSERT INTO approval_templates (
                template_code,
                template_name,
                category,
                description,
                form_schema,
                visible_scope,
                version,
                is_published,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :code,
                :name,
                'SALES',
                'invalid json regression',
                '{"fields":[{"name":"broken"}',
                '{"type":"ALL"}',
                1,
                0,
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"code": code, "name": "Batch 14 Approval Template"},
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/templates",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    item = next(item for item in payload["items"] if item["template_code"] == code)
    assert item["form_schema"] is None
    assert item["visible_scope"] == {"type": "ALL"}


def test_sales_conversion_by_person_uses_contract_sales_owner(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/conversion/by-person",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    assert "persons" in response.json()["data"]


def test_inventory_readonly_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    if admin.tenant_id is None:
        admin.tenant_id = 1
        db_session.commit()
    suffix = uuid4().hex[:8]
    material_id = 900000 + int(suffix[:4], 16)
    stock_location = f"B14-LOC-{suffix}"
    task_no = f"B14-SCT-{suffix}"

    db_session.execute(
        text(
            """
            INSERT INTO material_stock (
                tenant_id,
                material_id,
                material_code,
                material_name,
                location,
                quantity,
                available_quantity,
                reserved_quantity,
                unit,
                unit_price,
                total_value,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :tenant_id,
                :material_id,
                :material_code,
                :material_name,
                :location,
                5,
                5,
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
            "tenant_id": admin.tenant_id or 1,
            "material_id": material_id,
            "material_code": f"B14-MAT-{suffix}",
            "material_name": "Batch 14 Material",
            "location": stock_location,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO stock_count_task (
                tenant_id,
                task_no,
                count_type,
                location,
                count_date,
                status,
                created_by,
                total_items,
                counted_items,
                matched_items,
                diff_items,
                total_diff_value,
                created_at,
                updated_at
            )
            VALUES (
                :tenant_id,
                :task_no,
                NULL,
                :location,
                CURRENT_DATE,
                NULL,
                :created_by,
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
            "tenant_id": admin.tenant_id or 1,
            "task_no": task_no,
            "location": stock_location,
            "created_by": admin.id,
        },
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    stocks = client.get(
        f"{settings.API_V1_PREFIX}/inventory/stocks",
        headers=headers,
        follow_redirects=False,
    )
    tasks = client.get(
        f"{settings.API_V1_PREFIX}/inventory/count/tasks",
        headers=headers,
        follow_redirects=False,
    )
    turnover = client.get(
        f"{settings.API_V1_PREFIX}/inventory/analysis/turnover",
        headers=headers,
        follow_redirects=False,
    )

    assert stocks.status_code == 200, stocks.text
    stock_item = next(item for item in stocks.json() if item["material_id"] == material_id)
    assert stock_item["reserved_quantity"] == 0
    assert stock_item["unit"] == "件"
    assert stock_item["status"] == "NORMAL"

    assert tasks.status_code == 200, tasks.text
    task_item = next(item for item in tasks.json() if item["task_no"] == task_no)
    assert task_item["count_type"] == "FULL"
    assert task_item["total_items"] == 0
    assert task_item["total_diff_value"] == 0

    assert turnover.status_code == 200, turnover.text
    assert turnover.json()["avg_stock_value"] >= 0


def test_batch4_presale_ai_and_tender_routes_tolerate_legacy_values(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    suffix = uuid4().hex[:8]

    db_session.execute(
        text(
            """
            INSERT INTO customers (
                customer_code,
                customer_name,
                industry,
                created_at,
                updated_at
            )
            VALUES (
                :customer_code,
                :customer_name,
                '半导体',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "customer_code": f"B14-CUST-{suffix}",
            "customer_name": "Batch 14 Customer",
        },
    )
    customer_id = db_session.execute(
        text("SELECT id FROM customers WHERE customer_code = :customer_code"),
        {"customer_code": f"B14-CUST-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO opportunities (
                opp_code,
                customer_id,
                opp_name,
                project_type,
                stage,
                gate_status,
                owner_id,
                created_at,
                updated_at
            )
            VALUES (
                :opp_code,
                :customer_id,
                'Batch 14 Opportunity',
                'ATE',
                'DISCOVERY',
                'PENDING',
                :owner_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "opp_code": f"B14-OPP-{suffix}",
            "customer_id": customer_id,
            "owner_id": admin.id,
        },
    )
    opportunity_id = db_session.execute(
        text("SELECT id FROM opportunities WHERE opp_code = :opp_code"),
        {"opp_code": f"B14-OPP-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO presale_tender_record (
                opportunity_id,
                tender_no,
                tender_name,
                customer_name,
                budget_amount,
                our_bid_amount,
                result,
                leader_id,
                created_at,
                updated_at
            )
            VALUES (
                :opportunity_id,
                :tender_no,
                'Batch 14 Tender',
                'Batch 14 Customer',
                1000,
                900,
                'PENDING',
                :leader_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "opportunity_id": opportunity_id,
            "tender_no": f"B14-TENDER-{suffix}",
            "leader_id": admin.id,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO presale_ai_usage_stats (
                user_id,
                ai_function,
                usage_count,
                success_count,
                avg_response_time,
                date,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :ai_function,
                1,
                1,
                120,
                CURRENT_DATE,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"user_id": admin.id, "ai_function": f"legacy-{suffix}"},
    )
    db_session.execute(
        text(
            """
            INSERT INTO presale_ai_config (
                ai_function,
                enabled,
                temperature,
                max_tokens,
                timeout_seconds,
                created_at,
                updated_at
            )
            VALUES (
                :ai_function,
                NULL,
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"ai_function": f"legacy-config-{suffix}"},
    )
    db_session.execute(
        text(
            """
            INSERT INTO presale_support_ticket (
                ticket_no,
                title,
                ticket_type,
                applicant_id,
                applicant_name,
                customer_name,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :ticket_no,
                'Batch 14 Presale Ticket',
                'CONSULT',
                :applicant_id,
                :applicant_name,
                'Batch 14 Customer',
                'PENDING',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "ticket_no": f"B14-TK-{suffix}",
            "applicant_id": admin.id,
            "applicant_name": admin.real_name or admin.username,
        },
    )
    ticket_id = db_session.execute(
        text("SELECT id FROM presale_support_ticket WHERE ticket_no = :ticket_no"),
        {"ticket_no": f"B14-TK-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO presale_follow_up_reminder (
                presale_ticket_id,
                recommended_time,
                priority,
                follow_up_content,
                reason,
                status,
                created_at
            )
            VALUES (
                :ticket_id,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"ticket_id": ticket_id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    tender_analysis = client.get(
        f"{settings.API_V1_PREFIX}/presale/tenders/analysis",
        headers=headers,
        follow_redirects=False,
    )
    usage_stats = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/usage-stats",
        headers=headers,
        follow_redirects=False,
    )
    configs = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/config",
        headers=headers,
        follow_redirects=False,
    )
    reminders = client.get(
        f"{settings.API_V1_PREFIX}/presale/ai/follow-up-reminders",
        headers=headers,
        follow_redirects=False,
    )

    assert tender_analysis.status_code == 200, tender_analysis.text
    assert usage_stats.status_code == 200, usage_stats.text
    assert any(item["ai_function"] == f"legacy-{suffix}" for item in usage_stats.json())
    assert configs.status_code == 200, configs.text
    config = next(item for item in configs.json() if item["ai_function"] == f"legacy-config-{suffix}")
    assert config["enabled"] is True
    assert config["temperature"] == 0.7
    assert config["max_tokens"] == 2000
    assert config["timeout_seconds"] == 30
    assert reminders.status_code == 200, reminders.text
    reminder = next(
        item for item in reminders.json()["reminders"] if item["presale_ticket_id"] == ticket_id
    )
    assert reminder["priority"] == "medium"
    assert reminder["status"] == "pending"
    assert reminder["follow_up_content"] == ""
    assert reminder["reason"] == ""


def test_batch4_bonus_routes_tolerate_legacy_null_defaults(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    suffix = uuid4().hex[:8]

    db_session.execute(
        text(
            """
            INSERT INTO projects (
                project_code,
                project_name,
                customer_name,
                created_at,
                updated_at
            )
            VALUES (
                :project_code,
                'Batch 14 Project',
                'Batch 14 Customer',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_code": f"B14-PROJ-{suffix}"},
    )
    project_id = db_session.execute(
        text("SELECT id FROM projects WHERE project_code = :project_code"),
        {"project_code": f"B14-PROJ-{suffix}"},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO bonus_rules (
                rule_code,
                rule_name,
                bonus_type,
                is_active,
                priority,
                require_approval,
                created_at,
                updated_at
            )
            VALUES (
                :rule_code,
                'Batch 14 Bonus Rule',
                'PROJECT',
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"rule_code": f"B14-RULE-{suffix}"},
    )
    db_session.execute(
        text(
            """
            INSERT INTO team_bonus_allocations (
                project_id,
                total_bonus_amount,
                allocation_method,
                allocation_detail,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :project_id,
                1000,
                NULL,
                NULL,
                'PENDING',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_id": project_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO bonus_allocation_sheets (
                sheet_code,
                sheet_name,
                file_path,
                total_rows,
                valid_rows,
                invalid_rows,
                finance_confirmed,
                hr_confirmed,
                manager_confirmed,
                distribution_count,
                uploaded_by,
                created_at,
                updated_at
            )
            VALUES (
                :sheet_code,
                'Batch 14 Allocation Sheet',
                '/tmp/batch14.xlsx',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                :uploaded_by,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"sheet_code": f"B14-SHEET-{suffix}", "uploaded_by": admin.id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    rules = client.get(
        f"{settings.API_V1_PREFIX}/bonus/rules/rules",
        headers=headers,
        follow_redirects=False,
    )
    allocations = client.get(
        f"{settings.API_V1_PREFIX}/bonus/team/team-allocations",
        headers=headers,
        follow_redirects=False,
    )
    sheets = client.get(
        f"{settings.API_V1_PREFIX}/allocation-sheets",
        headers=headers,
        follow_redirects=False,
    )

    assert rules.status_code == 200, rules.text
    rule = next(item for item in rules.json()["items"] if item["rule_code"] == f"B14-RULE-{suffix}")
    assert rule["is_active"] is True
    assert rule["priority"] == 0
    assert rule["require_approval"] is True
    assert allocations.status_code == 200, allocations.text
    allocation = next(
        item for item in allocations.json()["items"] if item["project_id"] == project_id
    )
    assert allocation["allocation_method"] == "EQUAL"
    assert allocation["allocation_detail"] == []
    assert sheets.status_code == 200, sheets.text
    sheet = next(
        item for item in sheets.json()["data"]["items"] if item["sheet_code"] == f"B14-SHEET-{suffix}"
    )
    assert sheet["total_rows"] == 0
    assert sheet["finance_confirmed"] is False
    assert sheet["distribution_count"] == 0


def test_engineer_list_uses_user_display_name_without_legacy_name_field(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    username = f"b14-engineer-{suffix}"
    real_name = "Batch 14 Engineer"
    db_session.execute(
        text(
            """
            INSERT INTO users (
                username,
                password_hash,
                real_name,
                solution_credits,
                is_active,
                is_superuser,
                created_at,
                updated_at
            )
            VALUES (
                :username,
                'not-used',
                :real_name,
                100,
                1,
                0,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"username": username, "real_name": real_name},
    )
    user_id = db_session.execute(
        text("SELECT id FROM users WHERE username = :username"), {"username": username}
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO engineer_profile (
                user_id,
                job_type,
                job_level,
                skills,
                job_start_date,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                'PLC',
                'junior',
                '["PLC"]',
                :job_start_date,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"user_id": user_id, "job_start_date": date.today() - timedelta(days=30)},
    )
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/engineer-performance/engineer",
        headers=_auth_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    item = next(item for item in response.json()["data"]["items"] if item["user_id"] == user_id)
    assert item["user_name"] == real_name


def test_batch5_strategy_comparison_routes_use_current_model_fields(
    client: TestClient, admin_token: str, db_session: Session
):
    admin = _admin_user(db_session)
    suffix = uuid4().hex[:8]
    current_code = f"B14-STR-CUR-{suffix}"
    previous_code = f"B14-STR-PRE-{suffix}"
    db_session.execute(
        text(
            """
            INSERT INTO strategies (
                code,
                name,
                year,
                status,
                is_active,
                created_by,
                created_at,
                updated_at
            )
            VALUES
                (:current_code, 'Batch 14 Current Strategy', 2026, 'ACTIVE', 1, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                (:previous_code, 'Batch 14 Previous Strategy', 2025, 'ARCHIVED', 1, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "current_code": current_code,
            "previous_code": previous_code,
            "created_by": admin.id,
        },
    )
    current_strategy_id = db_session.execute(
        text("SELECT id FROM strategies WHERE code = :code"), {"code": current_code}
    ).scalar_one()
    previous_strategy_id = db_session.execute(
        text("SELECT id FROM strategies WHERE code = :code"), {"code": previous_code}
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO strategy_comparisons (
                current_strategy_id,
                previous_strategy_id,
                current_year,
                previous_year,
                generated_date,
                generated_by,
                summary,
                is_active,
                created_at,
                updated_at
            )
            VALUES (
                :current_strategy_id,
                :previous_strategy_id,
                2026,
                2025,
                CURRENT_DATE,
                :generated_by,
                'Batch 14 comparison',
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "current_strategy_id": current_strategy_id,
            "previous_strategy_id": previous_strategy_id,
            "generated_by": admin.id,
        },
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    for path in (
        f"{settings.API_V1_PREFIX}/strategy/comparisons",
        f"{settings.API_V1_PREFIX}/ai-strategy/comparisons",
    ):
        response = client.get(path, headers=headers, follow_redirects=False)
        assert response.status_code == 200, response.text
        item = next(
            item
            for item in response.json()["items"]
            if item["current_strategy_id"] == current_strategy_id
        )
        assert item["current_year"] == 2026
        assert item["previous_year"] == 2025
        assert item["generated_by"] == admin.id


def test_batch5_outsourcing_readonly_routes_tolerate_legacy_nulls(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    vendor_code = f"B14-VENDOR-{suffix}"
    project_code = f"B14-OS-PROJ-{suffix}"
    order_no = f"B14-OS-ORDER-{suffix}"
    delivery_no = f"B14-OS-DEL-{suffix}"
    inspection_no = f"B14-OS-INSP-{suffix}"
    payment_no = f"B14-OS-PAY-{suffix}"

    db_session.execute(
        text(
            """
            INSERT INTO vendors (
                supplier_code,
                supplier_name,
                vendor_type,
                created_at,
                updated_at
            )
            VALUES (
                :vendor_code,
                'Batch 14 Material Vendor',
                'MATERIAL',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"vendor_code": vendor_code},
    )
    vendor_id = db_session.execute(
        text("SELECT id FROM vendors WHERE supplier_code = :vendor_code"),
        {"vendor_code": vendor_code},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO projects (
                project_code,
                project_name,
                customer_name,
                created_at,
                updated_at
            )
            VALUES (
                :project_code,
                'Batch 14 Outsourcing Project',
                'Batch 14 Customer',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_code": project_code},
    )
    project_id = db_session.execute(
        text("SELECT id FROM projects WHERE project_code = :project_code"),
        {"project_code": project_code},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_orders (
                order_no,
                vendor_id,
                project_id,
                order_date,
                order_type,
                order_title,
                total_amount,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :order_no,
                :vendor_id,
                :project_id,
                CURRENT_DATE,
                'PROCESS',
                'Batch 14 Outsourcing Order',
                100,
                'DRAFT',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"order_no": order_no, "vendor_id": vendor_id, "project_id": project_id},
    )
    order_id = db_session.execute(
        text("SELECT id FROM outsourcing_orders WHERE order_no = :order_no"),
        {"order_no": order_no},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_order_items (
                order_id,
                item_no,
                material_code,
                material_name,
                quantity,
                created_at,
                updated_at
            )
            VALUES (
                :order_id,
                1,
                'B14-MAT',
                'Batch 14 Material',
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"order_id": order_id},
    )
    order_item_id = db_session.execute(
        text("SELECT id FROM outsourcing_order_items WHERE order_id = :order_id"),
        {"order_id": order_id},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_deliveries (
                delivery_no,
                order_id,
                vendor_id,
                delivery_date,
                delivery_type,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :delivery_no,
                :order_id,
                :vendor_id,
                CURRENT_DATE,
                NULL,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"delivery_no": delivery_no, "order_id": order_id, "vendor_id": vendor_id},
    )
    delivery_id = db_session.execute(
        text("SELECT id FROM outsourcing_deliveries WHERE delivery_no = :delivery_no"),
        {"delivery_no": delivery_no},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_delivery_items (
                delivery_id,
                order_item_id,
                material_code,
                material_name,
                delivery_quantity,
                created_at,
                updated_at
            )
            VALUES (
                :delivery_id,
                :order_item_id,
                'B14-MAT',
                'Batch 14 Material',
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"delivery_id": delivery_id, "order_item_id": order_item_id},
    )
    delivery_item_id = db_session.execute(
        text("SELECT id FROM outsourcing_delivery_items WHERE delivery_id = :delivery_id"),
        {"delivery_id": delivery_id},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_inspections (
                inspection_no,
                delivery_id,
                delivery_item_id,
                inspect_type,
                inspect_date,
                inspect_quantity,
                qualified_quantity,
                rejected_quantity,
                inspect_result,
                created_at,
                updated_at
            )
            VALUES (
                :inspection_no,
                :delivery_id,
                :delivery_item_id,
                NULL,
                CURRENT_DATE,
                1,
                1,
                0,
                'PASSED',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "inspection_no": inspection_no,
            "delivery_id": delivery_id,
            "delivery_item_id": delivery_item_id,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO outsourcing_payments (
                payment_no,
                vendor_id,
                order_id,
                payment_type,
                payment_amount,
                payment_date,
                payment_method,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :payment_no,
                :vendor_id,
                :order_id,
                'FINAL',
                100,
                CURRENT_DATE,
                'BANK_TRANSFER',
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"payment_no": payment_no, "vendor_id": vendor_id, "order_id": order_id},
    )
    db_session.commit()

    headers = _auth_headers(admin_token)
    deliveries = client.get(
        f"{settings.API_V1_PREFIX}/outsourcing-deliveries",
        headers=headers,
        follow_redirects=False,
    )
    inspections = client.get(
        f"{settings.API_V1_PREFIX}/outsourcing-inspections",
        headers=headers,
        follow_redirects=False,
    )
    payments = client.get(
        f"{settings.API_V1_PREFIX}/outsourcing-payments",
        headers=headers,
        follow_redirects=False,
    )

    assert deliveries.status_code == 200, deliveries.text
    delivery = next(item for item in deliveries.json()["items"] if item["delivery_no"] == delivery_no)
    assert delivery["vendor_name"] == "未知外协商"
    assert delivery["delivery_type"] == "NORMAL"
    assert delivery["status"] == "PENDING"
    assert inspections.status_code == 200, inspections.text
    inspection = next(
        item for item in inspections.json()["items"] if item["inspection_no"] == inspection_no
    )
    assert inspection["inspect_type"] == "INCOMING"
    assert payments.status_code == 200, payments.text
    payment = next(item for item in payments.json()["items"] if item["payment_no"] == payment_no)
    assert payment["status"] == "DRAFT"


def test_registered_routes_do_not_shadow_later_static_routes():
    from app.main import app

    routes_by_method = {}
    for index, route in enumerate(app.routes):
        path = getattr(route, "path", "")
        if not path.startswith(settings.API_V1_PREFIX):
            continue
        methods = (getattr(route, "methods", None) or set()) - {"HEAD", "OPTIONS"}
        for method in methods:
            routes_by_method.setdefault(method, []).append(
                (index, path, getattr(route, "name", ""))
            )

    conflicts = []
    for method, routes in routes_by_method.items():
        for later_position, (static_index, static_path, static_name) in enumerate(routes):
            if "{" in static_path:
                continue
            for dynamic_index, dynamic_path, dynamic_name in routes[:later_position]:
                if "{" not in dynamic_path:
                    continue
                if _dynamic_route_captures_static(dynamic_path, static_path):
                    conflicts.append(
                        f"{method} {dynamic_path} ({dynamic_name}) shadows "
                        f"{static_path} ({static_name})"
                    )
                    break

    assert conflicts == []
