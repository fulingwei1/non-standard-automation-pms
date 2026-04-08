# -*- coding: utf-8 -*-
"""batch单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.batch import BatchNotificationMixin

class TestBatchNotificationMixinInit:
    def test_init(self):
        service = BatchNotificationMixin(Mock())
        assert service is not None
