# -*- coding: utf-8 -*-
"""
批量操作 - 辅助函数

包含编号生成、操作日志等工具函数
"""

from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.task_center import TaskOperationLog, TaskUnified

# 使用统一的编码生成工具
from app.utils.domain_codes import task_center as task_center_codes

generate_task_code = task_center_codes.generate_task_code


def log_task_operation(
    db: Session,
    task_id: int,
    operation_type: str,
    operation_desc: str,
    operator_id: int,
    operator_name: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None
):
    """记录任务操作日志"""
    log = TaskOperationLog(
        task_id=task_id,
        operation_type=operation_type,
        operation_desc=operation_desc,
        operator_id=operator_id,
        operator_name=operator_name,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()
