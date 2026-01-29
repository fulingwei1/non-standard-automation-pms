# -*- coding: utf-8 -*-
"""
调度器状态和任务管理端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.core.auth import check_permission
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/status", response_model=ResponseModel)
def get_scheduler_status(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取调度器状态
    返回调度器运行状态和已注册的任务列表
    """
    try:
        from app.utils.scheduler import scheduler

        jobs = scheduler.get_jobs()

        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger) if job.trigger else None,
            })

        return ResponseModel(
            code=200,
            message="success",
            data={
                "running": scheduler.running,
                "job_count": len(jobs),
                "jobs": job_list
            }
        )
    except ImportError:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "running": False,
                "job_count": 0,
                "jobs": [],
                "error": "APScheduler未安装"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.get("/jobs", response_model=ResponseModel)
def get_scheduler_jobs(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取所有已注册的任务列表
    """
    try:
        from app.utils.scheduler import scheduler

        jobs = scheduler.get_jobs()

        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger) if job.trigger else None,
                "func": job.func.__name__ if job.func else None,
            })

        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(jobs),
                "jobs": job_list
            }
        )
    except ImportError:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": 0,
                "jobs": [],
                "error": "APScheduler未安装"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/jobs/{job_id}/trigger", response_model=ResponseModel)
def trigger_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    手动触发指定任务
    注意：需要管理员权限
    """
    # 检查管理员权限
    if not check_permission(current_user, "scheduler:admin", db):
        raise HTTPException(status_code=403, detail="需要管理员权限才能手动触发任务")

    try:
        from app.utils.scheduler import scheduler

        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在")

        # 手动触发任务
        job.modify(next_run_time=None)
        scheduler.wakeup()

        return ResponseModel(
            code=200,
            message="success",
            data={
                "job_id": job_id,
                "job_name": job.name,
                "message": "任务已触发"
            }
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="APScheduler未安装")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发任务失败: {str(e)}")


@router.get("/services/list", response_model=ResponseModel)
def list_all_services(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    列出所有可用的服务函数
    包含完整的元数据：依赖表、风险级别、SLA 等
    """
    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS

        services = []
        for task in SCHEDULER_TASKS:
            services.append({
                "id": task["id"],
                "name": task["name"],
                "module": task["module"],
                "callable": task["callable"],
                "cron": task.get("cron"),
                "owner": task.get("owner"),
                "category": task.get("category"),
                "enabled": task.get("enabled", True),
                "description": task.get("description"),
                "dependencies_tables": task.get("dependencies_tables", []),
                "risk_level": task.get("risk_level", "UNKNOWN"),
                "sla": task.get("sla", {}),
            })

        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(services),
                "services": services
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")
