# -*- coding: utf-8 -*-
"""
ProjectMilestone Model 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

try:
    from app.models.project.lifecycle import ProjectMilestone
except ImportError:
    pytest.skip("ProjectMilestone not importable from app.models.project.lifecycle", allow_module_level=True)


class TestProjectMilestoneModel:
    """ProjectMilestone 模型测试"""

    def test_create_milestone(self, db_session, sample_project):
        """测试创建里程碑"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="需求评审",
            planned_date=date.today() + timedelta(days=15),
            weight_pct=Decimal("20.00")
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.id is not None
        assert milestone.milestone_name == "需求评审"
        assert milestone.weight_pct == Decimal("20.00")

    def test_milestone_project_relationship(self, db_session, sample_project):
        """测试里程碑-项目关系"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="设计完成",
            planned_date=date.today() + timedelta(days=30)
        )
        db_session.add(milestone)
        db_session.commit()
        
        db_session.refresh(milestone)
        assert milestone.project is not None
        assert milestone.project.project_code == "PRJ001"

    def test_milestone_status(self, db_session, sample_project):
        """测试里程碑状态"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="开发完成",
            planned_date=date.today(),
            status="未开始"
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.status == "未开始"
        
        milestone.status = "进行中"
        db_session.commit()
        
        db_session.refresh(milestone)
        assert milestone.status == "进行中"

    def test_milestone_date_tracking(self, db_session, sample_project):
        """测试里程碑日期跟踪"""
        planned = date.today() + timedelta(days=30)
        actual = date.today() + timedelta(days=32)
        
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="测试完成",
            planned_date=planned,
            actual_date=actual
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.planned_date == planned
        assert milestone.actual_date == actual
        
        # 计算延期天数
        delay = (milestone.actual_date - milestone.planned_date).days
        assert delay == 2

    def test_milestone_completion(self, db_session, sample_project):
        """测试里程碑完成度"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="编码",
            planned_date=date.today(),
            completion_pct=Decimal("0.00")
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.completion_pct == Decimal("0.00")
        
        milestone.completion_pct = Decimal("50.00")
        db_session.commit()
        
        db_session.refresh(milestone)
        assert milestone.completion_pct == Decimal("50.00")

    def test_milestone_weight(self, db_session, sample_project):
        """测试里程碑权重"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="部署上线",
            planned_date=date.today() + timedelta(days=60),
            weight_pct=Decimal("30.00")
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.weight_pct == Decimal("30.00")

    def test_milestone_description(self, db_session, sample_project):
        """测试里程碑描述"""
        desc = "完成所有功能模块的单元测试，代码覆盖率达到80%以上"
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="单元测试",
            planned_date=date.today() + timedelta(days=20),
            description=desc
        )
        db_session.add(milestone)
        db_session.commit()
        
        assert milestone.description == desc

    def test_milestone_update(self, db_session, sample_project):
        """测试更新里程碑"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="初版",
            planned_date=date.today()
        )
        db_session.add(milestone)
        db_session.commit()
        
        new_name = "V1.0正式版"
        new_date = date.today() + timedelta(days=5)
        milestone.milestone_name = new_name
        milestone.planned_date = new_date
        db_session.commit()
        
        db_session.refresh(milestone)
        assert milestone.milestone_name == new_name
        assert milestone.planned_date == new_date

    def test_milestone_delete(self, db_session, sample_project):
        """测试删除里程碑"""
        milestone = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="临时里程碑",
            planned_date=date.today()
        )
        db_session.add(milestone)
        db_session.commit()
        milestone_id = milestone.id
        
        db_session.delete(milestone)
        db_session.commit()
        
        deleted = db_session.query(ProjectMilestone).filter_by(id=milestone_id).first()
        assert deleted is None

    def test_multiple_milestones(self, db_session, sample_project):
        """测试项目多个里程碑"""
        milestones = [
            ProjectMilestone(
                project_id=sample_project.id,
                milestone_name=f"里程碑{i}",
                planned_date=date.today() + timedelta(days=i*15),
                weight_pct=Decimal("20.00")
            ) for i in range(1, 6)
        ]
        db_session.add_all(milestones)
        db_session.commit()
        
        result = db_session.query(ProjectMilestone).filter_by(
            project_id=sample_project.id
        ).all()
        assert len(result) == 5
        
        # 验证权重总和
        total_weight = sum(m.weight_pct for m in result)
        assert total_weight == Decimal("100.00")

    def test_milestone_sorting(self, db_session, sample_project):
        """测试里程碑排序"""
        milestone1 = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="第三阶段",
            planned_date=date.today() + timedelta(days=60),
            sequence=3
        )
        milestone2 = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="第一阶段",
            planned_date=date.today(),
            sequence=1
        )
        milestone3 = ProjectMilestone(
            project_id=sample_project.id,
            milestone_name="第二阶段",
            planned_date=date.today() + timedelta(days=30),
            sequence=2
        )
        db_session.add_all([milestone1, milestone2, milestone3])
        db_session.commit()
        
        milestones = db_session.query(ProjectMilestone).filter_by(
            project_id=sample_project.id
        ).order_by(ProjectMilestone.sequence).all()
        
        assert len(milestones) == 3
        assert milestones[0].milestone_name == "第一阶段"
        assert milestones[1].milestone_name == "第二阶段"
        assert milestones[2].milestone_name == "第三阶段"
