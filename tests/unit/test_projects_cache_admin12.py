# -*- coding: utf-8 -*-
"""ADMIN-12 project cache management endpoint contracts."""

from app.api.v1.endpoints.projects import cache as cache_endpoint


class RecordingCacheService:
    def __init__(self):
        self.calls: list[tuple] = []

    def invalidate_project_list(self) -> int:
        self.calls.append(("invalidate_project_list",))
        return 2

    def invalidate_project_statistics(self) -> int:
        self.calls.append(("invalidate_project_statistics",))
        return 3

    def invalidate_all_project_cache(self) -> int:
        self.calls.append(("invalidate_all_project_cache",))
        return 7

    def delete_pattern(self, pattern: str) -> int:
        self.calls.append(("delete_pattern", pattern))
        return 5

    def clear(self) -> bool:
        raise AssertionError("project cache endpoint must not flush the whole cache database")

    def clear_all(self) -> bool:
        raise AssertionError("project cache endpoint must not flush the whole cache database")


def test_clear_cache_default_clears_only_project_namespace(monkeypatch):
    fake_cache = RecordingCacheService()
    monkeypatch.setattr("app.services.cache_service.CacheService", lambda: fake_cache)

    response = cache_endpoint.clear_cache(db=None, current_user=object())

    assert response.code == 200
    assert response.data["cache_type"] == "project"
    assert response.data["deleted_count"] == 7
    assert fake_cache.calls == [("invalidate_all_project_cache",)]


def test_clear_cache_supports_frontend_pattern_param_with_allowlist(monkeypatch):
    fake_cache = RecordingCacheService()
    monkeypatch.setattr("app.services.cache_service.CacheService", lambda: fake_cache)

    response = cache_endpoint.clear_cache(
        db=None,
        current_user=object(),
        pattern="project:detail:*",
    )

    assert response.code == 200
    assert response.data["cache_type"] == "project_detail"
    assert response.data["deleted_count"] == 5
    assert fake_cache.calls == [("delete_pattern", "project:detail:*")]
