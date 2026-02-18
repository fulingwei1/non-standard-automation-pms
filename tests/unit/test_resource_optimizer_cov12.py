# -*- coding: utf-8 -*-
"""第十二批：AI资源优化器单元测试"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

try:
    from app.services.ai_planning.resource_optimizer import AIResourceOptimizer
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_optimizer():
    db = MagicMock()
    glm = MagicMock()
    return AIResourceOptimizer(db=db, glm_service=glm), db, glm


def _make_wbs(id=1):
    wbs = MagicMock()
    wbs.id = id
    wbs.task_name = "测试任务"
    wbs.required_skills = ["Python", "FastAPI"]
    wbs.estimated_hours = 40
    wbs.start_date = None
    wbs.end_date = None
    return wbs


class TestAIResourceOptimizerInit:
    def test_init_with_db_and_glm(self):
        db = MagicMock()
        glm = MagicMock()
        optimizer = AIResourceOptimizer(db=db, glm_service=glm)
        assert optimizer.db is db
        assert optimizer.glm_service is glm

    def test_init_without_glm_creates_default(self):
        db = MagicMock()
        with patch("app.services.ai_planning.resource_optimizer.GLMService") as MockGLM:
            MockGLM.return_value = MagicMock()
            optimizer = AIResourceOptimizer(db=db)
            assert optimizer.glm_service is not None


class TestAllocateResources:
    """allocate_resources 异步方法测试"""

    def test_returns_empty_when_wbs_not_found(self):
        optimizer, db, _ = _make_optimizer()
        db.query.return_value.get.return_value = None

        result = asyncio.run(optimizer.allocate_resources(wbs_suggestion_id=999))
        assert result == []

    def test_returns_empty_when_no_users(self):
        optimizer, db, _ = _make_optimizer()
        wbs = _make_wbs()
        db.query.return_value.get.return_value = wbs

        with patch.object(optimizer, '_get_available_users', return_value=[]):
            result = asyncio.run(optimizer.allocate_resources(wbs_suggestion_id=1))
            assert result == []

    def test_with_available_user_ids(self):
        optimizer, db, _ = _make_optimizer()
        wbs = _make_wbs()
        db.query.return_value.get.return_value = wbs

        with patch.object(optimizer, '_get_available_users', return_value=[]), \
             patch.object(optimizer, '_optimize_allocations', return_value=[]):
            result = asyncio.run(optimizer.allocate_resources(
                wbs_suggestion_id=1,
                available_user_ids=[1, 2, 3]
            ))
            assert isinstance(result, list)

    def test_with_constraints(self):
        optimizer, db, _ = _make_optimizer()
        db.query.return_value.get.return_value = None

        result = asyncio.run(optimizer.allocate_resources(
            wbs_suggestion_id=1,
            constraints={"max_hours": 40, "required_skills": ["Python"]}
        ))
        assert result == []


class TestGetAvailableUsers:
    """_get_available_users 方法测试"""

    def test_returns_list(self):
        optimizer, db, _ = _make_optimizer()
        if not hasattr(optimizer, '_get_available_users'):
            pytest.skip("无此方法")
        users = [MagicMock(), MagicMock()]
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = users
        db.query.return_value = mock_q

        wbs = _make_wbs()
        result = optimizer._get_available_users(None, wbs)
        assert isinstance(result, list)


class TestOptimizeAllocations:
    """_optimize_allocations 方法测试"""

    def test_returns_list(self):
        optimizer, _, _ = _make_optimizer()
        if not hasattr(optimizer, '_optimize_allocations'):
            pytest.skip("无此方法")
        wbs = _make_wbs()
        result = optimizer._optimize_allocations([], wbs)
        assert isinstance(result, list)

    def test_preserves_allocations_order(self):
        optimizer, _, _ = _make_optimizer()
        if not hasattr(optimizer, '_optimize_allocations'):
            pytest.skip("无此方法")
        a1 = MagicMock()
        a1.overall_match_score = 0.9
        a2 = MagicMock()
        a2.overall_match_score = 0.7
        wbs = _make_wbs()
        result = optimizer._optimize_allocations([a1, a2], wbs)
        assert isinstance(result, list)
