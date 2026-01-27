# -*- coding: utf-8 -*-
"""
商机状态机

状态转换规则（阶段推进）：
- DISCOVERY → QUALIFIED: 发现 → 合格
- QUALIFIED → PROPOSAL: 合格 → 提案
- PROPOSAL → NEGOTIATION: 提案 → 谈判
- NEGOTIATION → WON: 谈判 → 赢单
- 任意阶段 → LOST: 输单
- 任意阶段 → ON_HOLD: 暂停
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.sales import Opportunity


class OpportunityStateMachine(StateMachine):
    """商机状态机"""

    def __init__(self, opportunity: Opportunity, db: Session):
        """初始化商机状态机"""
        super().__init__(opportunity, db, state_field='stage')

    @transition(
        from_state="DISCOVERY",
        to_state="QUALIFIED",
        required_permission="opportunity:update",
        action_type="QUALIFY",
        notify_users=["owner"],
        notification_template="opportunity_qualified",
    )
    def qualify(self, from_state: str, to_state: str, **kwargs):
        """
        商机合格化

        Args:
            score: 评分（可选）
            score_remark: 评分说明（可选）
        """
        if 'score' in kwargs:
            self.model.score = kwargs['score']
            # 根据评分自动更新风险等级
            if self.model.score >= 80:
                self.model.risk_level = "LOW"
            elif self.model.score >= 60:
                self.model.risk_level = "MEDIUM"
            else:
                self.model.risk_level = "HIGH"

    @transition(
        from_state="QUALIFIED",
        to_state="PROPOSAL",
        required_permission="opportunity:update",
        action_type="PROPOSE",
        notify_users=["owner"],
        notification_template="opportunity_proposal_ready",
    )
    def propose(self, from_state: str, to_state: str, **kwargs):
        """
        生成提案

        Args:
            expected_close_date: 预计成交日期（可选）
        """
        if 'expected_close_date' in kwargs:
            self.model.expected_close_date = kwargs['expected_close_date']

    @transition(
        from_state="PROPOSAL",
        to_state="NEGOTIATION",
        required_permission="opportunity:update",
        action_type="NEGOTIATE",
        notify_users=["owner"],
        notification_template="opportunity_negotiation_started",
    )
    def negotiate(self, from_state: str, to_state: str, **kwargs):
        """
        进入谈判阶段

        Args:
            probability: 成交概率（可选）
        """
        if 'probability' in kwargs:
            self.model.probability = kwargs['probability']

    @transition(
        from_state="NEGOTIATION",
        to_state="WON",
        required_permission="opportunity:win",
        action_type="WIN",
        notify_users=["owner", "created_by"],
        notification_template="opportunity_won",
    )
    def win(self, from_state: str, to_state: str, **kwargs):
        """
        赢单

        Args:
            est_amount: 预估金额（可选）
            actual_amount: 实际金额（可选）
        """
        self.model.gate_status = "PASS"
        self.model.gate_passed_at = datetime.now()

        if 'est_amount' in kwargs:
            self.model.est_amount = kwargs['est_amount']

        # 业务逻辑：赢单后自动创建项目或合同
        # 这里可以扩展业务逻辑

    # 特殊转换：从任意阶段输单
    @transition(
        from_state="DISCOVERY",
        to_state="LOST",
        required_permission="opportunity:update",
        action_type="LOSE",
        notify_users=["owner", "created_by"],
        notification_template="opportunity_lost",
    )
    def lose_from_discovery(self, from_state: str, to_state: str, **kwargs):
        """从发现阶段输单"""
        self._handle_lose(**kwargs)

    @transition(
        from_state="QUALIFIED",
        to_state="LOST",
        required_permission="opportunity:update",
        action_type="LOSE",
        notify_users=["owner", "created_by"],
        notification_template="opportunity_lost",
    )
    def lose_from_qualified(self, from_state: str, to_state: str, **kwargs):
        """从合格阶段输单"""
        self._handle_lose(**kwargs)

    @transition(
        from_state="PROPOSAL",
        to_state="LOST",
        required_permission="opportunity:update",
        action_type="LOSE",
        notify_users=["owner", "created_by"],
        notification_template="opportunity_lost",
    )
    def lose_from_proposal(self, from_state: str, to_state: str, **kwargs):
        """从提案阶段输单"""
        self._handle_lose(**kwargs)

    @transition(
        from_state="NEGOTIATION",
        to_state="LOST",
        required_permission="opportunity:update",
        action_type="LOSE",
        notify_users=["owner", "created_by"],
        notification_template="opportunity_lost",
    )
    def lose_from_negotiation(self, from_state: str, to_state: str, **kwargs):
        """从谈判阶段输单"""
        self._handle_lose(**kwargs)

    # ==================== 业务逻辑辅助方法 ====================

    def _handle_lose(self, **kwargs):
        """处理输单逻辑"""
        if 'lose_reason' in kwargs:
            self.model.lose_reason = kwargs['lose_reason']
        self.model.lost_at = datetime.now()

    def update_score(self, score: int, score_remark: Optional[str] = None):
        """
        更新评分（不改变状态）

        Args:
            score: 评分（0-100）
            score_remark: 评分说明
        """
        self.model.score = score

        # 根据评分自动更新风险等级
        if score >= 80:
            self.model.risk_level = "LOW"
        elif score >= 60:
            self.model.risk_level = "MEDIUM"
        else:
            self.model.risk_level = "HIGH"

    def update_gate_status(self, gate_status: str, gate_type: str = "G2"):
        """
        更新阶段门状态（不改变阶段）

        Args:
            gate_status: 阶段门状态 (PASS/REJECT)
            gate_type: 阶段门类型 (G1, G2, G3, G4)
        """
        self.model.gate_status = gate_status
        if gate_status == "PASS":
            self.model.gate_passed_at = datetime.now()
