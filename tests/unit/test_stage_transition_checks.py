# -*- coding: utf-8 -*-
"""Tests for stage_transition_checks"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestStageTransitionChecks:

    def test_get_stage_status_mapping(self):
        from app.services.stage_transition_checks import get_stage_status_mapping
        m = get_stage_status_mapping()
        assert m["S4"] == "ST09"
        assert m["S9"] == "ST30"
        assert len(m) == 5

    def test_s3_to_s4_no_contract_info(self):
        from app.services.stage_transition_checks import check_s3_to_s4_transition
        db = MagicMock()
        project = MagicMock()
        project.contract_no = None
        project.contract_date = None
        project.contract_amount = None
        ok, target, missing = check_s3_to_s4_transition(db, project)
        assert ok is False
        assert "合同信息不完整" in missing[0]

    def test_s3_to_s4_contract_signed(self):
        from app.services.stage_transition_checks import check_s3_to_s4_transition
        db = MagicMock()
        project = MagicMock()
        project.contract_no = "C001"
        project.contract_date = "2024-01-01"
        project.contract_amount = 100000
        contract = MagicMock()
        contract.status = "SIGNED"
        db.query.return_value.filter.return_value.first.return_value = contract
        ok, target, missing = check_s3_to_s4_transition(db, project)
        assert ok is True
        assert target == "S4"

    def test_s3_to_s4_contract_not_signed(self):
        from app.services.stage_transition_checks import check_s3_to_s4_transition
        db = MagicMock()
        project = MagicMock()
        project.contract_no = "C001"
        project.contract_date = "2024-01-01"
        project.contract_amount = 100000
        contract = MagicMock()
        contract.status = "DRAFT"
        db.query.return_value.filter.return_value.first.return_value = contract
        ok, target, missing = check_s3_to_s4_transition(db, project)
        assert ok is False

    def test_s4_to_s5_has_bom(self):
        from app.services.stage_transition_checks import check_s4_to_s5_transition
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 2
        ok, target, missing = check_s4_to_s5_transition(db, 1)
        assert ok is True
        assert target == "S5"

    def test_s4_to_s5_no_bom(self):
        from app.services.stage_transition_checks import check_s4_to_s5_transition
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        ok, target, missing = check_s4_to_s5_transition(db, 1)
        assert ok is False

    def test_s5_to_s6_passed(self):
        import sys
        import importlib
        mock_gate_fn = MagicMock(return_value=(True, []))
        # Ensure the projects module has check_gate_s5_to_s6
        projects_mod = sys.modules.get('app.api.v1.endpoints.projects')
        if projects_mod is None:
            projects_mod = MagicMock()
            sys.modules['app.api.v1.endpoints.projects'] = projects_mod
        projects_mod.check_gate_s5_to_s6 = mock_gate_fn
        # Force reimport
        if 'app.services.stage_transition_checks' in sys.modules:
            importlib.reload(sys.modules['app.services.stage_transition_checks'])
        from app.services.stage_transition_checks import check_s5_to_s6_transition
        db = MagicMock()
        project = MagicMock()
        ok, target, missing = check_s5_to_s6_transition(db, project)
        assert ok is True
        assert target == "S6"

    def test_s7_to_s8_fat_passed(self):
        from app.services.stage_transition_checks import check_s7_to_s8_transition
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 1
        ok, target, missing = check_s7_to_s8_transition(db, 1)
        assert ok is True
        assert target == "S8"

    def test_s8_to_s9_no_final(self):
        from app.services.stage_transition_checks import check_s8_to_s9_transition
        db = MagicMock()
        project = MagicMock()
        project.id = 1
        db.query.return_value.filter.return_value.count.return_value = 0
        ok, target, missing = check_s8_to_s9_transition(db, project)
        assert ok is False

    def test_s8_to_s9_payment_sufficient(self):
        from app.services.stage_transition_checks import check_s8_to_s9_transition
        db = MagicMock()
        project = MagicMock()
        project.id = 1
        project.contract_amount = 100000
        db.query.return_value.filter.return_value.count.return_value = 1
        plan = MagicMock()
        plan.actual_amount = 90000
        plan.planned_amount = 100000
        plan.status = "PAID"
        db.query.return_value.filter.return_value.all.return_value = [plan]
        ok, target, missing = check_s8_to_s9_transition(db, project)
        assert ok is True
        assert target == "S9"

    @patch("app.api.v1.endpoints.projects.utils.check_gate")
    def test_execute_stage_transition_success(self, mock_gate):
        from app.services.stage_transition_checks import execute_stage_transition
        mock_gate.return_value = (True, [])
        db = MagicMock()
        project = MagicMock()
        project.stage = "S3"
        ok, result = execute_stage_transition(db, project, "S4", "合同签订")
        assert ok is True
        assert result["auto_advanced"] is True
        assert project.stage == "S4"

    @patch("app.api.v1.endpoints.projects.utils.check_gate")
    def test_execute_stage_transition_gate_fail(self, mock_gate):
        from app.services.stage_transition_checks import execute_stage_transition
        mock_gate.return_value = (False, ["缺失项"])
        db = MagicMock()
        project = MagicMock()
        project.stage = "S3"
        ok, result = execute_stage_transition(db, project, "S4", "合同签订")
        assert ok is False
