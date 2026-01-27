# -*- coding: utf-8 -*-
"""
问题管理状态机

将 Issues 模块迁移到统一状态机框架
"""

from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.issue import Issue


class IssueStateMachine(StateMachine):
    """
    问题状态机

    状态转换规则：
    - OPEN → IN_PROGRESS: 开始处理（分配）
    - OPEN → CLOSED: 直接关闭
    - IN_PROGRESS → RESOLVED: 解决问题
    - IN_PROGRESS → OPEN: 重新打开
    - RESOLVED → VERIFIED/CLOSED: 验证通过
    - RESOLVED → IN_PROGRESS: 验证失败，重新处理
    - VERIFIED → CLOSED: 关闭
    - CLOSED → OPEN: 重新打开
    """

    def __init__(self, issue: Issue, db: Session):
        """初始化问题状态机"""
        super().__init__(issue, db, state_field='status')

    @transition(
        from_state="OPEN",
        to_state="IN_PROGRESS",
        required_permission="issue:assign",
        action_type="ASSIGN",
        notify_users=["assignee"],
        notification_template="issue_assigned",
    )
    def assign(self, from_state: str, to_state: str, **kwargs):
        """
        分配问题（状态从 OPEN 变为 IN_PROGRESS）

        Args:
            assignee_id: 被分配人ID
            assignee_name: 被分配人姓名
            due_date: 截止日期（可选）
        """
        # 更新分配信息
        if 'assignee_id' in kwargs:
            self.model.assignee_id = kwargs['assignee_id']
        if 'assignee_name' in kwargs:
            self.model.assignee_name = kwargs['assignee_name']
        if 'due_date' in kwargs:
            self.model.due_date = kwargs['due_date']

    @transition(
        from_state="IN_PROGRESS",
        to_state="RESOLVED",
        required_permission="issue:resolve",
        action_type="RESOLVE",
        notify_users=["reporter", "creator"],
        notification_template="issue_resolved",
    )
    def resolve(self, from_state: str, to_state: str, **kwargs):
        """
        解决问题

        Args:
            solution: 解决方案
            resolved_by: 解决人ID
            resolved_by_name: 解决人姓名
        """
        from datetime import datetime

        if 'solution' in kwargs:
            self.model.solution = kwargs['solution']
        if 'resolved_by' in kwargs:
            self.model.resolved_by = kwargs['resolved_by']
        if 'resolved_by_name' in kwargs:
            self.model.resolved_by_name = kwargs['resolved_by_name']

        self.model.resolved_at = datetime.now()

        # 业务逻辑：关闭阻塞问题预警
        if self.model.is_blocking:
            self._close_blocking_alerts()

        # 业务逻辑：更新项目健康度
        if self.model.is_blocking and self.model.project_id:
            self._update_project_health()

        # 业务逻辑：同步调试问题
        if self.model.category == 'PROJECT' and self.model.issue_type in ['DEFECT', 'BUG']:
            self._sync_debug_issue()

    @transition(
        from_state="RESOLVED",
        to_state="CLOSED",
        required_permission="issue:verify",
        action_type="VERIFY_PASS",
        notify_users=["assignee", "resolver"],
        notification_template="issue_verified",
    )
    def verify_pass(self, from_state: str, to_state: str, **kwargs):
        """
        验证通过（问题已解决）

        Args:
            verified_by: 验证人ID
            verified_by_name: 验证人姓名
        """
        from datetime import datetime

        if 'verified_by' in kwargs:
            self.model.verified_by = kwargs['verified_by']
        if 'verified_by_name' in kwargs:
            self.model.verified_by_name = kwargs['verified_by_name']

        self.model.verified_at = datetime.now()
        self.model.verified_result = 'VERIFIED'

    @transition(
        from_state="RESOLVED",
        to_state="IN_PROGRESS",
        required_permission="issue:verify",
        action_type="VERIFY_FAIL",
        notify_users=["assignee", "resolver"],
        notification_template="issue_verify_failed",
    )
    def verify_fail(self, from_state: str, to_state: str, **kwargs):
        """
        验证失败（需要重新处理）

        Args:
            verified_by: 验证人ID
            verified_by_name: 验证人姓名
        """
        from datetime import datetime

        if 'verified_by' in kwargs:
            self.model.verified_by = kwargs['verified_by']
        if 'verified_by_name' in kwargs:
            self.model.verified_by_name = kwargs['verified_by_name']

        self.model.verified_at = datetime.now()
        self.model.verified_result = 'FAILED'

    @transition(
        from_state="OPEN",
        to_state="CLOSED",
        required_permission="issue:close",
        action_type="CLOSE",
        notify_users=["assignee", "reporter"],
        notification_template="issue_closed",
    )
    def close_directly(self, from_state: str, to_state: str, **kwargs):
        """直接关闭问题（无需解决）"""
        pass

    @transition(
        from_state="CLOSED",
        to_state="OPEN",
        required_permission="issue:reopen",
        action_type="REOPEN",
        notify_users=["assignee", "reporter"],
        notification_template="issue_reopened",
    )
    def reopen(self, from_state: str, to_state: str, **kwargs):
        """重新打开已关闭的问题"""
        # 清除验证信息
        self.model.verified_at = None
        self.model.verified_by = None
        self.model.verified_by_name = None
        self.model.verified_result = None

    @transition(
        from_state="IN_PROGRESS",
        to_state="OPEN",
        required_permission="issue:assign",
        action_type="UNASSIGN",
        notify_users=["reporter"],
        notification_template="issue_unassigned",
    )
    def unassign(self, from_state: str, to_state: str, **kwargs):
        """取消分配"""
        # 清除分配信息
        self.model.assignee_id = None
        self.model.assignee_name = None
        self.model.due_date = None

    # ==================== 业务逻辑辅助方法 ====================

    def _close_blocking_alerts(self):
        """关闭阻塞问题的相关预警"""
        try:
            import logging
            from app.api.v1.endpoints.issues.utils import close_blocking_issue_alerts

            closed_count = close_blocking_issue_alerts(self.db, self.model)
            if closed_count > 0:
                logging.info(
                    f"问题 {self.model.issue_no} 已解决，自动关闭 {closed_count} 个预警"
                )
        except Exception as e:
            import logging
            logging.error(f"关闭阻塞问题预警失败: {str(e)}")

    def _update_project_health(self):
        """更新关联项目的健康度"""
        try:
            import logging
            from app.models.project import Project
            from app.services.health_calculator import HealthCalculator

            project = (
                self.db.query(Project)
                .filter(Project.id == self.model.project_id)
                .first()
            )
            if project:
                calculator = HealthCalculator(self.db)
                calculator.calculate_and_update(project, auto_save=True)
        except Exception as e:
            import logging
            logging.error(f"更新项目健康度失败: {str(e)}")

    def _sync_debug_issue(self):
        """同步调试问题"""
        try:
            import logging
            from app.services.debug_issue_sync_service import DebugIssueSyncService

            sync_service = DebugIssueSyncService(self.db)
            sync_service.sync_issue(self.model.id)
        except Exception as e:
            import logging
            logging.error(f"调试问题同步失败: {e}")
