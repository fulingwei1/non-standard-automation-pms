# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security_headers import setup_security_headers
from app.core.csrf import CSRFMiddleware
from app.core.logging_config import setup_logging
from app.core.exception_handlers import setup_exception_handlers
from app.api.v1.api import api_router

# 导入统一响应格式（确保可用）
from app.core.schemas.response import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    ListResponse,
)

# 配置日志
setup_logging()

# 安全配置：生产环境禁用 OpenAPI 文档和 debug 模式
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    debug=settings.DEBUG,
)

# 注册速率限制器和异常处理
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置异常处理器
setup_exception_handlers(app)

# CORS配置 - 严格限制来源和允许的头部
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
    )

# 安全HTTP响应头中间件
setup_security_headers(app)

# CSRF防护中间件
app.add_middleware(CSRFMiddleware)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 初始化进度跟踪定时任务调度器（如果启用）
try:
    from app.scheduler_progress import start_scheduler as start_progress_scheduler
    from app.scheduler_progress import stop_scheduler as stop_progress_scheduler
except ImportError:
    start_progress_scheduler = None
    stop_progress_scheduler = None

# 初始化定时任务调度器（如果启用）
try:
    from app.utils.scheduler import init_scheduler, shutdown_scheduler

    @app.on_event("startup")
    async def startup_event():
        import os

        # 初始化基础数据（预置模板等）
        try:
            from app.utils.init_data import init_all_data
            init_all_data()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"基础数据初始化失败: {e}")

        enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        if enable_scheduler:
            if start_progress_scheduler:
                start_progress_scheduler()
            init_scheduler()

    @app.on_event("shutdown")
    async def shutdown_event():
        if stop_progress_scheduler:
            stop_progress_scheduler()
        shutdown_scheduler()
except ImportError:
    pass


@app.get("/")
def root():
    return {
        "message": "Welcome to Non-standard Automation Project Management System API"
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
