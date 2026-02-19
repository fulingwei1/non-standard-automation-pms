# -*- coding: utf-8 -*-
"""业务缓存服务单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.cache.business_cache")

try:
    from app.services.cache.business_cache import (
        BusinessCacheService,
        get_business_cache,
        invalidate_cache_on_change,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    BusinessCacheService = get_business_cache = invalidate_cache_on_change = None


def make_service():
    """创建带 mock cache 的业务缓存服务"""
    with patch("app.services.cache.business_cache.get_cache") as mock_get_cache:
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        svc = BusinessCacheService()
        svc.cache = mock_cache
        return svc, mock_cache


class TestProjectListCache:
    def test_get_returns_none_on_miss(self):
        svc, mock_cache = make_service()
        mock_cache.get.return_value = None
        result = svc.get_project_list(skip=0, limit=20)
        assert result is None

    def test_get_returns_cached(self):
        svc, mock_cache = make_service()
        mock_cache.get.return_value = [{"id": 1}]
        result = svc.get_project_list(skip=0, limit=20)
        assert result == [{"id": 1}]

    def test_set_calls_cache_set(self):
        svc, mock_cache = make_service()
        svc.set_project_list([{"id": 1}], skip=0, limit=20)
        mock_cache.set.assert_called_once()


class TestProjectDashboardCache:
    def test_get_dashboard_miss(self):
        svc, mock_cache = make_service()
        mock_cache.get.return_value = None
        assert svc.get_project_dashboard(99) is None

    def test_set_dashboard(self):
        svc, mock_cache = make_service()
        svc.set_project_dashboard({"health": "H1"}, project_id=5)
        mock_cache.set.assert_called_once()


class TestAlertCache:
    def test_get_alert_statistics_miss(self):
        svc, mock_cache = make_service()
        mock_cache.get.return_value = None
        assert svc.get_alert_statistics(days=30) is None

    def test_set_alert_statistics(self):
        svc, mock_cache = make_service()
        svc.set_alert_statistics({"total": 5}, days=30)
        mock_cache.set.assert_called_once()


class TestInvalidateCaches:
    def test_invalidate_project_cache(self):
        svc, mock_cache = make_service()
        svc.invalidate_project_cache(project_id=3)
        assert mock_cache.delete.call_count >= 1
        mock_cache.clear_pattern.assert_called()

    def test_invalidate_user_cache(self):
        svc, mock_cache = make_service()
        svc.invalidate_user_cache(user_id=7)
        assert mock_cache.delete.call_count >= 1

    def test_invalidate_alert_cache(self):
        svc, mock_cache = make_service()
        svc.invalidate_alert_cache()
        mock_cache.clear_pattern.assert_called()

    def test_invalidate_config_cache_specific(self):
        svc, mock_cache = make_service()
        svc.invalidate_config_cache("some_key")
        mock_cache.delete.assert_called_once()


class TestInvalidateCacheOnChange:
    def test_project_type(self):
        with patch("app.services.cache.business_cache.get_business_cache") as mock_get:
            mock_svc = MagicMock()
            mock_get.return_value = mock_svc
            invalidate_cache_on_change("project", 1)
            mock_svc.invalidate_project_cache.assert_called_once_with(1)

    def test_user_type(self):
        with patch("app.services.cache.business_cache.get_business_cache") as mock_get:
            mock_svc = MagicMock()
            mock_get.return_value = mock_svc
            invalidate_cache_on_change("user", 2)
            mock_svc.invalidate_user_cache.assert_called_once_with(2)

    def test_alert_type(self):
        with patch("app.services.cache.business_cache.get_business_cache") as mock_get:
            mock_svc = MagicMock()
            mock_get.return_value = mock_svc
            invalidate_cache_on_change("alert")
            mock_svc.invalidate_alert_cache.assert_called_once()
