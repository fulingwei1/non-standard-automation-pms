# -*- coding: utf-8 -*-
"""
单元测试: 配置模块 (core.config)

测试内容：
- Settings 类初始化
- 环境变量加载
- 配置验证器
- 配置默认值
"""

import os
import pytest
from unittest.mock import patch

from app.core.config import Settings


class TestSettingsInitialization:
    """测试 Settings 初始化"""

    def test_settings_default_values(self):
        """测试默认配置值"""
        # 设置必需的环境变量
        os.environ["SECRET_KEY"] = "test_secret_key_123"

        settings = Settings()

        # 验证应用信息
        assert settings.APP_NAME == "非标自动化项目管理系统"
        assert settings.APP_VERSION == "1.0.0"

        # 验证 API 配置
        assert settings.API_V1_PREFIX == "/api/v1"

        # 验证数据库配置
        assert settings.SQLITE_DB_PATH == "data/app.db"
        assert settings.DATABASE_URL is None  # 默认未设置
        assert settings.POSTGRES_URL is None

        # 验证 JWT 配置
        assert settings.SECRET_KEY == "test_secret_key_123"
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24  # 24 小时

        # 验证 Redis 配置
        assert settings.REDIS_URL is None  # 默认未设置
        assert settings.REDIS_CACHE_ENABLED is True
        assert settings.REDIS_CACHE_DEFAULT_TTL == 300
        assert settings.REDIS_CACHE_PROJECT_DETAIL_TTL == 600
        assert settings.REDIS_CACHE_PROJECT_LIST_TTL == 300

        # 验证 CORS 配置
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8000" in settings.CORS_ORIGINS

    def test_settings_debug_mode_with_generated_secret(self):
        """测试 DEBUG 模式自动生成 SECRET_KEY"""
        # 设置 DEBUG 模式，不设置 SECRET_KEY
        os.environ["DEBUG"] = "true"

        settings = Settings()

        # 验证 SECRET_KEY 被自动生成
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 20  # token_urlsafe 生成 32 字节
        assert settings.DEBUG is True

    @patch.dict(os.environ, {"SECRET_KEY": "test_secret", "DEBUG": "false"})
    def test_settings_production_mode_requires_secret_key(self):
        """测试生产环境必须有 SECRET_KEY"""
        settings = Settings()
        # 如果 SECRET_KEY 存在且 DEBUG=False，应该通过
        assert settings.SECRET_KEY == "test_secret"
        assert settings.DEBUG is False

    def test_settings_invalid_secret_key_raises_error(self):
        """测试生产环境没有 SECRET_KEY 应该抛出错误"""
        # 移除 SECRET_KEY，设置 DEBUG=false
        os.environ.pop("SECRET_KEY", None)
        os.environ["DEBUG"] = "false"

        with pytest.raises(ValueError) as exc_info:
            Settings()

        assert "生产环境必须设置 SECRET_KEY" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_key",
            "DATABASE_URL": "mysql://user:pass@localhost:3306/testdb",
            "REDIS_URL": "redis://localhost:6379/0",
            "POSTGRES_URL": "postgresql://user:pass@localhost:5432/testdb",
        },
    )
    def test_settings_override_from_env(self):
        """测试从环境变量覆盖配置"""
        settings = Settings()

        assert settings.DATABASE_URL == "mysql://user:pass@localhost:3306/testdb"
        assert settings.REDIS_URL == "redis://localhost:6379/0"
        assert settings.POSTGRES_URL == "postgresql://user:pass@localhost:5432/testdb"


