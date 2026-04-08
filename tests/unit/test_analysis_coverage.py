# -*- coding: utf-8 -*-
"""analysis单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.adapters.analysis import WorkloadAnalysisAdapter

class TestWorkloadAnalysisAdapterInit:
    def test_init(self):
        service = WorkloadAnalysisAdapter(Mock())
        assert service is not None
