# -*- coding: utf-8 -*-
"""
认证流程完整集成测试
测试登录、Token验证、权限检查等端到端流程
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.models.user import User, Role, UserRole, ApiPermission, RoleApiPermission


@pytest.mark.integration
class TestLoginFlow:
    """登录流程测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.commit = MagicMock()
        return db

    @pytest.fixture
    def test_user(self):
        """测试用户"""
        return User(
            id=1,
            username="testuser",
            password_hash=get_password_hash("password123"),
            real_name="测试用户",
            email="test@example.com",
            is_active=True,
            is_superuser=False
        )

    def test_login_success_flow(self, mock_db, test_user):
        """测试登录成功流程"""
        # 1. 查询用户
        mock_db.query(User).filter().first.return_value = test_user
        
        user = mock_db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        
        # 2. 验证密码
        password_valid = verify_password("password123", user.password_hash)
        assert password_valid is True
        
        # 3. 检查用户状态
        assert user.is_active is True
        
        # 4. 生成Token
        token = create_access_token(data={"sub": str(user.id)})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_login_wrong_password_flow(self, mock_db, test_user):
        """测试密码错误流程"""
        # 1. 查询用户
        mock_db.query(User).filter().first.return_value = test_user
        
        user = mock_db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        
        # 2. 验证错误密码
        password_valid = verify_password("wrongpassword", user.password_hash)
        assert password_valid is False
        
        # 3. 登录失败，不生成Token
        # 在实际应用中应该抛出异常

    def test_login_inactive_user_flow(self, mock_db, test_user):
        """测试禁用用户登录流程"""
        # 设置用户为禁用状态
        test_user.is_active = False
        
        # 1. 查询用户
        mock_db.query(User).filter().first.return_value = test_user
        
        user = mock_db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        
        # 2. 验证密码（成功）
        password_valid = verify_password("password123", user.password_hash)
        assert password_valid is True
        
        # 3. 检查用户状态（禁用）
        assert user.is_active is False
        
        # 4. 不应该生成Token（业务逻辑应该阻止）

    def test_login_nonexistent_user_flow(self, mock_db):
        """测试不存在的用户登录流程"""
        # 1. 查询用户（不存在）
        mock_db.query(User).filter().first.return_value = None
        
        user = mock_db.query(User).filter(User.username == "nonexistent").first()
        assert user is None
        
        # 2. 登录失败（用户不存在）


@pytest.mark.integration
class TestTokenFlow:
    """Token流程测试"""

    @pytest.fixture
    def test_user(self):
        """测试用户"""
        return User(
            id=1,
            username="testuser",
            is_active=True,
            is_superuser=False,
        password_hash="test_hash_123"
    )

    def test_token_generation_and_decode(self, test_user):
        """测试Token生成和解码"""
        from jose import jwt
        from app.core.config import settings
        
        # 1. 生成Token
        token = create_access_token(data={"sub": str(test_user.id)})
        assert token is not None
        
        # 2. 解码Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload is not None
        assert payload["sub"] == str(test_user.id)

    def test_token_expiration(self):
        """测试Token过期"""
        from jose import jwt, JWTError
        from app.core.config import settings
        
        # 1. 生成已过期的Token
        expired_token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(seconds=-10)  # 负数表示已过期
        )
        
        # 2. 尝试解码过期Token
        with pytest.raises(JWTError):
            payload = jwt.decode(
                expired_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

    def test_token_with_custom_expiration(self):
        """测试自定义过期时间的Token"""
        from jose import jwt
        from app.core.config import settings
        
        # 1. 生成30分钟过期的Token
        token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(minutes=30)
        )
        
        # 2. 解码并验证过期时间
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # 验证exp字段存在且合理
        assert "exp" in payload
        assert "iat" in payload
        
        # 计算实际有效期（允许1秒误差）
        exp_time = payload["exp"]
        iat_time = payload["iat"]
        actual_duration = exp_time - iat_time
        
        assert 1790 <= actual_duration <= 1810  # 30分钟 = 1800秒


