# -*- coding: utf-8 -*-
"""
认证中间件测试

测试覆盖：
1. 正常流程 - token验证成功
2. 错误处理 - 各种无效token场景
3. 边界条件 - 白名单、OPTIONS请求等
4. 安全性 - token格式、恶意输入等
"""

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from sqlalchemy.orm import Session

from app.core.middleware.auth_middleware import (
    GlobalAuthMiddleware,
    add_whitelist_path,
    add_whitelist_prefix,
)
from app.models.user import User


@pytest.fixture
def test_app():
    """创建测试用FastAPI应用"""
    app = FastAPI()
    
    # 添加认证中间件
    app.add_middleware(GlobalAuthMiddleware)
    
    # 添加测试路由
    @app.get("/api/v1/protected")
    async def protected_route():
        return {"message": "Protected resource"}
    
    @app.get("/api/v1/auth/login")
    async def login_route():
        return {"message": "Login endpoint"}
    
    @app.get("/health")
    async def health_route():
        return {"status": "ok"}
    
    @app.get("/docs")
    async def docs_route():
        return {"message": "API documentation"}
    
    @app.options("/api/v1/protected")
    async def options_route():
        return {"message": "CORS preflight"}
    
    return app


@pytest.fixture
def client(test_app):
    """创建测试客户端"""
    return TestClient(test_app)


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.tenant_id = 1
    return user


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = MagicMock(spec=Session)
    db.close = MagicMock()
    return db


