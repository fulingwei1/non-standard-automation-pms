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
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """验证并设置 SECRET_KEY"""
        if self.SECRET_KEY is None:
            if self.DEBUG:
                # 开发环境生成临时密钥
                self.SECRET_KEY = secrets.token_urlsafe(32)
                warnings.warn(
                    "使用开发环境临时生成的 SECRET_KEY。"
                    "生产环境请务必通过环境变量 SECRET_KEY 设置安全的密钥。"
                )
            else:
                # 生产环境必须有密钥
                raise ValueError(
                    "生产环境必须设置 SECRET_KEY 环境变量。"
                    "请使用: python -c 'import secrets; print(secrets.token_urlsafe(32))' 生成安全密钥。"
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


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在（跳过 in-memory 数据库）
db_dir = os.path.dirname(settings.SQLITE_DB_PATH)
if db_dir:  # Skip for in-memory databases like ":memory:"
    os.makedirs(db_dir, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
