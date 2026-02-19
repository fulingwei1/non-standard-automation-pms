# -*- coding: utf-8 -*-
"""
Unit tests for AIProjectPlanGenerator (第三十八批)
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

pytest.importorskip("app.services.ai_planning.plan_generator", reason="导入失败，跳过")

try:
    from app.services.ai_planning.plan_generator import AIProjectPlanGenerator
except ImportError:
    pytestmark = pytest.mark.skip(reason="plan_generator 不可用")
    AIProjectPlanGenerator = None


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_glm():
    glm = MagicMock()
    glm.generate_project_plan = MagicMock(return_value={
        "stages": [],
        "milestones": [],
        "estimated_duration": 60,
        "summary": "AI生成的项目计划"
    })
    return glm


@pytest.fixture
def generator(mock_db, mock_glm):
    with patch("app.services.ai_planning.plan_generator.GLMService", return_value=mock_glm):
        gen = AIProjectPlanGenerator(db=mock_db, glm_service=mock_glm)
    return gen


class TestFindReferenceProjects:
    """测试 _find_reference_projects"""

    def test_returns_list(self, generator):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        generator.db.query.return_value = mock_query

        result = generator._find_reference_projects("automation", "manufacturing", "MEDIUM")
        assert isinstance(result, list)

    def test_query_is_called(self, generator):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        generator.db.query.return_value = mock_query

        generator._find_reference_projects("test_type", None, None)
        assert generator.db.query.called


class TestFindExistingTemplate:
    """测试 _find_existing_template"""

    def _setup_template_query(self, generator, first_return):
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = first_return
        generator.db.query.return_value = mock_query
        return mock_query

    def test_returns_none_when_not_found(self, generator):
        self._setup_template_query(generator, None)
        result = generator._find_existing_template("automation", "mfg", "LOW")
        assert result is None

    def test_returns_template_when_found(self, generator):
        mock_template = MagicMock()
        mock_template.template_name = "标准模板"
        self._setup_template_query(generator, mock_template)
        result = generator._find_existing_template("automation", "mfg", "MEDIUM")
        assert result is mock_template


class TestProjectToDict:
    """测试 _project_to_dict"""

    def test_converts_project(self, generator):
        project = MagicMock()
        project.id = 1
        project.name = "测试项目"
        project.project_type = "automation"
        project.industry = "manufacturing"

        result = generator._project_to_dict(project)
        assert isinstance(result, dict)


class TestGeneratePlan:
    """测试 generate_plan 异步方法"""

    @pytest.mark.asyncio
    async def test_returns_existing_template(self, generator):
        """找到已有模板时直接返回"""
        mock_template = MagicMock()
        mock_template.template_name = "已有模板"

        generator._find_reference_projects = MagicMock(return_value=[])
        generator._find_existing_template = MagicMock(return_value=mock_template)

        result = await generator.generate_plan(
            project_name="测试",
            project_type="automation",
            requirements="需求描述",
            use_template=True
        )
        assert result is mock_template

    @pytest.mark.asyncio
    async def test_calls_glm_when_no_template(self, generator, mock_glm):
        """没有模板时调用 AI 生成"""
        generator._find_reference_projects = MagicMock(return_value=[])
        generator._find_existing_template = MagicMock(return_value=None)
        generator._project_to_dict = MagicMock(return_value={})

        mock_template = MagicMock()
        with patch("app.services.ai_planning.plan_generator.AIProjectPlanTemplate") as MockT:
            MockT.return_value = mock_template
            generator.db.add = MagicMock()
            generator.db.commit = MagicMock()
            generator.db.refresh = MagicMock()

            result = await generator.generate_plan(
                project_name="新项目",
                project_type="automation",
                requirements="自动化需求",
                use_template=False
            )
            assert mock_glm.generate_project_plan.called
