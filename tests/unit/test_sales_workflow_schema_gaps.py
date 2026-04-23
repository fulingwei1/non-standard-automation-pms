from app.schemas.sales.workflow import ApprovalWorkflowCreate


def test_approval_workflow_create_normalizes_none_is_active():
    workflow = ApprovalWorkflowCreate(
        workflow_name="报价审批",
        workflow_type="QUOTE",
        is_active=None,
    )

    assert workflow.is_active is True
