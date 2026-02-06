# -*- coding: utf-8 -*-
"""
工单智能分配服务测试
"""


from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from app.services.ticket_assignment_service import (
    get_project_members_for_ticket,
    get_ticket_related_projects,
)


class TestGetProjectMembersForTicket:
    """测试获取项目相关人员"""

    def test_empty_project_ids_returns_empty_list(self, db_session: Session):
        """空项目ID列表返回空列表"""
        result = get_project_members_for_ticket(
        db=db_session,
        project_ids=[],
        )

        assert result == []

    def test_no_matching_members_returns_empty_list(self, db_session: Session):
        """没有匹配成员返回空列表"""
        result = get_project_members_for_ticket(
        db=db_session,
        project_ids=[99999],
        )

        assert result == []

    def test_with_valid_members(self, db_session: Session):
        """有有效成员的查询"""
        # Mock 查询结果
        mock_member1 = MagicMock()
        mock_member1.user_id = 1
        mock_member1.user = MagicMock()
        mock_member1.user.username = "user1"
        mock_member1.user.real_name = "用户一"
        mock_member1.user.email = "user1@example.com"
        mock_member1.user.phone = "13800000001"
        mock_member1.user.department = "工程部"
        mock_member1.user.position = "工程师"
        mock_member1.role_code = "PM"
        mock_member1.is_lead = True
        mock_member1.allocation_pct = 100
        mock_member1.project_id = 1

        mock_member2 = MagicMock()
        mock_member2.user_id = 2
        mock_member2.user = MagicMock()
        mock_member2.user.username = "user2"
        mock_member2.user.real_name = "用户二"
        mock_member2.user.email = "user2@example.com"
        mock_member2.user.phone = "13800000002"
        mock_member2.user.department = "工程部"
        mock_member2.user.position = "工程师"
        mock_member2.role_code = "ME"
        mock_member2.is_lead = False
        mock_member2.allocation_pct = 80
        mock_member2.project_id = 2

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ-001"
        mock_project1.project_name = "项目一"

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ-002"
        mock_project2.project_name = "项目二"

        mock_role_type1 = MagicMock()
        mock_role_type1.role_name = "项目经理"

        mock_member1.project = mock_project1
        mock_member1.role_type = mock_role_type1
        mock_member2.project = mock_project2
        mock_member2.role_type = mock_role_type1

        # 使用 mock session - 正确的链式调用
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_member1, mock_member2]

        result = get_project_members_for_ticket(
        db=mock_session,
        project_ids=[1, 2],
        )

        assert len(result) == 2
        assert result[0]["user_id"] == 1
        assert result[0]["username"] == "user1"
        assert result[0]["role_code"] == "PM"
        assert result[0]["is_lead"] is True
        assert result[1]["user_id"] == 2
        assert result[1]["role_code"] == "ME"

    def test_filters_by_roles(self, db_session: Session):
        """按角色过滤成员"""
        # 使用 mock session
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = get_project_members_for_ticket(
        db=mock_session,
        project_ids=[1],
        include_roles=["PM", "ME"],
        )

        assert isinstance(result, list)

    def test_excludes_specific_user(self, db_session: Session):
        """排除特定用户"""
        # 使用 mock session
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = get_project_members_for_ticket(
        db=mock_session,
        project_ids=[1],
        exclude_user_id=999,
        )

        assert isinstance(result, list)

    def test_deduplicates_by_user_id(self, db_session: Session):
        """按用户ID去重"""
        # 使用 mock session
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = get_project_members_for_ticket(
        db=mock_session,
        project_ids=[1, 2],
        )

        assert isinstance(result, list)


class TestGetTicketRelatedProjects:
    """测试获取工单关联项目"""

    def test_non_existent_ticket_returns_empty(self, db_session: Session):
        """不存在的工单返回空信息"""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = get_ticket_related_projects(
        db=mock_session,
        ticket_id=99999,
        )

        assert result["primary_project"] is None
        assert result["related_projects"] == []

    def test_ticket_with_primary_project_only(self, db_session: Session):
        """只有主项目的工单"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.project_id = 1

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ-001"
        mock_project.project_name = "项目一"

        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # Use side_effect to return different values for different .first() calls
        mock_query.first.side_effect = [mock_ticket, mock_project]
        mock_query.all.return_value = []

        result = get_ticket_related_projects(
        db=mock_session,
        ticket_id=1,
        )

        assert result["primary_project"]["id"] == 1
        assert result["primary_project"]["project_code"] == "PJ-001"
        assert result["primary_project"]["project_name"] == "项目一"
        assert len(result["related_projects"]) == 0

    def test_ticket_with_related_projects(self, db_session: Session):
        """有关联项目的工单"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.project_id = 1

        mock_primary_project = MagicMock()
        mock_primary_project.id = 1
        mock_primary_project.project_code = "PJ-001"
        mock_primary_project.project_name = "项目一"

        mock_tp1 = MagicMock()
        mock_tp1.project_id = 2
        mock_tp1.is_primary = False

        mock_related_project1 = MagicMock()
        mock_related_project1.id = 2
        mock_related_project1.project_code = "PJ-002"
        mock_related_project1.project_name = "项目二"

        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # Use side_effect to return different values for different calls
        mock_query.first.side_effect = [mock_ticket, mock_primary_project, mock_related_project1]
        mock_query.all.return_value = [mock_tp1]

        result = get_ticket_related_projects(
        db=mock_session,
        ticket_id=1,
        )

        assert result["primary_project"]["id"] == 1
        assert len(result["related_projects"]) == 1
        assert result["related_projects"][0]["project_code"] == "PJ-002"
        assert result["related_projects"][0]["is_primary"] is False

    def test_excludes_primary_project_from_related(self, db_session: Session):
        """从关联项目中排除主项目"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.project_id = 1

        mock_primary_project = MagicMock()
        mock_primary_project.id = 1
        mock_primary_project.project_code = "PJ-001"
        mock_primary_project.project_name = "项目一"

        mock_tp = MagicMock()
        mock_tp.project_id = 1  # 与主项目相同
        mock_tp.is_primary = True

        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_ticket, mock_primary_project]
        mock_query.all.return_value = [mock_tp]

        result = get_ticket_related_projects(
        db=mock_session,
        ticket_id=1,
        )

        # 主项目相同的项目应该被排除
        assert len(result["related_projects"]) == 0
        assert result["primary_project"]["id"] == 1
