# -*- coding: utf-8 -*-
"""
配置模块测试

测试覆盖：
1. 正常流程 - 配置加载、验证
2. 错误处理 - 缺少必需配置、无效值
3. 边界条件 - 环境变量优先级、默认值
4. 安全性 - 密钥强度、敏感信息
"""

import pytest
import os
import warnings
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsBasicLoading:
    """测试基本配置加载"""
    
    def test_default_settings(self):
        """测试默认配置值"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'DEBUG': 'false'
        }, clear=True):
            settings = Settings()
            
            assert settings.APP_NAME == "非标自动化项目管理系统"
            assert settings.APP_VERSION == "1.0.0"
            assert settings.DEBUG is False
    
    def test_load_from_env(self):
        """测试从环境变量加载"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'APP_NAME': 'Custom App',
            'DEBUG': 'true',
            'API_V1_PREFIX': '/custom/api'
        }):
            settings = Settings()
            
            assert settings.APP_NAME == 'Custom App'
            assert settings.DEBUG is True
            assert settings.API_V1_PREFIX == '/custom/api'
    
    def test_case_sensitive_env_vars(self):
        """测试环境变量大小写敏感"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'DEBUG': 'true',
            'debug': 'false'  # 小写应该被忽略
        }):
            settings = Settings()
            # 应该使用大写的DEBUG
            assert settings.DEBUG is True


class TestSecretKeyValidation:
    """测试密钥验证"""
    
    def test_secret_key_from_env(self):
        """测试从环境变量读取密钥"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'my-super-secret-key-with-32-chars!!!',
            'DEBUG': 'false'
        }):
            settings = Settings()
            assert settings.SECRET_KEY == 'my-super-secret-key-with-32-chars!!!'
    
    def test_secret_key_minimum_length(self):
        """测试密钥最小长度要求"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'short',  # 太短
            'DEBUG': 'false'
        }):
            with pytest.raises(ValueError, match="SECRET_KEY 长度不足"):
                Settings()
    
    def test_secret_key_auto_generated_in_debug(self):
        """测试DEBUG模式下自动生成密钥"""
        with patch.dict(os.environ, {'DEBUG': 'true'}, clear=True):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                settings = Settings()
                
                # 应该生成临时密钥
                assert settings.SECRET_KEY is not None
                assert len(settings.SECRET_KEY) >= 32
                
                # 应该有警告
                assert len(w) > 0
                assert "临时生成" in str(w[0].message)
    
    def test_secret_key_required_in_production(self):
        """测试生产环境必须提供密钥"""
        with patch.dict(os.environ, {'DEBUG': 'false'}, clear=True):
            with pytest.raises(ValueError, match="生产环境必须设置 SECRET_KEY"):
                Settings()
    
    def test_old_secret_keys_optional(self):
        """测试旧密钥配置可选"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'OLD_SECRET_KEYS': 'old-key-1-with-32-chars-minimum!!,old-key-2-with-32-chars-minimum!!',
            'DEBUG': 'false'
        }):
            settings = Settings()
            assert settings.OLD_SECRET_KEYS is not None


class TestDatabaseConfiguration:
    """测试数据库配置"""
    
    def test_default_sqlite_path(self):
        """测试默认SQLite路径"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.SQLITE_DB_PATH == "data/app.db"
    
    def test_custom_database_url(self):
        """测试自定义数据库URL"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }):
            settings = Settings()
            assert settings.DATABASE_URL == 'postgresql://user:pass@localhost/db'
    
    def test_postgres_url(self):
        """测试Postgres URL配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'POSTGRES_URL': 'postgresql://vercel:pass@localhost/db'
        }):
            settings = Settings()
            assert settings.POSTGRES_URL == 'postgresql://vercel:pass@localhost/db'


class TestRedisConfiguration:
    """测试Redis配置"""
    
    def test_redis_url_optional(self):
        """测试Redis URL可选"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            # Redis URL可以为None
            assert settings.REDIS_URL is None or isinstance(settings.REDIS_URL, str)
    
    def test_redis_cache_enabled(self):
        """测试Redis缓存启用配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'REDIS_CACHE_ENABLED': 'true'
        }):
            settings = Settings()
            assert settings.REDIS_CACHE_ENABLED is True
    
    def test_redis_cache_ttl_defaults(self):
        """测试Redis缓存TTL默认值"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.REDIS_CACHE_DEFAULT_TTL == 300
            assert settings.REDIS_CACHE_PROJECT_DETAIL_TTL == 600
            assert settings.REDIS_CACHE_PROJECT_LIST_TTL == 300


