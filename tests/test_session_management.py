# -*- coding: utf-8 -*-
"""
会话管理和Token刷新测试
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.session import UserSession
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_refresh_token,
    extract_jti_from_token,
)
from app.services.session_service import SessionService


client = TestClient(app)


class TestTokenGeneration:
    """Token生成测试"""
    
    def test_create_access_token(self):
        """测试创建Access Token"""
        token = create_access_token({"sub": "123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证可以提取JTI
        jti = extract_jti_from_token(token)
        assert jti is not None
    
    def test_create_refresh_token(self):
        """测试创建Refresh Token"""
        token = create_refresh_token({"sub": "123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证token类型
        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload.get("token_type") == "refresh"
    
    def test_create_token_pair(self):
        """测试创建Token对"""
        access_token, refresh_token, access_jti, refresh_jti = create_token_pair(
            {"sub": "123"}
        )
        
        assert access_token is not None
        assert refresh_token is not None
        assert access_jti is not None
        assert refresh_jti is not None
        assert access_jti != refresh_jti
    
    def test_verify_refresh_token_valid(self):
        """测试验证有效的Refresh Token"""
        token = create_refresh_token({"sub": "123"})
        payload = verify_refresh_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "123"
        assert payload.get("token_type") == "refresh"
    
    def test_verify_refresh_token_invalid(self):
        """测试验证无效的Refresh Token"""
        # 使用Access Token（类型错误）
        access_token = create_access_token({"sub": "123"})
        payload = verify_refresh_token(access_token)
        
        assert payload is None
    
    def test_extract_jti_from_token(self):
        """测试从Token提取JTI"""
        access_token, _, access_jti, _ = create_token_pair({"sub": "123"})
        
        extracted_jti = extract_jti_from_token(access_token)
        assert extracted_jti == access_jti


class TestSessionService:
    """会话服务测试"""
    
    @pytest.fixture
    def test_user(self, db: Session):
        """创建测试用户"""
        user = User(
            username="test_session_user",
            password_hash="hashed_password",
            employee_id=1,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def test_create_session(self, db: Session, test_user: User):
        """测试创建会话"""
        access_jti = "test_access_jti_001"
        refresh_jti = "test_refresh_jti_001"
        
        session = SessionService.create_session(
            db=db,
            user_id=test_user.id,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
            device_info={
                "device_id": "device_001",
                "device_name": "Chrome on Windows",
                "device_type": "desktop",
            },
        )
        
        assert session is not None
        assert session.user_id == test_user.id
        assert session.access_token_jti == access_jti
        assert session.refresh_token_jti == refresh_jti
        assert session.ip_address == "192.168.1.100"
        assert session.is_active is True
    
    def test_get_user_sessions(self, db: Session, test_user: User):
        """测试获取用户会话列表"""
        # 创建多个会话
        for i in range(3):
            SessionService.create_session(
                db=db,
                user_id=test_user.id,
                access_token_jti=f"access_jti_{i}",
                refresh_token_jti=f"refresh_jti_{i}",
            )
        
        sessions = SessionService.get_user_sessions(db, test_user.id)
        assert len(sessions) >= 3
    
    def test_get_session_by_jti(self, db: Session, test_user: User):
        """测试通过JTI获取会话"""
        access_jti = "test_access_jti_002"
        refresh_jti = "test_refresh_jti_002"
        
        created_session = SessionService.create_session(
            db=db,
            user_id=test_user.id,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
        )
        
        # 通过access JTI查找
        session = SessionService.get_session_by_jti(db, access_jti, "access")
        assert session is not None
        assert session.id == created_session.id
        
        # 通过refresh JTI查找
        session = SessionService.get_session_by_jti(db, refresh_jti, "refresh")
        assert session is not None
        assert session.id == created_session.id
    
    def test_update_session_activity(self, db: Session, test_user: User):
        """测试更新会话活动时间"""
        access_jti = "test_access_jti_003"
        refresh_jti = "test_refresh_jti_003"
        
        session = SessionService.create_session(
            db=db,
            user_id=test_user.id,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
        )
        
        original_activity_time = session.last_activity_at
        
        # 更新活动时间
        updated_session = SessionService.update_session_activity(
            db=db,
            jti=refresh_jti,
            new_access_jti="new_access_jti",
        )
        
        assert updated_session is not None
        assert updated_session.last_activity_at > original_activity_time
        assert updated_session.access_token_jti == "new_access_jti"
    
    def test_revoke_session(self, db: Session, test_user: User):
        """测试撤销会话"""
        session = SessionService.create_session(
            db=db,
            user_id=test_user.id,
            access_token_jti="revoke_test_access",
            refresh_token_jti="revoke_test_refresh",
        )
        
        assert session.is_active is True
        
        # 撤销会话
        success = SessionService.revoke_session(db, session.id, test_user.id)
        assert success is True
        
        # 验证会话已失效
        db.refresh(session)
        assert session.is_active is False
        assert session.logout_at is not None
    
    def test_revoke_all_sessions(self, db: Session, test_user: User):
        """测试撤销所有会话"""
        # 创建多个会话
        for i in range(3):
            SessionService.create_session(
                db=db,
                user_id=test_user.id,
                access_token_jti=f"revoke_all_access_{i}",
                refresh_token_jti=f"revoke_all_refresh_{i}",
            )
        
        # 撤销所有会话
        count = SessionService.revoke_all_sessions(db, test_user.id)
        assert count >= 3
        
        # 验证所有会话都已失效
        sessions = SessionService.get_user_sessions(db, test_user.id, active_only=True)
        assert len(sessions) == 0


class TestAuthAPI:
    """认证API测试"""
    
    def test_login_with_refresh_token(self):
        """测试登录返回Refresh Token"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "refresh_expires_in" in data
        
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_endpoint(self):
        """测试Token刷新接口"""
        # 先登录获取tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # 使用refresh token获取新的access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        
        assert "access_token" in new_tokens
        assert "token_type" in new_tokens
        assert "expires_in" in new_tokens
        
        # 新的access token应该与原来的不同
        assert new_tokens["access_token"] != tokens["access_token"]
    
    def test_logout_current_session(self):
        """测试登出当前会话"""
        # 登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )
        
        access_token = login_response.json()["access_token"]
        
        # 登出
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"logout_all": False},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert logout_response.status_code == 200
        
        # 验证token已失效
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert me_response.status_code == 401
    
    def test_list_sessions(self):
        """测试查看会话列表"""
        # 登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )
        
        access_token = login_response.json()["access_token"]
        
        # 查看会话列表
        sessions_response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert sessions_response.status_code == 200
        data = sessions_response.json()
        
        assert "sessions" in data
        assert "total" in data
        assert "active_count" in data
        assert len(data["sessions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
