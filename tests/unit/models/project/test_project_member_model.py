# -*- coding: utf-8 -*-
"""
ProjectMember Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.project.team import ProjectMember


class TestProjectMemberModel:
    """ProjectMember 模型测试"""

    def test_create_project_member(self, db_session, sample_project, sample_user):
        """测试创建项目成员"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="开发工程师",
            allocation_pct=Decimal("80.00")
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.id is not None
        assert member.project_id == sample_project.id
        assert member.user_id == sample_user.id
        assert member.role == "开发工程师"
        assert member.allocation_pct == Decimal("80.00")

    def test_project_member_unique_constraint(self, db_session, sample_project, sample_user):
        """测试项目成员唯一性约束"""
        member1 = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="工程师"
        )
        db_session.add(member1)
        db_session.commit()
        
        member2 = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,  # 同一用户同一项目
            role="测试工程师"
        )
        db_session.add(member2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_project_member_relationships(self, db_session, sample_project, sample_user):
        """测试项目成员关系"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="项目经理"
        )
        db_session.add(member)
        db_session.commit()
        
        db_session.refresh(member)
        assert member.project is not None
        assert member.project.project_code == "PRJ001"
        assert member.user is not None
        assert member.user.username == "testuser"

    def test_project_member_allocation(self, db_session, sample_project, sample_user):
        """测试成员分配比例"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="开发",
            allocation_pct=Decimal("50.00")
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.allocation_pct == Decimal("50.00")
        
        # 更新分配比例
        member.allocation_pct = Decimal("75.50")
        db_session.commit()
        
        db_session.refresh(member)
        assert member.allocation_pct == Decimal("75.50")

    def test_project_member_date_range(self, db_session, sample_project, sample_user):
        """测试成员时间范围"""
        start = date.today()
        end = start + timedelta(days=60)
        
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="工程师",
            start_date=start,
            end_date=end
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.start_date == start
        assert member.end_date == end

    def test_project_member_is_active(self, db_session, sample_project, sample_user):
        """测试成员激活状态"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="工程师",
            is_active=True
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.is_active is True
        
        member.is_active = False
        db_session.commit()
        
        db_session.refresh(member)
        assert member.is_active is False

    def test_project_member_update(self, db_session, sample_project, sample_user):
        """测试更新项目成员"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="初级工程师"
        )
        db_session.add(member)
        db_session.commit()
        
        member.role = "高级工程师"
        member.allocation_pct = Decimal("100.00")
        db_session.commit()
        
        db_session.refresh(member)
        assert member.role == "高级工程师"
        assert member.allocation_pct == Decimal("100.00")

    def test_project_member_delete(self, db_session, sample_project, sample_user):
        """测试删除项目成员"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="临时成员"
        )
        db_session.add(member)
        db_session.commit()
        member_id = member.id
        
        db_session.delete(member)
        db_session.commit()
        
        deleted = db_session.query(ProjectMember).filter_by(id=member_id).first()
        assert deleted is None

    def test_project_member_default_values(self, db_session, sample_project, sample_user):
        """测试成员默认值"""
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role="成员"
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.allocation_pct is None or member.allocation_pct == Decimal("0")
        assert member.is_active in [True, None]  # 根据实际模型定义

    def test_multiple_members_same_project(self, db_session, sample_project):
        """测试同一项目多个成员"""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user1 = User(username="user1", password_hash=get_password_hash("pass"), email="user1@test.com")
        user2 = User(username="user2", password_hash=get_password_hash("pass"), email="user2@test.com")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        member1 = ProjectMember(project_id=sample_project.id, user_id=user1.id, role="开发")
        member2 = ProjectMember(project_id=sample_project.id, user_id=user2.id, role="测试")
        db_session.add_all([member1, member2])
        db_session.commit()
        
        members = db_session.query(ProjectMember).filter_by(project_id=sample_project.id).all()
        assert len(members) == 2
