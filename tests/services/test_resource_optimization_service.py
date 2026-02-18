"""
资源优化服务测试
测试资源分配、冲突检测、利用率计算等功能
"""
import pytest
pytest.importorskip("app.services.resource_optimization_service")

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from typing import List

from app.services.resource_optimization_service import ResourceOptimizationService


class TestResourceAllocation:
    """资源分配测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ResourceOptimizationService(mock_database_session)

    @pytest.fixture
    def available_users(self):
        """可用用户列表"""
        return [
            MagicMock(
                id=1,
                name="张三",
                skills=["Python", "FastAPI"],
                hourly_rate=200,
                current_load=60,  # 当前负载60%
                performance_score=90
            ),
            MagicMock(
                id=2,
                name="李四",
                skills=["Python", "React"],
                hourly_rate=180,
                current_load=80,  # 当前负载80%
                performance_score=85
            ),
            MagicMock(
                id=3,
                name="王五",
                skills=["Java", "Spring"],
                hourly_rate=220,
                current_load=30,  # 当前负载30%
                performance_score=95
            ),
        ]

    @pytest.fixture
    def task_requirements(self):
        """任务需求"""
        return {
            "required_skills": ["Python", "FastAPI"],
            "estimated_hours": 80,
            "priority": "high",
            "start_date": date(2026, 2, 1),
            "end_date": date(2026, 2, 15)
        }

    def test_calculate_skill_match_score(self, service, available_users, task_requirements):
        """测试技能匹配度计算"""
        user = available_users[0]  # 张三: Python, FastAPI
        
        score = service.calculate_skill_match_score(
            user.skills,
            task_requirements["required_skills"]
        )
        
        # 完全匹配: 100分
        assert score == 100

    def test_partial_skill_match(self, service):
        """测试部分技能匹配"""
        user_skills = ["Python", "React"]
        required_skills = ["Python", "FastAPI", "PostgreSQL"]
        
        score = service.calculate_skill_match_score(user_skills, required_skills)
        
        # 1/3匹配: 33.33分
        assert score == pytest.approx(33.33, abs=0.1)

    def test_no_skill_match(self, service):
        """测试无技能匹配"""
        user_skills = ["Java", "Spring"]
        required_skills = ["Python", "FastAPI"]
        
        score = service.calculate_skill_match_score(user_skills, required_skills)
        
        assert score == 0

    def test_calculate_availability_score(self, service, available_users):
        """测试可用性评分计算"""
        user = available_users[0]  # 当前负载60%
        
        score = service.calculate_availability_score(user.current_load)
        
        # 负载60% → 可用性40% → 评分40
        assert score == 40

    def test_high_load_low_availability(self, service, available_users):
        """测试高负载低可用性"""
        user = available_users[1]  # 当前负载80%
        
        score = service.calculate_availability_score(user.current_load)
        
        # 负载80% → 可用性20% → 评分20
        assert score == 20

    def test_allocate_resources_optimal(self, service, available_users, task_requirements):
        """测试资源分配 - 选择最优人选"""
        with patch.object(service, '_get_available_users', return_value=available_users):
            allocations = service.allocate_resources(
                task_id=100,
                requirements=task_requirements,
                max_candidates=3
            )
        
        # 应该返回排序后的推荐列表
        assert len(allocations) > 0
        
        # 第一个推荐应该是技能匹配且负载较低的
        best_candidate = allocations[0]
        assert best_candidate.user_id in [1, 2]  # 张三或李四（都有Python技能）

    def test_resource_conflict_detection_100_percent(self, service):
        """测试资源冲突检测 - 100%检测率"""
        user = MagicMock(id=1)
        
        existing_allocations = [
            {
                'user_id': 1,
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 2, 15),
                'load_percentage': 80
            }
        ]
        
        new_allocation = {
            'start_date': date(2026, 2, 10),
            'end_date': date(2026, 2, 20),
            'load_percentage': 50
        }
        
        has_conflict = service.detect_resource_conflict(
            user_id=1,
            new_allocation=new_allocation,
            existing_allocations=existing_allocations
        )
        
        # 时间重叠且总负载超过100%
        assert has_conflict is True

    def test_no_conflict_different_periods(self, service):
        """测试无冲突 - 不同时间段"""
        existing_allocations = [
            {
                'user_id': 1,
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 2, 10),
                'load_percentage': 80
            }
        ]
        
        new_allocation = {
            'start_date': date(2026, 2, 11),  # 不重叠
            'end_date': date(2026, 2, 20),
            'load_percentage': 80
        }
        
        has_conflict = service.detect_resource_conflict(
            user_id=1,
            new_allocation=new_allocation,
            existing_allocations=existing_allocations
        )
        
        assert has_conflict is False

    def test_calculate_resource_utilization(self, service):
        """测试资源利用率计算"""
        allocations = [
            MagicMock(user_id=1, load_percentage=80, duration_days=10),
            MagicMock(user_id=1, load_percentage=60, duration_days=5),
            MagicMock(user_id=2, load_percentage=100, duration_days=15),
        ]
        
        utilization = service.calculate_resource_utilization(
            allocations=allocations,
            period_days=30
        )
        
        assert 'overall_utilization' in utilization
        assert 'by_user' in utilization
        assert utilization['overall_utilization'] > 0
        assert utilization['overall_utilization'] <= 100

    def test_optimize_multi_project_allocation(self, service):
        """测试多项目资源平衡"""
        projects = [
            {
                'id': 1,
                'priority': 'high',
                'required_users': 3,
                'start_date': date(2026, 2, 1)
            },
            {
                'id': 2,
                'priority': 'medium',
                'required_users': 2,
                'start_date': date(2026, 2, 1)
            },
            {
                'id': 3,
                'priority': 'low',
                'required_users': 1,
                'start_date': date(2026, 2, 1)
            },
        ]
        
        available_count = 5  # 总共5人
        
        allocation_plan = service.optimize_multi_project_allocation(
            projects=projects,
            available_users_count=available_count
        )
        
        # 应该优先分配给高优先级项目
        assert allocation_plan[1]['allocated_users'] >= 3  # 项目1至少3人
        assert sum(p['allocated_users'] for p in allocation_plan.values()) <= available_count

    def test_calculate_cost_efficiency(self, service):
        """测试成本效益计算"""
        allocation = {
            'user_id': 1,
            'hourly_rate': 200,
            'estimated_hours': 80,
            'skill_match_score': 90,
            'performance_score': 85
        }
        
        efficiency = service.calculate_cost_efficiency(allocation)
        
        # 成本效益 = (技能匹配 * 绩效) / 成本
        expected_efficiency = (90 * 85) / (200 * 80)
        
        assert efficiency == pytest.approx(expected_efficiency, abs=0.01)

    def test_suggest_resource_replacement(self, service, available_users):
        """测试资源替换建议"""
        current_user = MagicMock(
            id=1,
            performance_score=70,  # 表现不佳
            current_load=90  # 负载过高
        )
        
        task = MagicMock(
            id=100,
            required_skills=["Python", "FastAPI"]
        )
        
        with patch.object(service, '_get_available_users', return_value=available_users):
            replacement_suggestions = service.suggest_replacement(
                current_user=current_user,
                task=task
            )
        
        # 应该推荐表现更好或负载更低的人
        assert len(replacement_suggestions) > 0

    def test_balance_team_workload(self, service):
        """测试团队负载平衡"""
        team_members = [
            MagicMock(id=1, current_load=90),  # 过载
            MagicMock(id=2, current_load=40),  # 负载低
            MagicMock(id=3, current_load=60),  # 正常
        ]
        
        rebalance_plan = service.balance_team_workload(team_members, target_load=70)
        
        # 应该建议从过载的人转移任务到负载低的人
        assert len(rebalance_plan) > 0
        assert any(action['from_user_id'] == 1 for action in rebalance_plan)


class TestResourcePrioritization:
    """资源优先级测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ResourceOptimizationService(mock_database_session)

    def test_prioritize_by_skill_match(self, service):
        """测试按技能匹配度排序"""
        candidates = [
            {'user_id': 1, 'skill_match_score': 80, 'availability_score': 60},
            {'user_id': 2, 'skill_match_score': 95, 'availability_score': 50},
            {'user_id': 3, 'skill_match_score': 70, 'availability_score': 80},
        ]
        
        sorted_candidates = service.prioritize_candidates(
            candidates,
            weights={'skill': 0.6, 'availability': 0.4}
        )
        
        # 第一名应该是user_id=2 (技能匹配最高)
        assert sorted_candidates[0]['user_id'] == 2

    def test_prioritize_by_availability(self, service):
        """测试按可用性排序"""
        candidates = [
            {'user_id': 1, 'skill_match_score': 80, 'availability_score': 90},
            {'user_id': 2, 'skill_match_score': 85, 'availability_score': 50},
            {'user_id': 3, 'skill_match_score': 80, 'availability_score': 70},
        ]
        
        sorted_candidates = service.prioritize_candidates(
            candidates,
            weights={'skill': 0.3, 'availability': 0.7}
        )
        
        # 可用性权重高时，user_id=1应该排第一
        assert sorted_candidates[0]['user_id'] == 1


