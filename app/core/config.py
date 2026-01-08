# -*- coding: utf-8 -*-
"""
应用配置
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用信息
    APP_NAME: str = "非标自动化项目管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: Optional[str] = None
    SQLITE_DB_PATH: str = "data/app.db"
    
    # Redis配置
    REDIS_URL: Optional[str] = None  # Redis连接URL，格式: redis://localhost:6379/0
    REDIS_CACHE_ENABLED: bool = True  # 是否启用Redis缓存
    REDIS_CACHE_DEFAULT_TTL: int = 300  # 默认缓存过期时间（秒），5分钟
    REDIS_CACHE_PROJECT_DETAIL_TTL: int = 600  # 项目详情缓存过期时间（秒），10分钟
    REDIS_CACHE_PROJECT_LIST_TTL: int = 300  # 项目列表缓存过期时间（秒），5分钟

    # JWT配置
    SECRET_KEY: str = "dev-temp-secret-key-for-testing-only-change-in-production"  # TODO: 生产环境必须从环境变量读取
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]  # 开发环境默认值，生产环境从环境变量读取

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Notification channels
    EMAIL_ENABLED: bool = False
    EMAIL_FROM: Optional[str] = None
    EMAIL_SMTP_SERVER: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    WECHAT_WEBHOOK_URL: Optional[str] = None
    WECHAT_ENABLED: bool = False

    # 销售模块配置
    SALES_GROSS_MARGIN_THRESHOLD: float = 15.0  # 毛利率阈值（%），低于此值需要审批
    SALES_GROSS_MARGIN_WARNING: float = 20.0  # 毛利率警告阈值（%），低于此值发出警告
    SALES_MIN_LEAD_TIME_DAYS: int = 30  # 最小交期（天），低于此值发出警告
    
    # 销售模块提醒配置
    SALES_GATE_TIMEOUT_DAYS: int = 3  # 阶段门超时提醒阈值（天），默认3天
    SALES_QUOTE_EXPIRE_REMINDER_DAYS: List[int] = [7, 3, 1]  # 报价过期提醒时间点（天）
    SALES_CONTRACT_EXPIRE_REMINDER_DAYS: List[int] = [30, 15, 7]  # 合同到期提醒时间点（天）
    SALES_APPROVAL_TIMEOUT_HOURS: int = 24  # 审批超时提醒阈值（小时），默认24小时

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
