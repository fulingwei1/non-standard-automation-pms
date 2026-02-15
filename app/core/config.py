# -*- coding: utf-8 -*-
"""
应用配置
"""

import os
import secrets
import warnings
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # Load env vars from common local files.
    # Important for dev: without a stable SECRET_KEY, JWTs become invalid after
    # every backend restart (leading to persistent 401s in the frontend).
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    model_config = SettingsConfigDict(
        env_file=(
            str(_PROJECT_ROOT / ".env"),  # generic (gitignored)
            str(_PROJECT_ROOT / ".env.local"),  # local dev (gitignored)
        ),
        case_sensitive=True,
    )

    # 应用信息
    APP_NAME: str = "非标自动化项目管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # 生产环境默认为 False，开发环境可通过环境变量设置 DEBUG=true

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: Optional[str] = None
    SQLITE_DB_PATH: str = "data/app.db"
    POSTGRES_URL: Optional[str] = None  # Vercel Postgres

    # Redis配置
    REDIS_URL: Optional[str] = None  # Redis连接URL，格式: redis://localhost:6379/0
    REDIS_CACHE_ENABLED: bool = True  # 是否启用Redis缓存
    REDIS_CACHE_DEFAULT_TTL: int = 300  # 默认缓存过期时间（秒），5分钟
    REDIS_CACHE_PROJECT_DETAIL_TTL: int = 600  # 项目详情缓存过期时间（秒），10分钟
    REDIS_CACHE_PROJECT_LIST_TTL: int = 300  # 项目列表缓存过期时间（秒），5分钟

    # JWT配置
    # 生产环境必须从环境变量设置 SECRET_KEY
    # 开发环境如未设置将自动生成一个临时密钥
    SECRET_KEY: Optional[str] = None
    OLD_SECRET_KEYS: Optional[str] = None  # 旧密钥列表（逗号分隔），用于密钥轮转
    SECRET_KEY_FILE: Optional[str] = None  # 密钥文件路径（Docker Secrets）
    OLD_SECRET_KEYS_FILE: Optional[str] = None  # 旧密钥文件路径
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 密钥管理配置
    SECRET_KEY_MIN_LENGTH: int = 32  # 密钥最小长度（字符数）
    SECRET_KEY_ROTATION_DAYS: int = 90  # 推荐的密钥轮转周期（天）
    OLD_KEYS_GRACE_PERIOD_DAYS: int = 30  # 旧密钥有效期（天）
    OLD_KEYS_MAX_COUNT: int = 3  # 最多保留的旧密钥数量

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """验证并设置 SECRET_KEY
        
        注意: 密钥验证和加载逻辑已移至 SecretKeyManager
        这里仅做基本检查和开发环境的临时密钥生成
        """
        if self.SECRET_KEY is None:
            if self.DEBUG:
                # 开发环境生成临时密钥
                self.SECRET_KEY = secrets.token_urlsafe(32)
                warnings.warn(
                    "使用开发环境临时生成的 SECRET_KEY。"
                    "生产环境请务必通过环境变量 SECRET_KEY 设置安全的密钥。"
                    "使用 'python scripts/manage_secrets.py generate' 生成安全密钥。"
                )
            else:
                # 生产环境必须有密钥
                raise ValueError(
                    "生产环境必须设置 SECRET_KEY 环境变量或 SECRET_KEY_FILE。"
                    "使用 'python scripts/manage_secrets.py generate' 生成安全密钥。"
                )
        
        # 验证密钥长度（基本检查）
        if len(self.SECRET_KEY) < self.SECRET_KEY_MIN_LENGTH:
            raise ValueError(
                f"SECRET_KEY 长度不足 {self.SECRET_KEY_MIN_LENGTH} 字符。"
                f"当前长度: {len(self.SECRET_KEY)}。"
                "使用 'python scripts/manage_secrets.py generate' 生成安全密钥。"
            )
        
        return self

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]  # 开发环境默认值，生产环境从环境变量读取

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        """
        Support both JSON array and comma-separated strings in env vars.

        Examples:
        - CORS_ORIGINS='["http://a.com","http://b.com"]'
        - CORS_ORIGINS='http://a.com,http://b.com'
        """
        if v is None:
            return v
        if isinstance(v, str):
            value = v.strip()
            if not value:
                return []
            if value.startswith("["):
                import json

                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return v

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"]

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 1000

    # Notification channels
    EMAIL_ENABLED: bool = False
    EMAIL_FROM: Optional[str] = None
    EMAIL_SMTP_SERVER: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # 短信通知配置（阿里云）
    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = "aliyun"  # aliyun/tencent
    SMS_ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    SMS_ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    SMS_ALIYUN_SIGN_NAME: Optional[str] = None
    SMS_ALIYUN_TEMPLATE_CODE: Optional[str] = None
    SMS_ALIYUN_REGION: str = "cn-hangzhou"
    # 短信成本控制
    SMS_MAX_PER_DAY: int = 100  # 每天最多发送短信数
    SMS_MAX_PER_HOUR: int = 20  # 每小时最多发送短信数

    WECHAT_WEBHOOK_URL: Optional[str] = None
    WECHAT_ENABLED: bool = False

    # 企业微信API配置
    WECHAT_CORP_ID: Optional[str] = None  # 企业ID
    WECHAT_AGENT_ID: Optional[str] = None  # 应用ID
    WECHAT_SECRET: Optional[str] = None  # 应用Secret
    WECHAT_TOKEN_CACHE_TTL: int = 7000  # Token缓存时间（秒），默认7000秒（约2小时）

    # 销售模块配置
    SALES_GROSS_MARGIN_THRESHOLD: float = 15.0  # 毛利率阈值（%），低于此值需要审批
    SALES_GROSS_MARGIN_WARNING: float = 20.0  # 毛利率警告阈值（%），低于此值发出警告
    SALES_MIN_LEAD_TIME_DAYS: int = 30  # 最小交期（天），低于此值发出警告

    # 销售模块提醒配置
    SALES_GATE_TIMEOUT_DAYS: int = 3  # 阶段门超时提醒阈值（天），默认3天
    SALES_QUOTE_EXPIRE_REMINDER_DAYS: List[int] = [7, 3, 1]  # 报价过期提醒时间点（天）
    SALES_CONTRACT_EXPIRE_REMINDER_DAYS: List[int] = [
        30,
        15,
        7,
    ]  # 合同到期提醒时间点（天）
    SALES_APPROVAL_TIMEOUT_HOURS: int = 24  # 审批超时提醒阈值（小时），默认24小时

    # Kimi AI 配置
    KIMI_API_KEY: Optional[str] = None  # Kimi API Key
    KIMI_API_BASE: str = "https://api.moonshot.cn/v1"  # Kimi API 基础URL
    KIMI_MODEL: str = "moonshot-v1-8k"  # 默认模型，可选：moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    KIMI_MAX_TOKENS: int = 4000  # 最大生成token数
    KIMI_TEMPERATURE: float = 0.7  # 温度参数，控制随机性
    KIMI_TIMEOUT: int = 30  # 请求超时时间（秒）
    KIMI_ENABLED: bool = False  # 是否启用Kimi AI功能

    # GLM (智谱AI) 配置
    GLM_API_KEY: Optional[str] = None  # GLM API Key
    GLM_API_BASE: str = "https://open.bigmodel.cn/api/paas/v4"  # GLM API 基础URL
    GLM_MODEL: str = "glm-4"  # 默认模型，可选：glm-4, glm-4v, glm-3-turbo
    GLM_MAX_TOKENS: int = 4000  # 最大生成token数
    GLM_TEMPERATURE: float = 0.7  # 温度参数，控制随机性
    GLM_TIMEOUT: int = 30  # 请求超时时间（秒）
    GLM_ENABLED: bool = False  # 是否启用GLM AI功能

    # API速率限制配置
    RATE_LIMIT_ENABLED: bool = True  # 是否启用速率限制
    RATE_LIMIT_STORAGE_URL: Optional[str] = None  # Redis存储URL，未设置则使用内存存储
    RATE_LIMIT_DEFAULT: str = "100/minute"  # 全局默认速率限制
    RATE_LIMIT_LOGIN: str = "5/minute"  # 登录端点限制
    RATE_LIMIT_REGISTER: str = "3/hour"  # 注册端点限制
    RATE_LIMIT_REFRESH: str = "10/minute"  # Token刷新限制
    RATE_LIMIT_PASSWORD_CHANGE: str = "3/hour"  # 密码修改限制
    RATE_LIMIT_DELETE: str = "20/minute"  # 删除操作限制
    RATE_LIMIT_BATCH: str = "10/minute"  # 批量操作限制
    
    @model_validator(mode="after")
    def validate_rate_limit_storage(self) -> "Settings":
        """验证速率限制存储配置"""
        # 如果没有设置专用的速率限制存储URL，尝试使用通用Redis URL
        if self.RATE_LIMIT_ENABLED and self.RATE_LIMIT_STORAGE_URL is None:
            if self.REDIS_URL:
                self.RATE_LIMIT_STORAGE_URL = self.REDIS_URL
            else:
                warnings.warn(
                    "未配置Redis存储，速率限制将使用内存存储。"
                    "这在分布式部署中可能导致限流不准确。"
                    "建议设置 REDIS_URL 或 RATE_LIMIT_STORAGE_URL 环境变量。"
                )
        return self


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在（跳过 in-memory 数据库）
db_dir = os.path.dirname(settings.SQLITE_DB_PATH)
if db_dir:  # Skip for in-memory databases like ":memory:"
    os.makedirs(db_dir, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
