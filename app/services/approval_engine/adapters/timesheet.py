# -*- coding: utf-8 -*-
"""
工时审批适配器

将工时模块接入统一审批系统
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.timesheet import Timesheet

from .base import ApprovalAdapter


class TimesheetApprovalAdapter(ApprovalAdapter):
    """
    工时审批适配器

    工时审批特点:
    1. 通常由直属上级审批
    2. 加班工时可能需要额外审批层级
    3. 批量提交时可能涉及多条记录

    支持的条件字段:
    - entity.hours: 工时数
    - entity.overtime_type: 加班类型
    - entity.project_id: 项目ID
    """

    entity_type = "TIMESHEET"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Timesheet]:
        """获取工时实体"""
        return self.db.query(Timesheet).filter(Timesheet.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取工时数据用于条件路由

        Returns:
            包含工时关键数据的字典
        """
        timesheet = self.get_entity(entity_id)
        if not timesheet:
            return {}

        return {
            "timesheet_no": timesheet.timesheet_no,
            "status": timesheet.status,
            "user_id": timesheet.user_id,
            "user_name": timesheet.user_name,
            "department_id": timesheet.department_id,
            "department_name": timesheet.department_name,
            "project_id": timesheet.project_id,
            "project_code": timesheet.project_code,
            "project_name": timesheet.project_name,
            "task_name": timesheet.task_name,
            "work_date": timesheet.work_date.isoformat() if timesheet.work_date else None,
            "hours": float(timesheet.hours) if timesheet.hours else 0,
            "overtime_type": timesheet.overtime_type,
            "work_content": timesheet.work_content,
            "is_overtime": timesheet.overtime_type != "NORMAL",
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """提交审批时的回调"""
        from datetime import datetime

        timesheet = self.get_entity(entity_id)
        if timesheet:
            timesheet.status = "SUBMITTED"
            timesheet.submit_time = datetime.now()
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批通过时的回调"""
        from datetime import datetime

        timesheet = self.get_entity(entity_id)
        if timesheet:
            timesheet.status = "APPROVED"
            timesheet.approve_time = datetime.now()
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批驳回时的回调"""
        timesheet = self.get_entity(entity_id)
        if timesheet:
            timesheet.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        timesheet = self.get_entity(entity_id)
        if timesheet:
            timesheet.status = "DRAFT"
            timesheet.submit_time = None
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        timesheet = self.get_entity(entity_id)
        if timesheet:
            date_str = timesheet.work_date.strftime("%Y-%m-%d") if timesheet.work_date else ""
            return f"工时审批 - {timesheet.user_name} {date_str}"
        return f"工时审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("user_name"):
            parts.append(f"员工: {data['user_name']}")
        if data.get("work_date"):
            parts.append(f"日期: {data['work_date']}")
        if data.get("hours"):
            parts.append(f"工时: {data['hours']}小时")
        if data.get("project_name"):
            parts.append(f"项目: {data['project_name']}")
        if data.get("is_overtime"):
            parts.append(f"加班: {data['overtime_type']}")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        timesheet = self.get_entity(entity_id)
        if not timesheet:
            return False, "工时记录不存在"

        if timesheet.status not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({timesheet.status})不允许提交审批"

        if not timesheet.hours or timesheet.hours <= 0:
            return False, "工时必须大于0"

        if not timesheet.work_date:
            return False, "请填写工作日期"

        return True, ""
