# -*- coding: utf-8 -*-
"""batch单元测试"""
import pytest
from app.services.approval_engine.notify.batch import BatchNotificationMixin


class TestBatchNotificationMixinInit:
    def test_init(self):
        service = BatchNotificationMixin()
        assert service is not None
        assert hasattr(service, 'batch_notify')