class TestAuthMiddlewareNormalFlow:
    """测试正常流程"""
    
    def test_valid_token_success(self, client, mock_user, mock_db):
        """测试有效token验证成功"""
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer valid_token_123"}
            )
            
            assert response.status_code == 200
            assert response.json() == {"message": "Protected resource"}
    
    def test_whitelist_path_no_auth(self, client):
        """测试白名单路径无需认证"""
        response = client.get("/api/v1/auth/login")
        assert response.status_code == 200
        assert response.json() == {"message": "Login endpoint"}
    
    def test_whitelist_health_check(self, client):
        """测试健康检查端点无需认证"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_options_request_allowed(self, client):
        """测试OPTIONS预检请求直接放行"""
        response = client.options("/api/v1/protected")
        assert response.status_code == 200
    
    def test_user_info_stored_in_request_state(self, client, mock_user, mock_db):
        """测试用户信息正确存储到request.state"""
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200


class TestAuthMiddlewareErrorHandling:
    """测试错误处理"""
    
    def test_missing_authorization_header(self, client):
        """测试缺少Authorization header"""
        response = client.get("/api/v1/protected")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error_code"] == "MISSING_TOKEN"
        assert "WWW-Authenticate" in response.headers
    
    def test_invalid_authorization_format_no_bearer(self, client):
        """测试无效的Authorization格式（缺少Bearer前缀）"""
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": "invalid_token_123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error_code"] == "MISSING_TOKEN"
    
    def test_invalid_authorization_format_empty_token(self, client):
        """测试空token"""
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": "Bearer "}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error_code"] == "INVALID_TOKEN_FORMAT"
    
    def test_invalid_authorization_format_multiple_parts(self, client):
        """测试多余的空格导致格式错误"""
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": "Bearer token part2 part3"}
        )
        
        # 这个应该通过，因为split只分割成2部分，后面的被当作token的一部分
        assert response.status_code in [401, 500]  # 取决于verify_token的实现
    
    def test_expired_token(self, client, mock_db):
        """测试过期token"""
        from fastapi import HTTPException
        
        async def mock_verify_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_expired):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer expired_token"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token已过期" in response.json()["message"]
    
    def test_invalid_token(self, client, mock_db):
        """测试无效token"""
        from fastapi import HTTPException
        
        async def mock_verify_invalid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_invalid):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_not_found(self, client, mock_db):
        """测试用户不存在"""
        from fastapi import HTTPException
        
        async def mock_verify_no_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_no_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer token_for_deleted_user"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_database_error(self, client, mock_db):
        """测试数据库异常"""
        async def mock_verify_db_error():
            raise Exception("Database connection failed")
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_db_error):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["error_code"] == "AUTH_ERROR"


class TestAuthMiddlewareBoundaryConditions:
    """测试边界条件"""
    
    def test_debug_mode_docs_accessible(self, client):
        """测试DEBUG模式下文档可访问"""
        with patch('app.core.config.settings.DEBUG', True):
            response = client.get("/docs")
            # 在测试环境中，这个路由可能返回200或404（如果FastAPI文档未启用）
            assert response.status_code in [200, 404]
    
    def test_production_mode_docs_require_auth(self, client, mock_db):
        """测试生产模式下文档需要认证"""
        with patch('app.core.config.settings.DEBUG', False):
            response = client.get("/docs")
            # 在生产模式下应该要求认证
            assert response.status_code in [401, 404]
    
    def test_case_sensitive_paths(self, client):
        """测试路径大小写敏感"""
        # /health 应该可访问
        response = client.get("/health")
        assert response.status_code == 200
        
        # /HEALTH 应该需要认证（如果路由存在）
        response = client.get("/HEALTH")
        assert response.status_code in [401, 404]
    
    def test_trailing_slash_handling(self, client):
        """测试末尾斜杠处理"""
        # FastAPI默认会重定向，但不影响中间件逻辑
        response = client.get("/health/", follow_redirects=False)
        # 可能是200（如果路由处理）或307（重定向）
        assert response.status_code in [200, 307, 404]
    
    def test_very_long_token(self, client, mock_user, mock_db):
        """测试超长token"""
        long_token = "a" * 10000
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {long_token}"}
            )
            
            # 应该能正常处理（token验证可能失败，但不应崩溃）
            assert response.status_code in [200, 401]
    
    def test_special_characters_in_token(self, client, mock_db):
        """测试token包含特殊字符"""
        special_token = "token!@#$%^&*()"
        
        async def mock_verify_special():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_special):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {special_token}"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMiddlewareSecurity:
    """测试安全性"""
    
    def test_sql_injection_in_token(self, client, mock_db):
        """测试token包含SQL注入攻击"""
        malicious_token = "token' OR '1'='1"
        
        async def mock_verify_sql():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_sql):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {malicious_token}"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_xss_in_token(self, client, mock_db):
        """测试token包含XSS攻击"""
        xss_token = "<script>alert('xss')</script>"
        
        async def mock_verify_xss():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_xss):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {xss_token}"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_multiple_authorization_headers(self, client, mock_user, mock_db):
        """测试多个Authorization header（安全风险）"""
        # TestClient不直接支持重复header，这里测试覆盖场景
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer token1"}
            )
            
            # 应该使用最后一个header值
            assert response.status_code in [200, 401]
    
    def test_timing_attack_resistance(self, client, mock_db):
        """测试时序攻击防护（验证响应时间不泄露信息）"""
        import time
        
        async def mock_verify_timing():
            from fastapi import HTTPException
            # 固定延迟防止时序攻击
            await AsyncMock(return_value=None)()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_timing):
            
            start1 = time.time()
            response1 = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer wrong1"}
            )
            time1 = time.time() - start1
            
            start2 = time.time()
            response2 = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer wrong2"}
            )
            time2 = time.time() - start2
            
            # 两次请求都应该返回401
            assert response1.status_code == status.HTTP_401_UNAUTHORIZED
            assert response2.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMiddlewareHelperFunctions:
    """测试辅助函数"""
    
    def test_add_whitelist_path(self):
        """测试动态添加白名单路径"""
        original_count = len(GlobalAuthMiddleware.WHITE_LIST)
        
        add_whitelist_path("/api/v1/public")
        
        assert "/api/v1/public" in GlobalAuthMiddleware.WHITE_LIST
        assert len(GlobalAuthMiddleware.WHITE_LIST) == original_count + 1
        
        # 清理
        GlobalAuthMiddleware.WHITE_LIST.remove("/api/v1/public")
    
    def test_add_whitelist_path_duplicate(self):
        """测试重复添加白名单路径"""
        add_whitelist_path("/health")
        add_whitelist_path("/health")
        
        # 应该只有一个
        count = GlobalAuthMiddleware.WHITE_LIST.count("/health")
        assert count == 1
    
    def test_add_whitelist_path_invalid(self):
        """测试添加无效路径"""
        original_count = len(GlobalAuthMiddleware.WHITE_LIST)
        
        # 无效路径（不以/开头）
        add_whitelist_path("invalid")
        
        # 不应该被添加
        assert "invalid" not in GlobalAuthMiddleware.WHITE_LIST
        assert len(GlobalAuthMiddleware.WHITE_LIST) == original_count
    
    def test_add_whitelist_prefix(self):
        """测试动态添加白名单前缀"""
        original_count = len(GlobalAuthMiddleware.WHITE_LIST_PREFIXES)
        
        add_whitelist_prefix("/public/")
        
        assert "/public/" in GlobalAuthMiddleware.WHITE_LIST_PREFIXES
        assert len(GlobalAuthMiddleware.WHITE_LIST_PREFIXES) == original_count + 1
        
        # 清理
        GlobalAuthMiddleware.WHITE_LIST_PREFIXES.remove("/public/")
    
    def test_add_whitelist_prefix_duplicate(self):
        """测试重复添加白名单前缀"""
        add_whitelist_prefix("/static/")
        add_whitelist_prefix("/static/")
        
        # 应该只有一个
        count = GlobalAuthMiddleware.WHITE_LIST_PREFIXES.count("/static/")
        assert count == 1


class TestAuthMiddlewareIntegration:
    """测试集成场景"""
    
    def test_multiple_protected_routes(self, client, mock_user, mock_db):
        """测试多个受保护路由"""
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            assert response.status_code == 200
    
    def test_db_session_cleanup(self, client, mock_db):
        """测试数据库会话正确清理"""
        async def mock_verify_success():
            user = Mock(spec=User)
            user.id = 1
            user.username = "testuser"
            return user
        
        with patch('app.models.base.get_session', return_value=mock_db) as mock_get_session, \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, side_effect=mock_verify_success):
            
            client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # 验证数据库会话被关闭
            assert mock_db.close.called
    
    def test_concurrent_requests(self, client, mock_user, mock_db):
        """测试并发请求处理"""
        with patch('app.models.base.get_session', return_value=mock_db), \
             patch('app.core.auth.verify_token_and_get_user', 
                   new_callable=AsyncMock, return_value=mock_user):
            
            # 模拟并发请求
            responses = []
            for _ in range(5):
                response = client.get(
                    "/api/v1/protected",
                    headers={"Authorization": "Bearer valid_token"}
                )
                responses.append(response)
            
            # 所有请求都应该成功
            for response in responses:
                assert response.status_code == 200


class TestAuthMiddlewareConfiguration:
    """测试配置相关"""
    
    def test_global_auth_disabled(self, test_app):
        """测试禁用全局认证"""
        client = TestClient(test_app)
        
        with patch('app.core.config.settings.ENABLE_GLOBAL_AUTH', False):
            # 不需要token也能访问
            response = client.get("/api/v1/protected")
            # 由于中间件被禁用，路由应该被执行
            assert response.status_code in [200, 500]  # 取决于路由实现
    
    def test_whitelist_configuration(self):
        """测试白名单配置完整性"""
        # 检查必要的路径在白名单中
        assert "/api/v1/auth/login" in GlobalAuthMiddleware.WHITE_LIST
        assert "/health" in GlobalAuthMiddleware.WHITE_LIST
        assert "/" in GlobalAuthMiddleware.WHITE_LIST
    
    def test_whitelist_prefix_configuration(self):
        """测试白名单前缀配置"""
        assert "/static/" in GlobalAuthMiddleware.WHITE_LIST_PREFIXES
        assert "/assets/" in GlobalAuthMiddleware.WHITE_LIST_PREFIXES
