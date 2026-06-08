# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API 测试
测试立项管理、风险管理、项目结项、驾驶舱等功能
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.pmo import PmoProjectPhase
from app.models.enums import OpenItemStatusEnum
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.project import Customer, Project
from app.models.sales import Contract, Lead, OpenItem, Opportunity, Quote, QuoteVersion
from app.models.task_center import TaskUnified
from app.models.user import User
from app.services.pmo_initiation.service import PmoInitiationService


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_status(response, expected_status: int = 200):
    assert response.status_code == expected_status, response.text


def _items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    return []


def _create_initiation(
    client: TestClient, headers: dict, contract_no: str | None = None
) -> dict:
    contract_no = contract_no or f"PMO-TEST-{uuid4().hex[:8]}"
    response = client.post(
        f"{settings.API_V1_PREFIX}/pmo/initiations",
        json={
            "project_name": f"PMO立项测试-{date.today().isoformat()}",
            "project_type": "NEW",
            "customer_name": "测试客户",
            "contract_no": contract_no,
            "contract_amount": "10000.00",
            "required_start_date": date.today().isoformat(),
            "required_end_date": date.today().isoformat(),
            "requirement_summary": "PMO API 测试立项",
        },
        headers=headers,
    )
    _assert_status(response, 201)
    return response.json()


def _create_phase(db_session, project_id: int) -> PmoProjectPhase:
    phase = PmoProjectPhase(
        project_id=project_id,
        phase_code=f"PMO-{project_id}",
        phase_name="PMO阶段测试",
        phase_order=1,
        status="PENDING",
        progress=0,
        review_required=True,
    )
    db_session.add(phase)
    db_session.commit()
    db_session.refresh(phase)
    return phase


def _create_risk(client: TestClient, headers: dict, project_id: int) -> dict:
    response = client.post(
        f"{settings.API_V1_PREFIX}/pmo/projects/{project_id}/risks",
        json={
            "risk_category": "SCHEDULE",
            "risk_name": f"PMO风险测试-{project_id}",
            "description": "PMO API 测试风险",
            "probability": "MEDIUM",
            "impact": "HIGH",
            "trigger_condition": "关键节点延期",
        },
        headers=headers,
    )
    _assert_status(response, 201)
    return response.json()


def _ensure_closure(client: TestClient, headers: dict, project_id: int) -> dict:
    response = client.get(
        f"{settings.API_V1_PREFIX}/pmo/projects/{project_id}/closure", headers=headers
    )
    if response.status_code == 200:
        return response.json()

    assert response.status_code == 404, response.text
    response = client.post(
        f"{settings.API_V1_PREFIX}/pmo/projects/{project_id}/closure",
        json={
            "acceptance_date": date.today().isoformat(),
            "acceptance_result": "PASSED",
            "acceptance_notes": "验收通过",
            "project_summary": "PMO API 测试结项",
            "achievement": "完成测试覆盖",
            "lessons_learned": "接口测试需要显式准备数据",
            "improvement_suggestions": "持续清理动态 skip",
            "quality_score": 90,
            "customer_satisfaction": 92,
        },
        headers=headers,
    )
    _assert_status(response, 201)
    return response.json()


def _create_meeting(client: TestClient, headers: dict, project_id: int) -> dict:
    response = client.post(
        f"{settings.API_V1_PREFIX}/pmo/meetings",
        json={
            "project_id": project_id,
            "meeting_type": "PMO",
            "meeting_name": f"PMO例会测试-{project_id}",
            "meeting_date": date.today().isoformat(),
            "location": "测试会议室",
            "agenda": "项目状态同步",
        },
        headers=headers,
    )
    _assert_status(response, 201)
    return response.json()


