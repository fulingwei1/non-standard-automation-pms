# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API 测试
测试立项管理、风险管理、项目结项、驾驶舱等功能
"""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.pmo import PmoProjectPhase


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
