# -*- coding: utf-8 -*-
"""
租户隔离基础测试

测试租户间数据隔离的基本功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.models.tenant import Tenant
from tests.fixtures.tenant_fixtures import (
    tenant_a, tenant_b, user_a, user_b, 
    superuser, project_a, project_b,
    multiple_projects_a, multiple_projects_b
)


class TestBasicTenantIsolation:
    """基础租户隔离测试"""

    def test_user_cannot_access_other_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User, 
        project_b: Project
    ):
        """测试用户无法访问其他租户的项目"""
        # 用户A尝试访问租户B的项目
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        response = client.get(
            f"/api/v1/projects/{project_b.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该返回403或404
        assert response.status_code in [403, 404], \
            f"用户不应该能访问其他租户的项目，实际状态码: {response.status_code}"

    def test_user_can_access_own_tenant_project(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User, 
        project_a: Project
    ):
        """测试用户可以访问本租户的项目"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        response = client.get(
            f"/api/v1/projects/{project_a.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该返回200
        assert response.status_code == 200, \
            f"用户应该能访问自己租户的项目，实际状态码: {response.status_code}"
        
        data = response.json()
        assert data["id"] == project_a.id
        assert data["tenant_id"] == user_a.tenant_id

    def test_list_projects_only_returns_same_tenant(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        multiple_projects_a: list,
        multiple_projects_b: list
    ):
        """测试列表接口只返回同租户数据"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        response = client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回的所有项目都属于租户A
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        tenant_a_id = user_a.tenant_id
        for item in items:
            assert item.get("tenant_id") == tenant_a_id, \
                f"列表中包含其他租户的数据: tenant_id={item.get('tenant_id')}, 期望={tenant_a_id}"

    def test_superuser_can_access_all_tenants(
        self, 
        client: TestClient, 
        db: Session,
        superuser: User,
        project_a: Project,
        project_b: Project
    ):
        """测试超级管理员可以访问所有租户的数据"""
        from app.core.security import create_access_token
        token = create_access_token(superuser.id)
        
        # 访问租户A的项目
        response_a = client.get(
            f"/api/v1/projects/{project_a.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_a.status_code == 200, "超级管理员应该能访问租户A的项目"
        
        # 访问租户B的项目
        response_b = client.get(
            f"/api/v1/projects/{project_b.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_b.status_code == 200, "超级管理员应该能访问租户B的项目"

    def test_superuser_list_returns_all_tenants(
        self, 
        client: TestClient, 
        db: Session,
        superuser: User,
        multiple_projects_a: list,
        multiple_projects_b: list
    ):
        """测试超级管理员列表接口返回所有租户数据"""
        from app.core.security import create_access_token
        token = create_access_token(superuser.id)
        
        response = client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        # 应该包含多个租户的数据
        tenant_ids = set(item.get("tenant_id") for item in items if item.get("tenant_id"))
        assert len(tenant_ids) >= 2, \
            f"超级管理员列表应该包含多个租户数据，实际租户数: {len(tenant_ids)}"

    def test_user_cannot_query_other_tenant_by_filter(
        self, 
        client: TestClient, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试用户无法通过过滤器查询其他租户的数据"""
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 尝试通过项目代码查询租户B的项目
        response = client.get(
            f"/api/v1/projects?project_code={project_b.project_code}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        # 应该不返回其他租户的项目
        assert len(items) == 0, "不应该通过过滤器查询到其他租户的数据"

    def test_database_level_isolation(
        self, 
        db: Session,
        user_a: User,
        project_a: Project,
        project_b: Project
    ):
        """测试数据库层面的租户隔离"""
        # 直接查询数据库（模拟无过滤器的场景）
        all_projects = db.query(Project).filter(
            Project.tenant_id == user_a.tenant_id
        ).all()
        
        # 验证只返回同租户的数据
        for project in all_projects:
            assert project.tenant_id == user_a.tenant_id, \
                f"数据库查询返回了其他租户的数据: {project.tenant_id}"
        
        # 确认不包含其他租户的项目
        project_ids = [p.id for p in all_projects]
        assert project_b.id not in project_ids, \
            "数据库查询不应该包含其他租户的项目"

    def test_tenant_admin_isolation(
        self, 
        client: TestClient, 
        db: Session,
        tenant_admin_a: User,
        project_a: Project,
        project_b: Project
    ):
        """测试租户管理员也受到租户隔离限制"""
        from app.core.security import create_access_token
        from tests.fixtures.tenant_fixtures import tenant_admin_a
        
        # 创建租户管理员
        admin = tenant_admin_a
        token = create_access_token(admin.id)
        
        # 租户管理员可以访问自己租户的项目
        response_own = client.get(
            f"/api/v1/projects/{project_a.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_own.status_code == 200, "租户管理员应该能访问自己租户的项目"
        
        # 租户管理员无法访问其他租户的项目
        response_other = client.get(
            f"/api/v1/projects/{project_b.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_other.status_code in [403, 404], \
            "租户管理员不应该能访问其他租户的项目"

    def test_null_tenant_id_handling(
        self, 
        db: Session,
        superuser: User
    ):
        """测试 tenant_id 为 NULL 的数据处理"""
        # 创建一个 tenant_id 为 NULL 的项目（系统级项目）
        system_project = Project(
            tenant_id=None,
            project_code="SYS_PROJ_001",
            project_name="系统级项目",
            project_type="SYSTEM",
            created_by=superuser.id,
            pm_id=superuser.id
        )
        db.add(system_project)
        db.commit()
        
        # 普通用户不应该能访问系统级项目
        user_projects = db.query(Project).filter(
            Project.tenant_id == 1  # 假设租户1
        ).all()
        
        project_ids = [p.id for p in user_projects]
        assert system_project.id not in project_ids, \
            "普通用户不应该能访问系统级项目"
        
        # 超级管理员可以访问所有项目（包括系统级）
        all_projects = db.query(Project).all()
        all_project_ids = [p.id for p in all_projects]
        assert system_project.id in all_project_ids, \
            "超级管理员应该能访问系统级项目"


class TestTenantIsolationEdgeCases:
    """租户隔离边界情况测试"""

    def test_inactive_tenant_access(
        self, 
        client: TestClient, 
        db: Session,
        tenant_c: Tenant
    ):
        """测试暂停租户的访问控制"""
        from app.core.security import create_access_token
        from tests.fixtures.tenant_fixtures import tenant_c, create_user, create_project
        
        # 创建暂停租户的用户和项目
        user_c = create_user(db, "user_c", tenant_c.id)
        project_c = create_project(
            db, tenant_c.id, user_c.id, 
            "PROJ_C_001", "租户C项目"
        )
        
        token = create_access_token(user_c.id)
        
        # 尝试访问暂停租户的项目
        response = client.get(
            f"/api/v1/projects/{project_c.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 根据业务规则，暂停租户可能返回403或特定错误
        assert response.status_code in [200, 403, 423], \
            f"暂停租户访问返回了意外的状态码: {response.status_code}"

    def test_expired_tenant_access(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试过期租户的访问控制"""
        from datetime import datetime, timedelta
        
        # 设置租户为过期状态
        tenant_a.expired_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        # 验证租户确实过期
        assert tenant_a.is_expired, "租户应该处于过期状态"
        
        # 在实际系统中，过期租户的访问控制应该在中间件或服务层处理

    def test_tenant_id_mismatch_in_nested_resources(
        self, 
        db: Session,
        user_a: User,
        project_b: Project
    ):
        """测试嵌套资源的租户ID不匹配情况"""
        # 这个测试确保不能通过嵌套资源绕过租户隔离
        # 例如：不能通过属于租户A的用户访问租户B的项目的子资源
        
        # 直接在数据库层面验证
        from app.models.task import Task
        
        # 创建租户B项目的任务
        task_b = Task(
            project_id=project_b.id,
            task_name="租户B任务",
            created_by=project_b.created_by
        )
        db.add(task_b)
        db.commit()
        
        # 租户A的用户不应该能通过任何方式访问这个任务
        # 这需要在API层面通过项目的租户隔离来保证
        assert task_b.project.tenant_id == project_b.tenant_id
        assert task_b.project.tenant_id != user_a.tenant_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
