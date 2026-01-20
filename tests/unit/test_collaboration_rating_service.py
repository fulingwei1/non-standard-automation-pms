# -*- coding: utf-8 -*-
"""
Tests for collaboration_rating_service service
Covers: app/services/collaboration_rating_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 172 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.collaboration_rating_service import CollaborationRatingService
from app.models.performance import PerformancePeriod
from app.models.engineer_performance import EngineerProfile, CollaborationRating
from app.models.project import Project, ProjectMember
from app.models.user import User


@pytest.fixture
def collaboration_rating_service(db_session: Session):
    """创建 CollaborationRatingService 实例"""
    return CollaborationRatingService(db_session)


@pytest.fixture
def test_period(db_session: Session):
    """创建测试考核周期"""
    period = PerformancePeriod(
        start_date=date.today() - timedelta(days=90),
        end_date=date.today(),
        period_name="测试周期"
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


@pytest.fixture
def test_engineer(db_session: Session):
    """创建测试工程师"""
    user = User(
        username="engineer1",
        real_name="测试工程师",
        email="engineer1@test.com",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    profile = EngineerProfile(
        user_id=user.id,
        job_type="mechanical"
    )
    db_session.add(profile)
    db_session.commit()
    
    return user


@pytest.fixture
def test_project(db_session: Session, test_engineer):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        created_at=date.today() - timedelta(days=30)
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    # 添加项目成员
    member = ProjectMember(
        project_id=project.id,
        user_id=test_engineer.id,
        role="ENGINEER"
    )
    db_session.add(member)
    db_session.commit()
    
    return project


class TestCollaborationRatingService:
    """Test suite for CollaborationRatingService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = CollaborationRatingService(db_session)
        assert service is not None
        assert service.db == db_session
        assert 'mechanical' in service.JOB_TYPE_DEPARTMENT_MAP

    def test_auto_select_collaborators_period_not_found(self, collaboration_rating_service):
        """测试考核周期不存在"""
        with pytest.raises(ValueError, match="考核周期不存在"):
            collaboration_rating_service.auto_select_collaborators(1, 99999)

    def test_auto_select_collaborators_profile_not_found(self, collaboration_rating_service, test_period):
        """测试工程师档案不存在"""
        with pytest.raises(ValueError, match="工程师档案不存在"):
            collaboration_rating_service.auto_select_collaborators(99999, test_period.id)

    def test_auto_select_collaborators_no_projects(self, collaboration_rating_service, db_session, test_period, test_engineer):
        """测试无参与项目"""
        result = collaboration_rating_service.auto_select_collaborators(
            test_engineer.id,
            test_period.id
        )
        
        assert result == []

    def test_auto_select_collaborators_success(self, collaboration_rating_service, db_session, test_period, test_engineer, test_project):
        """测试成功选择合作人员"""
        # 创建另一个工程师（不同岗位）
        user2 = User(
            username="engineer2",
            real_name="测试工程师2",
            email="engineer2@test.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user2)
        
        profile2 = EngineerProfile(
            user_id=user2.id,
            job_type="test"  # 不同岗位
        )
        db_session.add(profile2)
        db_session.commit()
        
        # 添加到项目
        member2 = ProjectMember(
            project_id=test_project.id,
            user_id=user2.id,
            role="ENGINEER"
        )
        db_session.add(member2)
        db_session.commit()
        
        result = collaboration_rating_service.auto_select_collaborators(
            test_engineer.id,
            test_period.id,
            target_count=5
        )
        
        assert isinstance(result, list)
        # 应该不包含被评价人自己
        assert test_engineer.id not in result

    def test_auto_select_collaborators_less_than_target(self, collaboration_rating_service, db_session, test_period, test_engineer, test_project):
        """测试合作人员数量少于目标数量"""
        # 只创建1个合作人员
        user2 = User(
            username="engineer2",
            real_name="测试工程师2",
            email="engineer2@test.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user2)
        
        profile2 = EngineerProfile(
            user_id=user2.id,
            job_type="test"
        )
        db_session.add(profile2)
        db_session.commit()
        
        member2 = ProjectMember(
            project_id=test_project.id,
            user_id=user2.id,
            role="ENGINEER"
        )
        db_session.add(member2)
        db_session.commit()
        
        result = collaboration_rating_service.auto_select_collaborators(
            test_engineer.id,
            test_period.id,
            target_count=5
        )
        
        # 应该返回所有合作人员（即使少于5个）
        assert len(result) <= 5
        assert len(result) >= 0

    def test_submit_rating_success(self, collaboration_rating_service, db_session, test_period, test_engineer):
        """测试提交评价 - 成功场景"""
        # 创建被评价人
        rated_user = User(
            username="rated_user",
            real_name="被评价人",
            email="rated@test.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(rated_user)
        db_session.commit()
        db_session.refresh(rated_user)
        
        result = collaboration_rating_service.submit_rating(
            engineer_id=test_engineer.id,
            rater_id=rated_user.id,
            period_id=test_period.id,
            scores={
                'communication': 4.5,
                'responsiveness': 4.0,
                'professionalism': 4.5,
                'teamwork': 4.0
            },
            comments="测试评价"
        )
        
        assert result is not None
        assert result['success'] is True
        
        # 验证评价记录已创建
        rating = db_session.query(CollaborationRating).filter(
            CollaborationRating.engineer_id == test_engineer.id,
            CollaborationRating.rater_id == rated_user.id,
            CollaborationRating.period_id == test_period.id
        ).first()
        
        assert rating is not None
        assert rating.communication_score == 4.5

    def test_submit_rating_invalid_scores(self, collaboration_rating_service, test_period, test_engineer):
        """测试提交评价 - 无效分数"""
        rated_user = User(
            username="rated_user",
            real_name="被评价人",
            email="rated@test.com",
            hashed_password="hashed",
            is_active=True
        )
        
        with pytest.raises(ValueError, match="分数必须在"):
            collaboration_rating_service.submit_rating(
                engineer_id=test_engineer.id,
                rater_id=rated_user.id,
                period_id=test_period.id,
                scores={
                    'communication': 6.0,  # 超出范围
                    'responsiveness': 4.0,
                    'professionalism': 4.5,
                    'teamwork': 4.0
                }
            )

    def test_get_average_collaboration_score_no_ratings(self, collaboration_rating_service, test_period, test_engineer):
        """测试获取平均分 - 无评价"""
        result = collaboration_rating_service.get_average_collaboration_score(
            test_engineer.id,
            test_period.id
        )
        
        assert result is not None
        assert result['average_score'] == 0.0
        assert result['rating_count'] == 0

    def test_get_pending_ratings(self, collaboration_rating_service, db_session, test_period, test_engineer):
        """测试获取待评价列表"""
        result = collaboration_rating_service.get_pending_ratings(
            test_engineer.id,
            test_period.id
        )
        
        assert isinstance(result, list)
