# -*- coding: utf-8 -*-
"""
速率限制功能独立测试

不依赖conftest，可以独立运行
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock
from slowapi import Limiter


def test_import_rate_limiting_modules():
    """测试1: 导入速率限制模块"""
    from app.core import rate_limiting
    from app.middleware import rate_limit_middleware
    from app.utils import rate_limit_decorator
    
    assert rate_limiting is not None
    assert rate_limit_middleware is not None
    assert rate_limit_decorator is not None
    print("✅ 所有速率限制模块导入成功")


def test_limiter_instances():
    """测试2: 验证限制器实例"""
    from app.core.rate_limiting import limiter, user_limiter, strict_limiter
    
    assert limiter is not None
    assert user_limiter is not None
    assert strict_limiter is not None
    assert isinstance(limiter, Limiter)
    print("✅ 所有限制器实例创建成功")


def test_key_functions():
    """测试3: 测试键提取函数"""
    from app.core.rate_limiting import get_user_or_ip, get_ip_and_user
    from slowapi.util import get_remote_address
    
    # 创建模拟请求
    request = Mock()
    request.client.host = "192.168.1.100"
    
    # 测试IP提取
    ip = get_remote_address(request)
    assert ip == "192.168.1.100"
    print(f"✅ IP提取成功: {ip}")
    
    # 测试未认证用户（无user）
    request.state.user = None
    key = get_user_or_ip(request)
    assert "ip:192.168.1.100" in key
    print(f"✅ 未认证用户键: {key}")
    
    # 测试已认证用户
    request.state.user = Mock(id=123)
    key = get_user_or_ip(request)
    assert "user:123" in key
    print(f"✅ 已认证用户键: {key}")
    
    # 测试组合键
    key = get_ip_and_user(request)
    assert "ip:192.168.1.100" in key
    assert "user:123" in key
    print(f"✅ 组合键: {key}")


def test_configuration():
    """测试4: 验证配置"""
    from app.core.config import settings
    
    assert hasattr(settings, "RATE_LIMIT_ENABLED")
    assert hasattr(settings, "RATE_LIMIT_DEFAULT")
    assert hasattr(settings, "RATE_LIMIT_LOGIN")
    assert hasattr(settings, "RATE_LIMIT_REFRESH")
    assert hasattr(settings, "RATE_LIMIT_PASSWORD_CHANGE")
    assert hasattr(settings, "RATE_LIMIT_DELETE")
    assert hasattr(settings, "RATE_LIMIT_BATCH")
    
    print(f"✅ 速率限制配置:")
    print(f"  - 全局限制: {settings.RATE_LIMIT_DEFAULT}")
    print(f"  - 登录限制: {settings.RATE_LIMIT_LOGIN}")
    print(f"  - 刷新限制: {settings.RATE_LIMIT_REFRESH}")
    print(f"  - 密码修改: {settings.RATE_LIMIT_PASSWORD_CHANGE}")
    print(f"  - 删除操作: {settings.RATE_LIMIT_DELETE}")
    print(f"  - 批量操作: {settings.RATE_LIMIT_BATCH}")


def test_decorators():
    """测试5: 验证装饰器"""
    from app.utils.rate_limit_decorator import (
        rate_limit,
        user_rate_limit,
        strict_rate_limit,
        login_rate_limit,
        refresh_token_rate_limit,
        password_change_rate_limit,
        delete_rate_limit,
        batch_operation_rate_limit,
    )
    
    decorators = [
        rate_limit,
        user_rate_limit,
        strict_rate_limit,
        login_rate_limit,
        refresh_token_rate_limit,
        password_change_rate_limit,
        delete_rate_limit,
        batch_operation_rate_limit,
    ]
    
    for decorator in decorators:
        assert decorator is not None
        assert callable(decorator)
    
    print(f"✅ 所有装饰器可用: {len(decorators)}个")


def test_middleware():
    """测试6: 验证中间件"""
    from app.middleware.rate_limit_middleware import (
        RateLimitMiddleware,
        setup_rate_limit_middleware,
    )
    
    assert RateLimitMiddleware is not None
    assert setup_rate_limit_middleware is not None
    assert callable(setup_rate_limit_middleware)
    
    print("✅ 速率限制中间件可用")


def test_create_limiter_with_different_configs():
    """测试7: 测试不同配置的限制器创建"""
    from app.core.rate_limiting import create_limiter
    
    # 内存存储
    limiter1 = create_limiter(storage_uri=None, default_limits=["100/minute"])
    assert limiter1 is not None
    print("✅ 内存存储限制器创建成功")
    
    # 自定义限制
    limiter2 = create_limiter(default_limits=["50/minute", "500/hour"])
    assert limiter2 is not None
    print("✅ 自定义限制器创建成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("速率限制功能测试")
    print("="*60 + "\n")
    
    tests = [
        test_import_rate_limiting_modules,
        test_limiter_instances,
        test_key_functions,
        test_configuration,
        test_decorators,
        test_middleware,
        test_create_limiter_with_different_configs,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n运行: {test_func.__doc__.strip()}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