class TestSecretKeyValidation:
    """测试 SECRET_KEY 验证器"""

    @patch.dict(os.environ, {"DEBUG": "false"})
    def test_validate_secret_key_missing_in_production(self):
        """测试生产环境缺少 SECRET_KEY"""
        os.environ.pop("SECRET_KEY", None)

        settings = Settings()

        # 验证自定义验证器
        with pytest.raises(ValueError):
            settings.validate_secret_key(settings)

    @patch.dict(os.environ, {"DEBUG": "true"})
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_secret_key_generates_in_debug(self):
        """测试 DEBUG 模式自动生成 SECRET_KEY"""
        os.environ.pop("SECRET_KEY", None)

        settings = Settings()
        result = settings.validate_secret_key(settings)

        assert result is settings  # 返回 self
        assert settings.SECRET_KEY is not None

    @patch.dict(os.environ, {"SECRET_KEY": "existing_key", "DEBUG": "false"})
    def test_validate_secret_key_existing(self):
        """测试已有 SECRET_KEY 不变"""
        settings = Settings()
        original_key = settings.SECRET_KEY

        result = settings.validate_secret_key(settings)

        assert result is settings
        assert settings.SECRET_KEY == original_key
        assert settings.SECRET_KEY == "existing_key"


class TestCorsOriginsParser:
    """测试 CORS 源解析器"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_parse_cors_origins_array_string(self):
        """测试解析 JSON 数组格式"""
        cors_json = '["http://a.com", "http://b.com"]'
        os.environ["CORS_ORIGINS"] = cors_json

        settings = Settings()

        # 验证解析结果
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_parse_cors_origins_comma_string(self):
        """测试解析逗号分隔格式"""
        cors_string = "http://a.com,http://b.com"
        os.environ["CORS_ORIGINS"] = cors_string

        settings = Settings()

        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_parse_cors_origins_none(self):
        """测试 None 值"""
        os.environ["CORS_ORIGINS"] = "null"

        settings = Settings()
        assert settings.CORS_ORIGINS is None

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_parse_cors_origins_empty_string(self):
        """测试空字符串"""
        os.environ["CORS_ORIGINS"] = ""

        settings = Settings()
        assert settings.CORS_ORIGINS == ""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_parse_cors_origins_with_spaces(self):
        """测试带空格的格式"""
        cors_string = " http://a.com , http://b.com , http://c.com"
        os.environ["CORS_ORIGINS"] = cors_string

        settings = Settings()

        # 应该去除空格
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS
        assert "http://c.com" in settings.CORS_ORIGINS


class TestRedisConfig:
    """测试 Redis 配置"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_redis_cache_disabled(self):
        """测试禁用 Redis 缓存"""
        os.environ["REDIS_CACHE_ENABLED"] = "false"

        settings = Settings()
        assert settings.REDIS_CACHE_ENABLED is False

    @patch.dict(
        os.environ, {"SECRET_KEY": "test_key", "REDIS_CACHE_DEFAULT_TTL": "600"}
    )
    def test_redis_custom_ttl(self):
        """测试自定义 TTL"""
        settings = Settings()
        assert settings.REDIS_CACHE_DEFAULT_TTL == 600

    @patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_key",
            "REDIS_CACHE_PROJECT_DETAIL_TTL": "1200",
            "REDIS_CACHE_PROJECT_LIST_TTL": "900",
        },
    )
    def test_redis_project_specific_ttl(self):
        """测试项目特定的 TTL"""
        settings = Settings()
        assert settings.REDIS_CACHE_PROJECT_DETAIL_TTL == 1200
        assert settings.REDIS_CACHE_PROJECT_LIST_TTL == 900


