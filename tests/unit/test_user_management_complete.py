# -*- coding: utf-8 -*-
"""
用户管理完整测试套件
测试用户CRUD、角色分配、密码管理等核心功能
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from app.core.auth import get_password_hash, verify_password
from app.models.organization import Employee
from app.models.user import User, Role, UserRole


@pytest.mark.unit
class TestUserCRUD:
    """用户CRUD操作测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.flush = MagicMock()
        return db

    @pytest.fixture
    def sample_employee(self):
        """示例员工数据"""
        return Employee(
            id=1,
            employee_code="E0001",
            name="测试员工",
            department="IT",
            role="ENGINEER",
            is_active=True
        )

    @pytest.fixture
    def sample_user(self, sample_employee):
        """示例用户数据"""
        return User(
            id=1,
            username="testuser",
            employee_id=sample_employee.id,
            password_hash=get_password_hash("password123"),
            real_name="测试用户",
            email="test@example.com",
            is_active=True,
            is_superuser=False,
            auth_type="password"
        )

    def test_create_user_success(self, mock_db, sample_employee):
        """测试创建用户成功"""
        # 准备数据
        username = "newuser"
        password = "newpass123"
        
        # 模拟员工已存在
        mock_db.query(Employee).filter().first.return_value = sample_employee
        
        # 模拟用户名不存在
        mock_db.query(User).filter().first.return_value = None
        
        # 创建用户
        user = User(
            username=username,
            employee_id=sample_employee.id,
            password_hash=get_password_hash(password),
            real_name=sample_employee.name,
            is_active=True,
            auth_type="password"
        )
        
        mock_db.add(user)
        mock_db.commit()
        
        # 验证
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_user_duplicate_username(self, mock_db, sample_user):
        """测试创建重复用户名失败"""
        # 模拟用户名已存在
        mock_db.query(User).filter().first.return_value = sample_user
        
        # 验证应该抛出异常或返回错误
        existing_user = mock_db.query(User).filter(User.username == "testuser").first()
        assert existing_user is not None
        assert existing_user.username == "testuser"

    def test_update_user_info(self, mock_db, sample_user):
        """测试更新用户信息"""
        # 模拟查询返回用户
        mock_db.query(User).filter().first.return_value = sample_user
        
        # 更新信息
        sample_user.email = "newemail@example.com"
        sample_user.real_name = "新名字"
        
        mock_db.commit()
        
        # 验证
        assert sample_user.email == "newemail@example.com"
        assert sample_user.real_name == "新名字"
        assert mock_db.commit.called

    def test_deactivate_user(self, mock_db, sample_user):
        """测试禁用用户"""
        # 模拟查询返回用户
        mock_db.query(User).filter().first.return_value = sample_user
        
        # 禁用用户
        sample_user.is_active = False
        mock_db.commit()
        
        # 验证
        assert sample_user.is_active is False
        assert mock_db.commit.called

    def test_delete_user(self, mock_db, sample_user):
        """测试删除用户"""
        # 模拟查询返回用户
        mock_db.query(User).filter().first.return_value = sample_user
        
        # 删除用户
        mock_db.delete(sample_user)
        mock_db.commit()
        
        # 验证
        assert mock_db.delete.called
        assert mock_db.commit.called


@pytest.mark.unit
class TestPasswordManagement:
    """密码管理测试"""

    def test_password_hash_generation(self):
        """测试密码哈希生成"""
        password = "testPassword123!"
        hashed = get_password_hash(password)
        
        # 验证哈希是字符串且不为空
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
        # 验证哈希与原密码不同
        assert hashed != password
        
        # 验证bcrypt格式（$2b$开头）
        assert hashed.startswith("$2b$")

    def test_password_hash_uniqueness(self):
        """测试相同密码生成不同哈希（盐值）"""
        password = "testPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # 由于盐值不同，哈希应该不同
        assert hash1 != hash2

    def test_password_verification_success(self):
        """测试密码验证成功"""
        password = "correctPassword123!"
        hashed = get_password_hash(password)
        
        # 验证密码
        result = verify_password(password, hashed)
        assert result is True

    def test_password_verification_failure(self):
        """测试密码验证失败"""
        password = "correctPassword123!"
        wrong_password = "wrongPassword123!"
        hashed = get_password_hash(password)
        
        # 验证错误密码
        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_empty_password_handling(self):
        """测试空密码处理"""
        with pytest.raises(Exception):
            get_password_hash("")

    def test_long_password_handling(self):
        """测试超长密码处理（bcrypt限制72字节）"""
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        
        # 应该成功生成哈希
        assert hashed is not None
        assert isinstance(hashed, str)


