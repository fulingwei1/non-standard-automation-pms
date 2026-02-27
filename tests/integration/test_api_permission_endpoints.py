# -*- coding: utf-8 -*-
"""
API端点权限集成测试

测试目标：
1. 测试不同角色访问相同API的权限差异
   - 管理员应该可以访问所有端点
   - PM可以访问项目相关端点但不能访问用户管理
   - 工程师只能访问受限端点
2. 测试数据范围过滤是否生效
   - PM只能看到负责的项目
   - 销售只能看到自己的商机
3. 生成详细测试报告
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.project import Customer, Project, ProjectMember
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from tests.integration.api_test_helper import APITestHelper


class PermissionTestReport:
    """测试报告生成器"""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "by_role": {},
            "by_endpoint": {},
        }

    def add_result(
        self,
        test_name: str,
        role: str,
        endpoint: str,
        method: str,
        expected_status: int,
        actual_status: int,
        passed: bool,
        message: str = "",
    ):
        """添加测试结果"""
        result = {
            "test_name": test_name,
            "role": role,
            "endpoint": endpoint,
            "method": method,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        # 更新统计
        self.summary["total"] += 1
        if passed:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1

        # 按角色统计
        if role not in self.summary["by_role"]:
            self.summary["by_role"][role] = {"total": 0, "passed": 0, "failed": 0}
        self.summary["by_role"][role]["total"] += 1
        if passed:
            self.summary["by_role"][role]["passed"] += 1
        else:
            self.summary["by_role"][role]["failed"] += 1

        # 按端点统计
        if endpoint not in self.summary["by_endpoint"]:
            self.summary["by_endpoint"][endpoint] = {"total": 0, "passed": 0, "failed": 0}
        self.summary["by_endpoint"][endpoint]["total"] += 1
        if passed:
            self.summary["by_endpoint"][endpoint]["passed"] += 1
        else:
            self.summary["by_endpoint"][endpoint]["failed"] += 1

    def generate_report(self, output_file: str = "api_permission_test_report.md"):
        """生成Markdown格式的测试报告"""
        report_lines = [
            "# API端点权限集成测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试概览",
            "",
            f"- **总测试数**: {self.summary['total']}",
            f"- **通过数**: {self.summary['passed']}",
            f"- **失败数**: {self.summary['failed']}",
            f"- **通过率**: {self.summary['passed'] / self.summary['total'] * 100:.2f}%" if self.summary['total'] > 0 else "- **通过率**: 0%",
            "",
            "## 按角色统计",
            "",
            "| 角色 | 总数 | 通过 | 失败 | 通过率 |",
            "| --- | --- | --- | --- | --- |",
        ]

        for role, stats in sorted(self.summary["by_role"].items()):
            pass_rate = (
                f"{stats['passed'] / stats['total'] * 100:.2f}%"
                if stats['total'] > 0
                else "0%"
            )
            report_lines.append(
                f"| {role} | {stats['total']} | {stats['passed']} | {stats['failed']} | {pass_rate} |"
            )

        report_lines.extend(
            [
                "",
                "## 按端点统计",
                "",
                "| 端点 | 总数 | 通过 | 失败 | 通过率 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )

        for endpoint, stats in sorted(self.summary["by_endpoint"].items()):
            pass_rate = (
                f"{stats['passed'] / stats['total'] * 100:.2f}%"
                if stats['total'] > 0
                else "0%"
            )
            report_lines.append(
                f"| {endpoint} | {stats['total']} | {stats['passed']} | {stats['failed']} | {pass_rate} |"
            )

        report_lines.extend(
            [
                "",
                "## 详细测试结果",
                "",
                "| 测试名称 | 角色 | 端点 | 方法 | 期望状态码 | 实际状态码 | 结果 | 消息 |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )

        for result in self.test_results:
            status_icon = "✅" if result["passed"] else "❌"
            report_lines.append(
                f"| {result['test_name']} | {result['role']} | {result['endpoint']} | "
                f"{result['method']} | {result['expected_status']} | {result['actual_status']} | "
                f"{status_icon} | {result['message']} |"
            )

        report_content = "\n".join(report_lines)

        # 写入报告文件
        output_path = Path(output_file)
        output_path.write_text(report_content, encoding="utf-8")

        return output_path


# 全局测试报告实例
test_report = PermissionTestReport()


@pytest.fixture(scope="function")
def setup_test_users_and_roles(db_session: Session):
    """设置测试用户和角色"""
    # 创建角色
    roles = {
        "admin": Role(
            role_code="ADMIN",
            role_name="系统管理员",
            description="系统管理员，拥有所有权限",
            data_scope="ALL",
            is_system=True,
        ),
        "pm": Role(
            role_code="PM",
            role_name="项目经理",
            description="项目经理，管理项目",
            data_scope="PROJECT",
            is_system=True,
        ),
        "engineer": Role(
            role_code="ENGINEER",
            role_name="工程师",
            description="工程师，参与项目",
            data_scope="OWN",
            is_system=True,
        ),
        "sales": Role(
            role_code="SALES",
            role_name="销售",
            description="销售人员，管理商机",
            data_scope="OWN",
            is_system=True,
        ),
    }

    for role in roles.values():
        existing_role = db_session.query(Role).filter(Role.role_code == role.role_code).first()
        if not existing_role:
            db_session.add(role)
    db_session.flush()

    # 刷新角色对象
    for key in roles:
        roles[key] = db_session.query(Role).filter(Role.role_code == roles[key].role_code).first()

    # 创建API权限
    permissions = {
        "user:list": ApiPermission(
            perm_code="user:list",
            perm_name="用户列表",
            module="user",
            action="VIEW",
            is_system=True,
        ),
        "user:create": ApiPermission(
            perm_code="user:create",
            perm_name="创建用户",
            module="user",
            action="CREATE",
            is_system=True,
        ),
        "project:list": ApiPermission(
            perm_code="project:list",
            perm_name="项目列表",
            module="project",
            action="VIEW",
            is_system=True,
        ),
        "project:create": ApiPermission(
            perm_code="project:create",
            perm_name="创建项目",
            module="project",
            action="CREATE",
            is_system=True,
        ),
        "project:detail": ApiPermission(
            perm_code="project:detail",
            perm_name="项目详情",
            module="project",
            action="VIEW",
            is_system=True,
        ),
        "sales:list": ApiPermission(
            perm_code="sales:list",
            perm_name="商机列表",
            module="sales",
            action="VIEW",
            is_system=True,
        ),
        "sales:create": ApiPermission(
            perm_code="sales:create",
            perm_name="创建商机",
            module="sales",
            action="CREATE",
            is_system=True,
        ),
    }

    for perm in permissions.values():
        existing_perm = (
            db_session.query(ApiPermission)
            .filter(ApiPermission.perm_code == perm.perm_code)
            .first()
        )
        if not existing_perm:
            db_session.add(perm)
    db_session.flush()

    # 刷新权限对象
    for key in permissions:
        permissions[key] = (
            db_session.query(ApiPermission)
            .filter(ApiPermission.perm_code == permissions[key].perm_code)
            .first()
        )

    # 分配权限给角色
    # 管理员：所有权限
    for perm_code in permissions:
        existing_rap = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == roles["admin"].id,
                RoleApiPermission.permission_id == permissions[perm_code].id,
            )
            .first()
        )
        if not existing_rap:
            rap = RoleApiPermission(
                role_id=roles["admin"].id, permission_id=permissions[perm_code].id
            )
            db_session.add(rap)

    # PM：项目相关权限
    for perm_code in ["project:list", "project:create", "project:detail"]:
        existing_rap = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == roles["pm"].id,
                RoleApiPermission.permission_id == permissions[perm_code].id,
            )
            .first()
        )
        if not existing_rap:
            rap = RoleApiPermission(role_id=roles["pm"].id, permission_id=permissions[perm_code].id)
            db_session.add(rap)

    # 工程师：项目列表和详情
    for perm_code in ["project:list", "project:detail"]:
        existing_rap = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == roles["engineer"].id,
                RoleApiPermission.permission_id == permissions[perm_code].id,
            )
            .first()
        )
        if not existing_rap:
            rap = RoleApiPermission(
                role_id=roles["engineer"].id, permission_id=permissions[perm_code].id
            )
            db_session.add(rap)

    # 销售：商机权限
    for perm_code in ["sales:list", "sales:create"]:
        existing_rap = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == roles["sales"].id,
                RoleApiPermission.permission_id == permissions[perm_code].id,
            )
            .first()
        )
        if not existing_rap:
            rap = RoleApiPermission(
                role_id=roles["sales"].id, permission_id=permissions[perm_code].id
            )
            db_session.add(rap)

    db_session.commit()

    # 创建测试用户
    users = {
        "admin": User(
            username="test_admin",
            password_hash=get_password_hash("admin123"),
            real_name="测试管理员",
            email="admin@test.com",
            is_active=True,
            is_superuser=True,
        ),
        "pm": User(
            username="test_pm",
            password_hash=get_password_hash("pm123"),
            real_name="测试项目经理",
            email="pm@test.com",
            is_active=True,
            is_superuser=False,
        ),
        "engineer": User(
            username="test_engineer",
            password_hash=get_password_hash("engineer123"),
            real_name="测试工程师",
            email="engineer@test.com",
            is_active=True,
            is_superuser=False,
        ),
        "sales": User(
            username="test_sales",
            password_hash=get_password_hash("sales123"),
            real_name="测试销售",
            email="sales@test.com",
            is_active=True,
            is_superuser=False,
        ),
    }

    for user_type, user in users.items():
        existing_user = db_session.query(User).filter(User.username == user.username).first()
        if existing_user:
            users[user_type] = existing_user
        else:
            db_session.add(user)
            db_session.flush()
            users[user_type] = user

    # 分配角色给用户
    for user_type in ["admin", "pm", "engineer", "sales"]:
        existing_user_role = (
            db_session.query(UserRole)
            .filter(
                UserRole.user_id == users[user_type].id,
                UserRole.role_id == roles[user_type].id,
            )
            .first()
        )
        if not existing_user_role:
            user_role = UserRole(user_id=users[user_type].id, role_id=roles[user_type].id)
            db_session.add(user_role)

    db_session.commit()

    # 清理权限缓存
    try:
        from app.services.permission_cache_service import get_permission_cache_service

        cache_service = get_permission_cache_service()
        for user in users.values():
            cache_service.invalidate_user_permissions(user.id)
    except Exception:
        pass

    return users, roles


@pytest.fixture(scope="function")
def setup_test_data(db_session: Session, setup_test_users_and_roles):
    """设置测试数据"""
    users, roles = setup_test_users_and_roles

    # 创建客户
    customer = Customer(
        customer_code="CUST-TEST-PERM",
        customer_name="权限测试客户",
        contact_person="联系人",
        contact_phone="13800138000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    # 创建项目
    projects = {
        "pm_project": Project(
            project_code="PJ-PM-TEST",
            project_name="PM负责的项目",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            created_by=users["pm"].id,
            pm_id=users["pm"].id,
        ),
        "other_project": Project(
            project_code="PJ-OTHER-TEST",
            project_name="其他项目",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            created_by=users["admin"].id,
        ),
    }

    for project in projects.values():
        db_session.add(project)
    db_session.flush()

    # 添加项目成员
    pm_member = ProjectMember(
        project_id=projects["pm_project"].id,
        user_id=users["pm"].id,
        role_code="PM",
        start_date=date.today(),
    )
    db_session.add(pm_member)

    engineer_member = ProjectMember(
        project_id=projects["pm_project"].id,
        user_id=users["engineer"].id,
        role_code="ENGINEER",
        start_date=date.today(),
    )
    db_session.add(engineer_member)

    db_session.commit()

    return {
        "users": users,
        "roles": roles,
        "customer": customer,
        "projects": projects,
    }


@pytest.mark.integration
class TestUserManagementPermissions:
    """用户管理端点权限测试"""

    def test_admin_can_list_users(self, client: TestClient, setup_test_data):
        """测试管理员可以访问用户列表"""
        helper = APITestHelper(client)
        response = helper.get(
            "/users", username="test_admin", password="admin123"
        )

        passed = response["status_code"] == 200
        test_report.add_result(
            test_name="管理员访问用户列表",
            role="admin",
            endpoint="/users",
            method="GET",
            expected_status=200,
            actual_status=response["status_code"],
            passed=passed,
            message="管理员应该可以访问用户列表" if passed else f"访问失败: {response.get('text', '')}",
        )
        assert passed

    def test_pm_cannot_list_users(self, client: TestClient, setup_test_data):
        """测试PM不能访问用户列表"""
        helper = APITestHelper(client)
        response = helper.get(
            "/users", username="test_pm", password="pm123"
        )

        # PM没有user:list权限，应该返回403
        passed = response["status_code"] == 403
        test_report.add_result(
            test_name="PM访问用户列表（应被拒绝）",
            role="pm",
            endpoint="/users",
            method="GET",
            expected_status=403,
            actual_status=response["status_code"],
            passed=passed,
            message="PM不应该有访问用户列表的权限" if passed else f"期望403但得到{response['status_code']}",
        )
        assert passed

    def test_engineer_cannot_list_users(self, client: TestClient, setup_test_data):
        """测试工程师不能访问用户列表"""
        helper = APITestHelper(client)
        response = helper.get(
            "/users", username="test_engineer", password="engineer123"
        )

        passed = response["status_code"] == 403
        test_report.add_result(
            test_name="工程师访问用户列表（应被拒绝）",
            role="engineer",
            endpoint="/users",
            method="GET",
            expected_status=403,
            actual_status=response["status_code"],
            passed=passed,
            message="工程师不应该有访问用户列表的权限" if passed else f"期望403但得到{response['status_code']}",
        )
        assert passed

    def test_admin_can_create_user(self, client: TestClient, setup_test_data):
        """测试管理员可以创建用户"""
        helper = APITestHelper(client)
        user_data = {
            "username": f"new_user_{datetime.now().timestamp()}",
            "password": "password123",
            "real_name": "新用户",
            "email": f"new_user_{datetime.now().timestamp()}@test.com",
        }

        response = helper.post(
            "/users", data=user_data, username="test_admin", password="admin123"
        )

        passed = response["status_code"] in [200, 201]
        test_report.add_result(
            test_name="管理员创建用户",
            role="admin",
            endpoint="/users",
            method="POST",
            expected_status=201,
            actual_status=response["status_code"],
            passed=passed,
            message="管理员应该可以创建用户" if passed else f"创建失败: {response.get('text', '')}",
        )
        assert passed

    def test_pm_cannot_create_user(self, client: TestClient, setup_test_data):
        """测试PM不能创建用户"""
        helper = APITestHelper(client)
        user_data = {
            "username": f"new_user_pm_{datetime.now().timestamp()}",
            "password": "password123",
            "real_name": "PM创建的用户",
            "email": f"new_user_pm_{datetime.now().timestamp()}@test.com",
        }

        response = helper.post(
            "/users", data=user_data, username="test_pm", password="pm123"
        )

        passed = response["status_code"] == 403
        test_report.add_result(
            test_name="PM创建用户（应被拒绝）",
            role="pm",
            endpoint="/users",
            method="POST",
            expected_status=403,
            actual_status=response["status_code"],
            passed=passed,
            message="PM不应该有创建用户的权限" if passed else f"期望403但得到{response['status_code']}",
        )
        assert passed


@pytest.mark.integration
class TestProjectManagementPermissions:
    """项目管理端点权限测试"""

    def test_admin_can_list_projects(self, client: TestClient, setup_test_data):
        """测试管理员可以访问所有项目"""
        helper = APITestHelper(client)
        response = helper.get(
            "/projects", username="test_admin", password="admin123"
        )

        passed = response["status_code"] == 200
        test_report.add_result(
            test_name="管理员访问项目列表",
            role="admin",
            endpoint="/projects",
            method="GET",
            expected_status=200,
            actual_status=response["status_code"],
            passed=passed,
            message="管理员应该可以访问所有项目" if passed else f"访问失败: {response.get('text', '')}",
        )
        assert passed

    def test_pm_can_list_projects(self, client: TestClient, setup_test_data):
        """测试PM可以访问项目列表"""
        helper = APITestHelper(client)
        response = helper.get(
            "/projects", username="test_pm", password="pm123"
        )

        passed = response["status_code"] == 200
        test_report.add_result(
            test_name="PM访问项目列表",
            role="pm",
            endpoint="/projects",
            method="GET",
            expected_status=200,
            actual_status=response["status_code"],
            passed=passed,
            message="PM应该可以访问项目列表" if passed else f"访问失败: {response.get('text', '')}",
        )
        assert passed

    def test_engineer_can_list_projects(self, client: TestClient, setup_test_data):
        """测试工程师可以访问项目列表"""
        helper = APITestHelper(client)
        response = helper.get(
            "/projects", username="test_engineer", password="engineer123"
        )

        passed = response["status_code"] == 200
        test_report.add_result(
            test_name="工程师访问项目列表",
            role="engineer",
            endpoint="/projects",
            method="GET",
            expected_status=200,
            actual_status=response["status_code"],
            passed=passed,
            message="工程师应该可以访问项目列表" if passed else f"访问失败: {response.get('text', '')}",
        )
        assert passed

    def test_admin_can_create_project(self, client: TestClient, setup_test_data):
        """测试管理员可以创建项目"""
        helper = APITestHelper(client)
        test_data = setup_test_data
        project_data = {
            "project_code": f"PJ-ADMIN-{datetime.now().timestamp()}",
            "project_name": "管理员创建的项目",
            "customer_id": test_data["customer"].id,
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
        }

        response = helper.post(
            "/projects", data=project_data, username="test_admin", password="admin123"
        )

        passed = response["status_code"] in [200, 201]
        test_report.add_result(
            test_name="管理员创建项目",
            role="admin",
            endpoint="/projects",
            method="POST",
            expected_status=201,
            actual_status=response["status_code"],
            passed=passed,
            message="管理员应该可以创建项目" if passed else f"创建失败: {response.get('text', '')}",
        )
        assert passed

    def test_pm_can_create_project(self, client: TestClient, setup_test_data):
        """测试PM可以创建项目"""
        helper = APITestHelper(client)
        test_data = setup_test_data
        project_data = {
            "project_code": f"PJ-PM-{datetime.now().timestamp()}",
            "project_name": "PM创建的项目",
            "customer_id": test_data["customer"].id,
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
        }

        response = helper.post(
            "/projects", data=project_data, username="test_pm", password="pm123"
        )

        passed = response["status_code"] in [200, 201]
        test_report.add_result(
            test_name="PM创建项目",
            role="pm",
            endpoint="/projects",
            method="POST",
            expected_status=201,
            actual_status=response["status_code"],
            passed=passed,
            message="PM应该可以创建项目" if passed else f"创建失败: {response.get('text', '')}",
        )
        assert passed

    def test_engineer_cannot_create_project(self, client: TestClient, setup_test_data):
        """测试工程师不能创建项目"""
        helper = APITestHelper(client)
        test_data = setup_test_data
        project_data = {
            "project_code": f"PJ-ENG-{datetime.now().timestamp()}",
            "project_name": "工程师尝试创建的项目",
            "customer_id": test_data["customer"].id,
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
        }

        response = helper.post(
            "/projects", data=project_data, username="test_engineer", password="engineer123"
        )

        passed = response["status_code"] == 403
        test_report.add_result(
            test_name="工程师创建项目（应被拒绝）",
            role="engineer",
            endpoint="/projects",
            method="POST",
            expected_status=403,
            actual_status=response["status_code"],
            passed=passed,
            message="工程师不应该有创建项目的权限" if passed else f"期望403但得到{response['status_code']}",
        )
        assert passed


@pytest.mark.integration
class TestDataScopeFiltering:
    """数据范围过滤测试"""

    def test_pm_can_see_own_projects(self, client: TestClient, setup_test_data):
        """测试PM可以看到自己负责的项目"""
        helper = APITestHelper(client)
        test_data = setup_test_data

        response = helper.get(
            "/projects", username="test_pm", password="pm123"
        )

        if response["status_code"] == 200:
            data = response.get("data", {})
            items = data.get("items", []) if isinstance(data, dict) else data

            # PM应该能看到自己负责的项目
            pm_project_visible = any(
                p.get("project_code") == "PJ-PM-TEST" for p in items
            )

            passed = pm_project_visible
            test_report.add_result(
                test_name="PM查看自己的项目",
                role="pm",
                endpoint="/projects",
                method="GET",
                expected_status=200,
                actual_status=response["status_code"],
                passed=passed,
                message="PM应该能看到自己负责的项目" if passed else "PM看不到自己的项目",
            )
            assert passed
        else:
            test_report.add_result(
                test_name="PM查看自己的项目",
                role="pm",
                endpoint="/projects",
                method="GET",
                expected_status=200,
                actual_status=response["status_code"],
                passed=False,
                message=f"获取项目列表失败: {response.get('text', '')}",
            )
            assert False

    def test_engineer_can_see_assigned_projects(self, client: TestClient, setup_test_data):
        """测试工程师可以看到分配给自己的项目"""
        helper = APITestHelper(client)
        test_data = setup_test_data

        response = helper.get(
            "/projects", username="test_engineer", password="engineer123"
        )

        if response["status_code"] == 200:
            data = response.get("data", {})
            items = data.get("items", []) if isinstance(data, dict) else data

            # 工程师应该能看到自己参与的项目
            project_visible = any(
                p.get("project_code") == "PJ-PM-TEST" for p in items
            )

            passed = project_visible
            test_report.add_result(
                test_name="工程师查看分配的项目",
                role="engineer",
                endpoint="/projects",
                method="GET",
                expected_status=200,
                actual_status=response["status_code"],
                passed=passed,
                message="工程师应该能看到分配给自己的项目" if passed else "工程师看不到分配的项目",
            )
            assert passed
        else:
            test_report.add_result(
                test_name="工程师查看分配的项目",
                role="engineer",
                endpoint="/projects",
                method="GET",
                expected_status=200,
                actual_status=response["status_code"],
                passed=False,
                message=f"获取项目列表失败: {response.get('text', '')}",
            )
            assert False


@pytest.mark.integration
class TestRoleBasedAccessControl:
    """基于角色的访问控制综合测试"""

    def test_role_permission_matrix(self, client: TestClient, setup_test_data):
        """测试角色权限矩阵"""
        helper = APITestHelper(client)

        # 定义测试矩阵：(endpoint, method, admin_expected, pm_expected, engineer_expected)
        test_matrix = [
            ("/users", "GET", 200, 403, 403),
            ("/projects", "GET", 200, 200, 200),
            ("/roles", "GET", 200, 403, 403),
        ]

        users = {
            "admin": ("test_admin", "admin123"),
            "pm": ("test_pm", "pm123"),
            "engineer": ("test_engineer", "engineer123"),
        }

        for endpoint, method, admin_exp, pm_exp, engineer_exp in test_matrix:
            expectations = {
                "admin": admin_exp,
                "pm": pm_exp,
                "engineer": engineer_exp,
            }

            for role, (username, password) in users.items():
                if method == "GET":
                    response = helper.get(endpoint, username=username, password=password)
                else:
                    continue  # 暂不测试其他方法

                expected = expectations[role]
                passed = response["status_code"] == expected

                test_report.add_result(
                    test_name=f"角色权限矩阵测试: {role} {method} {endpoint}",
                    role=role,
                    endpoint=endpoint,
                    method=method,
                    expected_status=expected,
                    actual_status=response["status_code"],
                    passed=passed,
                    message=f"角色{role}访问{endpoint}应该返回{expected}"
                    if passed
                    else f"期望{expected}但得到{response['status_code']}",
                )


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时生成报告"""
    output_file = Path(__file__).parent.parent.parent / "api_permission_test_report.md"
    report_path = test_report.generate_report(str(output_file))
    print(f"\n✅ API权限测试报告已生成: {report_path}")
    print(f"   总测试数: {test_report.summary['total']}")
    print(f"   通过数: {test_report.summary['passed']}")
    print(f"   失败数: {test_report.summary['failed']}")
    print(
        f"   通过率: {test_report.summary['passed'] / test_report.summary['total'] * 100:.2f}%"
        if test_report.summary["total"] > 0
        else "   通过率: 0%"
    )