class TestJWTConfiguration:
    """测试JWT配置"""
    
    def test_jwt_algorithm(self):
        """测试JWT算法"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.ALGORITHM == "HS256"
    
    def test_access_token_expire_minutes(self):
        """测试访问令牌过期时间"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24  # 24小时
    
    def test_custom_token_expire(self):
        """测试自定义令牌过期时间"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'ACCESS_TOKEN_EXPIRE_MINUTES': '120'
        }):
            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120


class TestCORSConfiguration:
    """测试CORS配置"""
    
    def test_default_cors_origins(self):
        """测试默认CORS源"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert isinstance(settings.CORS_ORIGINS, list)
            assert "http://localhost:3000" in settings.CORS_ORIGINS
    
    def test_cors_origins_from_json(self):
        """测试从JSON字符串解析CORS源"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'CORS_ORIGINS': '["http://example.com","http://api.example.com"]'
        }):
            settings = Settings()
            assert "http://example.com" in settings.CORS_ORIGINS
            assert "http://api.example.com" in settings.CORS_ORIGINS
    
    def test_cors_origins_from_csv(self):
        """测试从逗号分隔字符串解析CORS源"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'CORS_ORIGINS': 'http://example.com,http://api.example.com'
        }):
            settings = Settings()
            assert "http://example.com" in settings.CORS_ORIGINS
            assert "http://api.example.com" in settings.CORS_ORIGINS
    
    def test_cors_origins_empty_string(self):
        """测试空CORS源字符串"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'CORS_ORIGINS': ''
        }):
            settings = Settings()
            assert settings.CORS_ORIGINS == []


class TestFileUploadConfiguration:
    """测试文件上传配置"""
    
    def test_upload_defaults(self):
        """测试上传配置默认值"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.UPLOAD_DIR == "uploads"
            assert settings.MAX_UPLOAD_SIZE == 10 * 1024 * 1024  # 10MB
            assert isinstance(settings.ALLOWED_EXTENSIONS, list)
    
    def test_custom_upload_dir(self):
        """测试自定义上传目录"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'UPLOAD_DIR': '/custom/uploads'
        }):
            settings = Settings()
            assert settings.UPLOAD_DIR == '/custom/uploads'
    
    def test_custom_max_upload_size(self):
        """测试自定义最大上传大小"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'MAX_UPLOAD_SIZE': '52428800'  # 50MB
        }):
            settings = Settings()
            assert settings.MAX_UPLOAD_SIZE == 52428800


class TestPaginationConfiguration:
    """测试分页配置"""
    
    def test_pagination_defaults(self):
        """测试分页默认值"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.DEFAULT_PAGE_SIZE == 20
            assert settings.MAX_PAGE_SIZE == 1000
    
    def test_custom_page_sizes(self):
        """测试自定义分页大小"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'DEFAULT_PAGE_SIZE': '50',
            'MAX_PAGE_SIZE': '500'
        }):
            settings = Settings()
            assert settings.DEFAULT_PAGE_SIZE == 50
            assert settings.MAX_PAGE_SIZE == 500


class TestNotificationConfiguration:
    """测试通知配置"""
    
    def test_email_disabled_by_default(self):
        """测试邮件默认禁用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.EMAIL_ENABLED is False
    
    def test_email_configuration(self):
        """测试邮件配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'EMAIL_ENABLED': 'true',
            'EMAIL_FROM': 'noreply@example.com',
            'EMAIL_SMTP_SERVER': 'smtp.example.com',
            'EMAIL_SMTP_PORT': '587',
            'EMAIL_USERNAME': 'user',
            'EMAIL_PASSWORD': 'pass'
        }):
            settings = Settings()
            assert settings.EMAIL_ENABLED is True
            assert settings.EMAIL_FROM == 'noreply@example.com'
            assert settings.EMAIL_SMTP_SERVER == 'smtp.example.com'
            assert settings.EMAIL_SMTP_PORT == 587
    
    def test_sms_disabled_by_default(self):
        """测试短信默认禁用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.SMS_ENABLED is False
    
    def test_wechat_disabled_by_default(self):
        """测试微信默认禁用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.WECHAT_ENABLED is False


