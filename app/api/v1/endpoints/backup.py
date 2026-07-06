# -*- coding: utf-8 -*-
"""Backup management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api import deps
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.backup_service import BackupService

router = APIRouter()


class BackupCreateRequest(BaseModel):
    backup_type: str = Field(default="database", description="database/files/full")


class BackupVerifyRequest(BaseModel):
    backup_file: str


class BackupRestoreRequest(BaseModel):
    backup_file: str
    confirm: bool = Field(default=False, description="Must be true to restore")
    database_url: Optional[str] = Field(default=None, description="Optional SQLite target URL")


def _wrap_result(result: dict, default_message: str) -> ResponseModel[dict]:
    status = result.get("status")
    code = 200 if status == "success" else 400
    return ResponseModel(code=code, message=result.get("message", default_message), data=result)


@router.get("/", response_model=ResponseModel[list[dict]])
def list_backups(
    backup_type: str = Query(default="database", description="database/uploads/configs/logs/full"),
    _current_user: User = Depends(deps.require_super_admin),
):
    backups = BackupService.list_backups(backup_type)
    return ResponseModel(code=200, message="备份列表获取成功", data=backups)


@router.post("/", response_model=ResponseModel[dict])
def create_backup(
    payload: BackupCreateRequest,
    _current_user: User = Depends(deps.require_super_admin),
):
    result = BackupService.create_backup(payload.backup_type)
    return _wrap_result(result, "备份创建完成")


@router.post("/database", response_model=ResponseModel[dict])
def create_database_backup(
    _current_user: User = Depends(deps.require_super_admin),
):
    result = BackupService.create_backup("database")
    return _wrap_result(result, "数据库备份创建完成")


@router.post("/verify", response_model=ResponseModel[dict])
def verify_backup(
    payload: BackupVerifyRequest,
    _current_user: User = Depends(deps.require_super_admin),
):
    result = BackupService.verify_backup(payload.backup_file)
    return _wrap_result(result, "备份验证完成")


@router.post("/restore", response_model=ResponseModel[dict])
def restore_backup(
    payload: BackupRestoreRequest,
    _current_user: User = Depends(deps.require_super_admin),
):
    result = BackupService.restore_backup(
        payload.backup_file,
        database_url=payload.database_url,
        confirm=payload.confirm,
    )
    return _wrap_result(result, "备份恢复完成")


@router.delete("/old", response_model=ResponseModel[dict])
def delete_old_backups(
    retention_days: int = Query(default=7, ge=1, le=365),
    backup_type: str = Query(default="database"),
    _current_user: User = Depends(deps.require_super_admin),
):
    result = BackupService.delete_old_backups(retention_days, backup_type)
    return _wrap_result(result, "过期备份清理完成")


@router.get("/stats", response_model=ResponseModel[dict])
def get_backup_stats(
    _current_user: User = Depends(deps.require_super_admin),
):
    return ResponseModel(code=200, message="备份统计获取成功", data=BackupService.get_backup_stats())


__all__ = ["router"]
