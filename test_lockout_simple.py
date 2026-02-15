#!/usr/bin/env python3
"""
简单的账户锁定功能测试脚本
"""

import sys
import os
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试AccountLockoutService
print("=" * 60)
print("测试 AccountLockoutService")
print("=" * 60)

# 首先导入模块
from app.services import account_lockout_service

# Mock Redis
with patch.object(account_lockout_service, 'get_redis_client') as mock_redis_client:
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.incr.return_value = 3
    mock_redis_client.return_value = mock_redis
    
    from app.services.account_lockout_service import AccountLockoutService
    
    # 测试1: 检查未锁定的账户
    print("\n✓ 测试1: 检查未锁定的账户")
    result = AccountLockoutService.check_lockout("testuser", None)
    assert result["locked"] == False
    print(f"  结果: {result}")
    
    # 测试2: 记录失败登录
    print("\n✓ 测试2: 记录失败登录")
    result = AccountLockoutService.record_failed_login(
        "testuser", "192.168.1.1", "Mozilla/5.0", db=None
    )
    assert result["attempts"] == 3
    print(f"  结果: 失败次数={result['attempts']}, 是否锁定={result['locked']}")
    
    # 测试3: 达到阈值触发锁定
    print("\n✓ 测试3: 达到阈值触发锁定")
    mock_redis.incr.return_value = 5
    result = AccountLockoutService.record_failed_login(
        "testuser", "192.168.1.1", "Mozilla/5.0", db=None
    )
    assert result["locked"] == True
    print(f"  结果: 失败次数={result['attempts']}, 已锁定={result['locked']}")
    
    # 测试4: 解锁账户
    print("\n✓ 测试4: 解锁账户")
    result = AccountLockoutService.unlock_account("testuser", "admin", None)
    assert result == True
    print(f"  结果: 解锁成功")
    
    # 测试5: IP黑名单检查
    print("\n✓ 测试5: IP黑名单检查")
    mock_redis.exists.return_value = 0
    result = AccountLockoutService.is_ip_blacklisted("192.168.1.1")
    assert result == False
    print(f"  结果: IP未在黑名单中")

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
print("\n核心功能验证:")
print("  ✓ 锁定状态检查")
print("  ✓ 失败登录记录")
print("  ✓ 自动锁定触发")
print("  ✓ 手动解锁")
print("  ✓ IP黑名单管理")
print("\n账户锁定机制已成功实现！")
