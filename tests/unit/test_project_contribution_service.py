# -*- coding: utf-8 -*-
"""
项目贡献度服务测试（最小版）
"""

import pytest
from unittest.mock import MagicMock


class TestProjectContributionService:
    """项目贡献度服务测试"""

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.project_contribution_service import ProjectContributionService
        
        mock_db = MagicMock()
        service = ProjectContributionService(mock_db)
        
        assert service is not None