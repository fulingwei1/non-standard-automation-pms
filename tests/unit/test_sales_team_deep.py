# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 销售团队服务"""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.sales_team import SalesTeamCreate, SalesTeamMemberCreate
from app.services.sales_team_service import SalesTeamService


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _user(db: Session) -> User:
    user = User(
        username=_unique("sales-team-user"),
        password_hash="test",
        real_name="销售团队测试用户",
        department="销售部",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


class TestSalesTeamServiceBusinessLogic:
    """销售团队服务业务逻辑测试"""

    def test_create_team(self, db_session: Session):
        """测试创建团队"""
        user = _user(db_session)
        team = SalesTeamService.create_team(
            db_session,
            SalesTeamCreate(team_code=_unique("T"), team_name="团队A", team_type="REGION"),
            created_by=user.id,
        )

        assert team.id is not None
        assert team.team_name == "团队A"

    def test_add_member(self, db_session: Session):
        """测试添加成员"""
        user = _user(db_session)
        team = SalesTeamService.create_team(
            db_session,
            SalesTeamCreate(team_code=_unique("T"), team_name="团队B", team_type="REGION"),
            created_by=user.id,
        )

        member = SalesTeamService.add_member(
            db_session,
            SalesTeamMemberCreate(team_id=team.id, user_id=user.id, role="MEMBER"),
        )

        assert member.id is not None
        assert member.team_id == team.id
        assert member.user_id == user.id

    def test_remove_member(self, db_session: Session):
        """测试移除成员"""
        user = _user(db_session)
        team = SalesTeamService.create_team(
            db_session,
            SalesTeamCreate(team_code=_unique("T"), team_name="团队C", team_type="REGION"),
            created_by=user.id,
        )
        SalesTeamService.add_member(
            db_session,
            SalesTeamMemberCreate(team_id=team.id, user_id=user.id, role="MEMBER"),
        )

        result = SalesTeamService.remove_member(db_session, team.id, user.id)

        assert result is True
        assert SalesTeamService.get_team_members(db_session, team.id) == []

    def test_get_team_members(self, db_session: Session):
        """测试获取团队成员"""
        user = _user(db_session)
        team = SalesTeamService.create_team(
            db_session,
            SalesTeamCreate(team_code=_unique("T"), team_name="团队D", team_type="REGION"),
            created_by=user.id,
        )
        SalesTeamService.add_member(
            db_session,
            SalesTeamMemberCreate(team_id=team.id, user_id=user.id, role="LEADER"),
        )

        members = SalesTeamService.get_team_members(db_session, team.id)

        assert len(members) == 1
        assert members[0].role == "LEADER"
