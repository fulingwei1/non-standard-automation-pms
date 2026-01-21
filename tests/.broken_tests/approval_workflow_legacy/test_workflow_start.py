# -*- coding: utf-8 -*-
"""
approval_workflow/workflow_start.py 单元测试

测试审批启动模块
"""

import pytest
from unittest.mock import MagicMock

from app.models.enums import ApprovalRecordStatusEnum
from app.services.approval_workflow.workflow_start import WorkflowStartMixin


class TestWorkflowStartService(WorkflowStartMixin):
    """测试用的服务类，继承混入类"""

    def __init__(self, db):
        self.db = db


@pytest.mark.unit
class TestStartApproval:
    """测试 start_approval 方法"""

    def test_start_with_workflow(self):
        """测试指定工作流"""
        mock_db = MagicMock()
        service = TestWorkflowStartService(db=mock_db)

        mock_workflow = MagicMock()
        mock_workflow.id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_workflow
        mock_db.query.return_value = mock_query

        mock_record = MagicMock()

        mock_db.query.side_effect = [
            mock_query,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = service.start_approval(
            entity_type="QUOTE",
            entity_id=1,
            initiator_id=10,
            workflow_id=100,
            comment="需要审批",
        )

        assert result == mock_record
        assert mock_record.status == ApprovalRecordStatusEnum.PENDING
        assert mock_record.current_step == 1
        mock_db.commit.assert_called()

    def test_start_auto_select_workflow(self):
        """测试自动选择工作流"""
        mock_db = MagicMock()
        service = TestWorkflowStartService(db=mock_db)

        mock_workflow = MagicMock()
        mock_workflow.id = 200

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_workflow
        mock_db.query.return_value = mock_query

        mock_query2 = MagicMock()
        mock_query2.filter.return_value = mock_query2
        mock_query2.first.return_value = None
        mock_db.query.side_effect = [mock_query, MagicMock(), MagicMock()]

        result = service.start_approval(
            entity_type="CONTRACT",
            entity_id=2,
            initiator_id=10,
        )

        assert mock_db.commit.assert_called()
        assert mock_record.current_step == 1

    def test_start_existing_record(self):
        """测试已有审批记录"""
        mock_db = MagicMock()
        service = TestWorkflowStartService(db=mock_db)

        mock_existing = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="已有待审批的记录"):
            service.start_approval(entity_type="INVOICE", entity_id=3, initiator_id=10)

    def test_start_workflow_not_found(self):
        """测试工作流不存在"""
        mock_db = MagicMock()
        service = TestWorkflowStartService(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="工作流.*不存在"):
            service.start_approval(entity_type="PROJECT", entity_id=4, initiator_id=10)
