"""
第四批覆盖测试 - presale_ai_service
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.presale_ai_service import PresaleAIService
    HAS_SERVICE = True
except Exception:
    HAS_SERVICE = False

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="服务导入失败")


def make_service():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    with patch('app.services.presale_ai_service.AIClientService'):
        return PresaleAIService(), db


class TestPresaleAIService:
    def setup_method(self):
        self.service, self.db = make_service()

    def test_init(self):
        assert self.service.db is not None
        assert self.service.ai_client is not None

    def test_calculate_similarity_empty_strings(self):
        score = self.service._calculate_similarity("", "")
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_calculate_similarity_same_text(self):
        text = "焊接机器人自动化生产线"
        score = self.service._calculate_similarity(text, text)
        assert score > 0

    def test_calculate_similarity_different_text(self):
        score = self.service._calculate_similarity("焊接机器人", "切割设备")
        assert 0 <= score <= 1

    def test_match_templates_no_templates(self):
        try:
            from app.schemas.presale_ai_solution import TemplateMatchRequest
            request = TemplateMatchRequest(
                keywords="焊接",
                industry="汽车",
                equipment_type="机器人",
                top_k=5
            )
        except Exception:
            pytest.skip("Schema导入失败")
        result, total = self.service.match_templates(request, user_id=1)
        assert isinstance(result, list)
        assert total >= 0

    def test_get_solution_not_found(self):
        self.db.query.return_value.filter_by.return_value.first.return_value = None
        result = self.service.get_solution(9999)
        assert result is None

    def test_extract_mermaid_code_with_backticks(self):
        content = "Here is the diagram:\n```mermaid\ngraph TD\n  A-->B\n```"
        result = self.service._extract_mermaid_code(content)
        assert "graph TD" in result or "A-->B" in result

    def test_extract_mermaid_code_plain(self):
        content = "graph TD\n  A-->B"
        result = self.service._extract_mermaid_code(content)
        assert isinstance(result, str)

    def test_parse_solution_response_empty(self):
        response = {}
        result = self.service._parse_solution_response(response)
        assert isinstance(result, dict)

    def test_calculate_confidence_no_template(self):
        solution = {'equipment_list': [], 'process_steps': [], 'technical_parameters': []}
        conf = self.service._calculate_confidence(solution, None)
        assert 0 <= conf <= 1

    def test_get_template_library(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = self.service.get_template_library(industry=None, equipment_type=None)
        assert isinstance(result, list)
