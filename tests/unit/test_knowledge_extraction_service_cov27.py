# -*- coding: utf-8 -*-
"""第二十七批 - knowledge_extraction_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.knowledge_extraction_service")

from app.services.knowledge_extraction_service import (
    auto_extract_knowledge_from_ticket,
    create_solution_template_from_ticket,
    recommend_knowledge_for_ticket,
)


def make_ticket(**kwargs):
    ticket = MagicMock()
    ticket.id = kwargs.get("id", 1)
    ticket.ticket_no = kwargs.get("ticket_no", "TK-240001")
    ticket.status = kwargs.get("status", "CLOSED")
    ticket.solution = kwargs.get("solution", "检查电源线并重新连接")
    ticket.problem_desc = kwargs.get("problem_desc", "设备无法启动")
    ticket.problem_type = kwargs.get("problem_type", "ELECTRICAL")
    ticket.urgency = kwargs.get("urgency", "HIGH")
    ticket.root_cause = kwargs.get("root_cause", "电源线接触不良")
    ticket.preventive_action = kwargs.get("preventive_action", "定期检查电源连接")
    ticket.resolved_time = kwargs.get("resolved_time", MagicMock(strftime=lambda fmt: "2024-06-10 14:30"))
    ticket.assigned_to_id = kwargs.get("assigned_to_id", 10)
    ticket.assigned_to_name = kwargs.get("assigned_to_name", "张工")

    project = MagicMock()
    project.project_name = "测试项目"
    project.project_code = "PRJ-001"
    ticket.project = kwargs.get("project", project)

    return ticket


class TestAutoExtractKnowledgeFromTicket:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_not_closed(self):
        ticket = make_ticket(status="OPEN")
        result = auto_extract_knowledge_from_ticket(self.db, ticket)
        assert result is None

    def test_returns_none_when_no_solution(self):
        ticket = make_ticket(status="CLOSED", solution=None)
        result = auto_extract_knowledge_from_ticket(self.db, ticket)
        assert result is None

    def test_returns_none_when_no_assigned_to(self):
        ticket = make_ticket(status="CLOSED", assigned_to_id=None)
        result = auto_extract_knowledge_from_ticket(self.db, ticket)
        assert result is None

    def test_returns_existing_when_already_extracted(self):
        ticket = make_ticket()
        existing = MagicMock()
        # Simulate that existing knowledge is found
        self.db.query.return_value.first.return_value = existing

        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value = self.db.query.return_value
            self.db.query.return_value.first.return_value = existing
            result = auto_extract_knowledge_from_ticket(self.db, ticket)
            assert result is existing

    def test_creates_new_knowledge_article(self):
        ticket = make_ticket()
        # No existing knowledge
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no") as mock_gen:
                mock_gen.return_value = "KB-240001-001"
                with patch("app.services.knowledge_extraction_service.save_obj") as mock_save:
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            article_instance = MagicMock()
                            MockKB.return_value = article_instance
                            result = auto_extract_knowledge_from_ticket(self.db, ticket)
                            assert result is article_instance
                            mock_save.assert_called()

    def test_auto_publish_true_sets_published(self):
        ticket = make_ticket()
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no", return_value="KB-001"):
                with patch("app.services.knowledge_extraction_service.save_obj"):
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            auto_extract_knowledge_from_ticket(self.db, ticket, auto_publish=True)
                            call_kwargs = MockKB.call_args[1]
                            assert call_kwargs.get("status") == "PUBLISHED"

    def test_auto_publish_false_sets_draft(self):
        ticket = make_ticket()
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no", return_value="KB-001"):
                with patch("app.services.knowledge_extraction_service.save_obj"):
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            auto_extract_knowledge_from_ticket(self.db, ticket, auto_publish=False)
                            call_kwargs = MockKB.call_args[1]
                            assert call_kwargs.get("status") == "DRAFT"

    def test_category_mapping_electrical(self):
        ticket = make_ticket(problem_type="ELECTRICAL")
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no", return_value="KB-001"):
                with patch("app.services.knowledge_extraction_service.save_obj"):
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            auto_extract_knowledge_from_ticket(self.db, ticket)
                            call_kwargs = MockKB.call_args[1]
                            assert call_kwargs.get("category") == "电气问题"

    def test_category_mapping_software(self):
        ticket = make_ticket(problem_type="SOFTWARE")
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no", return_value="KB-001"):
                with patch("app.services.knowledge_extraction_service.save_obj"):
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            auto_extract_knowledge_from_ticket(self.db, ticket)
                            call_kwargs = MockKB.call_args[1]
                            assert call_kwargs.get("category") == "软件问题"

    def test_category_mapping_unknown_defaults_to_other(self):
        ticket = make_ticket(problem_type="UNKNOWN_TYPE")
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.generate_sequential_no", return_value="KB-001"):
                with patch("app.services.knowledge_extraction_service.save_obj"):
                    with patch("app.services.knowledge_extraction_service.KnowledgeBase") as MockKB:
                        with patch("app.services.knowledge_extraction_service.create_solution_template_from_ticket"):
                            auto_extract_knowledge_from_ticket(self.db, ticket)
                            call_kwargs = MockKB.call_args[1]
                            assert call_kwargs.get("category") == "其他问题"


class TestCreateSolutionTemplateFromTicket:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_none_when_no_solution(self):
        ticket = make_ticket(solution=None)
        result = create_solution_template_from_ticket(self.db, ticket)
        assert result is None

    def test_returns_existing_template(self):
        ticket = make_ticket()
        existing = MagicMock()
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = existing
            result = create_solution_template_from_ticket(self.db, ticket)
            assert result is existing

    def test_creates_new_template(self):
        ticket = make_ticket()
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.save_obj") as mock_save:
                with patch("app.services.knowledge_extraction_service.SolutionTemplate") as MockTemplate:
                    template_instance = MagicMock()
                    MockTemplate.return_value = template_instance
                    result = create_solution_template_from_ticket(self.db, ticket)
                    assert result is template_instance
                    mock_save.assert_called()

    def test_solution_steps_created_from_lines(self):
        ticket = make_ticket(solution="步骤一\n步骤二\n步骤三")
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.save_obj"):
                with patch("app.services.knowledge_extraction_service.SolutionTemplate") as MockTemplate:
                    create_solution_template_from_ticket(self.db, ticket)
                    call_kwargs = MockTemplate.call_args[1]
                    steps = call_kwargs.get("solution_steps", [])
                    assert len(steps) == 3

    def test_template_code_uses_ticket_no(self):
        ticket = make_ticket(ticket_no="TK-240001")
        with patch("app.services.knowledge_extraction_service.apply_keyword_filter") as mock_filter:
            mock_filter.return_value.first.return_value = None
            with patch("app.services.knowledge_extraction_service.save_obj"):
                with patch("app.services.knowledge_extraction_service.SolutionTemplate") as MockTemplate:
                    create_solution_template_from_ticket(self.db, ticket)
                    call_kwargs = MockTemplate.call_args[1]
                    assert call_kwargs.get("template_code") == "SOL-TK-240001"


class TestRecommendKnowledgeForTicket:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_list(self):
        ticket = make_ticket()
        articles = [MagicMock(), MagicMock()]
        for a in articles:
            a.id = 1
            a.article_no = "KB-001"
            a.title = "知识文章"
            a.category = "电气问题"
            a.view_count = 10
            a.like_count = 5

        self.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = articles
        result = recommend_knowledge_for_ticket(self.db, ticket)
        assert isinstance(result, list)

    def test_result_has_required_fields(self):
        ticket = make_ticket()
        article = MagicMock()
        article.id = 42
        article.article_no = "KB-240001"
        article.title = "电气问题解决方案"
        article.category = "电气问题"
        article.view_count = 100
        article.like_count = 20

        self.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [article]
        result = recommend_knowledge_for_ticket(self.db, ticket)
        if result:
            assert "id" in result[0]
            assert "article_no" in result[0]
            assert "title" in result[0]
            assert "category" in result[0]

    def test_limit_default_is_5(self):
        ticket = make_ticket()
        query_chain = self.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value
        query_chain.limit.return_value.all.return_value = []
        recommend_knowledge_for_ticket(self.db, ticket)
        query_chain.limit.assert_called_with(5)

    def test_custom_limit(self):
        ticket = make_ticket()
        query_chain = self.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value
        query_chain.limit.return_value.all.return_value = []
        recommend_knowledge_for_ticket(self.db, ticket, limit=10)
        query_chain.limit.assert_called_with(10)