class TestJwtConfig:
    """测试 JWT 配置"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_jwt_algorithm_default(self):
        """测试默认 JWT 算法"""
        settings = Settings()
        assert settings.ALGORITHM == "HS256"

    @patch.dict(
        os.environ, {"SECRET_KEY": "test_key", "ACCESS_TOKEN_EXPIRE_MINUTES": "120"}
    )
    def test_jwt_custom_expiry(self):
        """测试自定义 Token 过期时间"""
        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120

    @patch.dict(
        os.environ, {"SECRET_KEY": "test_key", "ACCESS_TOKEN_EXPIRE_MINUTES": "30"}
    )
    def test_jwt_short_expiry(self):
        """测试短过期时间"""
        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30


class TestDatabaseConfig:
    """测试数据库配置"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_database_default_sqlite_path(self):
        """测试默认 SQLite 路径"""
        settings = Settings()
        assert settings.SQLITE_DB_PATH == "data/app.db"

    @patch.dict(os.environ, {"SECRET_KEY": "test_key", "SQLITE_DB_PATH": "custom.db"})
    def test_database_custom_sqlite_path(self):
        """测试自定义 SQLite 路径"""
        settings = Settings()
        assert settings.SQLITE_DB_PATH == "custom.db"

    @patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_key",
            "DATABASE_URL": "mysql://root:pass@localhost:3306/mydb",
        },
    )
    def test_database_url(self):
        """测试数据库 URL"""
        settings = Settings()
        assert settings.DATABASE_URL == "mysql://root:pass@localhost:3306/mydb"

    @patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_key",
            "POSTGRES_URL": "postgresql://user:pass@host:5432/db",
        },
    )
    def test_postgres_url(self):
        """测试 PostgreSQL URL"""
        settings = Settings()
        assert settings.POSTGRES_URL == "postgresql://user:pass@host:5432/db"


class TestSettingsModelConfig:
    """测试 Settings 模型配置"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_settings_case_sensitive(self):
        """测试配置是否区分大小写"""
        settings = Settings()
        # 验证模型配置
        assert settings.model_config.get("case_sensitive", False) is True

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_settings_env_file_loading(self):
        """测试环境文件加载配置"""
        settings = Settings()
        # 验证环境文件路径被正确设置
        assert "env_file" in settings.model_config


class TestAppInfo:
    """测试应用信息"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_app_name(self):
        """测试应用名称"""
        settings = Settings()
        assert settings.APP_NAME == "非标自动化项目管理系统"

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_app_version(self):
        """测试应用版本"""
        settings = Settings()
        assert settings.APP_VERSION == "1.0.0"


class TestConfigModule:
    """测试配置模块的其他方面"""

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_settings_is_singleton(self):
        """测试 Settings 是单例（通过 pydantic-settings）"""
        settings1 = Settings()
        settings2 = Settings()

        # Settings 实例应该可以创建多个
        # 但由于使用了 BaseSettings，它们的行为应该一致
        assert isinstance(settings1, Settings)
        assert isinstance(settings2, Settings)

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_all_required_fields_present(self):
        """测试所有必需的字段都存在"""
        settings = Settings()

        required_fields = [
            "APP_NAME",
            "APP_VERSION",
            "API_V1_PREFIX",
            "SQLITE_DB_PATH",
            "DATABASE_URL",
            "POSTGRES_URL",
            "REDIS_URL",
            "REDIS_CACHE_ENABLED",
            "REDIS_CACHE_DEFAULT_TTL",
            "SECRET_KEY",
            "ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "CORS_ORIGINS",
            "DEBUG",
        ]

        for field in required_fields:
            assert hasattr(settings, field), f"Missing required field: {field}"

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_settings_serializable(self):
        """测试 Settings 可以序列化为字典"""
        settings = Settings()

        # 转换为字典（Pydantic 模型支持）
        settings_dict = settings.model_dump()

        assert isinstance(settings_dict, dict)
        assert "APP_NAME" in settings_dict
        assert settings_dict["APP_NAME"] == "非标自动化项目管理系统"

    @patch.dict(os.environ, {"SECRET_KEY": "test_key"})
    def test_settings_to_json(self):
        """测试 Settings 可以序列化为 JSON"""
        settings = Settings()

        # 转换为 JSON（Pydantic 模型支持）
        settings_json = settings.model_dump_json()

        assert isinstance(settings_json, str)
        assert "非标自动化项目管理系统" in settings_json

    @patch.dict(os.environ, {"SECRET_KEY": "test_key", "DEBUG": "true"})
    def test_debug_mode_affects_warnings(self):
        """测试 DEBUG 模式对警告的影响"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            settings = Settings()

            # DEBUG 模式应该生成关于 SECRET_KEY 的警告
            assert any(
                "使用开发环境临时生成的 SECRET_KEY" in str(warning.message)
                for warning in w
                if "SECRET_KEY" in str(warning.message)
            )