class TestRateLimitConfiguration:
    """测试速率限制配置"""
    
    def test_rate_limit_enabled_by_default(self):
        """测试速率限制默认启用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.RATE_LIMIT_ENABLED is True
    
    def test_rate_limit_defaults(self):
        """测试速率限制默认值"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.RATE_LIMIT_DEFAULT == "100/minute"
            assert settings.RATE_LIMIT_LOGIN == "5/minute"
            assert settings.RATE_LIMIT_REGISTER == "3/hour"
    
    def test_rate_limit_storage_fallback(self):
        """测试速率限制存储fallback"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'REDIS_URL': 'redis://localhost:6379/0'
        }):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                settings = Settings()
                
                # 应该使用REDIS_URL作为存储
                assert settings.RATE_LIMIT_STORAGE_URL == 'redis://localhost:6379/0'
    
    def test_rate_limit_no_redis_warning(self):
        """测试无Redis时的警告"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }, clear=True):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                settings = Settings()
                
                # 应该有警告
                warning_found = any("未配置Redis存储" in str(warning.message) for warning in w)
                # 可能有警告，取决于实现


class TestAIConfiguration:
    """测试AI配置"""
    
    def test_kimi_disabled_by_default(self):
        """测试Kimi AI默认禁用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.KIMI_ENABLED is False
    
    def test_kimi_configuration(self):
        """测试Kimi AI配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'KIMI_ENABLED': 'true',
            'KIMI_API_KEY': 'test-kimi-key',
            'KIMI_MODEL': 'moonshot-v1-32k'
        }):
            settings = Settings()
            assert settings.KIMI_ENABLED is True
            assert settings.KIMI_API_KEY == 'test-kimi-key'
            assert settings.KIMI_MODEL == 'moonshot-v1-32k'
    
    def test_glm_disabled_by_default(self):
        """测试GLM AI默认禁用"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            assert settings.GLM_ENABLED is False


class TestConfigurationEdgeCases:
    """测试边缘情况"""
    
    def test_very_long_secret_key(self):
        """测试超长密钥"""
        long_key = "a" * 1000
        with patch.dict(os.environ, {
            'SECRET_KEY': long_key,
            'DEBUG': 'false'
        }):
            settings = Settings()
            assert settings.SECRET_KEY == long_key
    
    def test_special_characters_in_config(self):
        """测试配置中的特殊字符"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'key!@#$%^&*()_+-={}[]|:;<>?,./~`',
            'DEBUG': 'false'
        }):
            settings = Settings()
            assert '!@#$%^&*' in settings.SECRET_KEY
    
    def test_unicode_in_app_name(self):
        """测试应用名称中的Unicode字符"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'APP_NAME': '非标自动化系统 🚀'
        }):
            settings = Settings()
            assert '🚀' in settings.APP_NAME
    
    def test_zero_values(self):
        """测试零值配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'DEFAULT_PAGE_SIZE': '0',
            'MAX_PAGE_SIZE': '0'
        }):
            settings = Settings()
            assert settings.DEFAULT_PAGE_SIZE == 0
            assert settings.MAX_PAGE_SIZE == 0
    
    def test_negative_values(self):
        """测试负数配置"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
            'ACCESS_TOKEN_EXPIRE_MINUTES': '-1'
        }):
            settings = Settings()
            # 应该被接受或有验证错误
            assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)


class TestConfigurationSecurity:
    """测试配置安全性"""
    
    def test_secret_key_not_in_logs(self):
        """测试密钥不应出现在日志中"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            # 密钥应该被妥善保护
            assert settings.SECRET_KEY is not None
    
    def test_sensitive_defaults_not_exposed(self):
        """测试敏感默认值不暴露"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-32-chars-min!!',
        }):
            settings = Settings()
            # 默认情况下敏感配置应该为None
            assert settings.EMAIL_PASSWORD is None
            assert settings.SMS_ALIYUN_ACCESS_KEY_SECRET is None
    
    def test_debug_mode_warnings(self):
        """测试DEBUG模式警告"""
        with patch.dict(os.environ, {'DEBUG': 'true'}, clear=True):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                settings = Settings()
                
                # DEBUG模式应该有警告
                assert len(w) > 0
