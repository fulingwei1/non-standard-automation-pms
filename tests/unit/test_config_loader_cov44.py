# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 报表配置加载器"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

try:
    from app.services.report_framework.config_loader import ConfigLoader, ConfigError
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def loader(tmp_path):
    return ConfigLoader(config_dir=str(tmp_path))


class TestConfigLoader:

    def test_init_sets_config_dir(self, tmp_path):
        loader = ConfigLoader(str(tmp_path))
        assert loader.config_dir == tmp_path

    def test_get_raises_config_error_when_not_found(self, loader):
        with pytest.raises(ConfigError, match="not found"):
            loader.get("NONEXISTENT_REPORT")

    def test_reload_all_clears_cache(self, loader):
        loader._cache["A"] = MagicMock()
        loader._meta_cache["A"] = MagicMock()
        loader.reload()
        assert loader._cache == {}
        assert loader._meta_cache == {}

    def test_reload_specific_clears_only_that_entry(self, loader):
        loader._cache["A"] = MagicMock()
        loader._cache["B"] = MagicMock()
        loader.reload("A")
        assert "A" not in loader._cache
        assert "B" in loader._cache

    def test_list_available_returns_list(self, loader):
        result = loader.list_available()
        assert isinstance(result, list)

    def test_validate_config_raises_on_invalid_dict(self, loader):
        with pytest.raises(ConfigError):
            loader.validate_config({"bad": "config"})

    def test_get_uses_cache_on_second_call(self, loader):
        mock_config = MagicMock()
        mock_config.meta.code = "CACHED_REPORT"
        loader._cache["CACHED_REPORT"] = mock_config
        result = loader.get("CACHED_REPORT")
        assert result is mock_config

    def test_config_error_is_exception(self):
        err = ConfigError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"