class TestInitiations:
    """立项管理测试"""

    def test_list_initiations(self, client: TestClient, admin_token: str):
        """测试获取立项申请列表"""

        headers = _auth_headers(admin_token)
        _create_initiation(client, headers)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/initiations",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        _assert_status(response)
        data = response.json()
        assert _items(data)

    def test_list_initiations_by_status(self, client: TestClient, admin_token: str):
        """测试按状态筛选立项申请"""

        headers = _auth_headers(admin_token)
        _create_initiation(client, headers)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/initiations", params={"status": "DRAFT"}, headers=headers
        )

        _assert_status(response)
        assert all(item["status"] == "DRAFT" for item in _items(response.json()))

    def test_list_initiations_by_contract_no(self, client: TestClient, admin_token: str):
        """测试按合同编号筛选立项申请"""

        headers = _auth_headers(admin_token)
        target_contract_no = "PMO-FILTER-CONTRACT"
        target = _create_initiation(client, headers, contract_no=target_contract_no)
        _create_initiation(client, headers, contract_no="PMO-FILTER-OTHER")

        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/initiations",
            params={"contract_no": target_contract_no},
            headers=headers,
        )

        _assert_status(response)
        items = _items(response.json())
        assert any(item["id"] == target["id"] for item in items)
        assert all(item["contract_no"] == target_contract_no for item in items)

    def test_create_initiation_rejects_duplicate_active_contract_no(
        self, client: TestClient, admin_token: str
    ):
        """同一合同已有未终态立项申请时，接口返回 409。"""

        headers = _auth_headers(admin_token)
        target_contract_no = f"PMO-DUP-{uuid4().hex[:8]}"
        _create_initiation(client, headers, contract_no=target_contract_no)

        duplicate_response = client.post(
            f"{settings.API_V1_PREFIX}/pmo/initiations",
            json={
                "project_name": "重复立项",
                "project_type": "NEW",
                "customer_name": "测试客户",
                "contract_no": target_contract_no,
                "contract_amount": "10000.00",
                "required_start_date": date.today().isoformat(),
                "required_end_date": date.today().isoformat(),
                "requirement_summary": "重复创建应被拒绝",
            },
            headers=headers,
        )

        _assert_status(duplicate_response, 409)
        assert "已存在未完成的立项申请" in duplicate_response.text

    def test_get_initiation_by_id(self, client: TestClient, admin_token: str):
        """测试获取单个立项申请"""

        headers = _auth_headers(admin_token)
        initiation = _create_initiation(client, headers)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/initiations/{initiation['id']}", headers=headers
        )

        _assert_status(response)
        assert response.json()["id"] == initiation["id"]

    def test_approve_initiation_links_presale_solution_to_project(
        self, client: TestClient, db_session, admin_token: str
    ):
        """带售前技术方案的立项审批后，项目和方案要互相关联。"""
        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PMO-{unique}",
            customer_name=f"售前方案客户-{unique}",
            contact_person="王工",
            contact_phone="13800138000",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPP-PMO-{unique}",
            customer_id=customer.id,
            opp_name=f"售前方案商机-{unique}",
            stage="PROPOSAL",
            probability=80,
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(opportunity)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=f"SOL-PMO-{unique}",
            name=f"售前方案转项目-{unique}",
            solution_type="CUSTOM",
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            suggested_price=160000,
            estimated_cost=120000,
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        open_item = OpenItem(
            source_type="OPPORTUNITY",
            source_id=opportunity.id,
            item_code=f"OI-PMO-{unique}",
            item_type="TECHNICAL",
            description="客户样品治具接口图未冻结，项目启动后需要继续跟进",
            responsible_party="CUSTOMER",
            responsible_person_id=admin_user.id,
            due_date=datetime.now() + timedelta(days=5),
            status=OpenItemStatusEnum.PENDING.value,
            blocks_quotation=True,
        )
        db_session.add_all([solution, open_item])
        db_session.commit()

        created = client.post(
            f"{prefix}/pmo/initiations",
            json={
                "project_name": f"售前方案转项目-{unique}",
                "project_type": "NEW",
                "customer_name": customer.customer_name,
                "technical_solution_id": solution.id,
                "requirement_summary": "根据已批准售前技术方案发起立项",
            },
            headers=headers,
        )
        _assert_status(created, 201)
        initiation_id = created.json()["id"]

        submitted = client.put(
            f"{prefix}/pmo/initiations/{initiation_id}/submit",
            headers=headers,
        )
        _assert_status(submitted)

        approved = client.put(
            f"{prefix}/pmo/initiations/{initiation_id}/approve",
            json={"review_result": "同意立项", "approved_pm_id": admin_user.id},
            headers=headers,
        )
        _assert_status(approved)
        project_id = approved.json()["data"]["project_id"]

        db_session.expire_all()
        project = db_session.query(Project).filter(Project.id == project_id).first()
        linked_solution = (
            db_session.query(PresaleSolution)
            .filter(PresaleSolution.id == solution.id)
            .first()
        )
        handover_task = (
            db_session.query(TaskUnified)
            .filter(
                TaskUnified.project_id == project_id,
                TaskUnified.source_type == "PRESALE_OPEN_ITEM",
                TaskUnified.source_id == open_item.id,
            )
            .first()
        )

        assert project is not None
        assert project.customer_id == customer.id
        assert project.customer_name == customer.customer_name
        assert project.customer_contact == "王工"
        assert project.customer_phone == "13800138000"
        assert project.opportunity_id == opportunity.id
        assert float(project.contract_amount) == 160000.0
        assert linked_solution.project_id == project.id
        assert handover_task is not None
        assert handover_task.category == "PRESALE_HANDOVER"
        assert handover_task.assignee_id == admin_user.id
        assert handover_task.priority == "HIGH"
        assert handover_task.source_name == open_item.item_code
        assert "客户样品治具接口图未冻结" in handover_task.title

        before_count = (
            db_session.query(TaskUnified)
            .filter(
                TaskUnified.project_id == project_id,
                TaskUnified.source_type == "PRESALE_OPEN_ITEM",
                TaskUnified.source_id == open_item.id,
            )
            .count()
        )
        created_again = PmoInitiationService(db_session)._sync_presale_open_items_to_project_tasks(
            project,
            admin_user.id,
            admin_user,
        )
        after_count = (
            db_session.query(TaskUnified)
            .filter(
                TaskUnified.project_id == project_id,
                TaskUnified.source_type == "PRESALE_OPEN_ITEM",
                TaskUnified.source_id == open_item.id,
            )
            .count()
        )
        assert created_again == 0
        assert after_count == before_count

    def test_initiation_handover_resolves_presale_solution_from_contract_quote_version(
        self, client: TestClient, db_session, admin_token: str
    ):
        """合同只关联报价版本时，立项交接包仍应反查到售前方案。"""
        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-QV-{unique}",
            customer_name=f"报价版本客户-{unique}",
            contact_person="赵工",
            contact_phone="13700137000",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADQV{unique[:6]}",
            customer_name=customer.customer_name,
            industry="电子制造",
            demand_summary="报价版本链路售前需求",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        opportunity = Opportunity(
            opp_code=f"OPP-QV-{unique}",
            customer_id=customer.id,
            lead_id=lead.id,
            opp_name=f"报价版本商机-{unique}",
            stage="PROPOSAL",
            probability=80,
            owner_id=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(opportunity)
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"PST-QV-{unique}",
            title=f"报价版本售前支持-{unique}",
            ticket_type="SOLUTION_DESIGN",
            urgency="NORMAL",
            description="销售报价引用售前方案",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            lead_id=lead.id,
            opportunity_id=opportunity.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            actual_hours=6,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=f"SOL-QV-{unique}",
            name=f"报价版本售前方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            suggested_price=320000,
            estimated_cost=210000,
            estimated_hours=72,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        db_session.add(solution)
        db_session.flush()

        quote = Quote(
            quote_code=f"Q-PMOQ{unique[:6]}",
            opportunity_id=opportunity.id,
            customer_id=customer.id,
            status="APPROVED",
            owner_id=admin_user.id,
        )
        db_session.add(quote)
        db_session.flush()

        quote_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V1.0",
            presale_solution_id=solution.id,
            presale_ticket_id=ticket.id,
            total_price=320000,
            cost_total=210000,
        )
        db_session.add(quote_version)
        db_session.flush()
        quote.current_version_id = quote_version.id

        contract = Contract(
            contract_code=f"CT-QV-{unique}",
            contract_name=f"报价版本合同-{unique}",
            contract_type="sales",
            opportunity_id=opportunity.id,
            quote_id=quote_version.id,
            customer_id=customer.id,
            total_amount=320000,
            status="signed",
            sales_owner_id=admin_user.id,
        )
        db_session.add(contract)
        db_session.commit()

        created = client.post(
            f"{prefix}/pmo/initiations",
            json={
                "project_name": f"报价版本合同立项-{unique}",
                "project_type": "NEW",
                "customer_name": customer.customer_name,
                "contract_no": contract.contract_code,
                "contract_amount": "320000",
                "requirement_summary": "由报价版本合同发起立项",
            },
            headers=headers,
        )
        _assert_status(created, 201)

        detail = client.get(
            f"{prefix}/pmo/initiations/{created.json()['id']}",
            headers=headers,
        )
        _assert_status(detail)
        handover = detail.json()["presale_handover_context"]
        assert handover["contract"]["contract_code"] == contract.contract_code
        assert handover["presale_solution"]["id"] == solution.id
        assert handover["presale_ticket"]["id"] == ticket.id
        assert handover["baseline_cost"]["presale_estimated_cost"] == 210000.0
        assert "presale_solution" not in handover["handover_status"]["missing"]

    def test_approve_lead_stage_solution_initiation_keeps_lead_handover(
        self, client: TestClient, db_session, admin_token: str
    ):
        """线索阶段售前方案直接立项后，项目侧不能丢失线索和售前遗留事项。"""
        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-PMOL-{unique}",
            customer_name=f"线索阶段客户-{unique}",
            contact_person="李工",
            contact_phone="13900139000",
            created_by=admin_user.id,
        )
        lead = Lead(
            lead_code=f"LEADPMO{unique[:6]}",
            customer_name=customer.customer_name,
            industry="电子制造",
            demand_summary="客户线索阶段已明确EOL终测需求",
            owner_id=admin_user.id,
        )
        db_session.add_all([customer, lead])
        db_session.flush()

        ticket = PresaleSupportTicket(
            ticket_no=f"PST-PMOL-{unique}",
            title=f"线索阶段售前技术支持-{unique}",
            ticket_type="SOLUTION_DESIGN",
            urgency="NORMAL",
            description="销售在线索阶段发起方案设计",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            lead_id=lead.id,
            applicant_id=admin_user.id,
            applicant_name=admin_user.real_name or admin_user.username,
            status="COMPLETED",
            actual_hours=8,
            created_by=admin_user.id,
        )
        db_session.add(ticket)
        db_session.flush()

        solution = PresaleSolution(
            solution_no=f"SOL-PMOL-{unique}",
            name=f"线索阶段EOL方案-{unique}",
            solution_type="CUSTOM",
            ticket_id=ticket.id,
            customer_id=customer.id,
            suggested_price=260000,
            estimated_cost=180000,
            estimated_hours=80,
            status="APPROVED",
            review_status="APPROVED",
            author_id=admin_user.id,
            author_name=admin_user.real_name or admin_user.username,
        )
        open_item = OpenItem(
            source_type="LEAD",
            source_id=lead.id,
            item_code=f"OI-PMOL-{unique}",
            item_type="TECHNICAL",
            description="线索阶段样品测试夹具图纸未冻结",
            responsible_party="CUSTOMER",
            responsible_person_id=admin_user.id,
            due_date=datetime.now() + timedelta(days=3),
            status=OpenItemStatusEnum.PENDING.value,
            blocks_quotation=True,
        )
        db_session.add_all([solution, open_item])
        db_session.commit()

        created = client.post(
            f"{prefix}/pmo/initiations",
            json={
                "project_name": f"线索方案直转项目-{unique}",
                "project_type": "NEW",
                "customer_name": customer.customer_name,
                "technical_solution_id": solution.id,
                "requirement_summary": "根据线索阶段售前方案直接发起立项",
            },
            headers=headers,
        )
        _assert_status(created, 201)
        initiation_id = created.json()["id"]

        submitted = client.put(
            f"{prefix}/pmo/initiations/{initiation_id}/submit",
            headers=headers,
        )
        _assert_status(submitted)

        approved = client.put(
            f"{prefix}/pmo/initiations/{initiation_id}/approve",
            json={"review_result": "同意立项", "approved_pm_id": admin_user.id},
            headers=headers,
        )
        _assert_status(approved)
        project_id = approved.json()["data"]["project_id"]

        db_session.expire_all()
        project = db_session.query(Project).filter(Project.id == project_id).first()
        linked_solution = db_session.get(PresaleSolution, solution.id)
        linked_ticket = db_session.get(PresaleSupportTicket, ticket.id)
        handover_task = (
            db_session.query(TaskUnified)
            .filter(
                TaskUnified.project_id == project_id,
                TaskUnified.source_type == "PRESALE_OPEN_ITEM",
                TaskUnified.source_id == open_item.id,
            )
            .first()
        )

        assert project is not None
        assert project.customer_id == customer.id
        assert project.lead_id == lead.id
        assert project.opportunity_id is None
        assert float(project.contract_amount) == 260000.0
        assert linked_solution.project_id == project.id
        assert linked_ticket.project_id == project.id
        assert handover_task is not None
        assert handover_task.category == "PRESALE_HANDOVER"
        assert "样品测试夹具图纸未冻结" in handover_task.title

        workspace_context_response = client.get(
            f"{prefix}/project-workspace/projects/{project_id}/workspace/context",
            headers=headers,
        )
        _assert_status(workspace_context_response)
        workspace_context = workspace_context_response.json()
        assert workspace_context["project"]["lead_id"] == lead.id
        assert workspace_context["presale_tickets"][0]["id"] == ticket.id
        assert workspace_context["presale_solutions"][0]["id"] == solution.id
        assert workspace_context["open_items"]["total"] == 1
        assert workspace_context["open_items"]["items"][0]["id"] == open_item.id


