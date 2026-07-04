# -*- coding: utf-8 -*-
"""PRE-20: AI workflow must not fake auto-run without an executor."""

import pytest

from app.models.presale_ai import PresaleAIWorkflowLog, WorkflowStatusEnum
from app.services.presale.presale_ai_integration import PresaleAIIntegrationService


def test_start_workflow_rejects_auto_run_without_executor(db_session):
    service = PresaleAIIntegrationService(db_session)

    with pytest.raises(ValueError, match="自动运行|执行器|未实现"):
        service.start_workflow(
            presale_ticket_id=1001,
            initial_data={"requirement": "FCT测试需求"},
            auto_run=True,
        )

    assert (
        db_session.query(PresaleAIWorkflowLog)
        .filter(PresaleAIWorkflowLog.presale_ticket_id == 1001)
        .count()
        == 0
    )


def test_start_workflow_manual_mode_creates_pending_plan(db_session):
    service = PresaleAIIntegrationService(db_session)

    logs = service.start_workflow(
        presale_ticket_id=1002,
        initial_data={"requirement": "FCT测试需求"},
        auto_run=False,
    )

    assert len(logs) == 5
    assert {log.status for log in logs} == {WorkflowStatusEnum.PENDING}
    status = service.get_workflow_status(1002)
    assert status is not None
    assert status.overall_status == "pending"
    assert status.progress == 0
