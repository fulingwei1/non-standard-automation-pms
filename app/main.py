# -*- coding: utf-8 -*-

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.exception_handlers import setup_exception_handlers
from app.core.logging_config import setup_logging
from app.core.middleware.auth_middleware import GlobalAuthMiddleware
from app.core.middleware.tenant_middleware import TenantContextMiddleware
from app.core.rate_limiting import limiter
from app.core.security_headers import setup_security_headers
from app.middleware.audit import AuditMiddleware

# 导入统一响应格式（确保可用）

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

# 审计日志中间件
app.add_middleware(AuditMiddleware)

# 租户上下文中间件 - 设置租户隔离上下文
# 注意：必须在 GlobalAuthMiddleware 之前添加，这样它会在认证之后执行
app.add_middleware(TenantContextMiddleware)

# 全局认证中间件 - 默认拒绝策略（最后添加，最先执行）
# 注意：FastAPI中间件是后进先出(LIFO)，后添加的先执行
app.add_middleware(GlobalAuthMiddleware)

# 全局 IP 速率限制中间件（in-memory，无 Redis 依赖）
# 位于 GlobalAuthMiddleware 之后 → 执行顺序最靠前，优先拒绝高频请求
# 可通过环境变量 RATE_LIMIT_ENABLED=false 禁用
import os

if os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false":
    from app.core.middleware.rate_limiting import (  # noqa: E402
        RateLimitMiddleware as InMemoryRateLimitMiddleware,
    )

    app.add_middleware(InMemoryRateLimitMiddleware)

# 认证路由优先注册到主应用，确保 /api/v1/auth/* 先于 stub 兜底匹配
try:
    from app.api.v1.endpoints import auth as auth_router_module
    app.include_router(
        auth_router_module.router,
        prefix=f"{settings.API_V1_PREFIX}/auth",
        tags=["auth"],
    )
except Exception as e:  # noqa: BLE001
    if os.getenv("STRICT_API_ROUTER", "true").lower() == "true":
        raise RuntimeError(f"Auth router 注册失败: {e}") from e
    import logging
    logging.getLogger(__name__).warning("Auth router not registered at app level: %s", e)

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

        # 初始化状态流转引擎处理器
        try:
            from app.services.status_handlers import register_all_handlers

            register_all_handlers()
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"状态处理器注册失败: {e}")

        # 恢复上一进程遗留的 AI 后台任务（线程池不跨重启，PENDING/RUNNING 标 FAILED）
        try:
            from app.services.ai_job_service import recover_stale_jobs

            recover_stale_jobs()
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"AI任务启动恢复失败: {e}")

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

except ImportError as e:
    import logging

    logging.getLogger(__name__).error(f"定时任务调度器导入失败: {e}")


@app.get("/")
def root():
    return {"message": "Welcome to Non-standard Automation Project Management System API"}


def _probe_database():
    try:
        from sqlalchemy import text

        from app.models.base import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "up"}
    except Exception as exc:
        return {"status": "down", "error": str(exc)}


def _probe_scheduler():
    try:
        from app.utils.scheduler import scheduler

        running = bool(getattr(scheduler, "running", False))
        jobs = scheduler.get_jobs() if running else []
        return {
            "status": "up" if running else "disabled",
            "running": running,
            "job_count": len(jobs),
        }
    except Exception as exc:
        return {"status": "down", "error": str(exc), "running": False, "job_count": 0}


def _probe_redis():
    try:
        from app.utils.redis_client import get_redis_client

        client = get_redis_client()
        if client is None:
            return {"status": "disabled", "configured": False}
        client.ping()
        return {"status": "up", "configured": True}
    except Exception as exc:
        return {"status": "down", "configured": True, "error": str(exc)}


def _build_health_payload(api_style: bool = False):
    dependencies = {
        "database": _probe_database(),
        "scheduler": _probe_scheduler(),
        "redis": _probe_redis(),
    }
    required_ok = dependencies["database"]["status"] == "up" and dependencies["scheduler"][
        "status"
    ] in {"up", "disabled"}
    optional_ok = dependencies["redis"]["status"] in {"up", "disabled"}
    is_healthy = required_ok and optional_ok

    payload = {
        "status": ("healthy" if api_style else "ok") if is_healthy else "degraded",
        "version": settings.APP_VERSION,
        "dependencies": dependencies,
    }
    if api_style:
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    return payload


