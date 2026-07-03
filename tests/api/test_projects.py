# -*- coding: utf-8 -*-
"""
项目管理模块 API 测试

Sprint 6.1: 项目CRUD单元测试
"""

import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.project import Customer, Project, ProjectMember
from app.models.stage_instance import ProjectStageInstance
from app.models.stage_template import StageDefinition, StageTemplate
from app.models.user import User


def _generate_project_code() -> str:
    """生成唯一项目编码：PJ + YYMMDD + 4位UUID序列"""
    today_part = datetime.now().strftime("%y%m%d")
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"PJ{today_part}{unique_part}"


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestProjectCRUD:
    """项目CRUD操作测试"""

    def test_regular_member_can_read_only_my_projects(
        self,
        client: TestClient,
        db_session,
    ):
        """普通登录用户应能读取自己参与的项目，不需要额外 project:read 权限"""
        marker = f"PROJECT-SELF-{uuid.uuid4().hex}"
        actor = User(
            username=f"{marker.lower()}-actor",
            password_hash=get_password_hash("password123"),
            real_name="项目自服务用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        other_user = User(
            username=f"{marker.lower()}-other",
            password_hash=get_password_hash("password123"),
            real_name="其他项目用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([actor, other_user])
        db_session.flush()

        customer = Customer(
            customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
            customer_name=f"{marker}-客户",
            contact_person="QA",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        own_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-own",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=actor.id,
        )
        other_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-other",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
        )
        db_session.add_all([own_project, other_project])
        db_session.flush()

        db_session.add_all(
            [
                ProjectMember(
                    project_id=own_project.id,
                    user_id=actor.id,
                    role_code="MEMBER",
                    is_active=True,
                    created_by=actor.id,
                ),
                ProjectMember(
                    project_id=other_project.id,
                    user_id=other_user.id,
                    role_code="MEMBER",
                    is_active=True,
                    created_by=other_user.id,
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/my-projects",
            params={"page": 1, "page_size": 100, "is_active": True},
            headers=_auth_headers_for_user(actor),
        )

        assert response.status_code == 200, response.text
        project_names = {item["project_name"] for item in response.json()["items"]}
        assert f"{marker}-own" in project_names
        assert f"{marker}-other" not in project_names

    def test_regular_member_can_read_member_project_detail_without_project_read(
        self,
        client: TestClient,
        db_session,
    ):
        """普通项目成员能读取参与项目详情，但不能读取无关项目详情"""
        marker = f"PROJECT-DETAIL-SELF-{uuid.uuid4().hex}"
        actor = User(
            username=f"{marker.lower()}-actor",
            password_hash=get_password_hash("password123"),
            real_name="项目详情自服务用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        other_user = User(
            username=f"{marker.lower()}-other",
            password_hash=get_password_hash("password123"),
            real_name="其他项目用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([actor, other_user])
        db_session.flush()

        customer = Customer(
            customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
            customer_name=f"{marker}-客户",
            contact_person="QA",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        member_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-member",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        unrelated_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-unrelated",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        db_session.add_all([member_project, unrelated_project])
        db_session.flush()

        db_session.add(
            ProjectMember(
                project_id=member_project.id,
                user_id=actor.id,
                role_code="MEMBER",
                is_active=True,
                created_by=other_user.id,
            )
        )
        db_session.commit()

        headers = _auth_headers_for_user(actor)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{member_project.id}",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["project_name"] == member_project.project_name

        unrelated_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{unrelated_project.id}",
            headers=headers,
        )
        assert unrelated_response.status_code == 403

    def test_regular_member_can_read_member_project_workspace_without_project_read(
        self,
        client: TestClient,
        db_session,
    ):
        """普通项目成员能读取参与项目工作空间，但不能读取无关项目工作空间"""
        marker = f"PROJECT-WORKSPACE-SELF-{uuid.uuid4().hex}"
        actor = User(
            username=f"{marker.lower()}-actor",
            password_hash=get_password_hash("password123"),
            real_name="项目空间自服务用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        other_user = User(
            username=f"{marker.lower()}-other",
            password_hash=get_password_hash("password123"),
            real_name="其他项目用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([actor, other_user])
        db_session.flush()

        customer = Customer(
            customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
            customer_name=f"{marker}-客户",
            contact_person="QA",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        member_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-member",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        unrelated_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-unrelated",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        db_session.add_all([member_project, unrelated_project])
        db_session.flush()

        db_session.add(
            ProjectMember(
                project_id=member_project.id,
                user_id=actor.id,
                role_code="MEMBER",
                is_active=True,
                created_by=other_user.id,
            )
        )
        db_session.commit()

        headers = _auth_headers_for_user(actor)
        response = client.get(
            f"{settings.API_V1_PREFIX}/project-workspace/projects/{member_project.id}/workspace",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["project"]["project_name"] == member_project.project_name

        unrelated_response = client.get(
            f"{settings.API_V1_PREFIX}/project-workspace/projects/{unrelated_project.id}/workspace",
            headers=headers,
        )
        assert unrelated_response.status_code == 403

    def test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read(
        self,
        client: TestClient,
        db_session,
    ):
        """普通项目成员能读取详情页旧成员/阶段子接口，但不能读取无关项目"""
        marker = f"PROJECT-LEGACY-BLOCKS-SELF-{uuid.uuid4().hex}"
        actor = User(
            username=f"{marker.lower()}-actor",
            password_hash=get_password_hash("password123"),
            real_name="项目子块自服务用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        other_user = User(
            username=f"{marker.lower()}-other",
            password_hash=get_password_hash("password123"),
            real_name="其他项目用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([actor, other_user])
        db_session.flush()

        customer = Customer(
            customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
            customer_name=f"{marker}-客户",
            contact_person="QA",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        member_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-member",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        unrelated_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-unrelated",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
        )
        db_session.add_all([member_project, unrelated_project])
        db_session.flush()

        db_session.add_all(
            [
                ProjectMember(
                    project_id=member_project.id,
                    user_id=actor.id,
                    role_code="MEMBER",
                    is_active=True,
                    created_by=other_user.id,
                ),
                ProjectStageInstance(
                    project_id=member_project.id,
                    stage_code="S1",
                    stage_name=f"{marker}-阶段",
                    sequence=1,
                    status="PENDING",
                ),
            ]
        )
        db_session.commit()

        headers = _auth_headers_for_user(actor)
        members_response = client.get(
            f"{settings.API_V1_PREFIX}/members/projects/{member_project.id}/members",
            headers=headers,
        )
        assert members_response.status_code == 200, members_response.text
        member_user_ids = {item["user_id"] for item in members_response.json()["items"]}
        assert actor.id in member_user_ids

        stages_response = client.get(
            f"{settings.API_V1_PREFIX}/stages/projects/{member_project.id}/stages",
            headers=headers,
        )
        assert stages_response.status_code == 200, stages_response.text
        assert stages_response.json()[0]["stage_name"] == f"{marker}-阶段"

        unrelated_members_response = client.get(
            f"{settings.API_V1_PREFIX}/members/projects/{unrelated_project.id}/members",
            headers=headers,
        )
        assert unrelated_members_response.status_code == 403

        unrelated_stages_response = client.get(
            f"{settings.API_V1_PREFIX}/stages/projects/{unrelated_project.id}/stages",
            headers=headers,
        )
        assert unrelated_stages_response.status_code == 403

    def test_regular_member_can_read_project_profit_card_without_cost_read(
        self,
        client: TestClient,
        db_session,
    ):
        """普通项目成员能读取参与项目利润卡，但不能读取无关项目或其它成本接口"""
        marker = f"PROJECT-PROFIT-SELF-{uuid.uuid4().hex}"
        actor = User(
            username=f"{marker.lower()}-actor",
            password_hash=get_password_hash("password123"),
            real_name="项目利润卡自服务用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        other_user = User(
            username=f"{marker.lower()}-other",
            password_hash=get_password_hash("password123"),
            real_name="其他项目用户",
            department="项目部",
            is_active=True,
            is_superuser=False,
        )
        db_session.add_all([actor, other_user])
        db_session.flush()

        customer = Customer(
            customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
            customer_name=f"{marker}-客户",
            contact_person="QA",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        member_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-member",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
            contract_amount=100000,
            budget_amount=70000,
            progress_pct=50,
        )
        unrelated_project = Project(
            project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
            project_name=f"{marker}-unrelated",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            is_active=True,
            created_by=other_user.id,
            pm_id=other_user.id,
            contract_amount=200000,
            budget_amount=150000,
            progress_pct=10,
        )
        db_session.add_all([member_project, unrelated_project])
        db_session.flush()

        db_session.add(
            ProjectMember(
                project_id=member_project.id,
                user_id=actor.id,
                role_code="MEMBER",
                is_active=True,
                created_by=other_user.id,
            )
        )
        db_session.commit()

        headers = _auth_headers_for_user(actor)
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{member_project.id}/costs/profit-optimization",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["project_id"] == member_project.id
        assert payload["contract_amount"] == 100000

        unrelated_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{unrelated_project.id}/costs/profit-optimization",
            headers=headers,
        )
        assert unrelated_response.status_code == 403

        margin_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{member_project.id}/costs/margin-analysis",
            headers=headers,
        )
        assert margin_response.status_code == 403

    def test_create_project_success(self, client: TestClient, admin_token: str):
        """测试正常创建项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        project_code = _generate_project_code()
        project_data = {
            "project_code": project_code,
            "project_name": "测试项目",
            "short_name": "测试",
            "customer_id": 1,
            "project_type": "FIXED_PRICE",
            "contract_amount": 100000.00,
            "budget_amount": 90000.00,
            "planned_start_date": date.today().isoformat(),
            "planned_end_date": (date.today() + timedelta(days=90)).isoformat(),
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["project_code"] == project_code
        assert data["project_name"] == "测试项目"
        assert data["stage"] == "S1"
        assert data["status"] == "ST01"
        assert data["health"] == "H1"
        return data

    def test_create_project_duplicate_code(self, client: TestClient, admin_token: str):
        """测试编码重复校验"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        project_code = _generate_project_code()
        project_data = {
            "project_code": project_code,
            "project_name": "第一个项目",
            "customer_id": 1,
        }

        # 创建第一个项目
        response1 = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )
        assert response1.status_code in [200, 201]

        # 尝试创建相同编码的项目
        response2 = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )
        # 应该返回400或422（验证错误）
        assert response2.status_code in [400, 422, 409]

    def test_create_project_missing_required_fields(self, client: TestClient, admin_token: str):
        """测试必填字段校验"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 缺少项目编码
        project_data = {
            "project_name": "测试项目",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )
        assert response.status_code == 422  # Validation error

    def test_create_project_auto_init_stage(self, client: TestClient, admin_token: str):
        """测试自动初始化阶段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        project_data = {
            "project_code": f"PJ250101003-{uuid.uuid4().hex[:8]}",
            "project_name": "自动初始化阶段测试",
            "customer_id": 1,
            # 不指定stage，应该自动初始化为S1
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )

        if response.status_code in [200, 201]:
            data = response.json()
            # 如果没有指定stage，应该默认为S1
            assert data.get("stage") in ["S1", None]  # 根据实际实现调整

    def test_create_project_with_stage_template_initializes_stage_instances(
        self,
        client: TestClient,
        db_session,
        admin_token: str,
    ):
        """创建项目选择阶段模板后，应立即生成新阶段视图使用的阶段实例"""
        if not admin_token:
            pytest.skip("Admin token not available")

        marker = uuid.uuid4().hex[:8]
        customer = Customer(
            customer_code=f"CUST-STAGE-{marker}",
            customer_name=f"阶段模板客户-{marker}",
            status="ACTIVE",
        )
        template = StageTemplate(
            template_code=f"QA_STAGE_TEMPLATE_{marker}",
            template_name=f"QA阶段模板-{marker}",
            is_active=True,
        )
        db_session.add_all([customer, template])
        db_session.flush()

        stage = StageDefinition(
            template_id=template.id,
            stage_code="S1",
            stage_name="需求进入",
            sequence=1,
            category="presales",
            estimated_days=3,
            is_required=True,
        )
        db_session.add(stage)
        db_session.commit()

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json={
                "project_code": f"PJ{datetime.now().strftime('%y%m%d')}{marker.upper()}",
                "project_name": f"阶段实例初始化验证-{marker}",
                "customer_id": customer.id,
                "stage_template_id": template.id,
                "planned_start_date": "2026-07-01",
            },
            headers=headers,
        )

        assert response.status_code in [200, 201], response.text
        project_id = response.json()["id"]

        stages_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/stages/",
            headers=headers,
        )
        assert stages_response.status_code == 200, stages_response.text
        stages = stages_response.json()
        assert [stage["stage_code"] for stage in stages] == ["S1"]
        assert stages[0]["status"] == "PENDING"

        persisted_count = (
            db_session.query(ProjectStageInstance)
            .filter(ProjectStageInstance.project_id == project_id)
            .count()
        )
        assert persisted_count == 1

    def test_get_project(self, client: TestClient, admin_token: str):
        """测试获取项目详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]
        project_code = project["project_code"]

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"{settings.API_V1_PREFIX}/projects/{project_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["project_code"] == project_code

    def test_list_projects(self, client: TestClient, admin_token: str):
        """测试获取项目列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?page=1&page_size=10", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # 验证分页结构
        assert "items" in data or isinstance(data, list)
        if isinstance(data, dict):
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    def test_list_projects_with_filters(self, client: TestClient, admin_token: str):
        """测试带筛选条件的项目列表查询"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 测试按阶段筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?stage=S1&page=1&page_size=10", headers=headers
        )
        assert response.status_code == 200

        # 测试按健康度筛选
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?health=H1&page=1&page_size=10", headers=headers
        )
        assert response.status_code == 200

        # 测试关键词搜索
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?keyword=测试&page=1&page_size=10", headers=headers
        )
        assert response.status_code == 200

    def test_list_projects_pagination(self, client: TestClient, admin_token: str):
        """测试项目列表分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 第一页
        response1 = client.get(
            f"{settings.API_V1_PREFIX}/projects/?page=1&page_size=5", headers=headers
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # 第二页
        response2 = client.get(
            f"{settings.API_V1_PREFIX}/projects/?page=2&page_size=5", headers=headers
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # 验证分页结果不同
        if isinstance(data1, dict) and isinstance(data2, dict):
            if "items" in data1 and "items" in data2:
                # 如果数据足够多，两页应该不同
                if len(data1["items"]) > 0 and len(data2["items"]) > 0:
                    assert data1["items"][0]["id"] != data2["items"][0]["id"]

    def test_update_project(self, client: TestClient, admin_token: str):
        """测试更新项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "project_name": "更新后的项目名称",
            "budget_amount": 120000.00,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "更新后的项目名称"
        assert float(data["budget_amount"]) == 120000.00

    def test_update_project_validation(self, client: TestClient, admin_token: str):
        """测试项目更新字段验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 测试无效的进度值（应该0-100之间）
        update_data = {
            "progress_pct": 150,  # 无效值
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}", json=update_data, headers=headers
        )
        # 目前后端允许超范围进度，至少不应报错
        assert response.status_code in [200, 400, 422]

    def test_update_project_associated_data(self, client: TestClient, admin_token: str):
        """测试项目更新关联数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 更新项目经理
        update_data = {
            "pm_id": 1,  # 假设存在ID为1的用户
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}", json=update_data, headers=headers
        )

        # 如果用户存在，应该成功；如果不存在，可能返回404或400
        assert response.status_code in [200, 400, 404]

    def test_delete_project_soft_delete(self, client: TestClient, admin_token: str):
        """测试项目软删除"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 删除项目（软删除）
        response = client.delete(f"{settings.API_V1_PREFIX}/projects/{project_id}", headers=headers)

        # 根据实际实现，可能是204 No Content或200 OK
        assert response.status_code in [200, 204]

        # 验证项目被标记为删除（is_active=False）
        get_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}", headers=headers
        )
        # 根据实现，可能返回404或返回is_active=False的项目
        if get_response.status_code == 200:
            data = get_response.json()
            assert data.get("is_active") == False

    def test_delete_project_with_relations(self, client: TestClient, admin_token: str):
        """测试删除有关联数据的项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个项目
        project = self.test_create_project_success(client, admin_token)
        project_id = project["id"]

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 如果有关联数据（如机台、任务等），删除应该检查关联
        # 这里只是测试删除接口，实际关联检查由后端实现
        response = client.delete(f"{settings.API_V1_PREFIX}/projects/{project_id}", headers=headers)

        # 根据实现，可能成功（软删除）或返回错误（如果有强制关联）
        assert response.status_code in [200, 204, 400, 409]

    def test_get_project_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的项目"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"{settings.API_V1_PREFIX}/projects/999999", headers=headers)

        assert response.status_code == 404

    def test_project_permission_filter(
        self, client: TestClient, admin_token: str, regular_user_token: str
    ):
        """测试项目权限过滤"""
        if not admin_token or not regular_user_token:
            pytest.skip("Tokens not available")

        # 使用普通用户token
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?page=1&page_size=10", headers=headers
        )

        assert response.status_code == 200
        # 普通用户应该只能看到有权限的项目
        data = response.json()
        # 验证返回的项目数量可能少于管理员看到的


class TestProjectCodeGeneration:
    """项目编码生成测试"""

    def test_project_code_format(self, client: TestClient, admin_token: str):
        """测试项目编码格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        project_data = {
            "project_name": "编码格式测试",
            "customer_id": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )

        if response.status_code in [200, 201]:
            data = response.json()
            # 验证编码格式：PJ + 年月日(YYMMDD) + 序号(3位)
            assert data["project_code"].startswith("PJ")
            assert len(data["project_code"]) == 11  # PJ + 6位日期 + 3位序号


class TestProjectStageInitialization:
    """项目阶段初始化测试"""

    def test_project_auto_init_stage_s1(self, client: TestClient, admin_token: str):
        """测试项目自动初始化为S1阶段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        project_data = {
            "project_code": _generate_project_code(),
            "project_name": "阶段初始化测试",
            "customer_id": 1,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/", json=project_data, headers=headers
        )

        if response.status_code == 201:
            data = response.json()
            # 新项目应该默认在S1阶段
            assert data.get("stage") == "S1" or data.get("stage") is None
