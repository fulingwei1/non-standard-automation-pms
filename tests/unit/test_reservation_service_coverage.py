# -*- coding: utf-8 -*-
"""reservation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.reservation_service import ReservationService

class TestReservationServiceInit:
    def test_init(self):
        service = ReservationService(Mock())
        assert service is not None
