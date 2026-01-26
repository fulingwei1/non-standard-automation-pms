# -*- coding: utf-8 -*-
"""Tests for acceptance_completion_service"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

class TestAcceptanceCompletionService:
    """Test suite for AcceptanceCompletionService"""
    
    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.acceptance_completion_service import AcceptanceCompletionService
        return AcceptanceCompletionService(db_session)
    
    def test_complete_acceptance(self, service):
        """Test completing acceptance"""
        result = service.complete_acceptance(1, {'actual_date': date.today()})
        assert result is not None
