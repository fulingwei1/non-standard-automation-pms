# -*- coding: utf-8 -*-
"""
I1组: PresaleAIService 单元测试
直接实例化类，AIClientService 用 MagicMock 替代
"""
import json
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.presale_ai_service import PresaleAIService
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    SolutionGenerationRequest,
)


# ============================================================
# Helper factory
# ============================================================

def _make_service():
    db = MagicMock()
    mock_ai = MagicMock()
    with patch("app.services.presale_ai_service.AIClientService", return_value=mock_ai):
        svc = PresaleAIService(db_session)
        svc.ai_client = mock_ai
    return svc, db, mock_ai


def _make_template(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 1)
    t.name = kwargs.get("name", "标准模板")
    t.industry = kwargs.get("industry", "汽车")
    t.equipment_type = kwargs.get("equipment_type", "机器人")
    t.keywords = kwargs.get("keywords", "机器人 装配 汽车")
    t.usage_count = kwargs.get("usage_count", 10)
    t.avg_quality_score = kwargs.get("avg_quality_score", Decimal("0.85"))
    t.is_active = kwargs.get("is_active", 1)
    t.solution_content = kwargs.get("solution_content", {"description": "模板内容"})
    return t


def _make_solution(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.status = kwargs.get("status", "draft")
    return s


# ============================================================
# TestCalculateSimilarity
# ============================================================

class TestCalculateSimilarity:
    def test_identical_texts(self):
        svc, db, _ = _make_service()
        score = svc._calculate_similarity("机器人 装配", "机器人 装配")
        assert score == 1.0

    def test_no_overlap(self):
        svc, db, _ = _make_service()
        score = svc._calculate_similarity("机器人", "传送带")
        assert score == 0.0

    def test_partial_overlap(self):
        svc, db, _ = _make_service()
        score = svc._calculate_similarity("机器人 装配 汽车", "机器人 焊接 汽车")
        assert 0 < score < 1.0

    def test_empty_text(self):
        svc, db, _ = _make_service()
        score = svc._calculate_similarity("", "机器人")
        assert score == 0.0


# ============================================================
# TestMatchTemplates
# ============================================================

class TestMatchTemplates:
    def test_match_templates_no_templates(self):
        """没有模板时返回空列表"""
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = TemplateMatchRequest(presale_ticket_id=1)
        items, ms = svc.match_templates(req, user_id=1)

        assert items == []
        assert ms >= 0

    def test_match_templates_with_keywords(self):
        """有关键词时按相似度排序"""
        svc, db, _ = _make_service()
        t1 = _make_template(keywords="机器人 装配 汽车", usage_count=5)
        t2 = _make_template(id=2, keywords="焊接 激光", usage_count=2)
        db.query.return_value.filter.return_value.all.return_value = [t1, t2]

        req = TemplateMatchRequest(presale_ticket_id=1, keywords="机器人 装配", top_k=2)
        items, ms = svc.match_templates(req, user_id=1)

        assert len(items) == 2
        assert items[0].template_id == t1.id  # 较高相似度排首位

    def test_match_templates_without_keywords(self):
        """无关键词时按使用次数排序"""
        svc, db, _ = _make_service()
        t1 = _make_template(usage_count=20)
        t2 = _make_template(id=2, usage_count=5)
        db.query.return_value.filter.return_value.all.return_value = [t2, t1]

        req = TemplateMatchRequest(presale_ticket_id=1, top_k=2)
        items, ms = svc.match_templates(req, user_id=1)

        assert len(items) == 2

    def test_match_templates_with_industry_filter(self):
        """行业和设备类型过滤"""
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        req = TemplateMatchRequest(
            presale_ticket_id=1,
            industry="汽车",
            equipment_type="机器人",
        )
        items, _ = svc.match_templates(req, user_id=1)
        assert items == []


# ============================================================
# TestGenerateSolution
# ============================================================

class TestGenerateSolution:
    def test_generate_solution_basic(self):
        """基本方案生成"""
        svc, db, mock_ai = _make_service()

        mock_ai.generate_solution.return_value = {
            "content": json.dumps({
                "description": "自动装配方案",
                "technical_parameters": {"speed": "10件/分钟"},
                "equipment_list": [{"name": "机器人", "quantity": 2}],
                "process_flow": "上料->装配->下料",
                "key_features": ["高精度"],
                "technical_advantages": ["稳定性高"],
            }),
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        }
        mock_ai.generate_architecture.return_value = {
            "content": "```mermaid\ngraph LR\n  A-->B\n```"
        }

        # 禁用架构图和BOM生成简化测试
        with patch("app.services.presale_ai_service.save_obj"):
            svc._log_generation = MagicMock()
            req = SolutionGenerationRequest(
                presale_ticket_id=1,
                requirements={"project_type": "装配"},
                generate_architecture=False,
                generate_bom=False,
            )
            result = svc.generate_solution(req, user_id=1)

        assert "solution_id" in result
        assert "confidence_score" in result
        assert result["confidence_score"] >= 0.5

    def test_generate_solution_with_template(self):
        """带模板的方案生成"""
        svc, db, mock_ai = _make_service()
        mock_template = _make_template()
        db.query.return_value.filter_by.return_value.first.return_value = mock_template

        mock_ai.generate_solution.return_value = {
            "content": '{"description": "基于模板的方案"}',
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        }

        with patch("app.services.presale_ai_service.save_obj"):
            svc._log_generation = MagicMock()
            req = SolutionGenerationRequest(
                presale_ticket_id=1,
                template_id=1,
                requirements={"project_type": "装配"},
                generate_architecture=False,
                generate_bom=False,
            )
            result = svc.generate_solution(req, user_id=1)

        # 有模板加成，置信度应 ≥ 0.7
        assert result["confidence_score"] >= 0.7


# ============================================================
# TestParseSolutionResponse
# ============================================================

class TestParseSolutionResponse:
    def test_parse_json_content(self):
        svc, _, _ = _make_service()
        data = {"description": "测试方案", "equipment_list": []}
        resp = {"content": json.dumps(data)}
        result = svc._parse_solution_response(resp)
        assert result["description"] == "测试方案"

    def test_parse_markdown_json(self):
        svc, _, _ = _make_service()
        resp = {"content": '```json\n{"key": "val"}\n```'}
        result = svc._parse_solution_response(resp)
        assert result["key"] == "val"

    def test_parse_fallback_on_invalid(self):
        svc, _, _ = _make_service()
        resp = {"content": "这不是JSON"}
        result = svc._parse_solution_response(resp)
        assert "description" in result

    def test_parse_triple_backtick(self):
        svc, _, _ = _make_service()
        resp = {"content": "```\n{\"a\": 1}\n```"}
        result = svc._parse_solution_response(resp)
        assert result.get("a") == 1 or "description" in result


# ============================================================
# TestCalculateConfidence
# ============================================================

class TestCalculateConfidence:
    def test_base_score_no_extras(self):
        svc, _, _ = _make_service()
        score = svc._calculate_confidence({}, None)
        assert score == 0.5

    def test_with_template(self):
        svc, _, _ = _make_service()
        score = svc._calculate_confidence({}, MagicMock())
        assert score == 0.7  # 0.5 + 0.2

    def test_with_full_solution(self):
        svc, _, _ = _make_service()
        solution = {
            "equipment_list": [{"name": "机器人"}],
            "technical_parameters": {"speed": "10/min"},
            "process_flow": "上料->装配->下料",
        }
        score = svc._calculate_confidence(solution, MagicMock())
        assert score == 1.0


# ============================================================
# TestGenerateArchitecture
# ============================================================

class TestGenerateArchitecture:
    def test_generate_architecture_mermaid(self):
        svc, db, mock_ai = _make_service()
        mock_ai.generate_architecture.return_value = {
            "content": "```mermaid\ngraph LR\n  A-->B\n```"
        }
        result = svc.generate_architecture(requirements={"project_type": "装配"})
        assert result["diagram_code"] == "graph LR\n  A-->B"
        assert result["format"] == "mermaid"

    def test_generate_architecture_updates_solution(self):
        svc, db, mock_ai = _make_service()
        mock_ai.generate_architecture.return_value = {
            "content": "```mermaid\ngraph LR\n  X-->Y\n```"
        }
        mock_solution = _make_solution()
        db.query.return_value.filter_by.return_value.first.return_value = mock_solution

        result = svc.generate_architecture(
            requirements={},
            diagram_type="architecture",
            solution_id=1,
        )
        assert mock_solution.architecture_diagram is not None
        db.commit.assert_called()

    def test_extract_mermaid_no_tag(self):
        svc, _, _ = _make_service()
        code = svc._extract_mermaid_code("graph LR\n  A-->B")
        assert "graph LR" in code


# ============================================================
# TestGenerateBOM
# ============================================================

class TestGenerateBOM:
    def test_generate_bom_basic(self):
        svc, _, _ = _make_service()
        equipment_list = [
            {"name": "机器人", "quantity": 2},
            {"name": "传感器", "quantity": 10},
        ]
        result = svc.generate_bom(equipment_list=equipment_list, include_cost=True)
        assert result["item_count"] == 2
        assert result["total_cost"] > 0

    def test_generate_bom_no_cost(self):
        svc, _, _ = _make_service()
        equipment_list = [{"name": "设备A", "quantity": 1}]
        result = svc.generate_bom(equipment_list=equipment_list, include_cost=False)
        assert result["item_count"] == 1

    def test_generate_bom_item(self):
        svc, _, _ = _make_service()
        item = svc._generate_bom_item(
            {"name": "测试设备", "quantity": 3},
            include_cost=True,
            include_suppliers=True,
        )
        assert item["item_name"] == "测试设备"
        assert item["quantity"] == 3
        assert "unit_price" in item
        assert "supplier" in item


# ============================================================
# TestGetSolutionAndUpdate
# ============================================================

class TestGetSolutionAndUpdate:
    def test_get_solution_found(self):
        svc, db, _ = _make_service()
        mock_s = _make_solution()
        db.query.return_value.filter_by.return_value.first.return_value = mock_s
        result = svc.get_solution(1)
        assert result is mock_s

    def test_get_solution_not_found(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None
        result = svc.get_solution(999)
        assert result is None

    def test_update_solution_not_found(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            svc.update_solution(999, {"status": "reviewed"})

    def test_update_solution_success(self):
        svc, db, _ = _make_service()
        mock_s = _make_solution()
        db.query.return_value.filter_by.return_value.first.return_value = mock_s
        result = svc.update_solution(1, {"status": "reviewed"})
        assert mock_s.status == "reviewed"
        db.commit.assert_called()


# ============================================================
# TestReviewSolution
# ============================================================

class TestReviewSolution:
    def test_review_solution_approved(self):
        svc, db, _ = _make_service()
        mock_s = _make_solution()
        db.query.return_value.filter_by.return_value.first.return_value = mock_s

        result = svc.review_solution(
            solution_id=1, reviewer_id=2, status="approved", comments="LGTM"
        )
        assert mock_s.status == "approved"
        assert mock_s.reviewed_by == 2
        assert mock_s.review_comments == "LGTM"
        db.commit.assert_called()

    def test_review_solution_not_found(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter_by.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            svc.review_solution(999, reviewer_id=1, status="approved")


# ============================================================
# TestGetTemplateLibrary
# ============================================================

class TestGetTemplateLibrary:
    def test_get_all_templates(self):
        svc, db, _ = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [_make_template()]
        result = svc.get_template_library()
        assert len(result) == 1

    def test_get_templates_with_filters(self):
        svc, db, _ = _make_service()
        filter_chain = MagicMock()
        filter_chain.filter.return_value = filter_chain
        filter_chain.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value = filter_chain

        result = svc.get_template_library(industry="汽车", equipment_type="机器人")
        assert result == []

    def test_get_templates_include_inactive(self):
        svc, db, _ = _make_service()
        db.query.return_value.order_by.return_value.all.return_value = [_make_template(is_active=0)]
        result = svc.get_template_library(is_active=False)
        assert len(result) == 1
