# -*- coding: utf-8 -*-
"""attachment_service 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.sales.contract.attachment_service import ContractAttachmentService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value or []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value


class FakeAttachment:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DummyAttachmentCreate:
    def __init__(self, **data):
        self.data = data

    def model_dump(self):
        return dict(self.data)


class TestContractAttachmentServiceDeep:
    def test_add_attachment(self):
        db = Mock()
        service = ContractAttachmentService(db)
        data = DummyAttachmentCreate(file_name="a.pdf", file_url="/a.pdf", file_size=123)

        with patch("app.services.sales.contract.attachment_service.ContractAttachment", FakeAttachment), \
             patch("app.services.sales.contract.attachment_service.save_obj") as save_obj:
            att = service.add_attachment(10, data, user_id=5)

        assert att.contract_id == 10
        assert att.uploaded_by == 5
        assert att.file_name == "a.pdf"
        save_obj.assert_called_once_with(db, att)

    def test_get_attachments(self):
        db = Mock()
        rows = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        db.query.return_value = FakeQuery(all_value=rows)
        service = ContractAttachmentService(db)

        assert service.get_attachments(99) == rows

    def test_delete_attachment(self):
        db = Mock()
        service = ContractAttachmentService(db)
        db.query.side_effect = [FakeQuery(first_value=SimpleNamespace(id=1)), FakeQuery(first_value=None)]

        with patch("app.services.sales.contract.attachment_service.delete_obj") as delete_obj:
            ok = service.delete_attachment(1)
            missing = service.delete_attachment(2)

        assert ok is True
        assert missing is False
        delete_obj.assert_called_once()
