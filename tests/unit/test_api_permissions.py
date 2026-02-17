# -*- coding: utf-8 -*-
"""
权限管理 API 单元测试
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from tests.conftest import TestClient


class TestPermissionAPI:
    """权限管理 API 测试类"""

    @pytest.fixture
    def test_permissions(self, db: Session, test_user: User) -> list:
        """创建测试权限"""
        permissions = []
        
        # 系统级权限
        perm1 = ApiPermission(
            tenant_id=None,  # 系统级
            perm_code="system:read",
            perm_name="系统读取",
            module="system",
            action="READ",
            description="系统级读取权限",
            is_active=True,
            is_system=True,
        )
        
        # 租户级权限
        perm2 = ApiPermission(
            tenant_id=test_user.tenant_id,
            perm_code="project:create",
            perm_name="创建项目",
            module="project",
            action="CREATE",
            description="项目创建权限",
            is_active=True,
            is_system=False,
        )
        
        perm3 = ApiPermission(
            tenant_id=test_user.tenant_id,
            perm_code="project:delete",
            perm_name="删除项目",
            module="project",
            action="DELETE",
            description="项目删除权限",
            is_active=True,
            is_system=False,
        )
        
        db.add_all([perm1, perm2, perm3])
        db.commit()
        
        permissions = [perm1, perm2, perm3]
        return permissions

    @pytest.fixture
    def test_role_with_permissions(
        self, db: Session, test_user: User, test_permissions: list
    ) -> Role:
        """创建带权限的测试角色"""
        role = Role(
            tenant_id=test_user.tenant_id,
            role_code="TEST_MANAGER",
            role_name="测试管理员",
            description="测试角色",
            is_active=True,
        )
        db.add(role)
        db.commit()
        
        # 分配权限
        for perm in test_permissions:
            db.add(RoleApiPermission(role_id=role.id, permission_id=perm.id))
        
        db.commit()
        return role

    # ============================================================
    # 测试用例 1: 权限列表查询
    # ============================================================

    def test_list_permissions_success(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试获取权限列表 - 成功"""
        response = client.get("/api/v1/permissions/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "items" in data["data"]
        assert len(data["data"]["items"]) >= 3  # 至少包含3个测试权限

    def test_list_permissions_filter_by_module(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试权限列表 - 按模块筛选"""
        response = client.get(
            "/api/v1/permissions/?module=project", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["data"]["items"]
        
        # 所有返回的权限模块都应该是 project
        for item in items:
            if item["module"]:
                assert item["module"] == "project"

    def test_list_permissions_filter_by_keyword(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试权限列表 - 关键词搜索"""
        response = client.get(
            "/api/v1/permissions/?keyword=创建", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["data"]["items"]
        
        # 至少应该找到包含"创建"的权限
        assert any("创建" in item["permission_name"] for item in items)

    def test_list_permissions_pagination(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试权限列表 - 分页"""
        response = client.get(
            "/api/v1/permissions/?page=1&page_size=2", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 2
        assert len(data["data"]["items"]) <= 2

    def test_list_permissions_unauthorized(self, client: TestClient):
        """测试权限列表 - 未授权"""
        response = client.get("/api/v1/permissions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ============================================================
    # 测试用例 2: 权限详情查询
    # ============================================================

    def test_get_permission_success(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试获取权限详情 - 成功"""
        perm = test_permissions[0]
        response = client.get(
            f"/api/v1/permissions/{perm.id}", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == perm.id
        assert data["data"]["permission_code"] == perm.perm_code

    def test_get_permission_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取权限详情 - 不存在"""
        response = client.get("/api/v1/permissions/999999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================================
    # 测试用例 3: 创建权限
    # ============================================================

    def test_create_permission_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """测试创建权限 - 成功"""
        response = client.post(
            "/api/v1/permissions/",
            params={
                "perm_code": "test:execute",
                "perm_name": "执行测试",
                "module": "testing",
                "action": "EXECUTE",
                "description": "测试执行权限",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["code"] == 201
        assert data["data"]["permission_code"] == "test:execute"
        
        # 验证数据库
        perm = db.query(ApiPermission).filter(
            ApiPermission.perm_code == "test:execute"
        ).first()
        assert perm is not None
        assert perm.perm_name == "执行测试"

    def test_create_permission_duplicate(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试创建权限 - 重复编码"""
        perm = test_permissions[0]
        response = client.post(
            "/api/v1/permissions/",
            params={
                "perm_code": perm.perm_code,  # 使用已存在的编码
                "perm_name": "重复权限",
                "module": "test",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "已存在" in response.json()["detail"]

    def test_create_permission_unauthorized(self, client: TestClient):
        """测试创建权限 - 未授权"""
        response = client.post(
            "/api/v1/permissions/",
            params={
                "perm_code": "test:new",
                "perm_name": "新权限",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ============================================================
    # 测试用例 4: 更新权限
    # ============================================================

    def test_update_permission_success(
        self, client: TestClient, auth_headers: dict, test_permissions: list, db: Session
    ):
        """测试更新权限 - 成功"""
        perm = test_permissions[1]  # 使用非系统权限
        
        response = client.put(
            f"/api/v1/permissions/{perm.id}",
            params={
                "perm_name": "更新后的名称",
                "description": "更新后的描述",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        
        # 验证数据库
        db.refresh(perm)
        assert perm.perm_name == "更新后的名称"
        assert perm.description == "更新后的描述"

    def test_update_permission_system_protected(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试更新权限 - 系统权限受保护"""
        perm = test_permissions[0]  # 系统权限
        
        response = client.put(
            f"/api/v1/permissions/{perm.id}",
            params={"perm_name": "尝试修改"},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "系统预置权限" in response.json()["detail"]

    def test_update_permission_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试更新权限 - 不存在"""
        response = client.put(
            "/api/v1/permissions/999999",
            params={"perm_name": "更新"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================================
    # 测试用例 5: 删除权限
    # ============================================================

    def test_delete_permission_success(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """测试删除权限 - 成功"""
        # 创建一个临时权限用于删除
        temp_perm = ApiPermission(
            tenant_id=test_user.tenant_id,
            perm_code="temp:delete",
            perm_name="临时权限",
            module="temp",
            is_active=True,
            is_system=False,
        )
        db.add(temp_perm)
        db.commit()
        
        response = client.delete(
            f"/api/v1/permissions/{temp_perm.id}", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证已删除
        deleted = db.query(ApiPermission).filter(
            ApiPermission.id == temp_perm.id
        ).first()
        assert deleted is None

    def test_delete_permission_system_protected(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试删除权限 - 系统权限受保护"""
        perm = test_permissions[0]  # 系统权限
        
        response = client.delete(
            f"/api/v1/permissions/{perm.id}", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND  # 系统权限不属于租户

    def test_delete_permission_in_use(
        self, client: TestClient, auth_headers: dict, test_role_with_permissions: Role
    ):
        """测试删除权限 - 被角色使用"""
        # 获取角色使用的权限
        role_perm = (
            client.db.query(RoleApiPermission)
            .filter(RoleApiPermission.role_id == test_role_with_permissions.id)
            .first()
        )
        
        response = client.delete(
            f"/api/v1/permissions/{role_perm.permission_id}", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "被" in response.json()["detail"]
        assert "使用" in response.json()["detail"]

    # ============================================================
    # 测试用例 6: 角色权限查询
    # ============================================================

    def test_get_role_permissions_success(
        self, client: TestClient, auth_headers: dict, test_role_with_permissions: Role
    ):
        """测试获取角色权限 - 成功"""
        response = client.get(
            f"/api/v1/permissions/roles/{test_role_with_permissions.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["role_id"] == test_role_with_permissions.id
        assert "permissions" in data["data"]
        assert len(data["data"]["permissions"]) >= 3

    def test_get_role_permissions_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取角色权限 - 角色不存在"""
        response = client.get(
            "/api/v1/permissions/roles/999999", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================================
    # 测试用例 7: 分配角色权限
    # ============================================================

    def test_assign_role_permissions_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_role_with_permissions: Role,
        test_permissions: list,
        db: Session,
    ):
        """测试分配角色权限 - 成功"""
        # 选择2个权限
        perm_ids = [test_permissions[1].id, test_permissions[2].id]
        
        response = client.post(
            f"/api/v1/permissions/roles/{test_role_with_permissions.id}",
            params={"permission_ids": perm_ids},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["assigned_count"] == 2
        
        # 验证数据库
        role_perms = db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == test_role_with_permissions.id
        ).all()
        assert len(role_perms) == 2

    def test_assign_role_permissions_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        test_role_with_permissions: Role,
        db: Session,
    ):
        """测试分配角色权限 - 清空权限"""
        response = client.post(
            f"/api/v1/permissions/roles/{test_role_with_permissions.id}",
            params={"permission_ids": []},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证权限已清空
        role_perms = db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == test_role_with_permissions.id
        ).all()
        assert len(role_perms) == 0

    # ============================================================
    # 测试用例 8: 用户权限查询
    # ============================================================

    def test_get_user_permissions_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_role_with_permissions: Role,
        db: Session,
    ):
        """测试获取用户权限 - 成功"""
        # 给用户分配角色
        db.add(UserRole(user_id=test_user.id, role_id=test_role_with_permissions.id))
        db.commit()
        
        response = client.get(
            f"/api/v1/permissions/users/{test_user.id}", headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["user_id"] == test_user.id
        assert "permissions" in data["data"]
        assert data["data"]["permission_count"] >= 1

    def test_get_user_permissions_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取用户权限 - 用户不存在"""
        response = client.get(
            "/api/v1/permissions/users/999999", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_check_user_permission_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_role_with_permissions: Role,
        test_permissions: list,
        db: Session,
    ):
        """测试检查用户权限 - 成功"""
        # 给用户分配角色
        db.add(UserRole(user_id=test_user.id, role_id=test_role_with_permissions.id))
        db.commit()
        
        response = client.get(
            f"/api/v1/permissions/users/{test_user.id}/check",
            params={"permission_code": test_permissions[1].perm_code},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert "has_permission" in data["data"]

    # ============================================================
    # 测试用例 9: 模块列表查询
    # ============================================================

    def test_list_modules_success(
        self, client: TestClient, auth_headers: dict, test_permissions: list
    ):
        """测试获取模块列表 - 成功"""
        response = client.get("/api/v1/permissions/modules", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
        assert "system" in data["data"]
        assert "project" in data["data"]

    # ============================================================
    # 测试用例 10: 多租户隔离测试
    # ============================================================

    def test_tenant_isolation(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: User
    ):
        """测试多租户隔离 - 不同租户看不到对方的权限"""
        # 创建另一个租户的权限
        other_tenant_perm = ApiPermission(
            tenant_id=999,  # 不同的租户
            perm_code="other:read",
            perm_name="其他租户权限",
            module="other",
            is_active=True,
            is_system=False,
        )
        db.add(other_tenant_perm)
        db.commit()
        
        # 获取权限列表
        response = client.get("/api/v1/permissions/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 不应该包含其他租户的权限
        perm_codes = [item["permission_code"] for item in data["data"]["items"]]
        assert "other:read" not in perm_codes
        
        # 尝试直接访问其他租户的权限详情
        response = client.get(
            f"/api/v1/permissions/{other_tenant_perm.id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
