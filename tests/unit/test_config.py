# -*- coding: utf-8 -*-
"""
配置模块单元测试
"""


import pytest

from app.core.config import Settings


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """测试默认配置值"""
        settings = Settings()

        # 应用信息
        assert settings.APP_NAME == "非标自动化项目管理系统"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False

        # API配置
        assert settings.API_V1_PREFIX == "/api/v1"

        # 数据库配置
        assert settings.SQLITE_DB_PATH == "data/app.db"
        assert settings.DATABASE_URL is None

        # JWT配置
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24

        # 文件上传配置
        assert settings.UPLOAD_DIR == "uploads"
        assert settings.MAX_UPLOAD_SIZE == 10 * 1024 * 1024
        assert len(settings.ALLOWED_EXTENSIONS) > 0

        # 分页配置
        assert settings.DEFAULT_PAGE_SIZE == 20
        assert settings.MAX_PAGE_SIZE == 1000

        # 销售模块配置
        assert settings.SALES_GROSS_MARGIN_THRESHOLD == 15.0
        assert settings.SALES_GROSS_MARGIN_WARNING == 20.0
        assert settings.SALES_MIN_LEAD_TIME_DAYS == 30

    def test_secret_key_debug_mode(self):
        """测试 DEBUG 模式下自动生成 SECRET_KEY"""
        settings = Settings(DEBUG=True)

        # DEBUG模式下应该自动生成 SECRET_KEY
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_secret_key_production_missing(self):
        """测试生产环境缺少 SECRET_KEY 时抛出异常"""
        with pytest.raises(ValueError, match="生产环境必须设置 SECRET_KEY 环境变量"):
            Settings(DEBUG=False, SECRET_KEY=None)

    def test_secret_key_production_provided(self):
        """测试生产环境提供 SECRET_KEY"""
        secret = "test-secret-key-12345678"
        settings = Settings(DEBUG=False, SECRET_KEY=secret)

        assert settings.SECRET_KEY == secret

    def test_cors_origins_default(self):
        """测试默认的 CORS_ORIGINS"""
        settings = Settings()

        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS
        assert "http://127.0.0.1:5173" in settings.CORS_ORIGINS

    def test_cors_origins_from_comma_separated_string(self):
        """测试从逗号分隔的字符串解析 CORS_ORIGINS"""
        origins = "http://a.com,http://b.com,http://c.com"
        settings = Settings(CORS_ORIGINS=origins)

        assert len(settings.CORS_ORIGINS) == 3
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS
        assert "http://c.com" in settings.CORS_ORIGINS

    def test_cors_origins_from_json_array(self):
        """测试从 JSON 数组解析 CORS_ORIGINS"""
        origins = '["http://a.com","http://b.com"]'
        settings = Settings(CORS_ORIGINS=origins)

        assert len(settings.CORS_ORIGINS) == 2
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS

    def test_cors_origins_empty_string(self):
        """测试空字符串的 CORS_ORIGINS"""
        settings = Settings(CORS_ORIGINS="")

        assert settings.CORS_ORIGINS == []

    def test_cors_origins_none(self):
        """测试 None 的 CORS_ORIGINS"""
        settings = Settings(CORS_ORIGINS=None)

        assert settings.CORS_ORIGINS is None

    def test_cors_origins_with_whitespace(self):
        """测试带空格的 CORS_ORIGINS 字符串"""
        origins = "http://a.com, http://b.com,  http://c.com "
        settings = Settings(CORS_ORIGINS=origins)

        assert len(settings.CORS_ORIGINS) == 3
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS
        assert "http://c.com" in settings.CORS_ORIGINS

    def test_redis_configuration(self):
        """测试 Redis 配置"""
        settings = Settings(
            REDIS_URL="redis://localhost:6379/0",
            REDIS_CACHE_ENABLED=True,
            REDIS_CACHE_DEFAULT_TTL=600,
            REDIS_CACHE_PROJECT_DETAIL_TTL=1200,
            REDIS_CACHE_PROJECT_LIST_TTL=400,
        )

        assert settings.REDIS_URL == "redis://localhost:6379/0"
        assert settings.REDIS_CACHE_ENABLED is True
        assert settings.REDIS_CACHE_DEFAULT_TTL == 600
        assert settings.REDIS_CACHE_PROJECT_DETAIL_TTL == 1200
        assert settings.REDIS_CACHE_PROJECT_LIST_TTL == 400

    def test_email_configuration(self):
        """测试邮件配置"""
        settings = Settings(
            EMAIL_ENABLED=True,
            EMAIL_FROM="test@example.com",
            EMAIL_SMTP_SERVER="smtp.example.com",
            EMAIL_SMTP_PORT=587,
            EMAIL_USERNAME="user",
            EMAIL_PASSWORD="pass",
        )

        assert settings.EMAIL_ENABLED is True
        assert settings.EMAIL_FROM == "test@example.com"
        assert settings.EMAIL_SMTP_SERVER == "smtp.example.com"
        assert settings.EMAIL_SMTP_PORT == 587
        assert settings.EMAIL_USERNAME == "user"
        assert settings.EMAIL_PASSWORD == "pass"

    def test_sms_configuration(self):
        """测试短信配置"""
        settings = Settings(
            SMS_ENABLED=True,
            SMS_PROVIDER="aliyun",
            SMS_ALIYUN_ACCESS_KEY_ID="key_id",
            SMS_ALIYUN_ACCESS_KEY_SECRET="secret",
            SMS_ALIYUN_SIGN_NAME="sign",
            SMS_ALIYUN_TEMPLATE_CODE="template",
            SMS_ALIYUN_REGION="cn-hangzhou",
            SMS_MAX_PER_DAY=200,
            SMS_MAX_PER_HOUR=30,
        )

        assert settings.SMS_ENABLED is True
        assert settings.SMS_PROVIDER == "aliyun"
        assert settings.SMS_ALIYUN_ACCESS_KEY_ID == "key_id"
        assert settings.SMS_ALIYUN_ACCESS_KEY_SECRET == "secret"
        assert settings.SMS_ALIYUN_SIGN_NAME == "sign"
        assert settings.SMS_ALIYUN_TEMPLATE_CODE == "template"
        assert settings.SMS_ALIYUN_REGION == "cn-hangzhou"
        assert settings.SMS_MAX_PER_DAY == 200
        assert settings.SMS_MAX_PER_HOUR == 30

    def test_sales_reminder_configuration(self):
        """测试销售提醒配置"""
        settings = Settings(
            SALES_GATE_TIMEOUT_DAYS=5,
            SALES_QUOTE_EXPIRE_REMINDER_DAYS=[14, 7, 3, 1],
            SALES_CONTRACT_EXPIRE_REMINDER_DAYS=[60, 30, 15],
            SALES_APPROVAL_TIMEOUT_HOURS=12,
        )

        assert settings.SALES_GATE_TIMEOUT_DAYS == 5
        assert settings.SALES_QUOTE_EXPIRE_REMINDER_DAYS == [14, 7, 3, 1]
        assert settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS == [60, 30, 15]
        assert settings.SALES_APPROVAL_TIMEOUT_HOURS == 12

    def test_wechat_configuration(self):
        """测试企业微信配置"""
        settings = Settings(
            WECHAT_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            WECHAT_ENABLED=True,
            WECHAT_CORP_ID="corp_id",
            WECHAT_AGENT_ID="agent_id",
            WECHAT_SECRET="secret",
            WECHAT_TOKEN_CACHE_TTL=7200,
        )

        assert (
            settings.WECHAT_WEBHOOK_URL
            == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        )
        assert settings.WECHAT_ENABLED is True
        assert settings.WECHAT_CORP_ID == "corp_id"
        assert settings.WECHAT_AGENT_ID == "agent_id"
        assert settings.WECHAT_SECRET == "secret"
        assert settings.WECHAT_TOKEN_CACHE_TTL == 7200

    def test_database_url_configuration(self):
        """测试数据库 URL 配置"""
        postgres_url = "postgresql://user:pass@localhost:5432/db"
        settings = Settings(DATABASE_URL=postgres_url)

        assert settings.DATABASE_URL == postgres_url

    def test_postgres_url_configuration(self):
        """测试 Vercel Postgres 配置"""
        postgres_url = "postgres://user:pass@localhost:5432/db"
        settings = Settings(POSTGRES_URL=postgres_url)

        assert settings.POSTGRES_URL == postgres_url

    def test_allowed_extensions(self):
        """测试允许的文件扩展名"""
        settings = Settings()

        assert ".jpg" in settings.ALLOWED_EXTENSIONS
        assert ".png" in settings.ALLOWED_EXTENSIONS
        assert ".pdf" in settings.ALLOWED_EXTENSIONS
        assert ".docx" in settings.ALLOWED_EXTENSIONS
        assert ".xlsx" in settings.ALLOWED_EXTENSIONS

    def test_upload_size_validation(self):
        """测试上传大小配置"""
        settings = Settings(MAX_UPLOAD_SIZE=20 * 1024 * 1024)  # 20MB

        assert settings.MAX_UPLOAD_SIZE == 20 * 1024 * 1024

    def test_page_size_configuration(self):
        """测试分页配置"""
        settings = Settings(
            DEFAULT_PAGE_SIZE=50,
            MAX_PAGE_SIZE=500,
        )

        assert settings.DEFAULT_PAGE_SIZE == 50
        assert settings.MAX_PAGE_SIZE == 500
