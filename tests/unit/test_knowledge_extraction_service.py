# -*- coding: utf-8 -*-
"""
knowledge_extraction_service 单元测试

测试知识提取服务的各个方法：
- 工单知识自动提取
- 解决方案模板创建
- 知识推荐
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.knowledge_extraction_service import (
    auto_extract_knowledge_from_ticket,
    create_solution_template_from_ticket,
    recommend_knowledge_for_ticket,
)


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_ticket(
    ticket_no="ST250712001",
    status="CLOSED",
    problem_type="SOFTWARE",
    problem_desc="测试问题描述",
    solution="解决方案内容",
    root_cause="根本原因",
    preventive_action="预防措施",
    urgency="HIGH",
    assigned_to_id=1,
    assigned_to_name="测试工程师",
    resolved_time=None,
    project=None,
):
    """创建模拟的服务工单"""
    mock = MagicMock()
    mock.ticket_no = ticket_no
    mock.status = status
    mock.problem_type = problem_type
    mock.problem_desc = problem_desc
    mock.solution = solution
    mock.root_cause = root_cause
    mock.preventive_action = preventive_action
    mock.urgency = urgency
    mock.assigned_to_id = assigned_to_id
    mock.assigned_to_name = assigned_to_name
    mock.resolved_time = resolved_time or datetime.now()
    mock.project = project
    return mock


def create_mock_project(project_name="测试项目", project_code="PJ250712001"):
    """创建模拟的项目"""
    mock = MagicMock()
    mock.project_name = project_name
    mock.project_code = project_code
    return mock


def create_mock_knowledge_article(
    article_id=1,
    article_no="KB250712-001",
    title="测试文章",
    category="软件问题",
    tags=None,
    status="PUBLISHED",
    view_count=10,
    like_count=5,
):
    """创建模拟的知识库文章"""
    mock = MagicMock()
    mock.id = article_id
    mock.article_no = article_no
    mock.title = title
    mock.category = category
    mock.tags = tags or ["SOFTWARE"]
    mock.status = status
    mock.view_count = view_count
    mock.like_count = like_count
    mock.created_at = datetime.now()
    return mock


@pytest.mark.unit
class TestAutoExtractKnowledge:
    """测试 auto_extract_knowledge_from_ticket 函数"""

    def test_returns_none_for_non_closed_ticket(self):
        """测试未关闭工单返回None"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(status="OPEN")

        result = auto_extract_knowledge_from_ticket(db, ticket)

        assert result is None

    def test_returns_none_for_ticket_without_solution(self):
        """测试无解决方案工单返回None"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(solution=None)

        result = auto_extract_knowledge_from_ticket(db, ticket)

        assert result is None

    def test_returns_existing_article_if_already_extracted(self):
        """测试已提取过则返回已有文章"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        existing_article = create_mock_knowledge_article()
        db.query.return_value.filter.return_value.first.return_value = existing_article

        result = auto_extract_knowledge_from_ticket(db, ticket)

        assert result == existing_article

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_creates_article_with_correct_structure(self, mock_template, mock_gen_no):
        """测试创建正确结构的文章"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        result = auto_extract_knowledge_from_ticket(db, ticket)

        # 验证调用了db.add
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_builds_content_with_all_fields(self, mock_template, mock_gen_no):
        """测试内容包含所有字段"""
        db = create_mock_db_session()
        project = create_mock_project()
        ticket = create_mock_ticket(
        problem_desc="详细问题描述",
        root_cause="根本原因分析",
        solution="解决步骤",
        preventive_action="预防措施",
        project=project,
        )
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        result = auto_extract_knowledge_from_ticket(db, ticket)

        # 获取创建的文章对象
        created_article = db.add.call_args[0][0]
        assert "问题描述" in created_article.content
        assert "详细问题描述" in created_article.content
        assert "根本原因" in created_article.content
        assert "解决方案" in created_article.content
        assert "预防措施" in created_article.content

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_maps_problem_type_to_category(self, mock_template, mock_gen_no):
        """测试问题类型映射到分类"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(problem_type="MECHANICAL")
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        result = auto_extract_knowledge_from_ticket(db, ticket)

        created_article = db.add.call_args[0][0]
        assert created_article.category == "机械问题"

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_sets_published_status_when_auto_publish(self, mock_template, mock_gen_no):
        """测试自动发布时设置为已发布状态"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        result = auto_extract_knowledge_from_ticket(db, ticket, auto_publish=True)

        created_article = db.add.call_args[0][0]
        assert created_article.status == "PUBLISHED"

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_sets_draft_status_when_not_auto_publish(self, mock_template, mock_gen_no):
        """测试不自动发布时设置为草稿状态"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        result = auto_extract_knowledge_from_ticket(db, ticket, auto_publish=False)

        created_article = db.add.call_args[0][0]
        assert created_article.status == "DRAFT"


