# -*- coding: utf-8 -*-
"""data_audit_service 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.sales.data_audit import DataAuditStatusEnum
from app.models.sales.operation_log import SalesOperationType
from app.services.sales.data_audit_service import SalesDataAuditService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, count_value=0):
        self._first_value = first_value
        self._all_value = all_value or []
        self._count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value

    def count(self):
        return self._count_value


class FakeAuditRequest:
    entity_type = object()
    entity_id = object()
    status = object()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = 321


class FakeModel:
    id = object()


class TestSalesDataAuditServiceDeep:
    def test_submit_audit_request_changed_fields_and_requester_dept_none(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = SalesDataAuditService(db)
        requester = SimpleNamespace(id=7, username="u1", department=None)

        with patch("app.services.sales.data_audit_service.SalesDataAuditRequest", FakeAuditRequest):
            req = service.submit_audit_request(
                entity_type="quote",
                entity_id=9,
                old_value={"amount": 100, "remark": "a"},
                new_value={"amount": 120, "remark": "a", "new_field": "x"},
                requester=requester,
                entity_code="Q-1",
                change_reason="调价",
            )

        assert req.entity_type == "QUOTE"
        assert req.entity_id == 9
        assert req.entity_code == "Q-1"
        assert req.requester_id == 7
        assert req.requester_dept is None
        assert req.status == DataAuditStatusEnum.PENDING.value
        assert req.changed_fields == ["amount"]
        db.add.assert_called_once_with(req)
        db.flush.assert_called_once()

    def test_get_pending_requests_with_filters_and_getters(self):
        db = Mock()
        rows = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        request = SimpleNamespace(id=5)
        history = [SimpleNamespace(id=6)]
        db.query.side_effect = [
            FakeQuery(all_value=rows, count_value=8),
            FakeQuery(first_value=request),
            FakeQuery(all_value=history, count_value=3),
        ]
        service = SalesDataAuditService(db)

        pending, total = service.get_pending_requests(entity_type="contract", priority="high", skip=5, limit=2)
        detail = service.get_request_detail(5)
        hist, hist_total = service.get_entity_audit_history("quote", 99, skip=1, limit=1)

        assert pending == rows and total == 8
        assert detail is request
        assert hist == history and hist_total == 3

    def test_approve_without_apply_and_cancel_without_reason(self):
        db = Mock()
        request1 = SimpleNamespace(id=1, status=DataAuditStatusEnum.PENDING.value, requester_id=10, entity_type="QUOTE", entity_id=1)
        request2 = SimpleNamespace(id=2, status=DataAuditStatusEnum.PENDING.value, requester_id=10, entity_type="QUOTE", entity_id=2, review_comment=None)
        db.query.side_effect = [FakeQuery(first_value=request1), FakeQuery(first_value=request2)]
        service = SalesDataAuditService(db)
        reviewer = SimpleNamespace(id=20, username="rev")
        requester = SimpleNamespace(id=10, username="req")

        with patch("app.services.sales.data_audit_service.assert_status_allows") as allow, \
             patch.object(service, "_apply_change") as apply_change:
            approved = service.approve_request(1, reviewer, comment="ok", apply_immediately=False)
            cancelled = service.cancel_request(2, requester)

        assert approved.status == DataAuditStatusEnum.APPROVED.value
        assert approved.reviewer_id == 20
        assert approved.review_comment == "ok"
        apply_change.assert_not_called()
        assert cancelled.status == DataAuditStatusEnum.CANCELLED.value
        assert cancelled.review_comment == "申请人撤销"
        assert allow.call_count == 2
        assert db.flush.call_count == 2

    def test_apply_change_unknown_or_missing_entity(self):
        db = Mock()
        service = SalesDataAuditService(db)
        req = SimpleNamespace(entity_type="UNKNOWN", entity_id=1, new_value={}, old_value={}, changed_fields=[], entity_code=None, id=1)

        with patch.object(service, "_get_model_class", return_value=None), \
             patch("app.services.sales.data_audit_service.SalesOperationLogService.log_operation") as log_op:
            service._apply_change(req, SimpleNamespace(id=5, username="u"))
        log_op.assert_not_called()

        req2 = SimpleNamespace(entity_type="QUOTE", entity_id=2, new_value={"name": "x"}, old_value={}, changed_fields=["name"], entity_code="Q2", id=2)
        with patch.object(service, "_get_model_class", return_value=FakeModel), \
             patch("app.services.sales.data_audit_service.SalesOperationLogService.log_operation") as log_op:
            db.query.return_value = FakeQuery(first_value=None)
            service._apply_change(req2, SimpleNamespace(id=5, username="u"))
        log_op.assert_not_called()

    def test_apply_change_updates_entity_and_logs_operation(self):
        db = Mock()
        service = SalesDataAuditService(db)
        entity = SimpleNamespace(name="old", amount=1)
        request = SimpleNamespace(
            id=9,
            entity_type="QUOTE",
            entity_id=7,
            entity_code="Q-7",
            old_value={"name": "old", "amount": 1},
            new_value={"name": "new", "amount": 2, "missing": 3},
            changed_fields=["name", "amount"],
            applied_at=None,
            applied_by=None,
        )
        applier = SimpleNamespace(id=99, username="admin")
        db.query.return_value = FakeQuery(first_value=entity)

        with patch.object(service, "_get_model_class", return_value=FakeModel), \
             patch("app.services.sales.data_audit_service.SalesOperationLogService.log_operation") as log_op:
            service._apply_change(request, applier)

        assert entity.name == "new"
        assert entity.amount == 2
        assert request.applied_by == 99
        assert request.applied_at is not None
        log_op.assert_called_once()
        kwargs = log_op.call_args.kwargs
        assert kwargs["entity_type"] == "QUOTE"
        assert kwargs["entity_id"] == 7
        assert kwargs["operation_type"] == SalesOperationType.UPDATE
        assert kwargs["operator"] is applier
