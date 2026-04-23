# -*- coding: utf-8 -*-
"""gate_validators 深度测试"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.sales.sales_funnel import GateTypeEnum
from app.services.sales.gate_validators import (
    G1Validator,
    G2Validator,
    G3Validator,
    G4Validator,
    GateValidatorFactory,
    ValidationResult,
)


class FakeQuery:
    def __init__(self, first_value=None):
        self._first_value = first_value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def options(self, *args, **kwargs):
        return self


class TestGateValidatorsDeep:
    def test_validation_result_handles_non_bool_passed(self):
        result = ValidationResult("weird", score=10)

        assert result.passed is False
        assert result.to_dict()["score"] == 10

    def test_save_result_and_waive_gate(self):
        db = Mock()
        validator = G1Validator(db)
        validator.config = SimpleNamespace(can_be_waived=True)
        gate_result = SimpleNamespace(id=1, result=None)
        db.query.return_value = FakeQuery(first_value=gate_result)

        with patch(
            "app.services.sales.gate_validators.StageGateResult",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            saved = validator.save_result(
                entity_type="LEAD",
                entity_id=9,
                result=ValidationResult(True, score=88, threshold=60, details={"k": 1}),
                validated_by=7,
            )

        assert saved.entity_type == "LEAD"
        assert saved.score == 88
        assert db.add.called and db.commit.called and db.refresh.called

        waived = validator.waive_gate(1, waived_by=3, waive_reason="特批")
        assert waived.is_waived is True
        assert waived.waive_reason == "特批"

    def test_waive_gate_respects_config(self):
        db = Mock()
        validator = G1Validator(db)
        validator.config = SimpleNamespace(can_be_waived=False)
        db.query.return_value = FakeQuery(first_value=SimpleNamespace(id=1))

        with pytest.raises(ValueError):
            validator.waive_gate(1, waived_by=1, waive_reason="no")

    def test_g1_validate_passes(self):
        lead = SimpleNamespace(
            id=1,
            lead_code="L1",
            customer_name="客户A",
            contact_name="张三",
            contact_phone="123",
            demand_summary="a" * 60,
            industry="汽车",
            owner_id=8,
            assessment_id=1,
            assessment=SimpleNamespace(status="COMPLETED", decision="推荐立项"),
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=lead)
        validator = G1Validator(db)
        validator.config = None

        result = validator.validate(1)

        assert result.passed is True
        assert result.score == 100
        assert "技术评估通过" in result.passed_rules

    def test_g2_validate_fails_without_assessment(self):
        opp = SimpleNamespace(
            id=1,
            opp_code="O1",
            stage="DISCOVERY",
            est_amount=None,
            customer_id=None,
            assessment_id=None,
            assessment=None,
            expected_close_date=None,
            owner_id=None,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=opp)
        validator = G2Validator(db)
        validator.config = None

        result = validator.validate(1)

        assert result.passed is False
        assert "未进行技术评估" in result.failed_rules
        assert "商机阶段不满足要求: DISCOVERY" in result.failed_rules

    def test_g3_validate_margin_warning_and_expired_quote(self):
        current_version = SimpleNamespace(
            version_no="V1",
            status="APPROVED",
            total_amount=1000,
            margin_rate=12,
            valid_until=datetime.now().date() - timedelta(days=1),
        )
        quote = SimpleNamespace(id=1, quote_code="Q1", current_version=current_version, customer_id=6)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=quote)
        validator = G3Validator(db)
        validator.config = SimpleNamespace(validation_rules={"min_margin_rate": 15.0, "pass_threshold": 75})

        result = validator.validate(1)

        assert result.passed is False
        assert any("毛利率接近下限" in w for w in result.warnings)
        assert "报价已过期" in result.failed_rules

    def test_g4_validate_passes_signed_contract(self):
        contract = SimpleNamespace(
            id=1,
            contract_code="C1",
            status="signed",
            signing_date=datetime.now().date(),
            total_amount=5000,
            deliverables=[1, 2],
            payment_terms="30/70",
            customer_id=9,
        )
        db = Mock()
        db.query.return_value = FakeQuery(first_value=contract)
        validator = G4Validator(db)
        validator.config = None

        result = validator.validate(1)

        assert result.passed is True
        assert result.score == 100

    def test_factory_validate_gate_with_save_result(self):
        db = Mock()
        fake_validator = Mock()
        fake_validator.validate.return_value = ValidationResult(True, score=77)
        fake_validator.save_result.return_value = SimpleNamespace(id=5)

        with patch.object(GateValidatorFactory, "get_validator", return_value=fake_validator):
            result, gate_result = GateValidatorFactory.validate_gate(
                GateTypeEnum.G2, 12, db, validated_by=3, save_result=True
            )

        assert result.score == 77
        assert gate_result.id == 5
        fake_validator.save_result.assert_called_once()
        assert fake_validator.save_result.call_args.kwargs["entity_type"] == "OPPORTUNITY"

    def test_factory_get_validator_unsupported(self):
        with pytest.raises(ValueError):
            GateValidatorFactory.get_validator("BAD", Mock())