class TestProjectPhases:
    """项目阶段门管理测试"""

    def test_list_project_phases(
        self, client: TestClient, admin_token: str, test_project, db_session
    ):
        """测试获取项目阶段列表"""

        headers = _auth_headers(admin_token)
        phase = _create_phase(db_session, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/projects/{test_project.id}/phases", headers=headers
        )

        _assert_status(response)
        assert any(item["id"] == phase.id for item in response.json())

    def test_phase_entry_check_by_id(
        self, client: TestClient, admin_token: str, test_project, db_session
    ):
        """测试按阶段 ID 执行入口检查"""

        headers = _auth_headers(admin_token)
        phase = _create_phase(db_session, test_project.id)
        response = client.post(
            f"{settings.API_V1_PREFIX}/pmo/phases/{phase.id}/entry-check",
            json={"check_result": "PASSED", "notes": "入口条件满足"},
            headers=headers,
        )

        _assert_status(response)
        assert response.json()["id"] == phase.id
        assert response.json()["entry_check_result"]


class TestProjectRisks:
    """风险管理测试"""

    def test_list_project_risks(self, client: TestClient, admin_token: str, test_project):
        """测试获取项目风险列表"""

        headers = _auth_headers(admin_token)
        risk = _create_risk(client, headers, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/projects/{test_project.id}/risks",
            headers=headers,
        )

        _assert_status(response)
        assert any(item["id"] == risk["id"] for item in response.json())

    def test_list_risks_by_status(self, client: TestClient, admin_token: str, test_project):
        """测试按状态筛选风险"""

        headers = _auth_headers(admin_token)
        risk = _create_risk(client, headers, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/projects/{test_project.id}/risks",
            params={"status": "IDENTIFIED"},
            headers=headers,
        )

        _assert_status(response)
        assert any(item["id"] == risk["id"] for item in response.json())
        assert all(item["status"] == "IDENTIFIED" for item in response.json())

    def test_update_risk_status_by_id(self, client: TestClient, admin_token: str, test_project):
        """测试按风险 ID 更新状态"""

        headers = _auth_headers(admin_token)
        risk = _create_risk(client, headers, test_project.id)
        response = client.put(
            f"{settings.API_V1_PREFIX}/pmo/risks/{risk['id']}/status",
            json={"status": "MITIGATING", "last_update": "已制定缓解计划"},
            headers=headers,
        )

        _assert_status(response)
        assert response.json()["id"] == risk["id"]
        assert response.json()["status"] == "MITIGATING"