class TestEmergencyResourceScheduling:
    """紧急资源调度测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ResourceOptimizationService(mock_database_session)

    def test_emergency_allocation(self, service):
        """测试紧急任务资源分配"""
        emergency_task = {
            'id': 999,
            'priority': 'urgent',
            'required_skills': ['Python'],
            'required_hours': 40,
            'deadline': date.today() + timedelta(days=2)
        }
        
        team_members = [
            MagicMock(id=1, skills=['Python'], current_load=95, performance_score=90),
            MagicMock(id=2, skills=['Python', 'React'], current_load=70, performance_score=85),
        ]
        
        with patch.object(service, '_get_available_users', return_value=team_members):
            allocation = service.allocate_emergency_resource(emergency_task)
        
        # 即使负载高，也应该分配给表现最好的人
        assert allocation is not None

    def test_reallocate_resources_from_lower_priority(self, service):
        """测试从低优先级项目重新分配资源"""
        high_priority_task = {
            'id': 100,
            'priority': 'critical',
            'required_users': 2
        }
        
        current_allocations = [
            {'user_id': 1, 'task_id': 10, 'priority': 'low'},
            {'user_id': 2, 'task_id': 11, 'priority': 'medium'},
            {'user_id': 3, 'task_id': 12, 'priority': 'low'},
        ]
        
        reallocation = service.reallocate_for_critical_task(
            critical_task=high_priority_task,
            current_allocations=current_allocations
        )
        
        # 应该从低优先级任务中释放资源
        assert len(reallocation['released_users']) >= 2


class TestResourcePrediction:
    """资源需求预测测试"""

    @pytest.fixture
    def service(self, mock_database_session):
        return ResourceOptimizationService(mock_database_session)

    def test_predict_resource_demand(self, service):
        """测试资源需求预测"""
        historical_data = [
            {'month': '2026-01', 'users_count': 10, 'projects_count': 3},
            {'month': '2026-02', 'users_count': 12, 'projects_count': 4},
            {'month': '2026-03', 'users_count': 11, 'projects_count': 3},
        ]
        
        upcoming_projects = 5
        
        predicted_demand = service.predict_resource_demand(
            historical_data=historical_data,
            upcoming_projects=upcoming_projects
        )
        
        assert predicted_demand > 0
        assert predicted_demand >= upcoming_projects * 2  # 至少每个项目2人

    def test_forecast_resource_shortage(self, service):
        """测试资源短缺预警"""
        current_available = 10
        planned_projects = [
            {'required_users': 5, 'start_date': date(2026, 3, 1)},
            {'required_users': 4, 'start_date': date(2026, 3, 1)},
            {'required_users': 3, 'start_date': date(2026, 3, 15)},
        ]
        
        shortage_forecast = service.forecast_resource_shortage(
            current_available=current_available,
            planned_projects=planned_projects
        )
        
        # 3月1日需要9人，3月15日需要12人，应该预警短缺
        assert shortage_forecast['has_shortage'] is True
        assert shortage_forecast['shortage_count'] == 2  # 3月15日缺2人
