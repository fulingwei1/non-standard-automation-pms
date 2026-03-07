# -*- coding: utf-8 -*-
"""
里程碑服务分支测试
测试 app/services/milestone_service.py 的各种分支逻辑

覆盖目标:
- 里程碑创建分支
- 里程碑更新分支
- 里程碑完成分支
- 按项目查询分支
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMilestone
from app.services.milestone_service import MilestoneService
from app.schemas.project import MilestoneCreate, MilestoneUpdate


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S4",
        status="ST07",
        health="H1",
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def milestone_service(db_session: Session):
    """创建里程碑服务"""
    return MilestoneService(db_session)


class TestMilestoneCreateBranches:
    """测试里程碑创建的分支逻辑"""

    def test_create_milestone_success(self, milestone_service, test_project):
        """分支：成功创建里程碑"""
        data = MilestoneCreate(
            project_id=test_project.id,
            milestone_name="设计评审",
            planned_date=date.today() + timedelta(days=10),
            is_key=True,
            status="PENDING",
        )

        milestone = milestone_service.create(data)

        assert milestone.milestone_name == "设计评审"
        assert milestone.project_id == test_project.id
        assert milestone.is_key is True

    def test_create_non_key_milestone(self, milestone_service, test_project):
        """分支：创建非关键里程碑"""
        data = MilestoneCreate(
            project_id=test_project.id,
            milestone_name="内部审查",
            planned_date=date.today() + timedelta(days=5),
            is_key=False,
            status="PENDING",
        )

        milestone = milestone_service.create(data)

        assert milestone.is_key is False


class TestMilestoneUpdateBranches:
    """测试里程碑更新的分支逻辑"""

    def test_update_milestone_name(self, milestone_service, test_project, db_session):
        """分支：更新里程碑名称"""
        # 先创建里程碑
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="原名称",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        # 更新
        update_data = MilestoneUpdate(milestone_name="新名称")
        updated = milestone_service.update(milestone.id, update_data)

        assert updated.milestone_name == "新名称"

    def test_update_milestone_date(self, milestone_service, test_project, db_session):
        """分支：更新里程碑计划日期"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="测试里程碑",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        new_date = date.today() + timedelta(days=15)
        update_data = MilestoneUpdate(planned_date=new_date)
        updated = milestone_service.update(milestone.id, update_data)

        assert updated.planned_date == new_date

    def test_update_milestone_status(self, milestone_service, test_project, db_session):
        """分支：更新里程碑状态"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="测试里程碑",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        update_data = MilestoneUpdate(status="IN_PROGRESS")
        updated = milestone_service.update(milestone.id, update_data)

        assert updated.status == "IN_PROGRESS"


class TestMilestoneCompleteBranches:
    """测试里程碑完成的分支逻辑"""

    def test_complete_milestone_with_date(self, milestone_service, test_project, db_session):
        """分支：完成里程碑并指定实际日期"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="待完成里程碑",
            planned_date=date.today(),
            status="IN_PROGRESS",
        )
        db_session.add(milestone)
        db_session.commit()

        actual_date = date.today() - timedelta(days=1)
        result = milestone_service.complete_milestone(
            milestone_id=milestone.id,
            actual_date=actual_date
        )

        assert result.status == "COMPLETED"
        assert result.actual_date == actual_date

    def test_complete_milestone_without_date(self, milestone_service, test_project, db_session):
        """分支：完成里程碑不指定日期（使用今天）"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="待完成里程碑2",
            planned_date=date.today(),
            status="IN_PROGRESS",
        )
        db_session.add(milestone)
        db_session.commit()

        result = milestone_service.complete_milestone(milestone_id=milestone.id)

        assert result.status == "COMPLETED"
        assert result.actual_date == date.today()

    def test_complete_milestone_with_existing_actual_date(self, milestone_service, test_project, db_session):
        """分支：里程碑已有实际日期"""
        existing_date = date.today() - timedelta(days=5)
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="已有日期里程碑",
            planned_date=date.today(),
            status="IN_PROGRESS",
            actual_date=existing_date,
        )
        db_session.add(milestone)
        db_session.commit()

        # 不指定新日期，应该保留现有日期
        result = milestone_service.complete_milestone(milestone_id=milestone.id)

        assert result.status == "COMPLETED"
        assert result.actual_date == existing_date


class TestMilestoneQueryBranches:
    """测试里程碑查询的分支逻辑"""

    def test_get_by_project(self, milestone_service, test_project, db_session):
        """分支：按项目查询里程碑"""
        # 创建多个里程碑
        milestones = [
            ProjectMilestone(
                project_id=test_project.id,
                milestone_name=f"里程碑{i}",
                planned_date=date.today() + timedelta(days=i * 5),
                status="PENDING",
            )
            for i in range(1, 4)
        ]
        db_session.add_all(milestones)
        db_session.commit()

        result = milestone_service.get_by_project(test_project.id)

        assert len(result) >= 3
        # 验证按计划日期排序
        dates = [m.planned_date for m in result]
        assert dates == sorted(dates)

    def test_get_by_project_empty(self, milestone_service, test_project):
        """分支：项目无里程碑"""
        result = milestone_service.get_by_project(test_project.id)

        assert len(result) == 0

    def test_get_milestone_by_id(self, milestone_service, test_project, db_session):
        """分支：按ID查询里程碑"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="单个里程碑",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        result = milestone_service.get(milestone.id)

        assert result.id == milestone.id
        assert result.milestone_name == "单个里程碑"

    def test_get_milestone_not_found(self, milestone_service):
        """分支：里程碑不存在"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            milestone_service.get(99999)

        assert exc_info.value.status_code == 404


class TestMilestoneDeleteBranches:
    """测试里程碑删除的分支逻辑"""

    def test_delete_milestone(self, milestone_service, test_project, db_session):
        """分支：删除里程碑"""
        milestone = ProjectMilestone(
            project_id=test_project.id,
            milestone_name="待删除里程碑",
            planned_date=date.today(),
            status="PENDING",
        )
        db_session.add(milestone)
        db_session.commit()

        milestone_service.delete(milestone.id)

        # 验证删除
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            milestone_service.get(milestone.id)


class TestMilestoneListBranches:
    """测试里程碑列表查询的分支逻辑"""

    def test_list_all_milestones(self, milestone_service, test_project, db_session):
        """分支：列出所有里程碑"""
        # 创建多个里程碑
        for i in range(5):
            milestone = ProjectMilestone(
                project_id=test_project.id,
                milestone_name=f"里程碑{i}",
                planned_date=date.today() + timedelta(days=i),
                status="PENDING",
            )
            db_session.add(milestone)
        db_session.commit()

        result = milestone_service.list()

        assert len(result) >= 5

    def test_list_milestones_with_filters(self, milestone_service, test_project, db_session):
        """分支：带筛选条件的列表查询"""
        # 创建不同状态的里程碑
        for status in ["PENDING", "IN_PROGRESS", "COMPLETED"]:
            milestone = ProjectMilestone(
                project_id=test_project.id,
                milestone_name=f"{status}里程碑",
                planned_date=date.today(),
                status=status,
            )
            db_session.add(milestone)
        db_session.commit()

        # 注意：实际筛选需要 BaseService 支持
        # 这里只验证list方法能正常工作
        result = milestone_service.list()
        assert len(result) >= 3
