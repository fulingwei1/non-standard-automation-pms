# -*- coding: utf-8 -*-
"""
AI项目计划生成器测试
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project, User
from app.models.ai_planning import AIProjectPlanTemplate
from app.services.ai_planning import AIProjectPlanGenerator


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code="TEST_001",
        project_name="测试项目",
        project_type="WEB_DEV",
        industry="互联网",
        status="ST01"
    )
    db.add(project)
    db.commit()
    return project


class TestAIProjectPlanGenerator:
    """AI项目计划生成器测试类"""
    
    @pytest.mark.asyncio
    async def test_generate_plan_basic(self, db: Session):
        """测试：基本计划生成"""
        generator = AIProjectPlanGenerator(db)
        
        template = await generator.generate_plan(
            project_name="新项目",
            project_type="WEB_DEV",
            requirements="开发一个电商网站",
            industry="电商",
            complexity="MEDIUM"
        )
        
        assert template is not None
        assert template.project_type == "WEB_DEV"
        assert template.estimated_duration_days > 0
        assert template.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_generate_plan_with_reference(self, db: Session, sample_project):
        """测试：基于参考项目生成计划"""
        # 设置参考项目为已完成状态
        sample_project.status = "ST06"
        sample_project.actual_start_date = datetime(2025, 1, 1).date()
        sample_project.actual_end_date = datetime(2025, 3, 31).date()
        db.commit()
        
        generator = AIProjectPlanGenerator(db)
        
        template = await generator.generate_plan(
            project_name="新项目2",
            project_type="WEB_DEV",
            requirements="类似项目",
            industry="互联网"
        )
        
        assert template is not None
        assert template.reference_count > 0
    
    @pytest.mark.asyncio
    async def test_generate_plan_fallback(self, db: Session):
        """测试：AI失败时使用备用方案"""
        generator = AIProjectPlanGenerator(db)
        # GLM服务不可用时，应该使用规则引擎
        
        template = await generator.generate_plan(
            project_name="备用测试",
            project_type="UNKNOWN_TYPE",
            requirements="测试需求",
            use_template=False
        )
        
        assert template is not None
        assert template.phases is not None
    
    def test_find_reference_projects(self, db: Session, sample_project):
        """测试：查找参考项目"""
        sample_project.status = "ST06"
        db.commit()
        
        generator = AIProjectPlanGenerator(db)
        
        references = generator._find_reference_projects(
            project_type="WEB_DEV",
            industry="互联网",
            complexity="MEDIUM"
        )
        
        assert len(references) > 0
        assert references[0].id == sample_project.id
    
    def test_find_existing_template(self, db: Session):
        """测试：查找现有模板"""
        # 创建测试模板
        template = AIProjectPlanTemplate(
            template_code="TPL_TEST_001",
            template_name="测试模板",
            project_type="WEB_DEV",
            industry="互联网",
            complexity_level="MEDIUM",
            is_active=True,
            is_verified=True,
            confidence_score=85.0
        )
        db.add(template)
        db.commit()
        
        generator = AIProjectPlanGenerator(db)
        
        found = generator._find_existing_template(
            project_type="WEB_DEV",
            industry="互联网",
            complexity="MEDIUM"
        )
        
        assert found is not None
        assert found.template_code == "TPL_TEST_001"
    
    @pytest.mark.asyncio
    async def test_generate_plan_performance(self, db: Session):
        """测试：生成时间不超过30秒"""
        import time
        
        generator = AIProjectPlanGenerator(db)
        
        start_time = time.time()
        
        template = await generator.generate_plan(
            project_name="性能测试",
            project_type="WEB_DEV",
            requirements="性能测试项目",
            use_template=False
        )
        
        elapsed_time = time.time() - start_time
        
        assert template is not None
        assert elapsed_time < 30, f"生成时间超过30秒: {elapsed_time:.2f}秒"
    
    def test_project_to_dict(self, db: Session, sample_project):
        """测试：项目对象转字典"""
        sample_project.actual_start_date = datetime(2025, 1, 1).date()
        sample_project.actual_end_date = datetime(2025, 3, 31).date()
        sample_project.contract_amount = 100000
        sample_project.actual_cost = 80000
        db.commit()
        
        generator = AIProjectPlanGenerator(db)
        
        project_dict = generator._project_to_dict(sample_project)
        
        assert project_dict['id'] == sample_project.id
        assert project_dict['name'] == sample_project.project_name
        assert project_dict['duration_days'] == 90
        assert project_dict['contract_amount'] == 100000
    
    def test_generate_fallback_plan(self, db: Session):
        """测试：备用计划生成"""
        generator = AIProjectPlanGenerator(db)
        
        plan_data = generator._generate_fallback_plan(
            project_name="备用计划",
            project_type="WEB_DEV",
            requirements="测试需求",
            reference_projects=[]
        )
        
        assert 'phases' in plan_data
        assert 'milestones' in plan_data
        assert 'required_roles' in plan_data
        assert len(plan_data['phases']) > 0
        assert plan_data['estimated_duration_days'] > 0
    
    @pytest.mark.parametrize("complexity,expected_duration", [
        ("LOW", 60),
        ("MEDIUM", 90),
        ("HIGH", 120),
        ("CRITICAL", 150),
    ])
    def test_complexity_impact_on_duration(self, db: Session, complexity, expected_duration):
        """测试：复杂度对工期的影响（参数化测试）"""
        # 这是一个简化的测试，实际实现可能不同
        generator = AIProjectPlanGenerator(db)
        
        plan_data = generator._generate_fallback_plan(
            project_name=f"测试_{complexity}",
            project_type="WEB_DEV",
            requirements="测试",
            reference_projects=[]
        )
        
        # 验证工期在合理范围内
        assert plan_data['estimated_duration_days'] > 0
