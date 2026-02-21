# -*- coding: utf-8 -*-
"""
AI资源优化器单元测试 - 简化版本

目标：
1. 只mock外部依赖（数据库操作、GLMService）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
import json

from app.services.ai_planning.resource_optimizer import AIResourceOptimizer
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation


class TestAIResourceOptimizerSimplified(unittest.TestCase):
    """测试核心功能 - 简化版本"""

    def setUp(self):
        """测试前准备"""
        # Mock数据库会话
        self.db = MagicMock()
        
        # Mock GLM服务
        self.glm_service = MagicMock()
        self.glm_service.model = "glm-4"
        self.glm_service.is_available.return_value = True
        
        # 创建优化器实例
        self.optimizer = AIResourceOptimizer(
            db=self.db,
            glm_service=self.glm_service
        )

    # ========== 初始化测试 ==========
    
    def test_init_with_custom_glm(self):
        """测试使用自定义GLM服务初始化"""
        custom_glm = MagicMock()
        optimizer = AIResourceOptimizer(self.db, custom_glm)
        self.assertEqual(optimizer.db, self.db)
        self.assertEqual(optimizer.glm_service, custom_glm)

    def test_init_with_default_glm(self):
        """测试使用默认GLM服务初始化"""
        with patch('app.services.ai_planning.resource_optimizer.GLMService') as mock_glm_cls:
            optimizer = AIResourceOptimizer(self.db)
            mock_glm_cls.assert_called_once()

    # ========== _get_available_users() 测试 ==========
    
    def test_get_available_users_all(self):
        """测试获取所有可用用户"""
        users = [MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.all.return_value = users
        
        result = self.optimizer._get_available_users(None, MagicMock())
        
        self.assertEqual(result, users)

    def test_get_available_users_with_filter(self):
        """测试使用ID列表过滤用户"""
        users = [MagicMock()]
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = users
        
        result = self.optimizer._get_available_users([1, 2], MagicMock())
        
        self.assertEqual(result, users)

    # ========== _calculate_skill_match() 测试 ==========
    
    def test_calculate_skill_match_no_requirements(self):
        """测试无技能要求"""
        user = MagicMock()
        user.role = "Developer"
        
        wbs = MagicMock()
        wbs.required_skills = None
        
        score = self.optimizer._calculate_skill_match(user, wbs)
        
        self.assertEqual(score, 70.0)

    def test_calculate_skill_match_with_match(self):
        """测试技能匹配"""
        user = MagicMock()
        user.role = "Python Developer"
        
        wbs = MagicMock()
        wbs.required_skills = json.dumps([{"skill": "Python"}])
        
        score = self.optimizer._calculate_skill_match(user, wbs)
        
        self.assertGreater(score, 50.0)

    # ========== _calculate_experience_match() 测试 ==========
    
    def test_calculate_experience_no_history(self):
        """测试无历史经验"""
        user = MagicMock()
        user.id = 1
        
        wbs = MagicMock()
        wbs.task_type = "DEVELOPMENT"
        
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        
        score = self.optimizer._calculate_experience_match(user, wbs)
        
        self.assertEqual(score, 40.0)

    def test_calculate_experience_moderate_tasks(self):
        """测试中等经验"""
        user = MagicMock()
        user.id = 1
        
        wbs = MagicMock()
        wbs.task_type = "TESTING"
        
        self.db.query.return_value.filter.return_value.scalar.return_value = 5
        
        score = self.optimizer._calculate_experience_match(user, wbs)
        
        self.assertEqual(score, 80.0)

    # ========== _calculate_availability() 测试 ==========
    
    def test_calculate_availability_idle(self):
        """测试空闲用户"""
        user = MagicMock()
        user.id = 1
        
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        score = self.optimizer._calculate_availability(user, MagicMock())
        
        self.assertEqual(score, 100.0)

    def test_calculate_availability_busy(self):
        """测试繁忙用户"""
        user = MagicMock()
        user.id = 1
        
        tasks = [MagicMock(), MagicMock(), MagicMock()]
        self.db.query.return_value.filter.return_value.all.return_value = tasks
        
        score = self.optimizer._calculate_availability(user, MagicMock())
        
        self.assertEqual(score, 40.0)

    # ========== _get_current_workload() 测试 ==========
    
    def test_get_current_workload_no_tasks(self):
        """测试无任务"""
        user = MagicMock()
        user.id = 1
        
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        workload = self.optimizer._get_current_workload(user)
        
        self.assertEqual(workload, 0.0)

    def test_get_current_workload_capped_at_100(self):
        """测试工作负载上限100%"""
        user = MagicMock()
        user.id = 1
        
        tasks = [MagicMock() for _ in range(10)]
        self.db.query.return_value.filter.return_value.all.return_value = tasks
        
        workload = self.optimizer._get_current_workload(user)
        
        self.assertEqual(workload, 100.0)

    # ========== _calculate_performance_score() 测试 ==========
    
    def test_calculate_performance_no_history(self):
        """测试无历史绩效"""
        user = MagicMock()
        user.id = 1
        
        self.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        score = self.optimizer._calculate_performance_score(user, MagicMock())
        
        self.assertEqual(score, 70.0)

    def test_calculate_performance_all_on_time(self):
        """测试全部按时完成"""
        user = MagicMock()
        user.id = 1
        
        task1 = MagicMock()
        task1.planned_end_date = date(2025, 1, 10)
        task1.actual_end_date = date(2025, 1, 9)
        
        task2 = MagicMock()
        task2.planned_end_date = date(2025, 1, 20)
        task2.actual_end_date = date(2025, 1, 20)
        
        self.db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task1, task2]
        
        score = self.optimizer._calculate_performance_score(user, MagicMock())
        
        self.assertEqual(score, 100.0)

    # ========== _get_hourly_rate() 测试 ==========
    
    def test_get_hourly_rate_senior(self):
        """测试高级角色费率"""
        user = MagicMock()
        user.role = "Senior Developer"
        
        rate = self.optimizer._get_hourly_rate(user)
        
        self.assertEqual(rate, 200.0)

    def test_get_hourly_rate_default(self):
        """测试默认费率"""
        user = MagicMock()
        user.role = "Developer"
        
        rate = self.optimizer._get_hourly_rate(user)
        
        self.assertEqual(rate, 120.0)

    # ========== _calculate_cost_efficiency() 测试 ==========
    
    def test_calculate_cost_efficiency_normal(self):
        """测试正常成本效益"""
        score = self.optimizer._calculate_cost_efficiency(80.0, 100.0)
        
        self.assertEqual(score, 80.0)

    def test_calculate_cost_efficiency_low_rate(self):
        """测试低费率（被限制在100）"""
        score = self.optimizer._calculate_cost_efficiency(80.0, 50.0)
        
        self.assertEqual(score, 100.0)

    # ========== _generate_recommendation_reason() 测试 ==========
    
    def test_generate_recommendation_reason_excellent(self):
        """测试优秀匹配推荐理由"""
        reason = self.optimizer._generate_recommendation_reason(
            MagicMock(), MagicMock(),
            skill_match=85.0,
            experience_match=90.0,
            availability=85.0,
            performance=90.0
        )
        
        self.assertIn("技能高度匹配", reason)
        self.assertIn("拥有丰富的相关经验", reason)

    def test_generate_recommendation_reason_default(self):
        """测试默认推荐理由"""
        reason = self.optimizer._generate_recommendation_reason(
            MagicMock(), MagicMock(),
            skill_match=50.0,
            experience_match=50.0,
            availability=50.0,
            performance=50.0
        )
        
        self.assertIn("综合评估基本符合要求", reason)

    # ========== _analyze_strengths() 测试 ==========
    
    def test_analyze_strengths_high_skill(self):
        """测试高技能优势"""
        strengths = self.optimizer._analyze_strengths(
            MagicMock(), MagicMock(),
            skill_match=85.0,
            performance=70.0
        )
        
        self.assertEqual(len(strengths), 1)
        self.assertEqual(strengths[0]['category'], "技能")

    def test_analyze_strengths_none(self):
        """测试无优势"""
        strengths = self.optimizer._analyze_strengths(
            MagicMock(), MagicMock(),
            skill_match=60.0,
            performance=60.0
        )
        
        self.assertEqual(len(strengths), 0)

    # ========== _analyze_weaknesses() 测试 ==========
    
    def test_analyze_weaknesses_low_skill(self):
        """测试低技能劣势"""
        weaknesses = self.optimizer._analyze_weaknesses(
            MagicMock(), MagicMock(),
            skill_match=50.0,
            availability=80.0
        )
        
        self.assertEqual(len(weaknesses), 1)
        self.assertEqual(weaknesses[0]['category'], "技能")

    def test_analyze_weaknesses_none(self):
        """测试无劣势"""
        weaknesses = self.optimizer._analyze_weaknesses(
            MagicMock(), MagicMock(),
            skill_match=70.0,
            availability=70.0
        )
        
        self.assertEqual(len(weaknesses), 0)

    # ========== _optimize_allocations() 测试 ==========
    
    def test_optimize_allocations_empty(self):
        """测试空分配列表"""
        result = self.optimizer._optimize_allocations([], MagicMock())
        
        self.assertEqual(result, [])

    def test_optimize_allocations_single(self):
        """测试单个分配"""
        alloc = MagicMock(spec=AIResourceAllocation)
        
        result = self.optimizer._optimize_allocations([alloc], MagicMock())
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].allocation_type, "PRIMARY")

    def test_optimize_allocations_max_five(self):
        """测试最多5个推荐"""
        allocations = [MagicMock(spec=AIResourceAllocation) for _ in range(10)]
        
        result = self.optimizer._optimize_allocations(allocations, MagicMock())
        
        self.assertEqual(len(result), 5)


if __name__ == "__main__":
    unittest.main()
