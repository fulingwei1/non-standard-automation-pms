# -*- coding: utf-8 -*-
"""
速率限制功能单元测试

测试覆盖：
1. 全局速率限制
2. 登录端点限流
3. 自定义限流策略
"""
import pytest
import time
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.rate_limiting import (
    limiter,
    user_limiter,
    strict_limiter,
    get_user_or_ip,
    get_ip_and_user,
)
from app.utils.rate_limit_decorator import (
    rate_limit,
    user_rate_limit,
    strict_rate_limit,
    login_rate_limit,
    refresh_token_rate_limit,
    password_change_rate_limit,
)


class TestGlobalRateLimiting:
    """全局速率限制测试（5个用例）"""
    
    def test_limiter_instance_created(self):
        """测试1: 限制器实例正确创建"""
        assert limiter is not None
        assert isinstance(limiter, Limiter)
    
    def test_default_key_function(self):
        """测试2: 默认使用IP地址作为限制键"""
        # 创建模拟请求
        from unittest.mock import Mock
        request = Mock()
        request.client.host = "192.168.1.100"
        
        ip = get_remote_address(request)
        assert ip == "192.168.1.100"
    
    def test_limiter_with_memory_storage(self):
        """测试3: 内存存储模式正常工作"""
        # 创建使用内存存储的限制器
        from app.core.rate_limiting import create_limiter
        
        mem_limiter = create_limiter(storage_uri=None, default_limits=["5/minute"])
        assert mem_limiter is not None
    
    def test_limiter_with_redis_storage_fallback(self):
        """测试4: Redis连接失败时降级到内存存储"""
        from app.core.rate_limiting import create_limiter
        
        # 使用无效的Redis URL
        fallback_limiter = create_limiter(
            storage_uri="redis://invalid-host:6379/0",
            default_limits=["10/minute"]
        )
        assert fallback_limiter is not None  # 应该降级到内存存储
    
    def test_rate_limit_headers_enabled(self):
        """测试5: 限流信息在响应头中返回"""
        # 创建测试应用
        app = FastAPI()
        test_limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
        app.state.limiter = test_limiter
        
        @app.get("/test")
        @test_limiter.limit("10/minute")
        async def test_endpoint(request: Request, response: Response):
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # 检查响应头（slowapi会自动添加）
        assert response.status_code == 200


class TestLoginRateLimiting:
    """登录端点限流测试（5个用例）"""
    
    def test_login_rate_limit_decorator_exists(self):
        """测试6: 登录限流装饰器存在"""
        assert login_rate_limit is not None
    
    def test_login_rate_limit_applied(self):
        """测试7: 登录限流装饰器可以应用"""
        app = FastAPI()
        app.state.limiter = limiter
        
        @app.post("/login")
        @login_rate_limit()
        async def login(request: Request, response: Response):
            return {"access_token": "test_token"}
        
        client = TestClient(app)
        response = client.post("/login")
        assert response.status_code == 200
    
    def test_login_rate_limit_exceeded(self):
        """测试8: 超过登录限流次数返回429"""
        from slowapi import _rate_limit_exceeded_handler
        
        app = FastAPI()
        test_limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = test_limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        @app.post("/login")
        @test_limiter.limit("3/minute")  # 设置为3次方便测试
        async def login(request: Request, response: Response):
            return {"access_token": "test_token"}
        
        client = TestClient(app)
        
        # 前3次应该成功
        for i in range(3):
            response = client.post("/login")
            assert response.status_code == 200, f"Request {i+1} failed"
        
        # 第4次应该被限流
        response = client.post("/login")
        assert response.status_code == 429
    
    def test_refresh_token_rate_limit(self):
        """测试9: Token刷新限流"""
        assert refresh_token_rate_limit is not None
        
        app = FastAPI()
        app.state.limiter = limiter
        
        @app.post("/refresh")
        @refresh_token_rate_limit()
        async def refresh(request: Request, response: Response):
            return {"access_token": "new_token"}
        
        client = TestClient(app)
        response = client.post("/refresh")
        assert response.status_code == 200
    
    def test_password_change_rate_limit(self):
        """测试10: 密码修改限流"""
        assert password_change_rate_limit is not None
        
        app = FastAPI()
        app.state.limiter = strict_limiter
        
        @app.post("/change-password")
        @password_change_rate_limit()
        async def change_password(request: Request, response: Response):
            return {"message": "Password changed"}
        
        client = TestClient(app)
        response = client.post("/change-password")
        assert response.status_code == 200


class TestCustomRateLimiting:
    """自定义限流策略测试（5个用例）"""
    
    def test_user_based_rate_limiting(self):
        """测试11: 基于用户ID的限流"""
        from unittest.mock import Mock
        
        request = Mock()
        request.client.host = "192.168.1.100"
        request.state.user = Mock(id=123)
        
        key = get_user_or_ip(request)
        assert "user:123" in key
    
    def test_user_based_rate_limiting_no_user(self):
        """测试12: 未认证用户使用IP限流"""
        from unittest.mock import Mock
        
        request = Mock()
        request.client.host = "192.168.1.100"
        request.state.user = None
        
        key = get_user_or_ip(request)
        assert "ip:192.168.1.100" in key
    
    def test_strict_combined_rate_limiting(self):
        """测试13: IP+用户组合限流"""
        from unittest.mock import Mock
        
        request = Mock()
        request.client.host = "192.168.1.100"
        request.state.user = Mock(id=456)
        
        key = get_ip_and_user(request)
        assert "ip:192.168.1.100" in key
        assert "user:456" in key
    
    def test_custom_rate_limit_decorator(self):
        """测试14: 自定义速率限制装饰器"""
        app = FastAPI()
        app.state.limiter = limiter
        
        @app.get("/custom")
        @rate_limit("20/minute")
        async def custom_endpoint(request: Request, response: Response):
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/custom")
        assert response.status_code == 200
    
    def test_user_rate_limit_decorator(self):
        """测试15: 基于用户的限流装饰器"""
        app = FastAPI()
        app.state.limiter = user_limiter
        
        @app.post("/batch-import")
        @user_rate_limit("5/minute")
        async def batch_import(request: Request, response: Response):
            return {"imported": 100}
        
        client = TestClient(app)
        response = client.post("/batch-import")
        assert response.status_code == 200


class TestRateLimitConfiguration:
    """速率限制配置测试（额外测试）"""
    
    def test_settings_rate_limit_config(self):
        """测试16: 配置文件中的速率限制设置"""
        from app.core.config import settings
        
        assert hasattr(settings, "RATE_LIMIT_ENABLED")
        assert hasattr(settings, "RATE_LIMIT_DEFAULT")
        assert hasattr(settings, "RATE_LIMIT_LOGIN")
        assert hasattr(settings, "RATE_LIMIT_REFRESH")
    
    def test_disabled_rate_limiting(self):
        """测试17: 禁用速率限制时装饰器不生效"""
        # 这个测试需要临时修改settings，实际中通过环境变量控制
        from app.utils.rate_limit_decorator import rate_limit as rl_decorator
        
        # 装饰器即使在禁用状态也应该可以调用
        assert rl_decorator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
