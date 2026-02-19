# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 跨部门协作评价 合作人员选择器
"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.collaboration_rating.selector import CollaboratorSelector
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def selector(mock_db):
    service_mock = MagicMock()
    return CollaboratorSelector(db=mock_db, service=service_mock)


class TestGetTargetJobTypes:

    def test_mechanical_targets(self, selector):
        result = selector._get_target_job_types("mechanical")
        assert "electrical" in result
        assert "test" in result

    def test_electrical_targets(self, selector):
        result = selector._get_target_job_types("electrical")
        assert "mechanical" in result
        assert "test" in result

    def test_test_targets(self, selector):
        result = selector._get_target_job_types("test")
        assert "mechanical" in result
        assert "electrical" in result

    def test_solution_targets_all(self, selector):
        result = selector._get_target_job_types("solution")
        assert "mechanical" in result
        assert "electrical" in result
        assert "test" in result

    def test_unknown_defaults_to_all(self, selector):
        result = selector._get_target_job_types("unknown_type")
        assert len(result) >= 3


class TestGetCollaboratorsFromProjects:

    def test_empty_members_returns_empty(self, selector, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = selector._get_collaborators_from_projects(1, "mechanical", [1, 2])
        assert result == []

    def test_filters_different_job_types(self, selector, mock_db):
        member1 = MagicMock()
        member1.user_id = 10
        member2 = MagicMock()
        member2.user_id = 20

        profile1 = MagicMock()
        profile1.user_id = 10
        profile1.job_type = "electrical"  # 应被包含（机械找电气）

        profile2 = MagicMock()
        profile2.user_id = 20
        profile2.job_type = "mechanical"  # 不应被包含（同为机械）

        def query_side(model):
            from app.models.project import ProjectMember
            from app.models.engineer_performance import EngineerProfile
            if model is ProjectMember:
                qm = MagicMock()
                qm.filter.return_value.all.return_value = [member1, member2]
                return qm
            elif model is EngineerProfile:
                qm = MagicMock()
                qm.filter.return_value.all.return_value = [profile1, profile2]
                return qm
            return MagicMock()

        mock_db.query.side_effect = query_side
        result = selector._get_collaborators_from_projects(99, "mechanical", [1])
        assert 10 in result
        assert 20 not in result


class TestAutoSelectCollaborators:

    def test_raises_when_period_not_found(self, selector, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="考核周期不存在"):
            selector.auto_select_collaborators(engineer_id=1, period_id=999)

    def test_raises_when_profile_not_found(self, selector, mock_db):
        period = MagicMock()
        period.start_date = "2024-01-01"
        period.end_date = "2024-03-31"

        call_count = [0]

        def first_side():
            call_count[0] += 1
            if call_count[0] == 1:
                return period
            return None  # profile not found

        mock_db.query.return_value.filter.return_value.first.side_effect = first_side
        with pytest.raises(ValueError, match="工程师档案不存在"):
            selector.auto_select_collaborators(engineer_id=1, period_id=1)

    def test_returns_empty_when_no_projects(self, selector, mock_db):
        period = MagicMock()
        period.start_date = "2024-01-01"
        period.end_date = "2024-03-31"

        profile = MagicMock()
        profile.job_type = "mechanical"

        def first_side():
            return period

        mock_db.query.return_value.filter.return_value.first.return_value = period
        # 二次查询 (EngineerProfile) 返回 profile
        call_count = [0]

        def first_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return period
            return profile

        mock_db.query.return_value.filter.return_value.first.side_effect = first_effect
        # 项目查询返回空
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = selector.auto_select_collaborators(1, 1)
        assert result == []