def _metric_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _build_prometheus_metrics() -> str:
    payload = _build_health_payload(api_style=False)
    dependencies = payload["dependencies"]
    app_up = 1 if payload["status"] == "ok" else 0
    version = _metric_label(str(payload["version"]))

    lines = [
        "# HELP pms_app_health Application health status, 1 means ok.",
        "# TYPE pms_app_health gauge",
        f'pms_app_health{{version="{version}"}} {app_up}',
        "# HELP pms_dependency_up Dependency status, 1 means available.",
        "# TYPE pms_dependency_up gauge",
    ]
    for name, dependency in dependencies.items():
        status = dependency.get("status", "unknown")
        up = 1 if status in {"up", "disabled"} else 0
        lines.append(
            f'pms_dependency_up{{name="{_metric_label(name)}",status="{_metric_label(status)}"}} {up}'
        )

    scheduler = dependencies.get("scheduler", {})
    lines.extend(
        [
            "# HELP pms_scheduler_running Scheduler running flag.",
            "# TYPE pms_scheduler_running gauge",
            f"pms_scheduler_running {1 if scheduler.get('running') else 0}",
            "# HELP pms_scheduler_jobs Configured scheduler job count.",
            "# TYPE pms_scheduler_jobs gauge",
            f"pms_scheduler_jobs {int(scheduler.get('job_count') or 0)}",
        ]
    )

    try:
        from app.utils.scheduler_metrics import get_metrics_snapshot, get_metrics_statistics

        snapshot = get_metrics_snapshot()
        statistics = get_metrics_statistics()
        job_snapshot = snapshot.get("jobs", {})
        notification_snapshot = snapshot.get("notifications", {})

        lines.extend(
            [
                "# HELP pms_scheduler_job_success_total Total successful scheduler job runs.",
                "# TYPE pms_scheduler_job_success_total counter",
                "# HELP pms_scheduler_job_failure_total Total failed scheduler job runs.",
                "# TYPE pms_scheduler_job_failure_total counter",
                "# HELP pms_scheduler_job_last_duration_ms Last scheduler job duration in milliseconds.",
                "# TYPE pms_scheduler_job_last_duration_ms gauge",
            ]
        )
        for job_id, stats in job_snapshot.items():
            label = f'job_id="{_metric_label(str(job_id))}"'
            lines.append(
                f"pms_scheduler_job_success_total{{{label}}} {int(stats.get('success_count', 0))}"
            )
            lines.append(
                f"pms_scheduler_job_failure_total{{{label}}} {int(stats.get('failure_count', 0))}"
            )
            lines.append(
                f"pms_scheduler_job_last_duration_ms{{{label}}} {stats.get('last_duration_ms', 0)}"
            )

        lines.extend(
            [
                "# HELP pms_scheduler_job_duration_avg_ms Average scheduler job duration in milliseconds.",
                "# TYPE pms_scheduler_job_duration_avg_ms gauge",
                "# HELP pms_scheduler_job_duration_p95_ms P95 scheduler job duration in milliseconds.",
                "# TYPE pms_scheduler_job_duration_p95_ms gauge",
            ]
        )
        for job_id, stats in statistics.items():
            if stats.get("sample_count", 0) == 0:
                continue
            label = f'job_id="{_metric_label(str(job_id))}"'
            if stats.get("avg_duration_ms") is not None:
                lines.append(
                    f"pms_scheduler_job_duration_avg_ms{{{label}}} {stats['avg_duration_ms']:.2f}"
                )
            if stats.get("p95_duration_ms") is not None:
                lines.append(
                    f"pms_scheduler_job_duration_p95_ms{{{label}}} {stats['p95_duration_ms']:.2f}"
                )

        lines.extend(
            [
                "# HELP pms_scheduler_notification_success_total Successful scheduler notifications by channel.",
                "# TYPE pms_scheduler_notification_success_total counter",
                "# HELP pms_scheduler_notification_failure_total Failed scheduler notifications by channel.",
                "# TYPE pms_scheduler_notification_failure_total counter",
            ]
        )
        for channel, stats in notification_snapshot.items():
            label = f'channel="{_metric_label(str(channel))}"'
            lines.append(
                f"pms_scheduler_notification_success_total{{{label}}} {int(stats.get('success_count', 0))}"
            )
            lines.append(
                f"pms_scheduler_notification_failure_total{{{label}}} {int(stats.get('failure_count', 0))}"
            )
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).debug("调度器 Prometheus 指标生成失败，已跳过", exc_info=True)

    return "\n".join(lines) + "\n"


@app.get("/health")
def health_check():
    return _build_health_payload(api_style=False)


@app.get("/api/health")
def api_health_check():
    return _build_health_payload(api_style=True)


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    return PlainTextResponse(
        _build_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
