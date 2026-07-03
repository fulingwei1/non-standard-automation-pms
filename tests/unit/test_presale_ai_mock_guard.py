# -*- coding: utf-8 -*-
"""PRE 详#10/#7 契约：mock 演示数据不得混入真实业务数据。

1. 方案生成：AI 降级返回 mock（model 带 -mock 后缀）时必须拒绝入库并报错。
2. 会议纪要解析后台任务：AI 返回 mock 时必须 raise（job 标 FAILED），不得把演示 JSON 当抽取结果 SUCCESS。
3. BOM 成本：单价接物料库/模块库真实价格；查无价置 null 并标"待询价"，不得再写死 10000 元/"推荐供应商A"/30 天。
"""
import uuid
from decimal import Decimal

import pytest

from app.models.material import Material
from app.models.presale.core import PresaleSupportTicket
from app.models.presale_ai_solution import PresaleAISolution
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _user(db):
    return _get_or_create_user(
        db,
        username=_unique("mockg").lower(),
        password="test123",
        real_name="mock守卫用户",
        department="售前部",
    )


class _MockAIClient:
    """模拟 AI 降级：返回 -mock 后缀模型。"""

    def generate_solution(self, prompt=None, model=None, **kwargs):
        return {
            "content": '{"description": "自动上料机演示方案"}',
            "model": f"{model or 'gpt-4'}-mock",
            "usage": {"total_tokens": 10},
        }


def test_generate_solution_rejects_mock_response(db_session):
    from app.services.presale.presale_ai_service import PresaleAIService

    user = _user(db_session)
    ticket = PresaleSupportTicket(
        ticket_no=_unique("PST"),
        title="mock守卫工单",
        ticket_type="SOLUTION",
        applicant_id=user.id,
    )
    db_session.add(ticket)
    db_session.commit()

    from app.schemas.presale_ai_solution import SolutionGenerationRequest

    service = PresaleAIService(db_session)
    service.ai_client = _MockAIClient()
    request = SolutionGenerationRequest(
        presale_ticket_id=ticket.id,
        requirements={"raw_requirement": "FCT 测试系统需求描述足够长"},
        generate_architecture=False,
        generate_bom=False,
    )

    before = db_session.query(PresaleAISolution).count()
    with pytest.raises(ValueError, match="演示|mock|不可用"):
        service.generate_solution(request, user_id=user.id)
    assert db_session.query(PresaleAISolution).count() == before, "mock 方案不得入库"


def test_parse_meeting_minutes_handler_rejects_mock(db_session):
    from unittest.mock import patch

    from app.services import ai_job_service

    with patch(
        "app.services.ai_client_service.AIClientService.generate_solution",
        return_value={
            "content": '{"customer_name": "演示客户"}',
            "model": "qwen3-coder-plus-mock",
            "usage": {},
        },
    ):
        with pytest.raises(ValueError, match="演示|mock|不可用"):
            ai_job_service._HANDLERS["parse_meeting_minutes"](
                db_session, {"minutes_text": "今天与客户开会讨论了FCT测试需求"}, 1
            )


def test_bom_item_uses_material_library_price(db_session):
    from app.services.presale.presale_ai_service import PresaleAIService

    material = Material(
        material_code=_unique("MAT"),
        material_name="西门子PLC S7-1200",
        unit="台",
        last_price=Decimal("4200.5"),
        standard_price=Decimal("4000"),
    )
    db_session.add(material)
    db_session.commit()

    service = PresaleAIService(db_session)
    item = service._generate_bom_item(
        {"name": "西门子PLC S7-1200", "quantity": 2},
        include_cost=True,
        include_suppliers=True,
    )

    assert item["unit_price"] == 4200.5, "必须用物料库最近采购价"
    assert item["total_price"] == 8401.0
    assert item.get("price_source") == "material"


def test_bom_item_without_price_marks_pending_inquiry(db_session):
    from app.services.presale.presale_ai_service import PresaleAIService

    service = PresaleAIService(db_session)
    item = service._generate_bom_item(
        {"name": "完全不存在的神秘设备XYZ", "quantity": 3},
        include_cost=True,
        include_suppliers=True,
    )

    assert item["unit_price"] is None, "查无价必须置 null，不得写死 10000"
    assert item["total_price"] is None
    assert item.get("price_status") == "待询价"
    assert item.get("supplier") in (None, ""), "不得再返回假的'推荐供应商A'"
    assert item.get("lead_time_days") is None, "不得再写死 30 天交期"
