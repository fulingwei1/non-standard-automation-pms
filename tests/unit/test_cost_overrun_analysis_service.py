# -*- coding: utf-8 -*-
"""Tests for cost_overrun_analysis_service"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

class TestCostOverrunAnalysisService:
    """Test suite for CostOverrunAnalysisService"""
    
    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService
        return CostOverrunAnalysisService(db_session)
    
    def test_analyze_reasons(self, service):
        """Test analyzing cost overrun reasons"""
        result = service.analyze_reasons()
        assert result is not None
        assert isinstance(result, dict)
        assert 'analysis_period' in result
        assert 'total_overrun_projects' in result
        assert 'reasons' in result
