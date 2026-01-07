from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
)

# 初始化定时任务调度器（如果启用）
try:
    from app.utils.scheduler import init_scheduler, shutdown_scheduler
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化调度器"""
        # 可以通过环境变量控制是否启用定时任务
        import os
        enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        if enable_scheduler:
            init_scheduler()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时关闭调度器"""
        shutdown_scheduler()
except ImportError:
    # APScheduler未安装时跳过
    pass

# CORS配置 - 严格限制来源，不允许通配符
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # 严格限制允许的来源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
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
