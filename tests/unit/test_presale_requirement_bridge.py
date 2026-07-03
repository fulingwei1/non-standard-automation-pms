# -*- coding: utf-8 -*-
"""PRE-10 契约：AI 需求分析结果必须有下游消费，不再是数据孤岛。

1. 方案生成：给 requirement_analysis_id 即自动带出已存分析内容，前端不必重贴需求文本。
2. 三档报价：base_requirements 为空时从分析记录组装。
3. 确认回填：分析确认后增量回填商机 opportunity_requirements（只填空缺，不覆盖人工值）。
"""
import uuid

import pytest

from app.models.presale.core import PresaleSupportTicket
from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
from app.models.sales import Customer
from app.models.sales.leads import Opportunity, OpportunityRequirement
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_ticket_and_analysis(db, user, opportunity_id=None):
    ticket = PresaleSupportTicket(
        ticket_no=_unique("PST"),
        title="FCT 整机测试售前支持",
        ticket_type="SOLUTION",
        applicant_id=user.id,
        opportunity_id=opportunity_id,
    )
    db.add(ticket)
    db.flush()
    analysis = PresaleAIRequirementAnalysis(
        presale_ticket_id=ticket.id,
        raw_requirement="整机FCT功能测试系统，家电行业，15秒节拍，需 MES 对接与扫码追溯",
        structured_requirement={
            "project_type": "FCT功能测试系统",
            "industry": "家电制造",
            "core_objectives": ["整机功能测试自动化"],
            "functional_requirements": ["通电测试", "按键测试", "扫码追溯"],
            "constraints": ["现场空间受限", "需兼容3个机型"],
        },
        technical_parameters={"ct_seconds": 15, "interface_desc": "MES/RS232"},
        acceptance_criteria=["GRR<10%", "节拍15秒", "误判率<0.1%"],
        confidence_score=0.85,
        status="draft",
        created_by=user.id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(ticket)
    db.refresh(analysis)
    return ticket, analysis


def _user(db):
    return _get_or_create_user(
        db,
        username=_unique("preai").lower(),
        password="test123",
        real_name="售前桥接用户",
        department="售前部",
    )


class _StubAIClient:
    def __init__(self):
        self.prompts = []

    def generate_solution(self, prompt=None, model=None, **kwargs):
        self.prompts.append(prompt or "")
        return {
            "content": '{"description": "桥接测试方案", "technical_parameters": {}}',
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }


def test_generate_solution_pulls_requirements_from_analysis(db_session):
    """方案生成只给 requirement_analysis_id，也必须能带出已存分析内容进 prompt。"""
    from app.schemas.presale_ai_solution import SolutionGenerationRequest
    from app.services.presale.presale_ai_service import PresaleAIService

    user = _user(db_session)
    ticket, analysis = _seed_ticket_and_analysis(db_session, user)

    service = PresaleAIService(db_session)
    stub = _StubAIClient()
    service.ai_client = stub

    request = SolutionGenerationRequest(
        presale_ticket_id=ticket.id,
        requirement_analysis_id=analysis.id,
        generate_architecture=False,
        generate_bom=False,
    )
    result = service.generate_solution(request, user_id=user.id)

    assert result["solution_id"]
    prompt = stub.prompts[0]
    assert "FCT" in prompt, "分析记录的原始需求未进入方案生成 prompt"
    assert "MES" in prompt, "分析记录的技术参数未进入方案生成 prompt"


def test_generate_solution_requires_some_requirement_source(db_session):
    """requirements 与 requirement_analysis_id 都缺时必须显式报错，不能拿空需求去生成。"""
    from app.schemas.presale_ai_solution import SolutionGenerationRequest
    from app.services.presale.presale_ai_service import PresaleAIService

    user = _user(db_session)
    ticket, _ = _seed_ticket_and_analysis(db_session, user)

    service = PresaleAIService(db_session)
    service.ai_client = _StubAIClient()
    request = SolutionGenerationRequest(
        presale_ticket_id=ticket.id,
        generate_architecture=False,
        generate_bom=False,
    )
    with pytest.raises(ValueError):
        service.generate_solution(request, user_id=user.id)


def test_three_tier_quotation_composes_base_requirements_from_analysis(db_session):
    """三档报价 base_requirements 为空时，从 requirement_analysis_id 组装需求文本。"""
    from app.schemas.presale_ai_quotation import ThreeTierQuotationRequest
    from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService

    user = _user(db_session)
    ticket, analysis = _seed_ticket_and_analysis(db_session, user)

    service = AIQuotationGeneratorService(db_session)
    request = ThreeTierQuotationRequest(
        presale_ticket_id=ticket.id,
        requirement_analysis_id=analysis.id,
    )
    text = service.resolve_base_requirements(request)
    assert "FCT" in text
    assert "GRR" in text

    empty = ThreeTierQuotationRequest(presale_ticket_id=ticket.id)
    with pytest.raises(ValueError):
        service.resolve_base_requirements(empty)


def test_confirm_analysis_backfills_opportunity_requirements(db_session):
    """确认分析后：状态置 approved，商机需求表增量回填（不覆盖已有人工值）。"""
    from app.services.presale import requirement_analysis_bridge as bridge

    user = _user(db_session)
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="桥接客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db_session.add(customer)
    db_session.flush()
    opp = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="FCT 测试线商机",
        stage="REQUIREMENT",
        owner_id=user.id,
    )
    db_session.add(opp)
    db_session.flush()
    # 人工已填的字段不允许被覆盖
    existing = OpportunityRequirement(
        opportunity_id=opp.id,
        product_object="人工填写的产品对象",
    )
    db_session.add(existing)
    db_session.commit()

    ticket, analysis = _seed_ticket_and_analysis(db_session, user, opportunity_id=opp.id)

    summary = bridge.confirm_and_backfill(db_session, analysis.id, user.id)
    assert summary["backfilled"] is True

    db_session.expire_all()
    analysis = db_session.get(PresaleAIRequirementAnalysis, analysis.id)
    assert analysis.status == "approved"

    row = (
        db_session.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opp.id)
        .one()
    )
    assert row.product_object == "人工填写的产品对象", "增量合并不得覆盖人工值"
    assert "GRR" in (row.acceptance_criteria or ""), "验收标准未回填"
    assert row.ct_seconds == 15, "节拍未回填"
    assert "现场空间受限" in (row.site_constraints or ""), "现场约束未回填"
    assert "presale_ai_analysis" in (row.extra_json or ""), "缺少分析溯源"


