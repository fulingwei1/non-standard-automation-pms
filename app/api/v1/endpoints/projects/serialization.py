# -*- coding: utf-8 -*-
"""
项目模块 - 序列化工具函数

包含项目状态日志等对象的序列化
"""

from typing import Any, Dict

from app.models.project import ProjectStatusLog


def _serialize_project_status_log(log: ProjectStatusLog) -> Dict[str, Any]:
    """将ProjectStatusLog对象序列化为字典"""
    return {
        "id": log.id,
        "project_id": log.project_id,
        "old_stage": log.old_stage,
        "new_stage": log.new_stage,
        "old_status": log.old_status,
        "new_status": log.new_status,
        "old_health": log.old_health,
        "new_health": log.new_health,
        "change_type": log.change_type,
        "change_reason": log.change_reason,
        "changed_by": log.changed_by,
        "changed_at": log.changed_at.isoformat() if log.changed_at else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