class TestProjectClosures:
    """项目结项测试"""

    def test_create_and_read_closure(self, client: TestClient, admin_token: str, test_project):
        """测试创建并读取结项申请"""

        headers = _auth_headers(admin_token)
        closure = _ensure_closure(client, headers, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/projects/{test_project.id}/closure",
            headers=headers,
        )

        _assert_status(response)
        assert response.json()["id"] == closure["id"]

    def test_review_closure_by_id(self, client: TestClient, admin_token: str, test_project):
        """测试评审单个结项申请"""

        headers = _auth_headers(admin_token)
        closure = _ensure_closure(client, headers, test_project.id)
        response = client.put(
            f"{settings.API_V1_PREFIX}/pmo/closures/{closure['id']}/review",
            json={"review_result": "APPROVED", "review_notes": "结项评审通过"},
            headers=headers,
        )

        _assert_status(response)
        assert response.json()["id"] == closure["id"]
        assert response.json()["status"] == "REVIEWED"


class TestPmoDashboard:
    """PMO 驾驶舱测试"""

    def test_get_pmo_dashboard(self, client: TestClient, admin_token: str):
        """测试获取 PMO 驾驶舱数据"""

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/pmo/dashboard", headers=headers)

        _assert_status(response)

    def test_get_weekly_report(self, client: TestClient, admin_token: str):
        """测试获取周报"""

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/pmo/weekly-report", headers=headers)

        _assert_status(response)

    def test_get_resource_overview(self, client: TestClient, admin_token: str):
        """测试获取资源概览"""

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/pmo/resource-overview", headers=headers)

        _assert_status(response)

    def test_get_risk_wall(self, client: TestClient, admin_token: str):
        """测试获取风险墙"""

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/pmo/risk-wall", headers=headers)

        _assert_status(response)


class TestPmoMeetings:
    """PMO 会议管理测试"""

    def test_list_meetings(self, client: TestClient, admin_token: str, test_project):
        """测试获取会议列表"""

        headers = _auth_headers(admin_token)
        meeting = _create_meeting(client, headers, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/meetings",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        _assert_status(response)
        assert any(item["id"] == meeting["id"] for item in _items(response.json()))

    def test_get_meeting_by_id(self, client: TestClient, admin_token: str, test_project):
        """测试获取单个会议详情"""

        headers = _auth_headers(admin_token)
        meeting = _create_meeting(client, headers, test_project.id)
        response = client.get(
            f"{settings.API_V1_PREFIX}/pmo/meetings/{meeting['id']}", headers=headers
        )

        _assert_status(response)
        assert response.json()["id"] == meeting["id"]
