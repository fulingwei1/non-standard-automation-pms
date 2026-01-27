# -*- coding: utf-8 -*-
"""
安装调试派工状态机

状态转换规则：
- PENDING → ASSIGNED: 派工
- ASSIGNED → IN_PROGRESS: 开始执行
- IN_PROGRESS → COMPLETED: 完成
- 任意状态 → CANCELLED: 取消
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.installation_dispatch import InstallationDispatchOrder


class InstallationDispatchStateMachine(StateMachine):
    """安装调试派工单状态机"""

    def __init__(self, order: InstallationDispatchOrder, db: Session):
        """初始化派工单状态机"""
        super().__init__(order, db, state_field='status')

    @transition(
        from_state="PENDING",
        to_state="ASSIGNED",
        required_permission="installation_dispatch:assign",
        action_type="ASSIGN",
        notify_users=["assignee"],
        notification_template="dispatch_assigned",
    )
    def assign(self, from_state: str, to_state: str, **kwargs):
        """
        派工（分配给工程师）

        Args:
            assigned_to_id: 被派工人员ID
            assigned_to_name: 被派工人员姓名
            assigned_by_id: 派工人ID
            assigned_by_name: 派工人姓名
            remark: 派工备注（可选）
        """
        if 'assigned_to_id' in kwargs:
            self.model.assigned_to_id = kwargs['assigned_to_id']
        if 'assigned_to_name' in kwargs:
            self.model.assigned_to_name = kwargs['assigned_to_name']
        if 'assigned_by_id' in kwargs:
            self.model.assigned_by_id = kwargs['assigned_by_id']
        if 'assigned_by_name' in kwargs:
            self.model.assigned_by_name = kwargs['assigned_by_name']

        self.model.assigned_time = datetime.now()

        # 添加备注
        if 'remark' in kwargs and kwargs['remark']:
            current_remark = self.model.remark or ""
            self.model.remark = current_remark + f"\n派工备注：{kwargs['remark']}"

    @transition(
        from_state="ASSIGNED",
        to_state="IN_PROGRESS",
        required_permission="installation_dispatch:execute",
        action_type="START",
        notify_users=["assigned_by", "project_manager"],
        notification_template="dispatch_started",
    )
    def start(self, from_state: str, to_state: str, **kwargs):
        """
        开始执行安装调试任务

        Args:
            start_time: 开始时间（可选，默认当前时间）
        """
        self.model.start_time = kwargs.get('start_time', datetime.now())
        self.model.progress = 0

    @transition(
        from_state="IN_PROGRESS",
        to_state="COMPLETED",
        required_permission="installation_dispatch:execute",
        action_type="COMPLETE",
        notify_users=["assigned_by", "project_manager", "customer_contact"],
        notification_template="dispatch_completed",
    )
    def complete(self, from_state: str, to_state: str, **kwargs):
        """
        完成安装调试任务

        Args:
            end_time: 结束时间（可选，默认当前时间）
            actual_hours: 实际工时
            execution_notes: 执行说明
            issues_found: 发现的问题
            solution_provided: 提供的解决方案
            photos: 现场照片
        """
        self.model.end_time = kwargs.get('end_time', datetime.now())
        self.model.progress = 100

        if 'actual_hours' in kwargs:
            self.model.actual_hours = kwargs['actual_hours']

        # 添加完成说明
        if 'execution_notes' in kwargs and kwargs['execution_notes']:
            current_notes = self.model.execution_notes or ""
            self.model.execution_notes = current_notes + f"\n完成说明：{kwargs['execution_notes']}"

        if 'issues_found' in kwargs:
            self.model.issues_found = kwargs['issues_found']
        if 'solution_provided' in kwargs:
            self.model.solution_provided = kwargs['solution_provided']
        if 'photos' in kwargs:
            self.model.photos = kwargs['photos']

        # 业务逻辑：自动创建现场服务记录
        self._create_service_record(**kwargs)

    @transition(
        from_state="PENDING",
        to_state="CANCELLED",
        required_permission="installation_dispatch:cancel",
        action_type="CANCEL",
        notify_users=["assignee", "assigned_by"],
        notification_template="dispatch_cancelled",
    )
    def cancel_from_pending(self, from_state: str, to_state: str, **kwargs):
        """从待派工状态取消"""
        pass

    @transition(
        from_state="ASSIGNED",
        to_state="CANCELLED",
        required_permission="installation_dispatch:cancel",
        action_type="CANCEL",
        notify_users=["assignee", "assigned_by"],
        notification_template="dispatch_cancelled",
    )
    def cancel_from_assigned(self, from_state: str, to_state: str, **kwargs):
        """从已派工状态取消"""
        pass

    @transition(
        from_state="IN_PROGRESS",
        to_state="CANCELLED",
        required_permission="installation_dispatch:cancel",
        action_type="CANCEL",
        notify_users=["assignee", "assigned_by", "project_manager"],
        notification_template="dispatch_cancelled",
    )
    def cancel_from_in_progress(self, from_state: str, to_state: str, **kwargs):
        """从进行中状态取消"""
        pass

    # ==================== 业务逻辑辅助方法 ====================

    def _create_service_record(self, **kwargs):
        """完成任务时自动创建现场服务记录"""
        try:
            import logging
            from app.models.project import Machine
            from app.models.service import ServiceRecord
            from app.api.v1.endpoints.service import generate_record_no

            # 获取机台号
            machine_no = None
            if self.model.machine_id:
                machine = (
                    self.db.query(Machine)
                    .filter(Machine.id == self.model.machine_id)
                    .first()
                )
                if machine:
                    machine_no = machine.machine_no

            # 创建服务记录
            service_record = ServiceRecord(
                record_no=generate_record_no(self.db),
                service_type="INSTALLATION",
                project_id=self.model.project_id,
                machine_no=machine_no,
                customer_id=self.model.customer_id,
                location=self.model.location,
                service_date=self.model.scheduled_date,
                start_time=self.model.start_time.strftime("%H:%M")
                if self.model.start_time
                else None,
                end_time=self.model.end_time.strftime("%H:%M")
                if self.model.end_time
                else None,
                duration_hours=kwargs.get('actual_hours') or self.model.estimated_hours,
                service_engineer_id=self.model.assigned_to_id,
                service_engineer_name=self.model.assigned_to_name,
                customer_contact=self.model.customer_contact,
                customer_phone=self.model.customer_phone,
                service_content=self.model.task_description or self.model.task_title,
                service_result=kwargs.get('execution_notes'),
                issues_found=kwargs.get('issues_found'),
                solution_provided=kwargs.get('solution_provided'),
                photos=kwargs.get('photos'),
                status="COMPLETED",
            )
            self.db.add(service_record)
            self.db.flush()
            self.model.service_record_id = service_record.id

            logging.info(f"自动创建现场服务记录: {service_record.record_no}")

        except Exception as e:
            import logging
            # 创建服务记录失败不影响派工单完成
            logging.warning(f"自动创建现场服务记录失败：{str(e)}")

    def update_progress(self, progress: int, notes: Optional[str] = None):
        """
        更新任务进度（不改变状态）

        Args:
            progress: 进度百分比 (0-100)
            notes: 进度说明
        """
        if self.current_state != "IN_PROGRESS":
            raise ValueError("只有进行中状态的派工单才能更新进度")

        self.model.progress = progress

        if notes:
            current_notes = self.model.execution_notes or ""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.model.execution_notes = current_notes + f"\n{timestamp}：{notes}"
