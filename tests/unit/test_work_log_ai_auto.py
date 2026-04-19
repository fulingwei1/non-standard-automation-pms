# -*- coding: utf-8 -*-
"""Auto-generated tests for work_log_ai modules"""
from unittest.mock import MagicMock

import pytest


class TestWorkLogAICore:
    """Tests for work log AI core"""

    def test_core_init(self):
        """Test WorkLogAICore initialization"""
        from app.services.work_log_ai.core import WorkLogAICore
        core = WorkLogAICore(MagicMock())
        assert core is not None
        assert core.db is not None


class TestWorkLogAIAnalysis:
    """Tests for AI analysis"""

    def test_analysis_init(self):
        """Test AIAnalysis mixin availability"""
        from app.services.work_log_ai.ai_analysis import AIAnalysisMixin
        assert hasattr(AIAnalysisMixin, "_analyze_with_ai_sync")


class TestWorkLogAIPrompt:
    """Tests for AI prompt"""

    def test_prompt_init(self):
        """Test AIPrompt mixin availability"""
        from app.services.work_log_ai.ai_prompt import AIPromptMixin
        assert hasattr(AIPromptMixin, "_build_ai_prompt")


class TestWorkLogProjectMatching:
    """Tests for project matching"""

    def test_matching_init(self):
        """Test ProjectMatching mixin availability"""
        from app.services.work_log_ai.project_matching import ProjectMatchingMixin
        assert hasattr(ProjectMatchingMixin, "_match_project") or hasattr(ProjectMatchingMixin, "_get_user_projects")
