#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils 测试验证脚本
直接运行测试逻辑，不依赖 conftest
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from unittest.mock import MagicMock, Mock, patch
import time

def test_pinyin_utils():
    """测试 pinyin_utils"""
    print("=" * 60)
    print("测试 pinyin_utils.py")
    print("=" * 60)
    
    from app.utils.pinyin_utils import (
        name_to_pinyin,
        name_to_pinyin_initials,
        generate_unique_username,
        generate_initial_password
    )
    
    # Test name_to_pinyin
    assert name_to_pinyin("张三") == "zhangsan", "name_to_pinyin 测试失败"
    assert name_to_pinyin("") == "", "空字符串测试失败"
    print("  ✓ name_to_pinyin 测试通过")
    
    # Test name_to_pinyin_initials
    assert name_to_pinyin_initials("张三") == "ZS", "name_to_pinyin_initials 测试失败"
    assert name_to_pinyin_initials("") == "", "空字符串首字母测试失败"
    print("  ✓ name_to_pinyin_initials 测试通过")
    
    # Test generate_unique_username
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    
    result = generate_unique_username("张三", mock_db)
    assert result == "zhangsan", "generate_unique_username 测试失败"
    print("  ✓ generate_unique_username 测试通过")
    
    # Test generate_initial_password
    password = generate_initial_password()
    assert len(password) == 16, "密码长度测试失败"
    assert isinstance(password, str), "密码类型测试失败"
    print("  ✓ generate_initial_password 测试通过")
    
    print("✅ pinyin_utils 所有测试通过\n")


def test_logger():
    """测试 logger"""
    print("=" * 60)
    print("测试 logger.py")
    print("=" * 60)
    
    from app.utils.logger import get_logger, log_error_with_context, log_warning_with_context
    import logging
    
    # Test get_logger
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger), "get_logger 测试失败"
    assert logger.name == "test_module", "logger 名称测试失败"
    print("  ✓ get_logger 测试通过")
    
    # Test log functions
    test_logger = logging.getLogger("test")
    error = ValueError("Test error")
    
    with patch.object(test_logger, 'error') as mock_error:
        log_error_with_context(test_logger, "Test", error, {"key": "value"})
        mock_error.assert_called_once()
        print("  ✓ log_error_with_context 测试通过")
    
    with patch.object(test_logger, 'warning') as mock_warning:
        log_warning_with_context(test_logger, "Test", {"key": "value"})
        mock_warning.assert_called_once()
        print("  ✓ log_warning_with_context 测试通过")
    
    print("✅ logger 所有测试通过\n")


def test_scheduler():
    """测试 scheduler"""
    print("=" * 60)
    print("测试 scheduler.py")
    print("=" * 60)
    
    from app.utils.scheduler import _resolve_callable, job_listener
    from datetime import datetime, timezone
    
    # Test _resolve_callable
    task = {
        "module": "app.utils.scheduler",
        "callable": "job_listener"
    }
    func = _resolve_callable(task)
    assert callable(func), "_resolve_callable 测试失败"
    assert func.__name__ == "job_listener", "函数名称测试失败"
    print("  ✓ _resolve_callable 测试通过")
    
    # Test job_listener
    mock_event = MagicMock()
    mock_event.job_id = "test_job"
    mock_event.jobstore = "default"
    mock_event.scheduled_run_time = datetime.now(timezone.utc)
    mock_event.exception = None
    
    with patch('app.utils.scheduler.logger') as mock_logger:
        job_listener(mock_event)
        mock_logger.info.assert_called_once()
        print("  ✓ job_listener 测试通过")
    
    print("✅ scheduler 所有测试通过\n")


def test_cache_decorator():
    """测试 cache_decorator"""
    print("=" * 60)
    print("测试 cache_decorator.py")
    print("=" * 60)
    
    from app.utils.cache_decorator import get_cache_service, QueryStats
    
    # Test get_cache_service singleton
    service1 = get_cache_service()
    service2 = get_cache_service()
    assert service1 is service2, "单例模式测试失败"
    print("  ✓ get_cache_service 单例测试通过")
    
    # Test QueryStats
    stats = QueryStats()
    stats.record_query("test_func", 0.3, {"param": "value"})
    assert len(stats.queries) == 1, "QueryStats 记录测试失败"
    assert stats.total_time == 0.3, "QueryStats 时间统计测试失败"
    print("  ✓ QueryStats 测试通过")
    
    print("✅ cache_decorator 所有测试通过\n")


def test_wechat_client():
    """测试 wechat_client"""
    print("=" * 60)
    print("测试 wechat_client.py")
    print("=" * 60)
    
    from app.utils.wechat_client import WeChatTokenCache
    
    # Test WeChatTokenCache
    WeChatTokenCache.clear()
    WeChatTokenCache.set("test_key", "test_token", expires_in=7200)
    result = WeChatTokenCache.get("test_key")
    assert result == "test_token", "WeChatTokenCache get/set 测试失败"
    print("  ✓ WeChatTokenCache 测试通过")
    
    print("✅ wechat_client 所有测试通过\n")


def test_alert_escalation():
    """测试 alert_escalation_task"""
    print("=" * 60)
    print("测试 alert_escalation_task.py")
    print("=" * 60)
    
    try:
        # 尝试导入，如果失败则跳过
        from app.utils.alert_escalation_task import _determine_escalated_level
        from app.models.enums import AlertLevelEnum
        
        # Test _determine_escalated_level
        result = _determine_escalated_level(AlertLevelEnum.INFO.value)
        assert result == AlertLevelEnum.WARNING.value, "INFO 升级测试失败"
        
        result = _determine_escalated_level(AlertLevelEnum.WARNING.value)
        assert result == AlertLevelEnum.CRITICAL.value, "WARNING 升级测试失败"
        
        result = _determine_escalated_level(AlertLevelEnum.URGENT.value)
        assert result is None, "URGENT 无法升级测试失败"
        print("  ✓ _determine_escalated_level 测试通过")
        print("✅ alert_escalation_task 所有测试通过\n")
    except ImportError as e:
        print(f"  ⚠️  跳过测试（导入依赖问题）: {e}")
        print("  ℹ️  这是代码依赖问题，不是测试代码问题\n")
        raise  # 重新抛出，让调用者知道这是跳过


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Utils 模块测试验证")
    print("=" * 60 + "\n")
    
    tests = [
        test_pinyin_utils,
        test_logger,
        test_scheduler,
        test_cache_decorator,
        test_wechat_client,
        test_alert_escalation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
            print("=" * 60)
            print(f"测试总结: {passed} 个通过, {failed} 个失败")
            print("=" * 60)
    
            return 0 if failed == 0 else 1


            if __name__ == "__main__":
                sys.exit(main())