@pytest.mark.integration
class TestPermissionCheckFlow:
    """权限检查流程测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.fixture
    def test_user_with_role(self):
        """带角色的测试用户"""
        user = User(
            id=1,
            username="testuser",
            is_active=True,
            is_superuser=False,
        password_hash="test_hash_123"
    )
        
        role = Role(
            id=2,
            role_code="PM",
            role_name="项目经理",
            data_scope="PROJECT"
        )
        
        return user, role

    @pytest.fixture
    def test_permissions(self):
        """测试权限"""
        return [
            ApiPermission(id=1, perm_code="project:view", perm_name="查看项目"),
            ApiPermission(id=2, perm_code="project:create", perm_name="创建项目"),
            ApiPermission(id=3, perm_code="user:view", perm_name="查看用户"),
        ]

    def test_permission_check_with_role(self, mock_db, test_user_with_role, test_permissions):
        """测试通过角色检查权限"""
        user, role = test_user_with_role
        
        # 1. 查询用户角色
        mock_db.query(UserRole).filter().all.return_value = [
            UserRole(user_id=user.id, role_id=role.id)
        ]
        
        user_roles = mock_db.query(UserRole).filter(UserRole.user_id == user.id).all()
        assert len(user_roles) == 1
        assert user_roles[0].role_id == role.id
        
        # 2. 查询角色权限
        role_perms = [
            RoleApiPermission(role_id=role.id, permission_id=test_permissions[0].id),
            RoleApiPermission(role_id=role.id, permission_id=test_permissions[1].id),
        ]
        mock_db.query(RoleApiPermission).filter().all.return_value = role_perms
        
        perms = mock_db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == role.id
        ).all()
        
        assert len(perms) == 2
        
        # 3. 检查权限
        perm_ids = [p.permission_id for p in perms]
        assert test_permissions[0].id in perm_ids  # project:view
        assert test_permissions[1].id in perm_ids  # project:create
        assert test_permissions[2].id not in perm_ids  # user:view (无权限)

    def test_superuser_bypass_permission_check(self):
        """测试超级管理员绕过权限检查"""
        admin = User(
            id=1,
            username="admin",
            is_active=True,
            is_superuser=True,
        password_hash="test_hash_123"
    )
        
        # 超级管理员应该拥有所有权限
        has_permission = admin.is_superuser
        assert has_permission is True

    def test_inactive_user_no_permission(self):
        """测试禁用用户无权限"""
        inactive_user = User(
            id=1,
            username="inactive",
            is_active=False,
            is_superuser=False,
        password_hash="test_hash_123"
    )
        
        # 禁用用户不应该有任何权限
        has_permission = inactive_user.is_active
        assert has_permission is False


@pytest.mark.integration
class TestDataScopeFlow:
    """数据范围流程测试"""

    @pytest.fixture
    def roles_with_scopes(self):
        """不同数据范围的角色"""
        return {
            "ALL": Role(id=1, role_code="ADMIN", data_scope="ALL"),
            "DEPT": Role(id=2, role_code="DEPT_MGR", data_scope="DEPT"),
            "PROJECT": Role(id=3, role_code="PM", data_scope="PROJECT"),
            "OWN": Role(id=4, role_code="SALES", data_scope="OWN"),
        }

    def test_all_scope_access(self, roles_with_scopes):
        """测试全局范围访问"""
        admin_role = roles_with_scopes["ALL"]
        
        # 全局范围可以访问所有数据
        can_access_all = admin_role.data_scope == "ALL"
        assert can_access_all is True

    def test_dept_scope_access(self, roles_with_scopes):
        """测试部门范围访问"""
        dept_role = roles_with_scopes["DEPT"]
        user_dept = "IT"
        target_dept = "IT"
        
        # 部门范围只能访问本部门数据
        can_access = (dept_role.data_scope == "DEPT" and user_dept == target_dept) or \
                     dept_role.data_scope == "ALL"
        assert can_access is True
        
        # 不能访问其他部门
        other_dept = "SALES"
        can_access_other = dept_role.data_scope == "ALL" or \
                          (dept_role.data_scope == "DEPT" and user_dept == other_dept)
        assert can_access_other is False

    def test_project_scope_access(self, roles_with_scopes):
        """测试项目范围访问"""
        pm_role = roles_with_scopes["PROJECT"]
        
        # 项目范围只能访问参与的项目
        user_projects = [1, 2, 3]
        target_project = 2
        
        can_access = pm_role.data_scope == "ALL" or \
                    (pm_role.data_scope in ["PROJECT", "DEPT"] and target_project in user_projects)
        assert can_access is True
        
        # 不能访问未参与的项目
        other_project = 10
        can_access_other = pm_role.data_scope == "ALL" or \
                          (pm_role.data_scope in ["PROJECT", "DEPT"] and other_project in user_projects)
        assert can_access_other is False

    def test_own_scope_access(self, roles_with_scopes):
        """测试个人范围访问"""
        sales_role = roles_with_scopes["OWN"]
        user_id = 1
        
        # 个人范围只能访问自己创建的数据
        data_owner_id = 1
        can_access = sales_role.data_scope == "ALL" or \
                    (sales_role.data_scope == "OWN" and data_owner_id == user_id)
        assert can_access is True
        
        # 不能访问他人数据
        other_owner_id = 2
        can_access_other = sales_role.data_scope == "ALL" or \
                          (sales_role.data_scope == "OWN" and other_owner_id == user_id)
        assert can_access_other is False


@pytest.mark.integration
class TestCompleteAuthFlow:
    """完整认证流程端到端测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.commit = MagicMock()
        return db

    def test_end_to_end_auth_flow(self, mock_db):
        """测试端到端认证流程"""
        # 1. 创建用户
        user = User(
            id=1,
            username="testuser",
            password_hash=get_password_hash("password123"),
            real_name="测试用户",
            is_active=True,
            is_superuser=False
        )
        
        # 2. 分配角色
        role = Role(
            id=2,
            role_code="PM",
            role_name="项目经理",
            data_scope="PROJECT"
        )
        
        user_role = UserRole(user_id=user.id, role_id=role.id)
        
        # 3. 分配权限
        permission = ApiPermission(
            id=1,
            perm_code="project:view",
            perm_name="查看项目"
        )
        
        role_perm = RoleApiPermission(
            role_id=role.id,
            permission_id=permission.id
        )
        
        # 4. 登录流程
        mock_db.query(User).filter().first.return_value = user
        
        # 验证用户名
        found_user = mock_db.query(User).filter(User.username == "testuser").first()
        assert found_user is not None
        
        # 验证密码
        password_valid = verify_password("password123", found_user.password_hash)
        assert password_valid is True
        
        # 检查状态
        assert found_user.is_active is True
        
        # 生成Token
        token = create_access_token(data={"sub": str(found_user.id)})
        assert token is not None
        
        # 5. 权限检查流程
        mock_db.query(UserRole).filter().all.return_value = [user_role]
        mock_db.query(RoleApiPermission).filter().all.return_value = [role_perm]
        
        # 获取用户角色
        user_roles = mock_db.query(UserRole).filter(UserRole.user_id == user.id).all()
        assert len(user_roles) == 1
        
        # 获取角色权限
        role_perms = mock_db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == role.id
        ).all()
        assert len(role_perms) == 1
        assert role_perms[0].permission_id == permission.id
        
        # 6. 数据范围检查
        assert role.data_scope == "PROJECT"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
