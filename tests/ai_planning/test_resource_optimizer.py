# -*- coding: utf-8 -*-
"""
AI资源优化器测试
"""

import pytest
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project, User, TaskUnified
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import AIResourceOptimizer


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code="RES_TEST_001",
        project_name="资源测试项目",
        project_type="WEB_DEV",
        status="ST01"
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def sample_users(db: Session):
    """创建测试用户"""
    users = [
        User(username="dev1", real_name="开发1", position="高级开发", is_active=True,
        password_hash="test_hash_123"
    ),
        User(username="dev2", real_name="开发2", position="中级开发", is_active=True,
        password_hash="test_hash_123"
    ),
        User(username="test1", real_name="测试1", position="测试工程师", is_active=True,
        password_hash="test_hash_123"
    ),
    ]
    db.add_all(users)
    db.commit()
    return users


@pytest.fixture
def sample_wbs(db: Session, sample_project):
    """创建测试WBS任务"""
    wbs = AIWbsSuggestion(
        suggestion_code="WBS_RES_001",
        project_id=sample_project.id,
        wbs_level=2,
        wbs_code="1.1",
        task_name="后端开发",
        task_type="DEVELOPMENT",
        estimated_duration_days=20,
        estimated_effort_hours=160,
        required_skills=json.dumps([
            {"skill": "Python", "level": "Senior"},
            {"skill": "Django", "level": "Middle"}
        ], ensure_ascii=False)
    )
    db.add(wbs)
    db.commit()
    return wbs


