
# 初始化进度跟踪定时任务调度器（如果启用）
try:
    from app.scheduler_progress import start_scheduler as start_progress_scheduler
    from app.scheduler_progress import stop_scheduler as stop_progress_scheduler
except ImportError:
    start_progress_scheduler = None
    stop_progress_scheduler = None

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter

# 安全配置：生产环境禁用 OpenAPI 文档和 debug 模式
# 只在 DEBUG=True 时暴露 API 文档，避免接口泄露
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

# 初始化定时任务调度器（如果启用）
try:
    from app.utils.scheduler import init_scheduler, shutdown_scheduler

    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化所有调度器"""
        # 可以通过环境变量控制是否启用定时任务
        import os
        enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        if enable_scheduler:
            # 启动进度跟踪定时任务
            if start_progress_scheduler:
                start_progress_scheduler()
            # 启动其他定时任务
            init_scheduler()

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时关闭所有调度器"""
        # 关闭进度跟踪定时任务
        if stop_progress_scheduler:
            stop_progress_scheduler()
        # 关闭其他定时任务
        shutdown_scheduler()
except ImportError:
    # APScheduler未安装时跳过
    pass

# CORS配置 - 严格限制来源和允许的头部
# 安全改进：明确列出允许的头部，移除通配符
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # 严格限制允许的来源
        allow_credentials=True,  # 保留以支持可能的 cookie 场景
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",      # JWT token
            "Content-Type",       # 请求体类型
            "Accept",             # 响应类型
            "Origin",             # CORS 来源
            "X-Requested-With",   # AJAX 标识
        ],
    )

from app.api.v1.api import api_router

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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
