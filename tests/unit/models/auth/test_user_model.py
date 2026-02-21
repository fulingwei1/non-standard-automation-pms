# -*- coding: utf-8 -*-
"""
User Model 测试
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class TestUserModel:
    """User 模型测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            username="newuser",
            password_hash=get_password_hash("password123"),
            email="new@example.com",
            real_name="新用户"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"

    def test_username_unique(self, db_session):
        """测试用户名唯一性"""
        user1 = User(
            username="testuser",
            password_hash=get_password_hash("pass"),
            email="user1@example.com"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="testuser",
            password_hash=get_password_hash("pass"),
            email="user2@example.com"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_unique(self, db_session):
        """测试邮箱唯一性"""
        user1 = User(
            username="user1",
            password_hash=get_password_hash("pass"),
            email="same@example.com"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            password_hash=get_password_hash("pass"),
            email="same@example.com"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_password_hashing(self, db_session):
        """测试密码哈希"""
        password = "MySecurePassword123!"
        user = User(
            username="hashtest",
            password_hash=get_password_hash(password),
            email="hash@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # 验证密码哈希
        assert user.password_hash != password
        assert verify_password(password, user.password_hash)
        assert not verify_password("wrongpassword", user.password_hash)

    def test_user_is_active(self, db_session, sample_user):
        """测试用户激活状态"""
        assert sample_user.is_active is True
        
        sample_user.is_active = False
        db_session.commit()
        
        db_session.refresh(sample_user)
        assert sample_user.is_active is False

    def test_user_is_superuser(self, db_session):
        """测试超级用户标志"""
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            email="admin@example.com",
            is_superuser=True
        )
        db_session.add(admin)
        db_session.commit()
        
        assert admin.is_superuser is True

    def test_user_department(self, db_session, sample_department):
        """测试用户部门"""
        user = User(
            username="deptuser",
            password_hash=get_password_hash("pass"),
            email="dept@example.com",
            department_id=sample_department.id,
            department="技术部"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.department_id == sample_department.id
        assert user.department == "技术部"

    def test_user_position(self, db_session):
        """测试用户职位"""
        user = User(
            username="engineer",
            password_hash=get_password_hash("pass"),
            email="engineer@example.com",
            position="高级工程师"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.position == "高级工程师"

    def test_user_update(self, db_session, sample_user):
        """测试更新用户"""
        sample_user.real_name = "更新后的姓名"
        sample_user.phone = "13900000000"
        db_session.commit()
        
        db_session.refresh(sample_user)
        assert sample_user.real_name == "更新后的姓名"
        assert sample_user.phone == "13900000000"

    def test_user_delete(self, db_session):
        """测试删除用户"""
        user = User(
            username="tempuser",
            password_hash=get_password_hash("pass"),
            email="temp@example.com"
        )
        db_session.add(user)
        db_session.commit()
        uid = user.id
        
        db_session.delete(user)
        db_session.commit()
        
        deleted = db_session.query(User).filter_by(id=uid).first()
        assert deleted is None

    def test_user_last_login(self, db_session, sample_user):
        """测试用户最后登录时间"""
        now = datetime.utcnow()
        sample_user.last_login_at = now
        sample_user.last_login_ip = "192.168.1.100"
        db_session.commit()
        
        db_session.refresh(sample_user)
        assert sample_user.last_login_at is not None
        assert sample_user.last_login_ip == "192.168.1.100"

    def test_user_2fa_fields(self, db_session):
        """测试2FA字段"""
        user = User(
            username="2fauser",
            password_hash=get_password_hash("pass"),
            email="2fa@example.com",
            two_factor_enabled=True,
            two_factor_method="totp"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.two_factor_enabled is True
        assert user.two_factor_method == "totp"
