# -*- coding: utf-8 -*-
"""analysis_service单元测试"""

from unittest.mock import Mock

from app.services.inventory.analysis_service import AnalysisService


class TestAnalysisServiceInit:
    def test_init(self):
        service = AnalysisService(Mock(), 1)
        assert service is not None
        assert service.tenant_id == 1
