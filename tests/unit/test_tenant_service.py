# -*- coding: utf-8 -*-
"""
租户服务单元测试

测试 TenantService 的业务逻辑
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.tenant import Tenant, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.tenant_service import TenantService


_UNSET = object()


def _query(*, first=_UNSET, all_=_UNSET, scalar=_UNSET, subquery=_UNSET):
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    if first is not _UNSET:
        query.first.return_value = first
    if all_ is not _UNSET:
        query.all.return_value = all_
    if scalar is not _UNSET:
        query.scalar.return_value = scalar
    if subquery is not _UNSET:
        query.subquery.return_value = subquery
    return query


class TestTenantServiceCreate:
    """租户创建测试"""

    def test_generate_tenant_code(self):
        """测试生成租户编码"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        code = service.generate_tenant_code()

        assert code.startswith("T")
        assert len(code) == 9  # T + 8 hex chars

    def test_create_tenant_success(self):
        """测试成功创建租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant_in = TenantCreate(
            tenant_name="测试租户",
            plan_type="STANDARD",
            contact_name="张三",
            contact_email="zhangsan@example.com",
        )

        tenant = service.create_tenant(tenant_in)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_tenant_duplicate_code(self):
        """测试创建重复编码的租户"""
        mock_db = MagicMock()
        existing_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="已存在")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        tenant_in = TenantCreate(
            tenant_code="T12345678",
            tenant_name="新租户",
        )

        with pytest.raises(ValueError, match="已存在"):
            service.create_tenant(tenant_in)

    def test_create_tenant_with_plan_limits(self):
        """测试不同套餐的限制"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)

        # 测试免费套餐
        tenant_in = TenantCreate(tenant_name="免费租户", plan_type="FREE")
        service.create_tenant(tenant_in)

        # 验证调用了 add
        call_args = mock_db.add.call_args
        tenant = call_args[0][0]
        assert tenant.max_users == 5
        assert tenant.max_roles == 5


class TestTenantServiceRead:
    """租户查询测试"""

    def test_get_tenant_exists(self):
        """测试获取存在的租户"""
        mock_db = MagicMock()
        expected_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="测试")
        mock_db.query.return_value.filter.return_value.first.return_value = expected_tenant

        service = TenantService(mock_db)
        tenant = service.get_tenant(1)

        assert tenant == expected_tenant

    def test_get_tenant_not_exists(self):
        """测试获取不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant = service.get_tenant(999)

        assert tenant is None

    def test_get_tenant_by_code(self):
        """测试根据编码获取租户"""
        mock_db = MagicMock()
        expected_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="测试")
        mock_db.query.return_value.filter.return_value.first.return_value = expected_tenant

        service = TenantService(mock_db)
        tenant = service.get_tenant_by_code("T12345678")

        assert tenant == expected_tenant

    def test_list_tenants(self):
        """测试获取租户列表"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            Tenant(id=1, tenant_code="T001", tenant_name="租户1"),
            Tenant(id=2, tenant_code="T002", tenant_name="租户2"),
        ]

        service = TenantService(mock_db)
        result = service.list_tenants(page=1, page_size=20)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 20

    def test_list_tenants_with_filter(self):
        """测试带筛选条件的租户列表"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            Tenant(id=1, tenant_code="T001", tenant_name="活跃租户", status="ACTIVE"),
        ]

        service = TenantService(mock_db)
        result = service.list_tenants(status="ACTIVE", keyword="活跃")

        assert result["total"] == 1


class TestTenantServiceUpdate:
    """租户更新测试"""

    def test_update_tenant_success(self):
        """测试成功更新租户"""
        mock_db = MagicMock()
        existing_tenant = Tenant(
            id=1, tenant_code="T12345678", tenant_name="原名称", contact_name="原联系人"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        tenant_in = TenantUpdate(tenant_name="新名称", contact_name="新联系人")

        tenant = service.update_tenant(1, tenant_in)

        assert tenant.tenant_name == "新名称"
        assert tenant.contact_name == "新联系人"
        mock_db.commit.assert_called_once()

    def test_update_tenant_not_exists(self):
        """测试更新不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant_in = TenantUpdate(tenant_name="新名称")

        result = service.update_tenant(999, tenant_in)

        assert result is None


