# -*- coding: utf-8 -*-
"""ConfigLoader 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from app.services.report_framework.config_loader import ConfigLoader, ConfigError


class TestConfigLoader:
    def setup_method(self):
        self.loader = ConfigLoader(config_dir="/tmp/test_configs")

    def test_init(self):
        assert self.loader.config_dir == Path("/tmp/test_configs")
        assert self.loader._cache == {}

    def test_get_cached(self):
        mock_config = MagicMock()
        mock_config.meta.code = "TEST"
        self.loader._cache["TEST"] = mock_config
        result = self.loader.get("TEST")
        assert result is mock_config

    def test_get_not_found(self):
        with patch.object(self.loader, "_find_config_file", return_value=None):
            with pytest.raises(ConfigError, match="not found"):
                self.loader.get("MISSING")

    def test_get_code_mismatch(self):
        mock_config = MagicMock()
        mock_config.meta.code = "OTHER"
        with patch.object(self.loader, "_find_config_file", return_value=Path("/tmp/x.yaml")):
            with patch.object(self.loader, "_load_and_validate", return_value=mock_config):
                with pytest.raises(ConfigError, match="mismatch"):
                    self.loader.get("TEST")

    def test_reload_specific(self):
        self.loader._cache["A"] = MagicMock()
        self.loader._meta_cache["A"] = MagicMock()
        self.loader.reload("A")
        assert "A" not in self.loader._cache

    def test_reload_all(self):
        self.loader._cache["A"] = MagicMock()
        self.loader.reload()
        assert len(self.loader._cache) == 0

    def test_validate_config_invalid(self):
        with pytest.raises(ConfigError):
            self.loader.validate_config({})

    def test_load_and_validate_empty(self):
        with patch("builtins.open", mock_open(read_data="")):
            with patch("yaml.safe_load", return_value=None):
                with pytest.raises(ConfigError, match="Empty"):
                    self.loader._load_and_validate(Path("/tmp/empty.yaml"))
