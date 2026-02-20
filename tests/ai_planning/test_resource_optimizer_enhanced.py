# -*- coding: utf-8 -*-
"""
AI资源优化器增强测试 - 提升覆盖率到50%+
重点测试核心逻辑的输入输出
"""

import pytest
import json
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

from app.models import Project, User, TaskUnified
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import AIResourceOptimizer


@pytest.fixture
def mock_glm_service():
    """Mock GLM服务"""
    service = Mock()
    service.is_available.return_value = True
    service.model = "glm-4"
    return service


@pytest.fixture
def test_project(db: Session):
    """创建测试项目（使用唯一ID）"""
    import uuid
    code = f"RES_TEST_{uuid.uuid4().hex[:8].upper()}"
    project = Project(
        project_code=code,
        project_name="资源测试项目",
        project_type="WEB_DEV",
        status="ST01"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_users(db: Session):
    """创建测试用户（使用正确的字段名）"""
    import uuid
    users = []
    for i, role_name in enumerate(["高级开发", "中级开发", "初级测试"], 1):
        user = User(
            username=f"user_{uuid.uuid4().hex[:6]}",
            real_name=f"用户{i}",
            is_active=True
        )
        db.add(user)
        db.flush()
        users.append(user)
    
    db.commit()
    for u in users:
        db.refresh(u)
    return users


@pytest.fixture
def test_wbs(db: Session, test_project):
    """创建测试WBS任务"""
    import uuid
    wbs = AIWbsSuggestion(
        suggestion_code=f"WBS_{uuid.uuid4().hex[:8].upper()}",
        project_id=test_project.id,
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
    db.refresh(wbs)
    return wbs


class TestAIResourceOptimizerEnhanced:
    """AI资源优化器增强测试"""
    
    @pytest.mark.asyncio
    async def test_allocate_resources_empty_users(self, db: Session, test_wbs, mock_glm_service):
        """测试：无可用用户时的处理"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=test_wbs.id,
            available_user_ids=[]
        )
        
        assert allocations == []
    
    @pytest.mark.asyncio
    async def test_allocate_resources_invalid_wbs(self, db: Session, mock_glm_service):
        """测试：无效WBS ID"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=99999,  # 不存在的ID
            available_user_ids=[1, 2, 3]
        )
        
        assert allocations == []
    
    @pytest.mark.asyncio
    async def test_allocate_resources_with_constraints(self, db: Session, test_wbs, test_users, mock_glm_service):
        """测试：带约束条件的资源分配"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        constraints = {
            "max_allocations": 2,
            "min_skill_match": 60.0
        }
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=test_wbs.id,
            available_user_ids=[u.id for u in test_users],
            constraints=constraints
        )
        
        # 验证返回的分配数量
        assert len(allocations) <= constraints["max_allocations"]
    
    def test_get_available_users_filter(self, db: Session, test_wbs, test_users, mock_glm_service):
        """测试：过滤可用用户"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 测试指定用户ID
        users = optimizer._get_available_users([test_users[0].id], test_wbs)
        assert len(users) == 1
        assert users[0].id == test_users[0].id
        
        # 测试所有用户
        all_users = optimizer._get_available_users(None, test_wbs)
        assert len(all_users) >= 3
    
    def test_calculate_skill_match_no_requirements(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：无技能要求时的匹配度计算"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 修改WBS，移除技能要求
        test_wbs.required_skills = None
        
        skill_match = optimizer._calculate_skill_match(test_users[0], test_wbs)
        
        # 无特定技能要求应返回默认值70
        assert skill_match == 70.0
    
    def test_calculate_skill_match_with_requirements(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：有技能要求时的匹配度"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        skill_match = optimizer._calculate_skill_match(test_users[0], test_wbs)
        
        # 应该返回合理的匹配度
        assert 0 <= skill_match <= 100
        assert isinstance(skill_match, float)
    
    def test_calculate_experience_match_no_tasks(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：无历史任务的经验匹配度"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        experience = optimizer._calculate_experience_match(test_users[0], test_wbs)
        
        # 无历史任务应返回40分
        assert experience == 40.0
    
    def test_calculate_experience_match_with_tasks(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：有历史任务的经验匹配度"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 创建一些已完成的类似任务
        user = test_users[0]
        for i in range(5):
            task = TaskUnified(
                task_code=f"HIST_TASK_{i:03d}",
                title=f"历史任务{i}",
                task_type=test_wbs.task_type,
                assignee_id=user.id,
                status="COMPLETED"
            )
            db.add(task)
        db.commit()
        
        experience = optimizer._calculate_experience_match(user, test_wbs)
        
        # 有5个任务应该得到60-80分之间
        assert 60.0 <= experience <= 80.0
    
    def test_calculate_availability_zero_workload(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：无工作负载的可用性"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        availability = optimizer._calculate_availability(test_users[0], test_wbs)
        
        # 无工作负载应该是100%可用
        assert availability == 100.0
    
    def test_calculate_availability_high_workload(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：高工作负载的可用性"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 给用户分配多个进行中的任务
        user = test_users[0]
        for i in range(6):  # 6个任务 = 120%负载
            task = TaskUnified(
                task_code=f"ACTIVE_TASK_{i:03d}",
                title=f"进行中任务{i}",
                task_type="DEVELOPMENT",
                assignee_id=user.id,
                status="IN_PROGRESS"
            )
            db.add(task)
        db.commit()
        
        availability = optimizer._calculate_availability(user, test_wbs)
        
        # 高负载应该导致低可用性
        assert availability < 50.0
        assert availability >= 0.0
    
    def test_get_current_workload(self, db: Session, test_users, mock_glm_service):
        """测试：当前工作负载计算"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        user = test_users[0]
        
        # 初始负载应为0
        workload = optimizer._get_current_workload(user)
        assert workload == 0.0
        
        # 添加一些任务
        for i in range(3):
            task = TaskUnified(
                task_code=f"WL_TASK_{i:03d}",
                title=f"工作负载任务{i}",
                task_type="DEVELOPMENT",
                assignee_id=user.id,
                status="IN_PROGRESS"
            )
            db.add(task)
        db.commit()
        
        workload = optimizer._get_current_workload(user)
        # 3个任务 = 60%负载
        assert workload == 60.0
    
    def test_calculate_performance_score_no_history(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：无历史绩效数据"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        performance = optimizer._calculate_performance_score(test_users[0], test_wbs)
        
        # 无历史数据应返回默认70分
        assert performance == 70.0
    
    def test_calculate_performance_score_perfect_delivery(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：完美按时交付的绩效"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        user = test_users[0]
        # 创建全部按时完成的任务
        for i in range(10):
            task = TaskUnified(
                task_code=f"PERF_TASK_{i:03d}",
                title=f"绩效任务{i}",
                task_type="DEVELOPMENT",
                assignee_id=user.id,
                status="COMPLETED",
                planned_end_date=date(2026, 1, 31),
                actual_end_date=date(2026, 1, 30)  # 提前1天
            )
            db.add(task)
        db.commit()
        
        performance = optimizer._calculate_performance_score(user, test_wbs)
        
        # 全部按时应该是100分
        assert performance == 100.0
    
    def test_get_hourly_rate_by_role(self, db: Session, mock_glm_service):
        """测试：根据角色获取费率"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 模拟不同角色的用户
        senior = Mock()
        senior.role = "高级开发"
        
        middle = Mock()
        middle.role = "中级开发"
        
        junior = Mock()
        junior.role = "初级开发"
        
        unknown = Mock()
        unknown.role = None
        
        # 验证费率递减
        assert optimizer._get_hourly_rate(senior) > optimizer._get_hourly_rate(middle)
        assert optimizer._get_hourly_rate(middle) > optimizer._get_hourly_rate(junior)
        assert optimizer._get_hourly_rate(unknown) > 0
    
    def test_calculate_cost_efficiency(self, db: Session, mock_glm_service):
        """测试：成本效益计算"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 高匹配度 + 低费率 = 高效益
        high_eff = optimizer._calculate_cost_efficiency(90.0, 100.0)
        
        # 低匹配度 + 高费率 = 低效益
        low_eff = optimizer._calculate_cost_efficiency(50.0, 200.0)
        
        assert high_eff > low_eff
        assert 0 <= high_eff <= 100
        assert 0 <= low_eff <= 100
    
    def test_calculate_cost_efficiency_zero_rate(self, db: Session, mock_glm_service):
        """测试：零费率的成本效益"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        efficiency = optimizer._calculate_cost_efficiency(80.0, 0)
        
        # 零费率应该返回匹配度本身
        assert efficiency == 80.0
    
    def test_generate_recommendation_reason_high_scores(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：高评分的推荐理由"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        reason = optimizer._generate_recommendation_reason(
            test_users[0], test_wbs,
            skill_match=85.0,
            experience_match=85.0,
            availability=85.0,
            performance=85.0
        )
        
        assert reason is not None
        assert len(reason) > 0
        # 应该包含积极的关键词
        assert any(kw in reason for kw in ["高度匹配", "丰富", "优秀"])
    
    def test_generate_recommendation_reason_low_availability(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：低可用性的推荐理由"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        reason = optimizer._generate_recommendation_reason(
            test_users[0], test_wbs,
            skill_match=70.0,
            experience_match=70.0,
            availability=30.0,  # 低可用性
            performance=70.0
        )
        
        assert "负载" in reason or "谨慎" in reason
    
    def test_analyze_strengths(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：优势分析"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        strengths = optimizer._analyze_strengths(
            test_users[0], test_wbs,
            skill_match=85.0,
            performance=85.0
        )
        
        assert isinstance(strengths, list)
        assert len(strengths) >= 2  # 技能和绩效都高
        assert all('category' in s for s in strengths)
        assert all('score' in s for s in strengths)
    
    def test_analyze_weaknesses(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：劣势分析"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        weaknesses = optimizer._analyze_weaknesses(
            test_users[0], test_wbs,
            skill_match=40.0,  # 低技能匹配
            availability=30.0  # 低可用性
        )
        
        assert isinstance(weaknesses, list)
        assert len(weaknesses) >= 2
        assert all('category' in w for w in weaknesses)
        assert all('impact' in w for w in weaknesses)
    
    def test_optimize_allocations_limit_count(self, db: Session, test_wbs, mock_glm_service):
        """测试：优化分配数量限制"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # 创建10个模拟分配
        allocations = []
        for i in range(10):
            alloc = AIResourceAllocation(
                allocation_code=f"RA_TEST_{i}",
                project_id=test_wbs.project_id,
                wbs_suggestion_id=test_wbs.id,
                user_id=i+1,
                overall_match_score=100 - i*5  # 递减的匹配度
            )
            allocations.append(alloc)
        
        optimized = optimizer._optimize_allocations(allocations, test_wbs)
        
        # 应该最多返回5个
        assert len(optimized) <= 5
    
    def test_optimize_allocations_priority_assignment(self, db: Session, test_wbs, mock_glm_service):
        """测试：优先级分配"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        allocations = []
        for i in range(3):
            alloc = AIResourceAllocation(
                allocation_code=f"RA_PRIO_{i}",
                project_id=test_wbs.project_id,
                wbs_suggestion_id=test_wbs.id,
                user_id=i+1,
                overall_match_score=90 - i*10
            )
            allocations.append(alloc)
        
        optimized = optimizer._optimize_allocations(allocations, test_wbs)
        
        # 验证优先级设置
        assert optimized[0].allocation_type == "PRIMARY"
        assert optimized[0].priority == "HIGH"
        assert optimized[0].sequence == 1
        
        if len(optimized) > 1:
            assert optimized[1].allocation_type == "SECONDARY"
            assert optimized[1].sequence == 2
    
    @pytest.mark.asyncio
    async def test_analyze_user_match_complete_flow(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：完整的用户匹配分析流程"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        allocation = await optimizer._analyze_user_match(
            test_users[0], test_wbs, None
        )
        
        # 验证返回的分配对象
        if allocation:
            assert allocation.user_id == test_users[0].id
            assert allocation.wbs_suggestion_id == test_wbs.id
            assert allocation.skill_match_score is not None
            assert allocation.experience_match_score is not None
            assert allocation.availability_score is not None
            assert allocation.performance_score is not None
            assert allocation.overall_match_score is not None
            assert allocation.hourly_rate > 0
            assert allocation.estimated_cost >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_user_match_low_score_rejection(self, db: Session, test_users, test_wbs, mock_glm_service):
        """测试：低综合评分拒绝分配"""
        optimizer = AIResourceOptimizer(db, mock_glm_service)
        
        # Mock所有评分函数返回很低的值
        with patch.object(optimizer, '_calculate_skill_match', return_value=20.0):
            with patch.object(optimizer, '_calculate_experience_match', return_value=20.0):
                with patch.object(optimizer, '_calculate_availability', return_value=20.0):
                    with patch.object(optimizer, '_calculate_performance_score', return_value=20.0):
                        allocation = await optimizer._analyze_user_match(
                            test_users[0], test_wbs, None
                        )
                        
                        # 综合评分太低应该返回None
                        assert allocation is None