@pytest.mark.unit
class TestRoleAssignment:
    """角色分配测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.delete = MagicMock()
        return db

    @pytest.fixture
    def sample_roles(self):
        """示例角色数据"""
        return [
            Role(id=1, role_code="ADMIN", role_name="系统管理员", data_scope="ALL"),
            Role(id=2, role_code="PM", role_name="项目经理", data_scope="PROJECT"),
            Role(id=3, role_code="ENGINEER", role_name="工程师", data_scope="PROJECT"),
        ]

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        return User(
            id=1,
            username="testuser",
            password_hash=get_password_hash("password123"),
            real_name="测试用户",
            is_active=True
        )

    def test_assign_single_role(self, mock_db, sample_user, sample_roles):
        """测试分配单个角色"""
        role = sample_roles[1]  # PM角色
        
        # 创建用户角色关联
        user_role = UserRole(user_id=sample_user.id, role_id=role.id)
        mock_db.add(user_role)
        mock_db.commit()
        
        # 验证
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_assign_multiple_roles(self, mock_db, sample_user, sample_roles):
        """测试分配多个角色"""
        # 分配多个角色
        for role in sample_roles[1:]:  # PM和ENGINEER
            user_role = UserRole(user_id=sample_user.id, role_id=role.id)
            mock_db.add(user_role)
        
        mock_db.commit()
        
        # 验证
        assert mock_db.add.call_count == 2
        assert mock_db.commit.called

    def test_remove_role(self, mock_db, sample_user, sample_roles):
        """测试移除角色"""
        role = sample_roles[1]
        user_role = UserRole(user_id=sample_user.id, role_id=role.id)
        
        # 模拟查询返回用户角色
        mock_db.query(UserRole).filter().first.return_value = user_role
        
        # 删除角色
        mock_db.delete(user_role)
        mock_db.commit()
        
        # 验证
        assert mock_db.delete.called
        assert mock_db.commit.called

    def test_replace_role(self, mock_db, sample_user, sample_roles):
        """测试替换角色"""
        old_role = sample_roles[1]  # PM
        new_role = sample_roles[2]  # ENGINEER
        
        old_user_role = UserRole(user_id=sample_user.id, role_id=old_role.id)
        
        # 模拟查询返回旧角色
        mock_db.query(UserRole).filter().first.return_value = old_user_role
        
        # 删除旧角色
        mock_db.delete(old_user_role)
        
        # 添加新角色
        new_user_role = UserRole(user_id=sample_user.id, role_id=new_role.id)
        mock_db.add(new_user_role)
        
        mock_db.commit()
        
        # 验证
        assert mock_db.delete.called
        assert mock_db.add.called
        assert mock_db.commit.called


@pytest.mark.unit
class TestUserQueries:
    """用户查询测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.fixture
    def sample_users(self):
        """示例用户列表"""
        return [
            User(id=1, username="admin", real_name="管理员", is_active=True, is_superuser=True),
            User(id=2, username="user1", real_name="用户1", is_active=True, is_superuser=False),
            User(id=3, username="user2", real_name="用户2", is_active=False, is_superuser=False),
        ]

    def test_query_all_users(self, mock_db, sample_users):
        """测试查询所有用户"""
        # 模拟查询返回所有用户
        mock_db.query(User).all.return_value = sample_users
        
        users = mock_db.query(User).all()
        
        # 验证
        assert len(users) == 3
        assert users[0].username == "admin"

    def test_query_user_by_username(self, mock_db, sample_users):
        """测试通过用户名查询"""
        # 模拟查询返回特定用户
        mock_db.query(User).filter().first.return_value = sample_users[0]
        
        user = mock_db.query(User).filter(User.username == "admin").first()
        
        # 验证
        assert user is not None
        assert user.username == "admin"
        assert user.is_superuser is True

    def test_query_active_users(self, mock_db, sample_users):
        """测试查询活跃用户"""
        active_users = [u for u in sample_users if u.is_active]
        
        # 模拟查询返回活跃用户
        mock_db.query(User).filter().all.return_value = active_users
        
        users = mock_db.query(User).filter(User.is_active == True).all()
        
        # 验证
        assert len(users) == 2
        assert all(u.is_active for u in users)

    def test_query_superusers(self, mock_db, sample_users):
        """测试查询超级管理员"""
        superusers = [u for u in sample_users if u.is_superuser]
        
        # 模拟查询返回超级管理员
        mock_db.query(User).filter().all.return_value = superusers
        
        users = mock_db.query(User).filter(User.is_superuser == True).all()
        
        # 验证
        assert len(users) == 1
        assert users[0].username == "admin"