class TestTenantServiceDelete:
    """租户删除测试"""

    def test_delete_tenant_success(self):
        """测试成功删除租户（软删除）"""
        mock_db = MagicMock()
        existing_tenant = Tenant(
            id=1, tenant_code="T12345678", tenant_name="待删除", status="ACTIVE"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        result = service.delete_tenant(1)

        assert result is True
        assert existing_tenant.status == TenantStatus.DELETED.value
        mock_db.commit.assert_called_once()

    def test_delete_tenant_not_exists(self):
        """测试删除不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        result = service.delete_tenant(999)

        assert result is False


class TestTenantServiceStats:
    """租户统计测试"""

    def test_get_tenant_stats_not_exists(self):
        """测试获取不存在租户的统计信息"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        stats = service.get_tenant_stats(999)

        assert stats is None


class TestTenantServiceInitAndStats:
    def test_init_tenant_raises_when_tenant_missing(self):
        service = TenantService(MagicMock())
        service.get_tenant = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="租户不存在"):
            service.init_tenant(
                1,
                None,
            )

    @patch("app.services.tenant_service.get_password_hash", return_value="hashed-password")
    def test_init_tenant_copies_templates_and_creates_admin(self, mock_hash):
        mock_db = MagicMock()
        service = TenantService(mock_db)
        tenant = Tenant(id=1, tenant_code="T00000001", tenant_name="租户A")
        service.get_tenant = MagicMock(return_value=tenant)

        templates = [
            SimpleNamespace(
                id=11,
                template_code="TENANT_ADMIN",
                template_name="租户管理员",
                description="admin",
                data_scope="ALL",
                nav_groups=["system"],
                ui_config={"home": True},
                sort_order=1,
            ),
            SimpleNamespace(
                id=12,
                template_code="EXISTING_ROLE",
                template_name="已存在角色",
                description="exists",
                data_scope="OWN",
                nav_groups=None,
                ui_config=None,
                sort_order=2,
            ),
        ]
        tenant_admin_role = SimpleNamespace(id=88)
        mock_db.query.side_effect = [
            _query(all_=templates),
            _query(first=None),
            _query(first=SimpleNamespace(id=99)),
            _query(first=None),
            _query(first=tenant_admin_role),
        ]

        added_objects = []

        def add_side_effect(obj):
            added_objects.append(obj)

        def flush_side_effect():
            for obj in added_objects:
                if obj.__class__.__name__ == "Employee" and getattr(obj, "id", None) is None:
                    obj.id = 101
                if obj.__class__.__name__ == "User" and getattr(obj, "id", None) is None:
                    obj.id = 202

        mock_db.add.side_effect = add_side_effect
        mock_db.flush.side_effect = flush_side_effect

        result = service.init_tenant(
            1,
            SimpleNamespace(
                admin_username="tenant_admin",
                admin_password="secret123",
                admin_email="tenant@example.com",
                admin_real_name="Tenant Admin",
                copy_role_templates=True,
            ),
        )

        copied_role = next(obj for obj in added_objects if obj.__class__.__name__ == "Role")
        user_role = next(obj for obj in added_objects if obj.__class__.__name__ == "UserRole")
        employee = next(obj for obj in added_objects if obj.__class__.__name__ == "Employee")
        admin_user = next(obj for obj in added_objects if obj.__class__.__name__ == "User")

        assert copied_role.role_code == "TENANT_ADMIN"
        assert copied_role.role_name == "租户管理员"
        assert employee.employee_code.startswith("T1A")
        assert admin_user.username == "tenant_admin"
        assert user_role.user_id == 202
        assert user_role.role_id == 88
        assert result == {"tenant_id": 1, "roles_created": 1, "admin_created": True, "admin_user_id": 202}
        mock_hash.assert_called_once_with("secret123")
        mock_db.commit.assert_called_once()

    def test_init_tenant_raises_when_admin_username_exists(self):
        mock_db = MagicMock()
        service = TenantService(mock_db)
        service.get_tenant = MagicMock(return_value=Tenant(id=1, tenant_code="T0001", tenant_name="租户"))
        mock_db.query.side_effect = [_query(first=SimpleNamespace(id=7))]

        with pytest.raises(ValueError, match="用户名 existed 已存在"):
            service.init_tenant(
                1,
                SimpleNamespace(
                    admin_username="existed",
                    admin_password="secret123",
                    admin_email="tenant@example.com",
                    admin_real_name=None,
                    copy_role_templates=False,
                ),
            )

    def test_get_tenant_stats_aggregates_counts_projects_and_storage(self):
        mock_db = MagicMock()
        service = TenantService(mock_db)
        tenant = Tenant(id=1, tenant_code="T00000001", tenant_name="租户A", plan_type="STANDARD")
        service.get_tenant = MagicMock(return_value=tenant)
        project_user_ids = MagicMock(name="project_user_ids")
        attachment_user_ids = MagicMock(name="attachment_user_ids")
        mock_db.query.side_effect = [
            _query(scalar=5),
            _query(scalar=2),
            _query(subquery=project_user_ids),
            _query(scalar=7),
            _query(subquery=attachment_user_ids),
            _query(scalar=5 * 1024 * 1024),
        ]

        attachment_module = ModuleType("app.models.document")
        attachment_module.Attachment = SimpleNamespace(
            file_size=MagicMock(name="file_size"),
            uploaded_by=MagicMock(name="uploaded_by"),
        )
        attachment_module.Attachment.uploaded_by.in_.return_value = MagicMock(name="uploaded_by_filter")

        with patch.dict(sys.modules, {"app.models.document": attachment_module}):
            stats = service.get_tenant_stats(1)

        assert stats == {
            "tenant_id": 1,
            "tenant_code": "T00000001",
            "user_count": 5,
            "role_count": 2,
            "project_count": 7,
            "storage_used_mb": 5.0,
            "plan_limits": tenant.get_plan_limits(),
        }

    def test_get_tenant_stats_tolerates_project_and_attachment_query_failures(self):
        mock_db = MagicMock()
        service = TenantService(mock_db)
        tenant = Tenant(id=1, tenant_code="T00000001", tenant_name="租户A")
        service.get_tenant = MagicMock(return_value=tenant)

        query_calls = iter(
            [
                _query(scalar=1),
                _query(scalar=1),
                RuntimeError("project query failed"),
                RuntimeError("attachment query failed"),
            ]
        )

        def query_side_effect(*args, **kwargs):
            current = next(query_calls)
            if isinstance(current, Exception):
                raise current
            return current

        mock_db.query.side_effect = query_side_effect

        stats = service.get_tenant_stats(1)

        assert stats["project_count"] == 0
        assert stats["storage_used_mb"] == 0
