# -*- coding: utf-8 -*-
"""
核心配置模块测试
"""



class TestSettings:
    """测试应用配置类"""

    def test_settings_instance_exists(self):
        """测试 settings 单例存在"""
        from app.core.config import settings
        
        assert settings is not None
        assert settings.APP_NAME == "非标自动化项目管理系统"

    def test_app_info_config(self):
        """测试应用信息配置"""
        from app.core.config import settings
        
        assert settings.APP_VERSION == "1.0.0"
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_cors_origins_default(self):
        """测试CORS默认配置"""
        from app.core.config import settings
        
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_jwt_config(self):
        """测试JWT配置"""
        from app.core.config import settings
        
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24  # 24小时
        assert hasattr(settings, 'SECRET_KEY')

    def test_database_config(self):
        """测试数据库配置"""
        from app.core.config import settings
        
        assert hasattr(settings, 'DATABASE_URL')
        # SQLITE_DB_PATH 可能是 :memory: 或 data/app.db，取决于环境
        assert settings.SQLITE_DB_PATH in [':memory:', 'data/app.db']

    def test_redis_config(self):
        """测试Redis配置"""
        from app.core.config import settings
        
        assert hasattr(settings, 'REDIS_URL')
        assert settings.REDIS_CACHE_ENABLED is True
        assert settings.REDIS_CACHE_DEFAULT_TTL == 300

    def test_rate_limit_config(self):
        """测试速率限制配置"""
        from app.core.config import settings
        
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_DEFAULT == "100/minute"
        assert settings.RATE_LIMIT_LOGIN == "5/minute"

    def test_sales_config_defaults(self):
        """测试销售配置默认值"""
        from app.core.config import settings
        
        assert settings.SALES_GROSS_MARGIN_THRESHOLD == 20.0
        assert settings.SALES_GROSS_MARGIN_WARNING == 25.0
        assert settings.SALES_MIN_LEAD_TIME_DAYS == 30
        assert settings.SALES_TECH_SCORE_PASS == 60
        assert settings.SALES_TECH_SCORE_LOW_RISK == 80

    def test_pagination_config_defaults(self):
        """测试分页配置默认值"""
        from app.core.config import settings
        
        assert settings.DEFAULT_PAGE_SIZE == 20
        assert settings.MAX_PAGE_SIZE == 1000

    def test_ai_config_defaults(self):
        """测试AI配置"""
        from app.core.config import settings
        
        assert settings.KIMI_MODEL == "moonshot-v1-8k"
        assert settings.KIMI_MAX_TOKENS == 4000
        assert settings.GLM_MODEL == "glm-4"
        # KIMI_ENABLED 可以是 True 或 False，取决于环境变量
        assert isinstance(settings.KIMI_ENABLED, bool)
        assert isinstance(settings.GLM_ENABLED, bool)

    def test_upload_config(self):
        """测试上传配置"""
        from app.core.config import settings
        
        assert settings.UPLOAD_DIR == "uploads"
        assert settings.MAX_UPLOAD_SIZE == 10 * 1024 * 1024  # 10MB
        assert ".pdf" in settings.ALLOWED_EXTENSIONS
        assert ".xlsx" in settings.ALLOWED_EXTENSIONS

    def test_notification_config(self):
        """测试通知配置"""
        from app.core.config import settings
        
        assert settings.EMAIL_ENABLED is False
        assert settings.SMS_ENABLED is False
        assert settings.WECHAT_ENABLED is False
        assert settings.SMS_PROVIDER == "aliyun"

    def test_sales_aging_config(self):
        """测试账龄配置"""
        from app.core.config import settings
        
        assert settings.SALES_AGING_BUCKET_1 == 30
        assert settings.SALES_AGING_BUCKET_2 == 60
        assert settings.SALES_AGING_BUCKET_3 == 90

    def test_lead_reminder_config(self):
        """测试线索提醒配置"""
        from app.core.config import settings
        
        assert settings.SALES_LEAD_WEEKLY_REMINDER_WEEKDAY == 0
        assert settings.SALES_LEAD_OVERDUE_DAYS == 7
        assert settings.SALES_LEAD_HIGH_PRIORITY_SCORE == 80

    def test_itr_config(self):
        """测试ITR流程配置"""
        from app.core.config import settings
        
        assert settings.ITR_QUERY_LIMIT == 100
        assert settings.ITR_QUERY_TIMEOUT_SECONDS == 30
        assert settings.ITR_TIMELINE_ISSUE_LIMIT == 50