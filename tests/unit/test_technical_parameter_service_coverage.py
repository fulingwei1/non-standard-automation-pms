# -*- coding: utf-8 -*-
"""technical_parameter_service单元测试"""
import pytest
from types import SimpleNamespace
from unittest.mock import Mock
from app.services.presale.technical_parameter_service import TechnicalParameterService

class TestTechnicalParameterServiceInit:
    def test_init(self):
        service = TechnicalParameterService(Mock())
        assert service is not None


def test_estimate_cost_returns_sales_presale_project_context(monkeypatch):
    service = TechnicalParameterService(Mock())
    template = SimpleNamespace(
        id=1,
        name="FCT 标准测试模板",
        code="FCT-STD-001",
        cost_factors={
            "base_cost": 50000,
            "factors": {
                "test_station_count": {
                    "type": "linear",
                    "coefficient": 8000,
                }
            },
            "category_ratios": {"MECHANICAL": 1.0},
        },
        typical_labor_hours={"design_hours": 80},
    )

    monkeypatch.setattr(service, "get_template_by_id", lambda template_id: template)
    monkeypatch.setattr(service, "increment_use_count", lambda template_id: None)

    result = service.estimate_cost(
        template_id=1,
        parameters={"test_station_count": 4},
        lead_id=2026,
        opportunity_id=2,
        ticket_id=501,
        project_id=42,
    )

    assert result["total_cost"] == 82000.0
    assert result["lead_id"] == 2026
    assert result["opportunity_id"] == 2
    assert result["ticket_id"] == 501
    assert result["project_id"] == 42
