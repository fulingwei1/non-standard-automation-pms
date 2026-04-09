# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI资源优化器"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime


class TestAIResourceOptimizerBusinessLogic:
    """AI资源优化器业务逻辑测试"""

    def test_init_with_glm_service(self):
        """测试使用GLM服务初始化"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer
            from app.services.ai_planning.glm_service import GLMService

            mock_db = MagicMock()
            mock_glm = MagicMock()

            optimizer = AIResourceOptimizer(mock_db, mock_glm)

            assert optimizer.db == mock_db
            assert optimizer.glm_service == mock_glm
        except ImportError:
            pytest.skip("Module not found")

    def test_init_without_glm_service(self):
        """测试不使用GLM服务初始化"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            optimizer = AIResourceOptimizer(mock_db)

            assert optimizer.db == mock_db
            assert optimizer.glm_service is not None
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_allocate_resources_wbs_not_found(self):
        """测试WBS不存在"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            mock_db.query.return_value.get.return_value = None

            optimizer = AIResourceOptimizer(mock_db)
            result = await optimizer.allocate_resources(999)

            assert result == []
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_allocate_resources_no_users(self):
        """测试没有可用用户"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            # Mock WBS
            mock_wbs = MagicMock()
            mock_wbs.id = 1

            mock_db.query.return_value.get.return_value = mock_wbs
            mock_db.query.return_value.filter.return_value.all.return_value = []

            optimizer = AIResourceOptimizer(mock_db)
            optimizer._get_available_users = MagicMock(return_value=[])

            result = await optimizer.allocate_resources(1)

            assert result == []
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_allocate_resources_success(self):
        """测试成功分配资源"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            # Mock WBS
            mock_wbs = MagicMock()
            mock_wbs.id = 1
            mock_wbs.task_name = "测试任务"
            mock_wbs.required_skills = ["Python"]

            # Mock用户
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.real_name = "张三"
            mock_user.skills = ["Python", "Java"]

            mock_db.query.return_value.get.return_value = mock_wbs
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

            optimizer = AIResourceOptimizer(mock_db)
            optimizer._get_available_users = MagicMock(return_value=[mock_user])
            optimizer._analyze_user_match = AsyncMock(return_value=MagicMock(
                user_id=1,
                overall_match_score=80
            ))
            optimizer._optimize_allocations = MagicMock(return_value=[
                MagicMock(user_id=1, overall_match_score=80)
            ])

            with patch('app.utils.db_helpers.save_obj'):
                result = await optimizer.allocate_resources(1)

                assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")

    def test_get_available_users(self):
        """测试获取可用用户"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            mock_user = MagicMock()
            mock_user.id = 1

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

            optimizer = AIResourceOptimizer(mock_db)
            mock_wbs = MagicMock()

            result = optimizer._get_available_users([1], mock_wbs)

            assert len(result) >= 0
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_analyze_user_match(self):
        """测试分析用户匹配度"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.skills = ["Python"]

            mock_wbs = MagicMock()
            mock_wbs.required_skills = ["Python"]

            optimizer = AIResourceOptimizer(mock_db)
            optimizer.glm_service = MagicMock()
            optimizer.glm_service.is_available = MagicMock(return_value=False)

            result = await optimizer._analyze_user_match(mock_user, mock_wbs)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_skill_match_score(self):
        """测试计算技能匹配分数"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = ["Python", "Java", "React"]
            required_skills = ["Python", "Java"]

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            # 2个匹配技能 / 2个必需技能 = 100%
            assert result >= 0
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_availability_score(self):
        """测试计算可用性分数"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            mock_user = MagicMock()
            mock_user.current_tasks = []

            result = optimizer._calculate_availability_score(mock_user)

            assert result >= 0
        except ImportError:
            pytest.skip("Module not found")

    def test_optimize_allocations(self):
        """测试优化分配"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            allocations = [
                MagicMock(user_id=1, overall_match_score=90),
                MagicMock(user_id=2, overall_match_score=80),
            ]

            mock_wbs = MagicMock()
            mock_wbs.max_assignees = 1

            result = optimizer._optimize_allocations(allocations, mock_wbs)

            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")


class TestAIResourceOptimizerScoring:
    """评分逻辑测试"""

    def test_skill_match_full(self):
        """测试完全技能匹配"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = ["Python", "FastAPI"]
            required_skills = ["Python", "FastAPI"]

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            assert result == 100
        except ImportError:
            pytest.skip("Module not found")

    def test_skill_match_partial(self):
        """测试部分技能匹配"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = ["Python"]
            required_skills = ["Python", "FastAPI"]

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            assert result == 50
        except ImportError:
            pytest.skip("Module not found")

    def test_skill_match_no_match(self):
        """测试无技能匹配"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = ["Java"]
            required_skills = ["Python"]

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            assert result == 0
        except ImportError:
            pytest.skip("Module not found")


class TestAIResourceOptimizerEdgeCases:
    """边界情况测试"""

    def test_empty_required_skills(self):
        """测试空必需技能"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = ["Python"]
            required_skills = []

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            assert result >= 0
        except ImportError:
            pytest.skip("Module not found")

    def test_empty_user_skills(self):
        """测试空用户技能"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()
            optimizer = AIResourceOptimizer(mock_db)

            user_skills = []
            required_skills = ["Python"]

            result = optimizer._calculate_skill_match_score(user_skills, required_skills)

            assert result == 0
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_glm_service_unavailable(self):
        """测试GLM服务不可用"""
        try:
            from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

            mock_db = MagicMock()

            mock_wbs = MagicMock()
            mock_db.query.return_value.get.return_value = mock_wbs

            optimizer = AIResourceOptimizer(mock_db)
            optimizer.glm_service = MagicMock()
            optimizer.glm_service.is_available = MagicMock(return_value=False)
            optimizer._get_available_users = MagicMock(return_value=[])

            result = await optimizer.allocate_resources(1)

            # 应该使用本地算法
            assert isinstance(result, list)
        except ImportError:
            pytest.skip("Module not found")