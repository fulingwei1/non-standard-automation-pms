# -*- coding: utf-8 -*-
"""funnel_state_machine 深度测试"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.sales.sales_funnel import FunnelEntityTypeEnum, GateTypeEnum
from app.services.sales.funnel_state_machine import FunnelStateMachine
from app.services.sales.gate_validators import ValidationResult


class FakeQuery:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value

    def order_by(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self


class TestFunnelStateMachineDeep:
    def test_get_entity_stage_and_can_transition(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        lead = SimpleNamespace(id=1, status="NEW", created_at=datetime.now(), lead_code="L1")
        stage_cfg = SimpleNamespace(is_terminal=False, allowed_next_stages=["QUALIFIED"], required_gate=None)
        db.query.return_value = FakeQuery(first_value=lead)

        assert sm.get_entity_stage(FunnelEntityTypeEnum.LEAD, 1) == "NEW"

        sm._get_entity = Mock(return_value=lead)
        sm.get_entity_stage = Mock(return_value="NEW")
        db.query.return_value = FakeQuery(first_value=stage_cfg)
        can, reasons = sm.can_transition(FunnelEntityTypeEnum.LEAD, 1, "QUALIFIED")
        assert can is True and reasons == []

    def test_can_transition_blocks_terminal_and_gate_failures(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        opp = SimpleNamespace(id=2, stage="DISCOVERY", created_at=datetime.now(), opp_code="O2")
        terminal_cfg = SimpleNamespace(is_terminal=True, allowed_next_stages=["X"], required_gate=None)
        db.query.side_effect = [FakeQuery(first_value=opp), FakeQuery(first_value=opp), FakeQuery(first_value=terminal_cfg)]
        can, reasons = sm.can_transition(FunnelEntityTypeEnum.OPPORTUNITY, 2, "PROPOSAL")
        assert can is False
        assert "终止状态" in reasons[0]

        gate_cfg = SimpleNamespace(is_terminal=False, allowed_next_stages=["PROPOSAL"], required_gate=GateTypeEnum.G2.value)
        db.query.side_effect = [FakeQuery(first_value=opp), FakeQuery(first_value=opp), FakeQuery(first_value=gate_cfg)]
        with patch("app.services.sales.funnel_state_machine.GateValidatorFactory.validate_gate", return_value=(ValidationResult(False, failed_rules=["缺资料"]), None)):
            can, reasons = sm.can_transition(FunnelEntityTypeEnum.OPPORTUNITY, 2, "PROPOSAL")
        assert can is False
        assert "未通过阶段门" in reasons[0]

    def test_transition_updates_entity_and_logs(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        lead = SimpleNamespace(id=1, status="NEW", created_at=datetime.now() - timedelta(hours=5), updated_at=None, lead_code="L1")
        stage_cfg = SimpleNamespace(required_gate=None)
        db.query.side_effect = [
            FakeQuery(first_value=lead),
            FakeQuery(first_value=lead),
            FakeQuery(first_value=stage_cfg),
            FakeQuery(first_value=None),
        ]
        sm.can_transition = Mock(return_value=(True, []))

        with patch("app.services.sales.funnel_state_machine.FunnelTransitionLog", side_effect=lambda **kwargs: SimpleNamespace(**kwargs)):
            ok, log, messages = sm.transition(FunnelEntityTypeEnum.LEAD, 1, "QUALIFIED", transitioned_by=7)

        assert ok is True
        assert log.from_stage == "NEW"
        assert log.to_stage == "QUALIFIED"
        assert lead.status == "QUALIFIED"
        assert messages == ["状态已从 NEW 转换为 QUALIFIED"]

    def test_update_entity_stage_quote_and_calculate_dwell(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        quote = SimpleNamespace(id=3, current_version_id=8, updated_at=None, created_at=datetime.now() - timedelta(hours=10))
        version = SimpleNamespace(id=8, status="DRAFT")
        db.query.side_effect = [FakeQuery(first_value=version), FakeQuery(first_value=SimpleNamespace(transitioned_at=datetime.now() - timedelta(hours=4)))]

        sm._update_entity_stage(FunnelEntityTypeEnum.QUOTE, quote, "APPROVED")
        dwell = sm._calculate_dwell_hours(FunnelEntityTypeEnum.QUOTE, quote)

        assert version.status == "APPROVED"
        assert dwell >= 3

    def test_lead_to_opportunity_and_opportunity_to_quote(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        lead = SimpleNamespace(id=1, lead_code="L1", customer_name="客户A", owner_id=9, status="NEW")
        opp = SimpleNamespace(id=2, opp_code="O2", customer_id=11, opp_name="商机A", stage="QUALIFICATION", gate_status=None, gate_passed_at=None)
        db.query.side_effect = [
            FakeQuery(first_value=lead),
            FakeQuery(first_value=opp),
        ]

        with patch("app.services.sales.funnel_state_machine.GateValidatorFactory.validate_gate", side_effect=[(ValidationResult(True), SimpleNamespace(id=5)), (ValidationResult(True), SimpleNamespace(id=6))]), patch(
            "app.services.sales.funnel_state_machine.Opportunity",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ), patch(
            "app.services.sales.funnel_state_machine.Quote",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ), patch(
            "app.services.sales.funnel_state_machine.FunnelTransitionLog",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            ok1, new_opp, _ = sm.lead_to_opportunity(1, {"opp_code": "OPP-X"}, transitioned_by=3)
            ok2, quote, _ = sm.opportunity_to_quote(2, {"quote_code": "QT-X"}, transitioned_by=4)

        assert ok1 is True and new_opp.opp_code == "OPP-X"
        assert lead.status == "CONVERTED"
        assert ok2 is True and quote.quote_code == "QT-X"
        assert opp.stage == "PROPOSAL"

    def test_quote_to_contract_history_and_summary(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        quote = SimpleNamespace(id=3, quote_code="Q3", quote_name="报价A", opportunity_id=9, current_version_id=12, customer_id=7)
        version = SimpleNamespace(id=12, status="APPROVED", total_amount=888)
        history = [SimpleNamespace(id=1)]
        db.query.side_effect = [
            FakeQuery(first_value=quote),
            FakeQuery(first_value=version),
            FakeQuery(all_value=history),
            FakeQuery(all_value=[("NEW", 2)]),
            FakeQuery(all_value=[("PROPOSAL", 3)]),
        ]

        with patch("app.services.sales.funnel_state_machine.GateValidatorFactory.validate_gate", return_value=(ValidationResult(True), SimpleNamespace(id=8))), patch(
            "app.services.sales.funnel_state_machine.Contract",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ), patch(
            "app.services.sales.funnel_state_machine.FunnelTransitionLog",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            ok, contract, _ = sm.quote_to_contract(3, {"contract_code": "CT-X"}, transitioned_by=5)
            logs = sm.get_transition_history(FunnelEntityTypeEnum.QUOTE, 3)
            summary = sm.get_funnel_summary()

        assert ok is True and contract.contract_code == "CT-X"
        assert version.status == "ACCEPTED"
        assert logs == history
        assert summary["leads"]["NEW"] == 2
        assert summary["opportunities"]["PROPOSAL"] == 3

    def test_quote_to_contract_and_compare_failures(self):
        db = Mock()
        sm = FunnelStateMachine(db)
        with patch("app.services.sales.funnel_state_machine.GateValidatorFactory.validate_gate", return_value=(ValidationResult(False, failed_rules=["未审批"]), None)):
            ok, contract, msgs = sm.quote_to_contract(1, {}, transitioned_by=1)
        assert ok is False and contract is None
        assert msgs[0] == "G3 阶段门验证失败"

        with pytest.raises(ValueError):
            FunnelStateMachine._coerce_entity_type("bad")
