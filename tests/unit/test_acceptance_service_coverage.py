# -*- coding: utf-8 -*-
"""acceptance_service单元测试"""

from app.services.acceptance.acceptance_service import AcceptanceService


class TestAcceptanceServiceInit:
    def test_static_service_contract(self):
        assert AcceptanceService is not None
        assert hasattr(AcceptanceService, "complete_acceptance_order")