@pytest.mark.unit
class TestCreateSolutionTemplate:
    """测试 create_solution_template_from_ticket 函数"""

    def test_returns_none_without_solution(self):
        """测试无解决方案返回None"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(solution=None)

        result = create_solution_template_from_ticket(db, ticket)

        assert result is None

    def test_returns_existing_template_if_exists(self):
        """测试已存在模板则返回已有模板"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        existing_template = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing_template

        result = create_solution_template_from_ticket(db, ticket)

        assert result == existing_template

    def test_creates_template_with_correct_code(self):
        """测试创建正确编码的模板"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(ticket_no="ST250712001")
        db.query.return_value.filter.return_value.first.return_value = None

        result = create_solution_template_from_ticket(db, ticket)

        created_template = db.add.call_args[0][0]
        assert created_template.template_code == "SOL-ST250712001"

    def test_parses_solution_steps(self):
        """测试解析解决方案步骤"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(solution="步骤1\n步骤2\n步骤3")
        db.query.return_value.filter.return_value.first.return_value = None

        result = create_solution_template_from_ticket(db, ticket)

        created_template = db.add.call_args[0][0]
        assert len(created_template.solution_steps) == 3
        assert created_template.solution_steps[0]["step"] == 1
        assert created_template.solution_steps[0]["description"] == "步骤1"

    def test_skips_empty_lines_and_comments(self):
        """测试跳过空行和注释"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(solution="步骤1\n\n# 这是注释\n步骤2")
        db.query.return_value.filter.return_value.first.return_value = None

        result = create_solution_template_from_ticket(db, ticket)

        created_template = db.add.call_args[0][0]
        assert len(created_template.solution_steps) == 2

    def test_uses_ticket_urgency_as_severity(self):
        """测试使用工单紧急程度作为严重性"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(urgency="HIGH")
        db.query.return_value.filter.return_value.first.return_value = None

        result = create_solution_template_from_ticket(db, ticket)

        created_template = db.add.call_args[0][0]
        assert created_template.severity == "HIGH"

    def test_uses_default_values_when_missing(self):
        """测试缺少值时使用默认值"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(
        assigned_to_id=None,
        assigned_to_name=None,
        preventive_action=None,
        )
        db.query.return_value.filter.return_value.first.return_value = None

        result = create_solution_template_from_ticket(db, ticket)

        created_template = db.add.call_args[0][0]
        assert created_template.created_by == 1
        assert created_template.created_by_name == "系统"
        assert "预防措施" in created_template.precautions


@pytest.mark.unit
class TestRecommendKnowledge:
    """测试 recommend_knowledge_for_ticket 函数"""

    def test_returns_empty_list_when_no_articles(self):
        """测试无文章时返回空列表"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = recommend_knowledge_for_ticket(db, ticket)

        assert result == []

    def test_returns_recommended_articles(self):
        """测试返回推荐文章"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(problem_type="SOFTWARE")
        articles = [
        create_mock_knowledge_article(article_id=1, title="文章1"),
        create_mock_knowledge_article(article_id=2, title="文章2"),
        ]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = articles

        result = recommend_knowledge_for_ticket(db, ticket)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["title"] == "文章1"

    def test_respects_limit_parameter(self):
        """测试遵守限制参数"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = recommend_knowledge_for_ticket(db, ticket, limit=3)

        mock_query.limit.assert_called_with(3)

    def test_returns_article_details(self):
        """测试返回文章详情"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        article = create_mock_knowledge_article(
        article_id=1,
        article_no="KB250712-001",
        title="测试文章",
        category="软件问题",
        view_count=100,
        like_count=50,
        )
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        article
        ]

        result = recommend_knowledge_for_ticket(db, ticket)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["article_no"] == "KB250712-001"
        assert result[0]["title"] == "测试文章"
        assert result[0]["category"] == "软件问题"
        assert result[0]["view_count"] == 100
        assert result[0]["like_count"] == 50

    def test_filters_by_published_status(self):
        """测试过滤已发布状态"""
        db = create_mock_db_session()
        ticket = create_mock_ticket()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = recommend_knowledge_for_ticket(db, ticket)

        # 验证调用了filter方法（用于status过滤）
        assert mock_query.filter.called


@pytest.mark.unit
class TestCategoryMapping:
    """测试分类映射"""

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_maps_software_to_category(self, mock_template, mock_gen_no):
        """测试SOFTWARE映射到软件问题"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(problem_type="SOFTWARE")
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        auto_extract_knowledge_from_ticket(db, ticket)

        created_article = db.add.call_args[0][0]
        assert created_article.category == "软件问题"

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_maps_electrical_to_category(self, mock_template, mock_gen_no):
        """测试ELECTRICAL映射到电气问题"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(problem_type="ELECTRICAL")
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        auto_extract_knowledge_from_ticket(db, ticket)

        created_article = db.add.call_args[0][0]
        assert created_article.category == "电气问题"

    @patch("app.services.knowledge_extraction_service.generate_sequential_no")
    @patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket")
    def test_maps_unknown_to_other(self, mock_template, mock_gen_no):
        """测试未知类型映射到其他问题"""
        db = create_mock_db_session()
        ticket = create_mock_ticket(problem_type="UNKNOWN")
        db.query.return_value.filter.return_value.first.return_value = None
        mock_gen_no.return_value = "KB250712-001"

        auto_extract_knowledge_from_ticket(db, ticket)

        created_article = db.add.call_args[0][0]
        assert created_article.category == "其他问题"
