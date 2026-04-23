# -*- coding: utf-8 -*-
"""assessment_template_service 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.sales.assessment_template import RiskLevelEnum, RiskStatusEnum, TemplateCategoryEnum
from app.services.sales.assessment_template_service import (
    AssessmentRiskService,
    AssessmentTemplateService,
    AssessmentVersionService,
)


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, count_value=0):
        self._first_value = first_value
        self._all_value = all_value or []
        self._count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def count(self):
        return self._count_value

    def all(self):
        return self._all_value

    def first(self):
        return self._first_value

    def update(self, *args, **kwargs):
        return 1


class FakeTemplate:
    @staticmethod
    def get_default_weights():
        return {"technical": 0.4, "business": 0.6}

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestAssessmentTemplateServiceDeep:
    def test_create_template_uses_defaults(self):
        db = Mock()
        service = AssessmentTemplateService(db)

        with patch("app.services.sales.assessment_template_service.AssessmentTemplate", FakeTemplate):
            template = service.create_template("TMP1", "模板1", created_by=9)

        assert template.template_code == "TMP1"
        assert template.dimension_weights == {"technical": 0.4, "business": 0.6}
        assert template.score_thresholds["good"] == 75
        assert template.is_active is True
        assert db.add.called and db.commit.called and db.refresh.called

    def test_list_update_delete_set_default(self):
        db = Mock()
        service = AssessmentTemplateService(db)
        template = SimpleNamespace(id=1, template_code="TMP1", category="STD")
        db.query.side_effect = [
            FakeQuery(all_value=[template], count_value=1),
            FakeQuery(first_value=template),
            FakeQuery(first_value=template),
            FakeQuery(),
            FakeQuery(first_value=template),
        ]

        templates, total = service.list_templates(category="STD", is_active=True, skip=0, limit=10)
        updated = service.update_template(1, template_name="新模板", bad_field="x", is_default=True)
        deleted = service.delete_template(1)
        defaulted = service.set_default_template(1, "STD")

        assert total == 1 and templates == [template]
        assert updated.template_name == "新模板"
        assert updated.is_default is True
        assert deleted is True
        assert template.is_active is False
        assert defaulted is template

    def test_get_items_update_item_delete_and_batch_add(self):
        db = Mock()
        service = AssessmentTemplateService(db)
        item = SimpleNamespace(id=2)
        db.query.side_effect = [
            FakeQuery(all_value=[item]),
            FakeQuery(first_value=item),
            FakeQuery(first_value=item),
        ]

        items = service.get_items_by_template(1, dimension="TECH")
        updated = service.update_assessment_item(2, item_name="条目", weight=2.0)
        deleted = service.delete_assessment_item(2)

        with patch(
            "app.services.sales.assessment_template_service.AssessmentItem",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            created = service.batch_add_items(1, [
                {"item_code": "I1", "item_name": "A", "dimension": "TECH"},
                {"item_code": "I2", "item_name": "B", "dimension": "BIZ", "sort_order": 2},
            ])

        assert items == [item]
        assert updated.item_name == "条目"
        assert deleted is True
        assert len(created) == 2
        assert db.add.call_count == 2


class TestAssessmentRiskServiceDeep:
    def test_create_risk_and_status_queries(self):
        db = Mock()
        service = AssessmentRiskService(db)
        service._generate_risk_code = Mock(return_value="RSK202604120010")
        db.query.side_effect = [
            FakeQuery(all_value=[SimpleNamespace(id=1)]),
            FakeQuery(first_value=SimpleNamespace(id=7, risk_code="R7")),
            FakeQuery(all_value=[SimpleNamespace(id=8)]),
        ]

        class FakeRisk:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def calculate_risk_score(self):
                return 6

        with patch("app.services.sales.assessment_template_service.AssessmentRisk", FakeRisk):
            risk = service.create_risk(1, "高风险", "描述", probability="HIGH", impact="HIGH")

        assert risk.risk_code.endswith("0010")
        assert risk.risk_score == 6
        assert risk.risk_level == RiskLevelEnum.CRITICAL

        risks = service.get_risks_by_assessment(1, status="OPEN")
        updated = service.update_risk_status(7, RiskStatusEnum.RESOLVED, resolution_notes="已解决")
        high = service.get_high_risks(limit=5)

        assert len(risks) == 1
        assert updated.status == RiskStatusEnum.RESOLVED
        assert updated.resolution_notes == "已解决"
        assert len(high) == 1

    def test_determine_risk_level_thresholds(self):
        service = AssessmentRiskService(Mock())
        assert service._determine_risk_level(6) == RiskLevelEnum.CRITICAL
        assert service._determine_risk_level(4) == RiskLevelEnum.HIGH
        assert service._determine_risk_level(2) == RiskLevelEnum.MEDIUM
        assert service._determine_risk_level(1) == RiskLevelEnum.LOW


class TestAssessmentVersionServiceDeep:
    def test_create_version_and_compare(self):
        db = Mock()
        service = AssessmentVersionService(db)
        assessment = SimpleNamespace(
            id=1,
            source_type="LEAD",
            source_id=9,
            status="DONE",
            veto_triggered=False,
            veto_rules='["r1"]',
            risks='["risk"]',
            conditions='["c1"]',
            ai_analysis="ok",
            dimension_scores='{"tech": 80, "biz": 70}',
            total_score=75,
            decision="通过",
            evaluator_id=5,
        )
        db.query.side_effect = [
            FakeQuery(first_value=assessment),
            FakeQuery(first_value=SimpleNamespace(version_no="V1.2")),
            FakeQuery(first_value=SimpleNamespace(total_score=70, decision="暂缓", dimension_scores={"tech": 70, "biz": 70})),
            FakeQuery(first_value=SimpleNamespace(total_score=75, decision="通过", dimension_scores={"tech": 80, "biz": 70})),
        ]

        with patch(
            "app.services.sales.assessment_template_service.AssessmentVersion",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            version = service.create_version(1, version_note="snapshot")

        assert version.version_no == "V1.3"
        assert version.snapshot_data["veto_rules"] == ["r1"]
        assert version.dimension_scores == {"tech": 80, "biz": 70}

        comparison = service.compare_versions(1, "V1.2", "V1.3")
        assert comparison["score_change"] == 5
        assert comparison["decision_change"]["from"] == "暂缓"
        assert comparison["dimension_score_changes"]["tech"]["change"] == 10

    def test_create_version_raises_when_missing(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = AssessmentVersionService(db)

        with pytest.raises(ValueError):
            service.create_version(99)

    def test_compare_versions_raises_when_missing(self):
        db = Mock()
        db.query.side_effect = [FakeQuery(first_value=None), FakeQuery(first_value=SimpleNamespace())]
        service = AssessmentVersionService(db)

        with pytest.raises(ValueError):
            service.compare_versions(1, "V1.0", "V1.1")
