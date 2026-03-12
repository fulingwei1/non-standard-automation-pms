# -*- coding: utf-8 -*-
"""
方案版本服务测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.solution_version_service import SolutionVersionService


class TestSolutionVersionService:
    """SolutionVersionService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return SolutionVersionService(mock_db)

    # ========== 版本号计算测试 ==========
    def test_calculate_next_version_first(self, service):
        """首个版本应为 V1.0"""
        result = service._calculate_next_version(None)
        assert result == "V1.0"

    def test_calculate_next_version_from_draft(self, service):
        """基于 draft 版本，次版本号 +1"""
        mock_version = MagicMock()
        mock_version.version_no = "V1.0"
        mock_version.status = "draft"

        result = service._calculate_next_version(mock_version)
        assert result == "V1.1"

    def test_calculate_next_version_from_pending(self, service):
        """基于 pending_review 版本，次版本号 +1"""
        mock_version = MagicMock()
        mock_version.version_no = "V2.3"
        mock_version.status = "pending_review"

        result = service._calculate_next_version(mock_version)
        assert result == "V2.4"

    def test_calculate_next_version_from_approved(self, service):
        """基于 approved 版本，主版本号 +1"""
        mock_version = MagicMock()
        mock_version.version_no = "V1.5"
        mock_version.status = "approved"

        result = service._calculate_next_version(mock_version)
        assert result == "V2.0"

    def test_calculate_next_version_from_rejected(self, service):
        """基于 rejected 版本，次版本号 +1"""
        mock_version = MagicMock()
        mock_version.version_no = "V3.2"
        mock_version.status = "rejected"

        result = service._calculate_next_version(mock_version)
        assert result == "V3.3"

    def test_calculate_next_version_invalid_format(self, service):
        """无效版本号格式，返回 V1.0"""
        mock_version = MagicMock()
        mock_version.version_no = "invalid"
        mock_version.status = "draft"

        result = service._calculate_next_version(mock_version)
        assert result == "V1.0"


class TestVersionNumberProgression:
    """版本号递进场景测试"""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        return SolutionVersionService(mock_db)

    def test_version_progression_scenario(self, service):
        """
        模拟完整的版本递进场景：
        V1.0 (draft) → V1.1 (draft) → V1.2 (approved) → V2.0 (draft) → V2.1 (approved) → V3.0
        """
        # Step 1: 首个版本
        v1 = None
        assert service._calculate_next_version(v1) == "V1.0"

        # Step 2: draft 基础上修改
        v1_0 = MagicMock(version_no="V1.0", status="draft")
        assert service._calculate_next_version(v1_0) == "V1.1"

        # Step 3: draft 继续修改
        v1_1 = MagicMock(version_no="V1.1", status="draft")
        assert service._calculate_next_version(v1_1) == "V1.2"

        # Step 4: 审批通过后创建新版本
        v1_2 = MagicMock(version_no="V1.2", status="approved")
        assert service._calculate_next_version(v1_2) == "V2.0"

        # Step 5: 新主版本下继续修改
        v2_0 = MagicMock(version_no="V2.0", status="draft")
        assert service._calculate_next_version(v2_0) == "V2.1"

        # Step 6: 再次审批通过
        v2_1 = MagicMock(version_no="V2.1", status="approved")
        assert service._calculate_next_version(v2_1) == "V3.0"
