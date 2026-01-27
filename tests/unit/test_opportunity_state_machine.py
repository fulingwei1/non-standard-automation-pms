# -*- coding: utf-8 -*-
"""
测试 Opportunity 状态机
"""

import pytest
from unittest.mock import Mock, patch

from app.core.state_machine.opportunity import OpportunityStateMachine


class TestOpportunityStateMachine:
    """测试 Opportunity 状态机"""

    @pytest.fixture
    def mock_opportunity(self):
        """创建模拟的 Opportunity 对象"""
        opp = Mock()
        opp.id = 1
        opp.stage = "DISCOVERY"
        opp.opp_code = "OPP-001"
        opp.opp_name = "测试商机"
        opp.score = 0
        opp.risk_level = "MEDIUM"
        opp.gate_status = "PENDING"
        opp.gate_passed_at = None
        opp.lose_reason = None
        opp.lost_at = None
        opp.__class__.__name__ = "Opportunity"
        return opp

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库会话"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = Mock()
        user.id = 10
        user.name = "测试用户"
        user.username = "testuser"
        user.real_name = "测试用户"
        user.has_permission = Mock(return_value=True)
        return user

    def test_opportunity_state_machine_initialization(self, mock_opportunity, mock_db):
        """测试状态机初始化"""
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        assert state_machine.model == mock_opportunity
        assert state_machine.db == mock_db
        assert state_machine.state_field == "stage"
        assert state_machine.current_state == "DISCOVERY"

    def test_qualify_transition(self, mock_opportunity, mock_db, mock_user):
        """测试合格化转换 (DISCOVERY → QUALIFIED)"""
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "QUALIFIED",
                current_user=mock_user,
                score=85,
            )

        assert result is True
        assert mock_opportunity.stage == "QUALIFIED"
        assert mock_opportunity.score == 85
        assert mock_opportunity.risk_level == "LOW"  # score >= 80

    def test_propose_transition(self, mock_opportunity, mock_db, mock_user):
        """测试提案转换 (QUALIFIED → PROPOSAL)"""
        mock_opportunity.stage = "QUALIFIED"
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "PROPOSAL",
                current_user=mock_user,
            )

        assert result is True
        assert mock_opportunity.stage == "PROPOSAL"

    def test_negotiate_transition(self, mock_opportunity, mock_db, mock_user):
        """测试谈判转换 (PROPOSAL → NEGOTIATION)"""
        mock_opportunity.stage = "PROPOSAL"
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "NEGOTIATION",
                current_user=mock_user,
                probability=75,
            )

        assert result is True
        assert mock_opportunity.stage == "NEGOTIATION"
        assert mock_opportunity.probability == 75

    def test_win_transition(self, mock_opportunity, mock_db, mock_user):
        """测试赢单转换 (NEGOTIATION → WON)"""
        mock_opportunity.stage = "NEGOTIATION"
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "WON",
                current_user=mock_user,
            )

        assert result is True
        assert mock_opportunity.stage == "WON"
        assert mock_opportunity.gate_status == "PASS"
        assert mock_opportunity.gate_passed_at is not None

    def test_lose_from_discovery(self, mock_opportunity, mock_db, mock_user):
        """测试从发现阶段输单 (DISCOVERY → LOST)"""
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "LOST",
                current_user=mock_user,
                lose_reason="价格不匹配",
            )

        assert result is True
        assert mock_opportunity.stage == "LOST"
        assert mock_opportunity.lose_reason == "价格不匹配"
        assert mock_opportunity.lost_at is not None

    def test_lose_from_negotiation(self, mock_opportunity, mock_db, mock_user):
        """测试从谈判阶段输单 (NEGOTIATION → LOST)"""
        mock_opportunity.stage = "NEGOTIATION"
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "LOST",
                current_user=mock_user,
                lose_reason="竞争对手价格更低",
            )

        assert result is True
        assert mock_opportunity.stage == "LOST"
        assert mock_opportunity.lose_reason == "竞争对手价格更低"

    def test_invalid_transition(self, mock_opportunity, mock_db, mock_user):
        """测试无效的状态转换"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        # 尝试从 DISCOVERY 直接到 WON（无效）
        with pytest.raises(InvalidStateTransitionError):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("WON", current_user=mock_user)

    def test_get_allowed_transitions(self, mock_opportunity, mock_db):
        """测试获取允许的状态转换"""
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        # DISCOVERY 状态允许的转换
        allowed = state_machine.get_allowed_transitions()
        assert "QUALIFIED" in allowed
        assert "LOST" in allowed

    def test_score_updates_risk_level(self, mock_opportunity, mock_db, mock_user):
        """测试评分自动更新风险等级"""
        state_machine = OpportunityStateMachine(mock_opportunity, mock_db)

        # 高分 - 低风险
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "QUALIFIED",
                current_user=mock_user,
                score=85,
            )
        assert mock_opportunity.risk_level == "LOW"

        # 中分 - 中风险
        mock_opportunity.stage = "DISCOVERY"
        mock_opportunity.score = 0
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "QUALIFIED",
                current_user=mock_user,
                score=70,
            )
        assert mock_opportunity.risk_level == "MEDIUM"


def test_opportunity_state_machine_import():
    """测试 OpportunityStateMachine 可以正确导入"""
    from app.core.state_machine.opportunity import OpportunityStateMachine

    assert OpportunityStateMachine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
