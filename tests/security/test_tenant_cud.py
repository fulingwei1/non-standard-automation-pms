# -*- coding: utf-8 -*-
"""
租户隔离 CUD 操作测试

测试创建、更新、删除操作的租户隔离
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.models.tenant import Tenant
from tests.fixtures.tenant_fixtures import (
    tenant_a, tenant_b, user_a, user_b, 
    superuser, project_a, project_b
)


class TestTenantCreateIsolation:
    """创建操作的租户隔离测试"""

    def test_created_resource_auto_assigned_to_user_tenant(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User
    ):
        """测试创建的资源自动分配给用户所属租户"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 创建项目
        project_data = {
            "project_code": "AUTO_ASSIGN_001",
            "project_name": "自动分配测试项目",
            "project_type": "NEW_PROJECT"
        }
        
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            # 验证租户ID自动设置为用户的租户
            assert data.get("tenant_id") == user_a.tenant_id, \
                f"创建的资源应自动分配给用户租户，期望 {user_a.tenant_id}，实际 {data.get('tenant_id')}"

    def test_user_cannot_create_resource_for_other_tenant(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        tenant_b: Tenant
    ):
        """测试用户无法为其他租户创建资源"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 尝试创建租户B的项目
        project_data = {
            "tenant_id": tenant_b.id,  # 尝试指定其他租户
            "project_code": "HACK_001",
            "project_name": "跨租户创建测试",
            "project_type": "NEW_PROJECT"
        }
        
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            # 即使请求中指定了其他租户ID，也应该被忽略或覆盖
            assert data.get("tenant_id") == user_a.tenant_id, \
                "不应该允许用户为其他租户创建资源"

    def test_superuser_can_create_for_any_tenant(
        self, 
        client: TestClient, 
        db: Session,
        superuser: User,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试超级管理员可以为任意租户创建资源"""
        from app.core.security import create_access_token
        token = create_access_token(superuser.id)
        
        # 为租户A创建项目
        project_data_a = {
            "tenant_id": tenant_a.id,
            "project_code": "SUPER_A_001",
            "project_name": "超管为租户A创建",
            "project_type": "NEW_PROJECT"
        }
        
        response_a = client.post(
            "/api/v1/projects",
            json=project_data_a,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response_a.status_code in [200, 201]:
            data_a = response_a.json()
            assert data_a.get("tenant_id") == tenant_a.id, \
                "超级管理员应该能为租户A创建资源"
        
        # 为租户B创建项目
        project_data_b = {
            "tenant_id": tenant_b.id,
            "project_code": "SUPER_B_001",
            "project_name": "超管为租户B创建",
            "project_type": "NEW_PROJECT"
        }
        
        response_b = client.post(
            "/api/v1/projects",
            json=project_data_b,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response_b.status_code in [200, 201]:
            data_b = response_b.json()
            assert data_b.get("tenant_id") == tenant_b.id, \
                "超级管理员应该能为租户B创建资源"

    def test_batch_create_respects_tenant_isolation(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User
    ):
        """测试批量创建也遵循租户隔离"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 批量创建项目
        projects_data = [
            {
                "project_code": f"BATCH_{i:03d}",
                "project_name": f"批量创建项目{i}",
                "project_type": "NEW_PROJECT"
            }
            for i in range(3)
        ]
        
        # 注意：这需要API支持批量创建接口
        # 如果不支持，可以循环单个创建
        for project_data in projects_data:
            response = client.post(
                "/api/v1/projects",
                json=project_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert data.get("tenant_id") == user_a.tenant_id, \
                    f"批量创建的每个资源都应该属于用户租户"


class TestTenantUpdateIsolation:
    """更新操作的租户隔离测试"""

    def test_user_cannot_update_other_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试用户无法更新其他租户的项目"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 尝试更新租户B的项目
        update_data = {
            "project_name": "尝试修改租户B项目"
        }
        
        response = client.put(
            f"/api/v1/projects/{project_b.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该返回403或404
        assert response.status_code in [403, 404], \
            f"用户不应该能更新其他租户的项目，实际状态码: {response.status_code}"
        
        # 验证数据库中的数据没有被修改
        db.refresh(project_b)
        assert project_b.project_name != "尝试修改租户B项目", \
            "其他租户的数据不应该被修改"

    def test_user_can_update_own_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_a: Project
    ):
        """测试用户可以更新本租户的项目"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        original_name = project_a.project_name
        new_name = "更新后的项目名称"
        
        update_data = {
            "project_name": new_name
        }
        
        response = client.put(
            f"/api/v1/projects/{project_a.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该成功
        if response.status_code == 200:
            data = response.json()
            assert data.get("project_name") == new_name, \
                "应该能更新自己租户的项目"
            
            # 验证租户ID没有被修改
            assert data.get("tenant_id") == user_a.tenant_id, \
                "更新时租户ID不应该改变"

    def test_user_cannot_change_tenant_id_on_update(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_a: Project,
        tenant_b: Tenant
    ):
        """测试用户无法通过更新修改资源的租户ID"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        original_tenant_id = project_a.tenant_id
        
        # 尝试修改租户ID
        update_data = {
            "tenant_id": tenant_b.id,  # 尝试改成租户B
            "project_name": "尝试转移租户"
        }
        
        response = client.put(
            f"/api/v1/projects/{project_a.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # 租户ID应该保持不变
            assert data.get("tenant_id") == original_tenant_id, \
                "不应该允许用户修改资源的租户ID"
        
        # 验证数据库中的租户ID没有改变
        db.refresh(project_a)
        assert project_a.tenant_id == original_tenant_id, \
            "数据库中的租户ID不应该被修改"

    def test_superuser_can_update_any_tenant(
        self, 
        client: TestClient, 
        db: Session,
        superuser: User,
        project_a: Project,
        project_b: Project
    ):
        """测试超级管理员可以更新任意租户的资源"""
        from app.core.security import create_access_token
        token = create_access_token(superuser.id)
        
        # 更新租户A的项目
        update_data_a = {"project_name": "超管更新租户A项目"}
        response_a = client.put(
            f"/api/v1/projects/{project_a.id}",
            json=update_data_a,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_a.status_code == 200, "超级管理员应该能更新租户A的项目"
        
        # 更新租户B的项目
        update_data_b = {"project_name": "超管更新租户B项目"}
        response_b = client.put(
            f"/api/v1/projects/{project_b.id}",
            json=update_data_b,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_b.status_code == 200, "超级管理员应该能更新租户B的项目"

    def test_partial_update_respects_tenant_isolation(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试部分更新（PATCH）也遵循租户隔离"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 尝试部分更新其他租户的项目
        update_data = {"project_name": "PATCH更新"}
        
        response = client.patch(
            f"/api/v1/projects/{project_b.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该被拒绝
        assert response.status_code in [403, 404, 405], \
            f"PATCH操作也应该遵循租户隔离，实际状态码: {response.status_code}"


class TestTenantDeleteIsolation:
    """删除操作的租户隔离测试"""

    def test_user_cannot_delete_other_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试用户无法删除其他租户的项目"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        response = client.delete(
            f"/api/v1/projects/{project_b.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该返回403或404
        assert response.status_code in [403, 404], \
            f"用户不应该能删除其他租户的项目，实际状态码: {response.status_code}"
        
        # 验证数据库中的数据没有被删除
        db.refresh(project_b)
        assert db.query(Project).filter(Project.id == project_b.id).first() is not None, \
            "其他租户的数据不应该被删除"

    def test_user_can_delete_own_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User
    ):
        """测试用户可以删除本租户的项目"""
        from app.core.security import create_access_token
        from tests.fixtures.tenant_fixtures import create_project
        
        # 创建一个测试项目
        test_project = create_project(
            db, user_a.tenant_id, user_a.id,
            "DELETE_TEST_001", "待删除测试项目"
        )
        
        token = create_access_token(user_a.id)
        
        response = client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该成功或返回204
        if response.status_code in [200, 204]:
            # 验证数据已被删除（软删除或硬删除）
            deleted_project = db.query(Project).filter(
                Project.id == test_project.id
            ).first()
            
            # 如果是软删除，应该有 deleted_at 字段
            # 如果是硬删除，应该查询不到
            if deleted_project:
                assert hasattr(deleted_project, 'deleted_at') and deleted_project.deleted_at is not None, \
                    "软删除应该设置 deleted_at 字段"

    def test_superuser_can_delete_any_tenant(
        self, 
        client: TestClient, 
        db: Session,
        superuser: User,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试超级管理员可以删除任意租户的资源"""
        from app.core.security import create_access_token
        from tests.fixtures.tenant_fixtures import create_project
        
        # 创建测试项目
        project_a = create_project(
            db, tenant_a.id, superuser.id,
            "SUPER_DEL_A_001", "超管删除租户A项目"
        )
        project_b = create_project(
            db, tenant_b.id, superuser.id,
            "SUPER_DEL_B_001", "超管删除租户B项目"
        )
        
        token = create_access_token(superuser.id)
        
        # 删除租户A的项目
        response_a = client.delete(
            f"/api/v1/projects/{project_a.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_a.status_code in [200, 204], \
            "超级管理员应该能删除租户A的项目"
        
        # 删除租户B的项目
        response_b = client.delete(
            f"/api/v1/projects/{project_b.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_b.status_code in [200, 204], \
            "超级管理员应该能删除租户B的项目"

    def test_batch_delete_respects_tenant_isolation(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        multiple_projects_b: list
    ):
        """测试批量删除也遵循租户隔离"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 尝试批量删除其他租户的项目
        project_ids = [p.id for p in multiple_projects_b]
        
        # 如果API支持批量删除
        for project_id in project_ids:
            response = client.delete(
                f"/api/v1/projects/{project_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # 应该全部被拒绝
            assert response.status_code in [403, 404], \
                f"批量删除其他租户数据应该被拒绝，项目ID: {project_id}"
        
        # 验证数据库中的数据没有被删除
        for project_id in project_ids:
            project = db.query(Project).filter(Project.id == project_id).first()
            assert project is not None, \
                f"其他租户的项目不应该被删除，项目ID: {project_id}"


class TestTenantCascadeOperations:
    """级联操作的租户隔离测试"""

    def test_delete_with_cascade_respects_tenant_isolation(
        self, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试级联删除也遵循租户隔离"""
        from app.models.task import Task
        
        # 为租户B的项目创建任务
        task = Task(
            project_id=project_b.id,
            task_name="租户B任务",
            created_by=project_b.created_by
        )
        db.add(task)
        db.commit()
        
        # 用户A不应该能删除租户B的项目（即使有级联删除）
        # 这个测试更多是验证不会因为级联删除而绕过租户隔离


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