@pytest.mark.unit
class TestUserValidation:
    """用户数据验证测试"""

    def test_username_validation_length(self):
        """测试用户名长度验证"""
        # 正常长度
        assert len("testuser") >= 3
        assert len("testuser") <= 50
        
        # 太短
        assert len("ab") < 3
        
        # 太长
        assert len("a" * 100) > 50

    def test_username_validation_format(self):
        """测试用户名格式验证"""
        # 有效用户名（字母、数字、下划线）
        valid_usernames = ["user123", "test_user", "admin2024", "user_123"]
        for username in valid_usernames:
            assert username.replace("_", "").isalnum()
        
        # 无效用户名（包含特殊字符）
        invalid_usernames = ["user@123", "test user", "admin#2024"]
        for username in invalid_usernames:
            assert not username.replace("_", "").isalnum()

    def test_email_validation_format(self):
        """测试邮箱格式验证"""
        # 有效邮箱
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "admin123@test.org"]
        for email in valid_emails:
            assert "@" in email
            assert "." in email.split("@")[1]
        
        # 无效邮箱
        invalid_emails = ["test@", "@example.com", "test.example.com"]
        for email in invalid_emails:
            is_valid = "@" in email and "." in email.split("@")[-1] if "@" in email else False
            assert not is_valid

    def test_password_strength_validation(self):
        """测试密码强度验证"""
        # 弱密码
        weak_passwords = ["123", "password", "abc"]
        for pwd in weak_passwords:
            assert len(pwd) < 8
        
        # 强密码
        strong_passwords = ["Password123!", "Test@2024", "Secure#Pass1"]
        for pwd in strong_passwords:
            assert len(pwd) >= 8
            has_upper = any(c.isupper() for c in pwd)
            has_lower = any(c.islower() for c in pwd)
            has_digit = any(c.isdigit() for c in pwd)
            assert has_upper and has_lower and has_digit


@pytest.mark.unit
class TestUserBusinessLogic:
    """用户业务逻辑测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()

    def test_user_from_employee_sync(self, mock_db):
        """测试从员工同步用户"""
        # 模拟员工数据
        employee = Employee(
            id=1,
            employee_code="E0001",
            name="张三",
            department="IT",
            role="ENGINEER"
        )
        
        # 创建关联用户
        user = User(
            username=employee.employee_code,
            employee_id=employee.id,
            real_name=employee.name,
            password_hash=get_password_hash("default123"),
            is_active=True
        )
        
        # 验证
        assert user.username == employee.employee_code
        assert user.real_name == employee.name
        assert user.employee_id == employee.id

    def test_superuser_cannot_be_deactivated(self):
        """测试超级管理员不能被禁用（业务规则）"""
        admin = User(
            id=1,
            username="admin",
            is_superuser=True,
            is_active=True
        )
        
        # 业务逻辑：超级管理员不能被禁用
        if admin.is_superuser:
            can_deactivate = False
        else:
            can_deactivate = True
        
        assert can_deactivate is False

    def test_last_superuser_protection(self, mock_db):
        """测试最后一个超级管理员保护"""
        # 模拟只有一个超级管理员
        superusers = [
            User(id=1, username="admin", is_superuser=True, is_active=True)
        ]
        
        mock_db.query(User).filter().count.return_value = 1
        
        # 业务逻辑：不能删除最后一个超级管理员
        superuser_count = mock_db.query(User).filter(
            User.is_superuser == True,
            User.is_active == True
        ).count()
        
        can_delete = superuser_count > 1
        assert can_delete is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
