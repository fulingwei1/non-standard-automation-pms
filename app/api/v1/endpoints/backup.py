"""
备份管理API端点
提供备份相关的REST API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.services.backup_service import BackupService
from app.core.auth import get_current_user
from app.models.user import User
from app.core.auth import is_superuser

router = APIRouter()


class BackupRequest(BaseModel):
    """备份请求"""
    backup_type: str = Field(
        default="full",
        description="备份类型: full/database/files"
    )


class BackupResponse(BaseModel):
    """备份响应"""
    status: str
    message: str
    timestamp: Optional[str] = None
    backup_type: Optional[str] = None
    output: Optional[str] = None


class BackupFile(BaseModel):
    """备份文件信息"""
    filename: str
    path: str
    size: int
    size_human: str
    created_at: str
    has_checksum: bool
    md5: Optional[str] = None
    type: str


class BackupStats(BaseModel):
    """备份统计信息"""
    database: dict
    uploads: dict
    configs: dict
    full: dict
    disk: Optional[dict] = None


@router.post("/backups", response_model=BackupResponse, tags=["backup"])
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    创建备份
    
    需要管理员权限
    """
    # 检查权限（仅管理员可以执行备份）
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 在后台执行备份
    def run_backup():
        BackupService.create_backup(request.backup_type)
    
    background_tasks.add_task(run_backup)
    
    return BackupResponse(
        status="scheduled",
        message=f"{request.backup_type} 备份已加入队列，正在后台执行",
        timestamp=datetime.now().isoformat(),
        backup_type=request.backup_type
    )


@router.get("/backups", response_model=List[BackupFile], tags=["backup"])
async def list_backups(
    backup_type: str = "database",
    current_user: User = Depends(get_current_user)
):
    """
    列出所有备份文件
    
    参数:
    - backup_type: 备份类型 (database/uploads/configs/logs/full)
    """
    # 检查权限
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    backups = BackupService.list_backups(backup_type)
    return backups


@router.get("/backups/latest", response_model=BackupFile, tags=["backup"])
async def get_latest_backup(
    backup_type: str = "database",
    current_user: User = Depends(get_current_user)
):
    """
    获取最新的备份
    """
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    backup = BackupService.get_latest_backup(backup_type)
    
    if not backup:
        raise HTTPException(status_code=404, detail="未找到备份")
    
    return backup


@router.post("/backups/verify", tags=["backup"])
async def verify_backup(
    backup_file: str,
    current_user: User = Depends(get_current_user)
):
    """
    验证备份文件完整性
    
    参数:
    - backup_file: 备份文件名或完整路径
    """
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = BackupService.verify_backup(backup_file)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.delete("/backups/cleanup", tags=["backup"])
async def cleanup_old_backups(
    retention_days: int = 7,
    backup_type: str = "database",
    current_user: User = Depends(get_current_user)
):
    """
    清理过期备份
    
    参数:
    - retention_days: 保留天数（默认7天）
    - backup_type: 备份类型
    """
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    if retention_days < 1:
        raise HTTPException(status_code=400, detail="保留天数必须大于0")
    
    result = BackupService.delete_old_backups(retention_days, backup_type)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/backups/stats", response_model=BackupStats, tags=["backup"])
async def get_backup_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取备份统计信息
    
    包括:
    - 各类型备份的数量和大小
    - 最新备份信息
    - 磁盘空间使用情况
    """
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    stats = BackupService.get_backup_stats()
    
    if not stats:
        raise HTTPException(status_code=500, detail="无法获取统计信息")
    
    return stats


@router.get("/backups/health", tags=["backup"])
async def check_backup_health(
    current_user: User = Depends(get_current_user)
):
    """
    检查备份系统健康状态
    
    返回:
    - 最新备份时间
    - 备份是否过期
    - 磁盘空间是否充足
    - 备份完整性状态
    """
    if not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    stats = BackupService.get_backup_stats()
    
    # 健康检查
    health = {
        "status": "healthy",
        "checks": {},
        "warnings": []
    }
    
    # 检查最新备份时间
    latest_db = stats.get("database", {}).get("latest")
    if latest_db:
        latest_time = datetime.fromisoformat(latest_db["created_at"])
        hours_ago = (datetime.now() - latest_time).total_seconds() / 3600
        
        health["checks"]["latest_backup"] = {
            "status": "ok" if hours_ago < 26 else "warning",
            "hours_ago": round(hours_ago, 2),
            "timestamp": latest_time.isoformat()
        }
        
        if hours_ago > 26:
            health["warnings"].append(f"最新备份已超过 {int(hours_ago)} 小时")
            health["status"] = "warning"
    else:
        health["checks"]["latest_backup"] = {"status": "error", "message": "未找到备份"}
        health["status"] = "error"
    
    # 检查磁盘空间
    disk = stats.get("disk", {})
    if disk:
        disk_percent = disk.get("percent", 0)
        
        health["checks"]["disk_space"] = {
            "status": "ok" if disk_percent < 80 else "warning" if disk_percent < 90 else "critical",
            "used_percent": disk_percent,
            "free": disk.get("free_human")
        }
        
        if disk_percent > 90:
            health["warnings"].append(f"磁盘空间严重不足: {disk_percent}%")
            health["status"] = "critical"
        elif disk_percent > 80:
            health["warnings"].append(f"磁盘空间不足: {disk_percent}%")
            if health["status"] == "healthy":
                health["status"] = "warning"
    
    # 检查备份数量
    db_count = stats.get("database", {}).get("count", 0)
    health["checks"]["backup_count"] = {
        "status": "ok" if db_count >= 3 else "warning",
        "count": db_count
    }
    
    if db_count < 3:
        health["warnings"].append(f"备份数量过少: {db_count}个")
        if health["status"] == "healthy":
            health["status"] = "warning"
    
    return health