def test_confirm_analysis_without_opportunity_still_approves(db_session):
    """工单没挂商机时确认不报错：只置状态，明确返回未回填。"""
    from app.services.presale import requirement_analysis_bridge as bridge

    user = _user(db_session)
    _, analysis = _seed_ticket_and_analysis(db_session, user, opportunity_id=None)

    summary = bridge.confirm_and_backfill(db_session, analysis.id, user.id)
    assert summary["backfilled"] is False

    db_session.expire_all()
    analysis = db_session.get(PresaleAIRequirementAnalysis, analysis.id)
    assert analysis.status == "approved"


def test_solution_generation_job_handler_registered(db_session):
    """方案生成必须有后台任务出口（旧同步路由已下线，走 ai_job 基建）。"""
    from unittest.mock import patch

    from app.services import ai_job_service

    assert "presale_solution_generation" in ai_job_service._HANDLERS

    user = _user(db_session)
    ticket, analysis = _seed_ticket_and_analysis(db_session, user)
    with patch(
        "app.services.presale.presale_ai_service.PresaleAIService.generate_solution",
        return_value={"solution_id": 77, "confidence_score": 0.8},
    ) as mocked:
        result = ai_job_service._HANDLERS["presale_solution_generation"](
            db_session,
            {
                "presale_ticket_id": ticket.id,
                "requirement_analysis_id": analysis.id,
                "generate_architecture": False,
                "generate_bom": False,
            },
            user.id,
        )
    assert result["solution_id"] == 77
    request = mocked.call_args.args[0]
    assert request.requirement_analysis_id == analysis.id


def test_generate_solution_endpoint_mounted():
    """POST /presale/ai/generate-solution 必须真实挂载。"""
    from app.main import app

    paths = {r.path for r in app.routes}
    assert any(p.endswith("/presale/ai/generate-solution") for p in paths), "生成方案端点未挂载"
