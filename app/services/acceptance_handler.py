# -*- coding: utf-8 -*-
"""旧的验收处理器导入路径兼容层。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler


def check_acceptance_eligibility(
    db: Session,
    project_id: int,
    acceptance_type: str,
    machine_id: Optional[int] = None,
) -> bool:
    """旧接口兼容，当前仅返回可调用占位结果。"""
    return True


def initiate_acceptance_process(
    db: Session,
    project_id: int,
    acceptance_type: str,
    machine_id: Optional[int] = None,
    created_by: Optional[int] = None,
) -> Dict[str, Any]:
    """旧接口兼容，返回简单启动结果。"""
    return {
        "project_id": project_id,
        "acceptance_type": acceptance_type,
        "machine_id": machine_id,
        "created_by": created_by,
        "status": "initiated",
    }


def get_acceptance_status(
    db: Session,
    project_id: int,
    acceptance_type: Optional[str] = None,
    machine_id: Optional[int] = None,
) -> Dict[str, Any]:
    """旧接口兼容，返回简单状态视图。"""
    return {
        "project_id": project_id,
        "acceptance_type": acceptance_type,
        "machine_id": machine_id,
        "status": "unknown",
    }


def record_acceptance_result(
    db: Session,
    project_id: int,
    acceptance_type: str,
    result: str,
    machine_id: Optional[int] = None,
    issues: Optional[List[str]] = None,
) -> bool:
    """旧接口兼容，委托到当前 AcceptanceStatusHandler。"""
    handler = AcceptanceStatusHandler(db)
    normalized_type = (acceptance_type or "").upper()
    normalized_result = (result or "").upper()

    if normalized_type == "FAT":
        if normalized_result in {"PASSED", "PASS"}:
            return handler.handle_fat_passed(project_id, machine_id)
        return handler.handle_fat_failed(project_id, machine_id, issues=issues)

    if normalized_type == "SAT":
        if normalized_result in {"PASSED", "PASS"}:
            return handler.handle_sat_passed(project_id, machine_id)
        return handler.handle_sat_failed(project_id, machine_id, issues=issues)

    if normalized_type == "FINAL":
        if normalized_result in {"PASSED", "PASS"}:
            return handler.handle_final_acceptance_passed(project_id)
        return False

    return False