class TestAIResourceOptimizer:
    """AI资源优化器测试类"""
    
    @pytest.mark.asyncio
    async def test_allocate_resources_basic(self, db: Session, sample_wbs, sample_users):
        """测试：基本资源分配"""
        optimizer = AIResourceOptimizer(db)
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=sample_wbs.id,
            available_user_ids=[u.id for u in sample_users]
        )
        
        assert len(allocations) > 0
        # 验证所有分配都有匹配度评分
        for alloc in allocations:
            assert alloc.overall_match_score is not None
            assert 0 <= alloc.overall_match_score <= 100
    
    @pytest.mark.asyncio
    async def test_allocate_resources_sorted(self, db: Session, sample_wbs, sample_users):
        """测试：资源分配按匹配度排序"""
        optimizer = AIResourceOptimizer(db)
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=sample_wbs.id
        )
        
        if len(allocations) > 1:
            # 验证按匹配度降序排列
            for i in range(len(allocations) - 1):
                assert allocations[i].overall_match_score >= allocations[i+1].overall_match_score
    
    @pytest.mark.asyncio
    async def test_resource_conflict_detection(self, db: Session, sample_wbs, sample_users):
        """测试：资源冲突检测 100%"""
        optimizer = AIResourceOptimizer(db)
        
        # 给用户分配大量任务，模拟高负载
        user = sample_users[0]
        for i in range(5):
            task = TaskUnified(
                task_code=f"TASK_{i:03d}",
                title=f"测试任务{i}",
                task_type="DEVELOPMENT",
                assignee_id=user.id,
                status="IN_PROGRESS"
            )
            db.add(task)
        db.commit()
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=sample_wbs.id,
            available_user_ids=[user.id]
        )
        
        # 验证检测到了高负载
        if allocations:
            assert allocations[0].current_workload > 0
    
    def test_calculate_skill_match(self, db: Session, sample_users, sample_wbs):
        """测试：技能匹配度计算"""
        optimizer = AIResourceOptimizer(db)
        
        user = sample_users[0]  # 高级开发
        
        skill_match = optimizer._calculate_skill_match(user, sample_wbs)
        
        assert 0 <= skill_match <= 100
    
    def test_calculate_availability(self, db: Session, sample_users, sample_wbs):
        """测试：可用性计算"""
        optimizer = AIResourceOptimizer(db)
        
        user = sample_users[0]
        
        availability = optimizer._calculate_availability(user, sample_wbs)
        
        assert 0 <= availability <= 100
    
    def test_calculate_performance_score(self, db: Session, sample_users, sample_wbs):
        """测试：绩效评分计算"""
        optimizer = AIResourceOptimizer(db)
        
        # 创建一些已完成的任务
        user = sample_users[0]
        for i in range(3):
            task = TaskUnified(
                task_code=f"COMP_TASK_{i:03d}",
                title=f"已完成任务{i}",
                task_type="DEVELOPMENT",
                assignee_id=user.id,
                status="COMPLETED",
                planned_end_date=datetime(2025, 1, 31).date(),
                actual_end_date=datetime(2025, 1, 30).date()
            )
            db.add(task)
        db.commit()
        
        performance = optimizer._calculate_performance_score(user, sample_wbs)
        
        assert 0 <= performance <= 100
        # 按时完成的任务应该得到高分
        assert performance >= 70
    
    def test_get_hourly_rate(self, db: Session, sample_users):
        """测试：小时费率获取"""
        optimizer = AIResourceOptimizer(db)
        
        senior_dev = sample_users[0]  # 高级开发
        middle_dev = sample_users[1]  # 中级开发
        
        senior_rate = optimizer._get_hourly_rate(senior_dev)
        middle_rate = optimizer._get_hourly_rate(middle_dev)
        
        # 高级费率应该高于中级
        assert senior_rate > middle_rate
        assert senior_rate > 0
    
    def test_calculate_cost_efficiency(self, db: Session):
        """测试：成本效益计算"""
        optimizer = AIResourceOptimizer(Session())
        
        # 高匹配度 + 低费率 = 高效益
        high_efficiency = optimizer._calculate_cost_efficiency(90.0, 100.0)
        
        # 低匹配度 + 高费率 = 低效益
        low_efficiency = optimizer._calculate_cost_efficiency(50.0, 200.0)
        
        assert high_efficiency > low_efficiency
    
    def test_generate_recommendation_reason(self, db: Session, sample_users, sample_wbs):
        """测试：推荐理由生成"""
        optimizer = AIResourceOptimizer(db)
        
        user = sample_users[0]
        
        reason = optimizer._generate_recommendation_reason(
            user, sample_wbs,
            skill_match=85.0,
            experience_match=80.0,
            availability=90.0,
            performance=88.0
        )
        
        assert reason is not None
        assert len(reason) > 0
        # 应该包含关键词
        assert "匹配" in reason or "经验" in reason or "负载" in reason
    
    @pytest.mark.asyncio
    async def test_optimize_allocations(self, db: Session, sample_wbs, sample_users):
        """测试：分配优化（最多推荐5人）"""
        optimizer = AIResourceOptimizer(db)
        
        # 模拟生成多个候选分配
        allocations = []
        for i, user in enumerate(sample_users):
            alloc = AIResourceAllocation(
                allocation_code=f"RA_TEST_{i}",
                project_id=sample_wbs.project_id,
                wbs_suggestion_id=sample_wbs.id,
                user_id=user.id,
                overall_match_score=90 - i*10  # 递减的匹配度
            )
            allocations.append(alloc)
        
        optimized = optimizer._optimize_allocations(allocations, sample_wbs)
        
        # 验证不超过5人
        assert len(optimized) <= 5
        # 验证第一个是PRIMARY
        if optimized:
            assert optimized[0].allocation_type == "PRIMARY"
    
    @pytest.mark.asyncio
    async def test_allocation_performance(self, db: Session, sample_wbs, sample_users):
        """测试：资源分配性能"""
        import time
        
        optimizer = AIResourceOptimizer(db)
        
        start_time = time.time()
        
        await optimizer.allocate_resources(
            wbs_suggestion_id=sample_wbs.id
        )
        
        elapsed_time = time.time() - start_time
        
        # 资源分配应该很快完成（< 5秒）
        assert elapsed_time < 5
