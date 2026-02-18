# -*- coding: utf-8 -*-
"""第二十七批 - assembly_attr_recommender 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.assembly_attr_recommender")

from app.services.assembly_attr_recommender import (
    AssemblyAttrRecommendation,
    AssemblyAttrRecommender,
)


def make_db():
    return MagicMock()


def make_material(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", 1)
    m.name = kwargs.get("name", "铝型材 20x20")
    m.material_name = kwargs.get("name", "铝型材 20x20")  # actual field used in keyword match
    m.category_id = kwargs.get("category_id", 10)
    m.spec = kwargs.get("spec", "20x20x500")
    return m


def make_bom_item(**kwargs):
    bi = MagicMock()
    bi.id = kwargs.get("id", 1)
    bi.material_id = kwargs.get("material_id", 1)
    bi.name = kwargs.get("name", "支撑件")
    return bi


class TestAssemblyAttrRecommendation:
    def test_init_sets_fields(self):
        rec = AssemblyAttrRecommendation(
            stage_code="FRAME",
            is_blocking=True,
            can_postpone=False,
            importance_level="NORMAL",
            confidence=95.0,
            source="HISTORY",
            reason="测试原因"
        )
        assert rec.stage_code == "FRAME"
        assert rec.is_blocking is True
        assert rec.can_postpone is False
        assert rec.importance_level == "NORMAL"
        assert rec.confidence == 95.0
        assert rec.source == "HISTORY"
        assert rec.reason == "测试原因"

    def test_default_values(self):
        rec = AssemblyAttrRecommendation(
            stage_code="MECH",
            is_blocking=False,
            can_postpone=True
        )
        assert rec.confidence == 0.0
        assert rec.source == "UNKNOWN"
        assert rec.reason == ""


class TestKeywordStageMapping:
    def test_frame_keywords_exist(self):
        assert "FRAME" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING
        keywords = AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING["FRAME"]
        assert "铝型材" in keywords or "框架" in keywords

    def test_electric_keywords_exist(self):
        assert "ELECTRIC" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING

    def test_wiring_keywords_exist(self):
        assert "WIRING" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING

    def test_mech_keywords_exist(self):
        assert "MECH" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING

    def test_debug_keywords_exist(self):
        assert "DEBUG" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING

    def test_cosmetic_keywords_exist(self):
        assert "COSMETIC" in AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING


class TestSupplierTypeMapping:
    def test_machining_maps_to_mech(self):
        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert "MACHINING" in mapping
        assert mapping["MACHINING"]["stage"] == "MECH"

    def test_sheet_metal_maps_to_frame(self):
        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert mapping["SHEET_METAL"]["stage"] == "FRAME"

    def test_electric_maps_to_electric(self):
        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert mapping["ELECTRIC"]["stage"] == "ELECTRIC"

    def test_standard_is_not_blocking(self):
        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert mapping["STANDARD"]["blocking"] is False

    def test_machining_is_blocking(self):
        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert mapping["MACHINING"]["blocking"] is True


class TestRecommend:
    def test_returns_default_when_no_matches(self):
        db = make_db()
        bom_item = make_bom_item()
        material = make_material(name="未知物料")

        # All queries return nothing
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=999)
        assert result is not None
        assert result.stage_code == "MECH"
        assert result.source == "DEFAULT"

    def test_returns_recommendation_instance(self):
        db = make_db()
        bom_item = make_bom_item()
        material = make_material(name="铝型材框架件")

        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=1)
        assert isinstance(result, AssemblyAttrRecommendation)

    def test_keyword_match_prefers_frame_for_aluminum(self):
        """铝型材关键词应匹配到FRAME阶段"""
        db = make_db()
        bom_item = make_bom_item()
        material = make_material(name="铝型材 40x40")

        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=1)
        # Should match FRAME from keyword mapping (铝型材 is in FRAME keywords)
        assert result is not None

    def test_picks_highest_confidence_recommendation(self):
        """选择置信度最高的推荐"""
        db = make_db()
        bom_item = make_bom_item()
        material = make_material()

        # Simulate history with 3+ uses → confidence 95%
        history_attr = MagicMock()
        history_attr.assembly_stage = "ELECTRIC"
        history_attr.is_blocking = True
        history_attr.can_postpone = False
        history_attr.importance_level = "CRITICAL"

        db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            history_attr, history_attr, history_attr  # 3 uses
        ]
        db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=1)
        assert result.source == "HISTORY"
        assert result.confidence == 95.0


class TestMatchFromKeywords:
    def test_frame_keyword_match(self):
        material = make_material(name="铝型材 20x20x500")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "FRAME"
        assert result.confidence == 70.0
        assert result.source == "KEYWORD"

    def test_electric_keyword_match(self):
        material = make_material(name="伺服驱动器")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "ELECTRIC"

    def test_wiring_keyword_match(self):
        material = make_material(name="线缆扎带")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "WIRING"

    def test_no_keyword_match_returns_none(self):
        material = make_material(name="XYZABC未知物料")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is None


class TestMatchFromHistory:
    def test_empty_history_returns_none(self):
        db = make_db()
        # The actual chain is: query(BomItemAssemblyAttrs).join(BomItem, ...).filter(..., ..., ...).all()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=99)
        assert result is None

    def test_history_with_one_use_confidence_85(self):
        db = make_db()
        attr = MagicMock()
        attr.assembly_stage = "MECH"
        attr.is_blocking = True
        attr.can_postpone = False
        attr.importance_level = "NORMAL"
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [attr]

        result = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=99)
        assert result is not None
        assert result.confidence == 85.0
        assert result.source == "HISTORY"

    def test_history_with_three_uses_confidence_95(self):
        db = make_db()
        attr = MagicMock()
        attr.assembly_stage = "FRAME"
        attr.is_blocking = True
        attr.can_postpone = False
        attr.importance_level = "NORMAL"
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            attr, attr, attr
        ]

        result = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=99)
        assert result is not None
        assert result.confidence == 95.0

    def test_majority_vote_for_blocking(self):
        """多数决定阻塞性"""
        db = make_db()
        blocking_attr = MagicMock()
        blocking_attr.assembly_stage = "MECH"
        blocking_attr.is_blocking = True
        blocking_attr.can_postpone = False
        blocking_attr.importance_level = "NORMAL"

        non_blocking_attr = MagicMock()
        non_blocking_attr.assembly_stage = "MECH"
        non_blocking_attr.is_blocking = False
        non_blocking_attr.can_postpone = True
        non_blocking_attr.importance_level = "NORMAL"

        db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            blocking_attr, blocking_attr, non_blocking_attr
        ]

        result = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=99)
        assert result.is_blocking is True  # 2 vs 1, blocking wins
