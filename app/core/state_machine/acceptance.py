# -*- coding: utf-8 -*-
"""
验收单状态机

状态转换规则：
- DRAFT → PENDING: 提交验收单
- DRAFT → IN_PROGRESS: 直接开始验收
- PENDING → IN_PROGRESS: 开始验收
- IN_PROGRESS → PASSED: 验收通过
- IN_PROGRESS → FAILED: 验收失败
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.acceptance import AcceptanceOrder


class AcceptanceStateMachine(StateMachine):
    """验收单状态机"""

    def __init__(self, order: AcceptanceOrder, db: Session):
        """初始化验收单状态机"""
        super().__init__(order, db, state_field='status')

    @transition(
        from_state="DRAFT",
        to_state="PENDING",
        required_permission="acceptance:submit",
        action_type="SUBMIT",
        notify_users=["project_manager", "team_members"],
        notification_template="acceptance_submitted",
    )
    def submit(self, from_state: str, to_state: str, **kwargs):
        """
        提交验收单（草稿→待验收）

        Args:
            无特殊参数
        """
        # 验证检查项数量
        if self.model.total_items == 0:
            raise ValueError("验收单没有检查项，无法提交")

    @transition(
        from_state="DRAFT",
        to_state="IN_PROGRESS",
        required_permission="acceptance:start",
        action_type="START",
        notify_users=["project_manager"],
        notification_template="acceptance_started",
    )
    def start_from_draft(self, from_state: str, to_state: str, **kwargs):
        """
        直接开始验收（草稿→验收中）

        Args:
            location: 验收地点（可选）
        """
        self.model.actual_start_date = datetime.now()
        if 'location' in kwargs:
            self.model.location = kwargs['location']

        # 验证检查项数量
        if self.model.total_items == 0:
            raise ValueError("验收单没有检查项，无法开始验收")

    @transition(
        from_state="PENDING",
        to_state="IN_PROGRESS",
        required_permission="acceptance:start",
        action_type="START",
        notify_users=["project_manager"],
        notification_template="acceptance_started",
    )
    def start_from_pending(self, from_state: str, to_state: str, **kwargs):
        """
        开始验收（待验收→验收中）

        Args:
            location: 验收地点（可选）
        """
        self.model.actual_start_date = datetime.now()
        if 'location' in kwargs:
            self.model.location = kwargs['location']

    @transition(
        from_state="IN_PROGRESS",
        to_state="PASSED",
        required_permission="acceptance:complete",
        action_type="COMPLETE_PASS",
        notify_users=["project_manager", "owner", "created_by"],
        notification_template="acceptance_passed",
    )
    def complete_pass(self, from_state: str, to_state: str, **kwargs):
        """
        完成验收并通过

        Args:
            overall_result: 验收结果 (PASSED)
            conclusion: 验收结论
            conditions: 附加条件
            auto_trigger_invoice: 是否自动触发开票（默认True）
        """
        self.model.actual_end_date = datetime.now()
        self.model.overall_result = "PASSED"

        if 'conclusion' in kwargs:
            self.model.conclusion = kwargs['conclusion']
        if 'conditions' in kwargs:
            self.model.conditions = kwargs['conditions']

        # 业务逻辑：验证必检项
        self._validate_required_items()

        # 业务逻辑：验证阻塞问题
        self._validate_blocking_issues()

        # 业务逻辑：自动触发开票
        auto_trigger_invoice = kwargs.get('auto_trigger_invoice', True)
        if auto_trigger_invoice:
            self._trigger_invoice()

        # 业务逻辑：FAT/SAT状态联动
        self._handle_acceptance_status_transition("PASSED")

        # 业务逻辑：进度跟踪联动
        self._handle_progress_integration("PASSED")

        # 业务逻辑：阶段流转检查
        self._check_auto_stage_transition("PASSED")

        # 业务逻辑：质保期触发
        self._trigger_warranty_period("PASSED")

        # 业务逻辑：奖金计算
        self._trigger_bonus_calculation("PASSED")

    @transition(
        from_state="IN_PROGRESS",
        to_state="FAILED",
        required_permission="acceptance:complete",
        action_type="COMPLETE_FAIL",
        notify_users=["project_manager", "owner", "created_by"],
        notification_template="acceptance_failed",
    )
    def complete_fail(self, from_state: str, to_state: str, **kwargs):
        """
        完成验收但失败

        Args:
            overall_result: 验收结果 (FAILED或CONDITIONAL_PASS)
            conclusion: 验收结论
            conditions: 附加条件
        """
        self.model.actual_end_date = datetime.now()

        overall_result = kwargs.get('overall_result', 'FAILED')
        self.model.overall_result = overall_result

        if 'conclusion' in kwargs:
            self.model.conclusion = kwargs['conclusion']
        if 'conditions' in kwargs:
            self.model.conditions = kwargs['conditions']

        # 业务逻辑：验证必检项
        self._validate_required_items()

        # 业务逻辑：FAT/SAT状态联动
        self._handle_acceptance_status_transition(overall_result)

        # 业务逻辑：进度跟踪联动
        self._handle_progress_integration(overall_result)

    # ==================== 业务逻辑辅助方法 ====================

    def _validate_required_items(self):
        """验证必检项是否都已检查"""
        try:
            from app.services.acceptance_completion_service import validate_required_check_items
            validate_required_check_items(self.db, self.model.id)
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过必检项验证")
        except Exception as e:
            import logging
            logging.error(f"验证必检项失败: {str(e)}")
            raise

    def _validate_blocking_issues(self):
        """验证是否存在未闭环的阻塞问题"""
        try:
            from app.api.v1.endpoints.acceptance.utils import validate_completion_rules
            validate_completion_rules(self.db, self.model.id)
        except ImportError:
            import logging
            logging.warning("Acceptance utils 不存在，跳过阻塞问题验证")
        except Exception as e:
            import logging
            logging.error(f"验证阻塞问题失败: {str(e)}")
            raise

    def _trigger_invoice(self):
        """自动触发开票"""
        try:
            import logging
            from app.services.acceptance_completion_service import trigger_invoice_on_acceptance
            trigger_invoice_on_acceptance(self.db, self.model.id, True)
            logging.info(f"验收单 {self.model.order_no} 自动触发开票")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过自动开票")
        except Exception as e:
            import logging
            logging.warning(f"自动触发开票失败：{str(e)}")

    def _handle_acceptance_status_transition(self, result: str):
        """FAT/SAT状态联动"""
        try:
            import logging
            from app.services.acceptance_completion_service import handle_acceptance_status_transition
            handle_acceptance_status_transition(self.db, self.model, result)
            logging.info(f"验收单 {self.model.order_no} FAT/SAT状态联动完成")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过状态联动")
        except Exception as e:
            import logging
            logging.warning(f"FAT/SAT状态联动失败：{str(e)}")

    def _handle_progress_integration(self, result: str):
        """进度跟踪联动"""
        try:
            import logging
            from app.services.acceptance_completion_service import handle_progress_integration
            handle_progress_integration(self.db, self.model, result)
            logging.info(f"验收单 {self.model.order_no} 进度跟踪联动完成")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过进度联动")
        except Exception as e:
            import logging
            logging.warning(f"进度跟踪联动失败：{str(e)}")

    def _check_auto_stage_transition(self, result: str):
        """阶段流转检查"""
        try:
            import logging
            from app.services.acceptance_completion_service import check_auto_stage_transition_after_acceptance
            check_auto_stage_transition_after_acceptance(self.db, self.model, result)
            logging.info(f"验收单 {self.model.order_no} 阶段流转检查完成")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过阶段流转检查")
        except Exception as e:
            import logging
            logging.warning(f"阶段流转检查失败：{str(e)}")

    def _trigger_warranty_period(self, result: str):
        """质保期触发"""
        try:
            import logging
            from app.services.acceptance_completion_service import trigger_warranty_period
            trigger_warranty_period(self.db, self.model, result)
            logging.info(f"验收单 {self.model.order_no} 质保期触发完成")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过质保期触发")
        except Exception as e:
            import logging
            logging.warning(f"质保期触发失败：{str(e)}")

    def _trigger_bonus_calculation(self, result: str):
        """奖金计算"""
        try:
            import logging
            from app.services.acceptance_completion_service import trigger_bonus_calculation
            trigger_bonus_calculation(self.db, self.model, result)
            logging.info(f"验收单 {self.model.order_no} 奖金计算完成")
        except ImportError:
            import logging
            logging.warning("AcceptanceCompletionService 不存在，跳过奖金计算")
        except Exception as e:
            import logging
            logging.warning(f"奖金计算失败：{str(e)}")
