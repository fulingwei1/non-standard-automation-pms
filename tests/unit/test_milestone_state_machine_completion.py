# -*- coding: utf-8 -*-
"""Milestone state-machine completion gates."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.core.state_machine.milestone import MilestoneStateMachine


def test_completion_requirement_failure_raises_http_400():
    milestone = Mock(status="IN_PROGRESS")
    db = Mock()
    machine = MilestoneStateMachine(milestone, db)

    with patch(
        "app.services.progress_integration_service.ProgressIntegrationService"
    ) as mock_service_cls:
        mock_service = mock_service_cls.return_value
        mock_service.check_milestone_completion_requirements.return_value = (
            False,
            ["交付物未全部审批"],
        )

        with pytest.raises(HTTPException) as exc:
            machine._ensure_can_complete()

    assert exc.value.status_code == 400
    assert "交付物未全部审批" in exc.value.detail
