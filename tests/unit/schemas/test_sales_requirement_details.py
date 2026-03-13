# -*- coding: utf-8 -*-
"""
销售需求详情 schema 单元测试
"""

from app.schemas.sales.requirement_details import (
    LeadRequirementDetailCreate,
    LeadRequirementDetailResponse,
    LeadRequirementDetailUpdate,
)


class TestLeadRequirementDetailSchemas:
    """LeadRequirementDetail schema 测试"""

    def test_create_payload_does_not_require_lead_id(self):
        """创建请求应从路径参数获取 lead_id，而不是要求请求体携带。"""
        payload = LeadRequirementDetailCreate(
            customer_factory_location="苏州工厂",
            requirement_maturity=4,
            cycle_time_seconds="",
            workstation_count="",
            expected_delivery_date="",
        )

        dumped = payload.model_dump()

        assert "lead_id" not in dumped
        assert dumped["customer_factory_location"] == "苏州工厂"
        assert dumped["requirement_maturity"] == 4
        assert dumped["cycle_time_seconds"] is None
        assert dumped["workstation_count"] is None
        assert dumped["expected_delivery_date"] is None

    def test_update_payload_normalizes_empty_scalars(self):
        """更新请求需要兼容表单空字符串。"""
        payload = LeadRequirementDetailUpdate(
            cycle_time_seconds="",
            workstation_count="12",
        )

        assert payload.cycle_time_seconds is None
        assert payload.workstation_count == 12

    def test_response_exposes_requirement_summary_fields(self):
        """响应应返回工作台和需求详情页实际使用的汇总字段。"""
        payload = LeadRequirementDetailResponse(
            id=9,
            lead_id=3,
            acceptance_method="FAT",
            requirement_version="REQ-2.0",
            is_frozen=True,
            frozen_by_name="张三",
        )

        assert payload.lead_id == 3
        assert payload.acceptance_method == "FAT"
        assert payload.requirement_version == "REQ-2.0"
        assert payload.is_frozen is True
        assert payload.frozen_by_name == "张三"
