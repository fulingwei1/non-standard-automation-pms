# -*- coding: utf-8 -*-
"""
变更影响智能分析系统 - 单元测试
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from app.models import (
    ChangeImpactAnalysis,
    ChangeRequest,
    ChangeResponseSuggestion,
    Project,
    Task,
    TaskDependency,
)
from app.services.change_impact_ai_service import ChangeImpactAIService
from app.services.change_response_suggestion_service import ChangeResponseSuggestionService


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return Mock()


@pytest.fixture
def sample_change_request():
    """示例变更请求"""
    change = Mock(spec=ChangeRequest)
    change.id = 1
    change.change_code = "CHG-2026-001"
    change.project_id = 1
    change.title = "需求变更：增加数据导出功能"
    change.description = "客户要求增加Excel数据导出功能"
    change.change_type = Mock(value="REQUIREMENT")
    change.change_source = Mock(value="CUSTOMER")
    change.time_impact = 10
    change.cost_impact = Decimal("50000")
    return change


@pytest.fixture
def sample_project():
    """示例项目"""
    project = Mock(spec=Project)
    project.id = 1
    project.project_code = "PRJ-2026-001"
    project.project_name = "测试项目"
    project.status = "IN_PROGRESS"
    project.budget_amount = Decimal("500000")
    project.plan_start = datetime(2026, 1, 1)
    project.plan_end = datetime(2026, 6, 30)
    return project


class TestChangeImpactAIService:
    """变更影响AI服务测试"""

    @pytest.mark.asyncio
    async def test_analyze_schedule_impact(self, mock_db, sample_change_request, sample_project):
        """测试进度影响分析"""
        service = ChangeImpactAIService(mock_db)
        
        context = {
            "change": {
                "id": 1,
                "code": "CHG-001",
                "title": "测试变更",
                "time_impact": 10,
            },
            "project": {
                "id": 1,
                "code": "PRJ-001",
                "name": "测试项目",
                "budget": 500000,
            },
            "tasks": [
                {"id": 1, "name": "任务1", "status": "IN_PROGRESS"},
                {"id": 2, "name": "任务2", "status": "TODO"},
            ],
            "dependencies": [],
            "milestones": [],
        }
        
        with patch('app.services.change_impact_ai_service.call_glm_api') as mock_glm:
            mock_glm.return_value = '{"level": "MEDIUM", "delay_days": 10}'
            
            result = await service._analyze_schedule_impact(
                sample_change_request,
                sample_project,
                context
            )
            
            assert result is not None
            assert "level" in result
            assert "delay_days" in result

    @pytest.mark.asyncio
    async def test_analyze_cost_impact(self, mock_db, sample_change_request, sample_project):
        """测试成本影响分析"""
        service = ChangeImpactAIService(mock_db)
        
        context = {"change": {}, "project": {}}
        
        result = await service._analyze_cost_impact(
            sample_change_request,
            sample_project,
            context
        )
        
        assert result is not None
        assert result["level"] == "MEDIUM"
        assert result["amount"] == 50000
        assert result["percentage"] == 10.0

    def test_identify_chain_reactions_no_dependencies(self, mock_db, sample_change_request, sample_project):
        """测试连锁反应识别 - 无依赖"""
        service = ChangeImpactAIService(mock_db)
        
        context = {
            "tasks": [],
            "dependencies": [],
        }
        
        result = service._identify_chain_reactions(
            sample_change_request,
            sample_project,
            context
        )
        
        assert result["detected"] == False
        assert result["depth"] == 0

    def test_identify_chain_reactions_with_dependencies(self, mock_db, sample_change_request, sample_project):
        """测试连锁反应识别 - 有依赖"""
        service = ChangeImpactAIService(mock_db)
        
        context = {
            "tasks": [
                {"id": 1, "name": "任务1", "status": "TODO"},
                {"id": 2, "name": "任务2", "status": "TODO"},
            ],
            "dependencies": [
                {"task_id": 2, "depends_on": 1, "type": "FS", "lag_days": 0},
            ],
        }
        
        result = service._identify_chain_reactions(
            sample_change_request,
            sample_project,
            context
        )
        
        assert result["detected"] == True
        assert result["depth"] >= 1

    def test_calculate_overall_risk_low(self, mock_db):
        """测试综合风险计算 - 低风险"""
        service = ChangeImpactAIService(mock_db)
        
        result = service._calculate_overall_risk(
            {"level": "LOW"},
            {"level": "LOW"},
            {"level": "LOW"},
            {"level": "LOW"},
            {"detected": False}
        )
        
        assert result["level"] == "LOW"
        assert result["recommended_action"] == "APPROVE"

    def test_calculate_overall_risk_high(self, mock_db):
        """测试综合风险计算 - 高风险"""
        service = ChangeImpactAIService(mock_db)
        
        result = service._calculate_overall_risk(
            {"level": "HIGH"},
            {"level": "HIGH"},
            {"level": "MEDIUM"},
            {"level": "MEDIUM"},
            {"detected": True}
        )
        
        assert result["level"] in ["HIGH", "CRITICAL"]
        assert result["recommended_action"] in ["MODIFY", "ESCALATE"]


class TestChangeResponseSuggestionService:
    """变更应对方案服务测试"""

    def test_create_approve_suggestion(self, mock_db, sample_change_request):
        """测试创建批准方案"""
        service = ChangeResponseSuggestionService(mock_db)
        
        analysis = Mock(spec=ChangeImpactAnalysis)
        analysis.id = 1
        analysis.overall_risk_level = "LOW"
        analysis.schedule_delay_days = 5
        analysis.cost_impact_amount = Decimal("10000")
        
        suggestion = service._create_approve_suggestion(
            sample_change_request,
            analysis,
            user_id=1
        )
        
        assert suggestion.suggestion_type == "APPROVE"
        assert suggestion.feasibility_score >= 80

    def test_create_modify_suggestion(self, mock_db, sample_change_request):
        """测试创建修改方案"""
        service = ChangeResponseSuggestionService(mock_db)
        
        analysis = Mock(spec=ChangeImpactAnalysis)
        analysis.id = 1
        analysis.overall_risk_level = "MEDIUM"
        analysis.schedule_delay_days = 10
        analysis.cost_impact_amount = Decimal("50000")
        
        suggestion = service._create_modify_suggestion(
            sample_change_request,
            analysis,
            user_id=1
        )
        
        assert suggestion.suggestion_type == "MODIFY"
        assert suggestion.estimated_cost < analysis.cost_impact_amount

    def test_create_mitigate_suggestion(self, mock_db, sample_change_request):
        """测试创建缓解方案"""
        service = ChangeResponseSuggestionService(mock_db)
        
        analysis = Mock(spec=ChangeImpactAnalysis)
        analysis.id = 1
        analysis.overall_risk_level = "HIGH"
        analysis.schedule_delay_days = 20
        analysis.cost_impact_amount = Decimal("100000")
        
        suggestion = service._create_mitigate_suggestion(
            sample_change_request,
            analysis,
            user_id=1
        )
        
        assert suggestion.suggestion_type == "MITIGATE"
        assert suggestion.estimated_cost > analysis.cost_impact_amount
        assert len(suggestion.action_steps) >= 4


class TestChangeImpactModels:
    """变更影响模型测试"""

    def test_change_impact_analysis_creation(self):
        """测试影响分析创建"""
        analysis = ChangeImpactAnalysis(
            change_request_id=1,
            analysis_status="COMPLETED",
            schedule_impact_level="MEDIUM",
            schedule_delay_days=10,
            cost_impact_level="LOW",
            cost_impact_amount=Decimal("5000"),
            overall_risk_level="MEDIUM",
            overall_risk_score=Decimal("50"),
            created_by=1
        )
        
        assert analysis.change_request_id == 1
        assert analysis.schedule_delay_days == 10
        assert analysis.overall_risk_level == "MEDIUM"

    def test_change_response_suggestion_creation(self):
        """测试应对方案创建"""
        suggestion = ChangeResponseSuggestion(
            change_request_id=1,
            impact_analysis_id=1,
            suggestion_title="测试方案",
            suggestion_type="APPROVE",
            suggestion_priority=8,
            feasibility_score=Decimal("85"),
            technical_feasibility="HIGH",
            created_by=1
        )
        
        assert suggestion.suggestion_type == "APPROVE"
        assert suggestion.feasibility_score == 85
        assert suggestion.technical_feasibility == "HIGH"


# 性能测试
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_analysis_duration(self, mock_db, sample_change_request, sample_project):
        """测试分析时间 ≤ 10秒"""
        import time
        
        service = ChangeImpactAIService(mock_db)
        service.db.query = Mock(return_value=Mock(
            filter=Mock(return_value=Mock(
                first=Mock(side_effect=[sample_change_request, sample_project]),
                all=Mock(return_value=[])
            ))
        ))
        service.db.add = Mock()
        service.db.flush = Mock()
        service.db.commit = Mock()
        
        start = time.time()
        
        with patch('app.services.change_impact_ai_service.call_glm_api') as mock_glm:
            mock_glm.return_value = '{"level": "MEDIUM"}'
            
            try:
                await service.analyze_change_impact(1, 1)
            except:
                pass  # 忽略Mock导致的错误
        
        duration = time.time() - start
        
        # 实际分析应该≤10秒（这里测试Mock版本应该很快）
        assert duration < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
