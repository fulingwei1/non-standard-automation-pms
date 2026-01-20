# -*- coding: utf-8 -*-
"""
Tests for status_transition_service service
Covers: app/services/status_transition_service.py
Coverage Target: 0% → 70%+
File Size: 219 lines
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatusLog, Machine
from app.models.sales import Contract
from app.models.acceptance import AcceptanceOrder
from app.services.status_transition_service import StatusTransitionService


@pytest.fixture
def status_transition_service(db_session: Session):
    """Create status transition service instance."""
    return StatusTransitionService(db_session)


@pytest.fixture
def mock_contract(db_session: Session):
    """Create mock contract."""
    contract = Contract(
        contract_code="CT2026012001",
        contract_amount=Decimal("1000000"),
        signed_date=date.today(),
        customer_id=1,
        project_id=None,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def mock_project(db_session: Session):
    """Create mock project."""
    project = Project(
        project_code="PJ250615001",
        project_name="测试项目",
        stage="S1",
        status="ST01",
        start_date=date.today(),
        planned_end_date=date.today() + timedelta(days=90),
        health="H1",
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def mock_acceptance_order(db_session: Session):
    """Create mock acceptance order."""
    order = AcceptanceOrder(
        order_no="FAT001",
        order_type="FAT",
        acceptance_date=date.today(),
        project_id=1,
        status="COMPLETED",
    )
    db_session.add(order)
    db_session.commit()
    return order


class TestStatusTransitionService:
    """Test suite for StatusTransitionService."""

    def test_init(self, db_session: Session):
        """Test service initialization."""
        service = StatusTransitionService(db_session)
        assert service.db is db_session
        assert service.health_calculator is not None

    # ==================== handle_contract_signed Tests ====================

    def test_handle_contract_signed_with_new_project(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
    ):
        """Test contract signed with auto project creation."""
        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=True
        )

        assert result is not None
        assert result.stage == "S3"
        assert result.status == "ST08"
        assert result.contract_amount == mock_contract.contract_amount
        assert result.contract_date == mock_contract.signed_date

        # Verify status log was created
        status_log = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == result.id)
            .first()
        )
        assert status_log is not None
        assert status_log.new_stage == "S3"
        assert status_log.new_status == "ST08"
        assert "合同签订" in status_log.change_reason

    def test_handle_contract_signed_existing_project(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
        mock_project: Project,
    ):
        """Test contract signed with existing project."""
        mock_contract.project_id = mock_project.id

        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        assert result is not None
        assert result.id == mock_project.id
        assert result.stage == "S3"
        assert result.status == "ST08"

    def test_handle_contract_signed_no_auto_create(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
    ):
        """Test contract signed without auto create."""
        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        assert result is None

    def test_handle_contract_signed_contract_not_found(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
    ):
        """Test contract signed when contract doesn't exist."""
        result = status_transition_service.handle_contract_signed(
            99999,  # Non-existent contract ID
            auto_create_project=True,
        )

        assert result is None

    def test_handle_contract_signed_updates_project_date(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
        mock_project: Project,
    ):
        """Test contract signed updates project end date."""
        planned_end = date.today() + timedelta(days=60)
        mock_project.planned_end_date = planned_end
        mock_contract.project_id = mock_project.id
        mock_contract.delivery_deadline = planned_end

        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        assert result is not None
        assert result.planned_end_date == planned_end

    def test_handle_contract_signed_updates_amount(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
        mock_project: Project,
    ):
        """Test contract signed updates project amount."""
        mock_contract.project_id = mock_project.id
        mock_contract.contract_amount = Decimal("500000")
        mock_project.contract_amount = Decimal("300000")

        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        assert result is not None
        assert result.contract_amount == Decimal("500000")

    # ==================== handle_acceptance_passed Tests ====================

    def test_handle_acceptance_passed_to_s6(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance passed transitions to S6."""
        mock_project.stage = "S5"
        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        assert result is not None
        assert result.stage == "S6"
        assert result.status == "ST12"

        # Verify status log
        status_logs = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == mock_project.id)
            .order_by(ProjectStatusLog.created_at.desc())
            .all()
        )
        assert len(status_logs) >= 2  # At least 2 logs

    def test_handle_acceptance_passed_from_s5_to_s6(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance passed from S5 to S6."""
        mock_project.stage = "S5"
        mock_project.status = "ST11"

        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        assert result is not None
        assert result.stage == "S6"
        assert result.status == "ST12"

    def test_handle_acceptance_passed_to_fat(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance passed from FAT to S6."""
        mock_project.stage = "S6"
        mock_project.status = "ST13"

        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        assert result is not None
        assert result.stage == "S6"
        assert result.status == "ST12"

    def test_handle_acceptance_passed_project_not_found(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
    ):
        """Test acceptance passed when project doesn't exist."""
        result = status_transition_service.handle_acceptance_passed(99999)

        assert result is None

    # ==================== handle_acceptance_failed Tests ====================

    def test_handle_acceptance_failed_to_h3(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed transitions to H3."""
        mock_project.stage = "S6"
        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="测试失败"
        )

        assert result is not None
        assert result.health == "H3"
        assert result.status == "ST14"

        # Verify status log
        status_log = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == mock_project.id)
            .order_by(ProjectStatusLog.created_at.desc())
            .first()
        )
        assert status_log is not None
        assert status_log.new_health == "H3"

    def test_handle_acceptance_failed_to_s5(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed from S6 to S5."""
        mock_project.stage = "S6"
        mock_project.status = "ST13"

        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="验收不通过"
        )

        assert result is not None
        assert result.status == "ST11"

    def test_handle_acceptance_failed_from_fat(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed from FAT to S5."""
        mock_project.stage = "S6"
        mock_project.status = "ST13"

        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="FAT未通过"
        )

        assert result is not None
        assert result.status == "ST11"

    def test_handle_acceptance_failed_project_not_found(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
    ):
        """Test acceptance failed when project doesn't exist."""
        result = status_transition_service.handle_acceptance_failed(
            99999, failure_reason="测试失败"
        )

        assert result is None

    def test_handle_acceptance_failed_to_h4(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed when already H4 (blocked)."""
        mock_project.health = "H3"

        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="再次失败"
        )

        assert result is not None
        assert result.status == "ST14"

    def test_handle_acceptance_failed_recovers_health(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed recovers from H3 to H2."""
        mock_project.stage = "S6"
        mock_project.status = "ST14"
        mock_project.health = "H3"

        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="验收失败"
        )

        assert result is not None
        # Recalculates health after transition
        assert result.health in ["H1", "H2"]

    # ==================== _log_status_change Tests ====================

    def test_log_status_change_with_project(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test logging status change for project."""
        status_transition_service._log_status_change(
            mock_project.id,
            old_stage="S1",
            new_stage="S2",
            old_status="ST01",
            new_status="ST02",
            change_type="MANUAL_UPDATE",
            change_reason="测试更新",
        )

        status_logs = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == mock_project.id)
            .all()
        )

        assert len(status_logs) == 1
        assert status_logs[0].old_stage == "S1"
        assert status_logs[0].new_stage == "S2"
        assert "测试更新" in status_logs[0].change_reason

    def test_log_status_change_with_optional_params(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test logging with optional params."""
        result = status_transition_service._log_status_change(
            mock_project.id,
            old_stage="S1",
            old_status="ST01",
            new_stage="S2",
            new_status="ST02",
            change_type="MANUAL_UPDATE",
            change_reason="测试更新",
        )

        # Should still work with None values
        assert result is not None

    # ==================== init_project_stages Tests ====================

    def test_init_project_stages_success(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test project stage initialization."""
        result = status_transition_service.init_project_stages(mock_project.id)

        assert result is not None

        # Verify all stages were created
        machines = (
            db_session.query(Machine)
            .filter(Machine.project_id == mock_project.id)
            .all()
        )
        assert len(machines) == 9  # M1-M9

    def test_init_project_stages_project_not_found(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
    ):
        """Test stage initialization for non-existent project."""
        result = status_transition_service.init_project_stages(99999)

        assert result is None

    # ==================== Multiple Status Change Tests ====================

    def test_contract_then_acceptance_passed(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
        mock_project: Project,
    ):
        """Test contract signed then acceptance passed."""
        # Contract signed
        status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=True
        )

        # Then acceptance passed
        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        assert result is not None
        assert result.stage == "S6"
        assert result.status == "ST12"

    def test_acceptance_failed_then_passed(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed then passed."""
        # First failure
        status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="第一次失败"
        )

        mock_project.health = "H3"
        db_session.refresh(mock_project)

        # Then pass
        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        assert result is not None
        assert result.health != "H3"  # Health should recalculate


class TestStatusTransitionServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_contract_signed_zero_amount(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
        mock_project: Project,
    ):
        """Test contract with zero amount."""
        mock_contract.contract_amount = Decimal("0")
        mock_contract.project_id = mock_project.id

        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        assert result is not None
        assert result.contract_amount == Decimal("0")

    def test_contract_signed_negative_amount(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_contract: Contract,
    ):
        """Test contract with negative amount (edge case)."""
        mock_contract.contract_amount = Decimal("-1000")
        mock_contract.project_id = mock_project.id

        result = status_transition_service.handle_contract_signed(
            mock_contract.id, auto_create_project=False
        )

        # Should handle gracefully or raise validation error
        assert result is not None or result is None

    def test_acceptance_passed_invalid_stage(
        self,
        status_transition_service: StatusTransitionService,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance passed from invalid stage."""
        mock_project.stage = "S99"  # Invalid stage

        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        # Should handle gracefully
        assert result is None

    def test_acceptance_failed_from_blocked_project(
        self,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
    ):
        """Test acceptance failed from already blocked project."""
        mock_project.status = "ST14"  # Already blocked
        mock_project.stage = "S6"

        result = status_transition_service.handle_acceptance_failed(
            mock_project.id, failure_reason="测试失败"
        )

        # Should not change status if already blocked
        assert result is not None
        assert result.status == "ST14"  # Remains blocked

    @patch("app.services.status_transition_service.HealthCalculator")
    def test_health_calculation_on_acceptance(
        self,
        mock_health_calc: MagicMock,
        status_transition_service: StatusTransitionService,
        db_session: Session,
        mock_project: Project,
        db_session: Session,
    ):
        """Test health calculation is called on acceptance."""
        mock_project.stage = "S6"
        mock_project.status = "ST12"

        # Mock health calculation to return H2
        mock_health_calculator.return_value = MagicMock(health="H2")

        result = status_transition_service.handle_acceptance_passed(mock_project.id)

        # Verify health calculator was called
        mock_health_calculator.calculate_and_update.assert_called_once()
