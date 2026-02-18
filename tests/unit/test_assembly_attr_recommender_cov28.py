# -*- coding: utf-8 -*-
"""第二十八批 - assembly_attr_recommender 单元测试（BOM装配属性智能推荐）"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.assembly_attr_recommender")

from app.services.assembly_attr_recommender import (
    AssemblyAttrRecommendation,
    AssemblyAttrRecommender,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_material(
    material_id=1,
    material_name="铝型材框架",
    category_id=None,
    default_supplier_id=None,
):
    m = MagicMock()
    m.id = material_id
    m.material_name = material_name
    m.category_id = category_id
    m.default_supplier_id = default_supplier_id
    m.category = None
    return m


def _make_bom_item(bom_item_id=1, material_id=1):
    b = MagicMock()
    b.id = bom_item_id
    b.material_id = material_id
    return b


# ─── AssemblyAttrRecommendation ──────────────────────────────

class TestAssemblyAttrRecommendation:

    def test_stores_all_fields(self):
        rec = AssemblyAttrRecommendation(
            stage_code="FRAME",
            is_blocking=True,
            can_postpone=False,
            importance_level="HIGH",
            confidence=95.0,
            source="HISTORY",
            reason="历史匹配",
        )
        assert rec.stage_code == "FRAME"
        assert rec.is_blocking is True
        assert rec.confidence == 95.0
        assert rec.source == "HISTORY"

    def test_default_importance_is_normal(self):
        rec = AssemblyAttrRecommendation(
            stage_code="MECH",
            is_blocking=True,
            can_postpone=False,
        )
        assert rec.importance_level == "NORMAL"
        assert rec.confidence == 0.0


# ─── _match_from_keywords ────────────────────────────────────

class TestMatchFromKeywords:

    def test_matches_frame_keyword(self):
        material = _make_material(material_name="铝型材框架")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code == "FRAME"
        assert rec.source == "KEYWORD"
        assert rec.confidence == 70.0

    def test_matches_electric_keyword(self):
        material = _make_material(material_name="伺服驱动器")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code == "ELECTRIC"

    def test_matches_mech_keyword(self):
        material = _make_material(material_name="直线导轨组件")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code == "MECH"

    def test_matches_wiring_keyword_can_postpone(self):
        material = _make_material(material_name="线缆100m")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code == "WIRING"
        assert rec.can_postpone is True

    def test_no_keyword_match_returns_none(self):
        material = _make_material(material_name="未知物料ABC")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is None

    def test_empty_material_name_returns_none(self):
        material = _make_material(material_name=None)
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is None

    def test_frame_stage_is_blocking(self):
        material = _make_material(material_name="钣金底座")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.is_blocking is True
        assert rec.can_postpone is False

    def test_debug_stage_can_postpone(self):
        material = _make_material(material_name="工装夹具")
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code == "DEBUG"
        assert rec.can_postpone is True


# ─── _match_from_category ────────────────────────────────────

class TestMatchFromCategory:

    def test_returns_none_when_no_category_id(self):
        db = MagicMock()
        material = _make_material(category_id=None)
        rec = AssemblyAttrRecommender._match_from_category(db, material)
        assert rec is None

    def test_returns_none_when_no_mapping_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        material = _make_material(category_id=5)
        rec = AssemblyAttrRecommender._match_from_category(db, material)
        assert rec is None

    def test_returns_recommendation_from_mapping(self):
        db = MagicMock()
        mapping = MagicMock()
        mapping.stage_code = "ELECTRIC"
        mapping.is_blocking = True
        mapping.can_postpone = False
        mapping.importance_level = "HIGH"
        db.query.return_value.filter.return_value.first.return_value = mapping

        material = _make_material(category_id=3)
        category = MagicMock()
        category.name = "电气元件"
        material.category = category

        rec = AssemblyAttrRecommender._match_from_category(db, material)
        assert rec is not None
        assert rec.stage_code == "ELECTRIC"
        assert rec.confidence == 90.0
        assert rec.source == "CATEGORY"

    def test_none_importance_level_defaults_to_normal(self):
        db = MagicMock()
        mapping = MagicMock()
        mapping.stage_code = "MECH"
        mapping.is_blocking = True
        mapping.can_postpone = False
        mapping.importance_level = None
        db.query.return_value.filter.return_value.first.return_value = mapping

        material = _make_material(category_id=2)
        material.category = None
        rec = AssemblyAttrRecommender._match_from_category(db, material)
        assert rec.importance_level == "NORMAL"


# ─── _match_from_history ─────────────────────────────────────

class TestMatchFromHistory:

    def test_returns_none_when_no_history(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        rec = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=10)
        assert rec is None

    def test_selects_most_common_stage(self):
        db = MagicMock()
        attrs = []
        for _ in range(3):
            a = MagicMock()
            a.assembly_stage = "FRAME"
            a.is_blocking = True
            a.can_postpone = False
            a.importance_level = "NORMAL"
            a.confirmed = True
            attrs.append(a)
        for _ in range(1):
            a = MagicMock()
            a.assembly_stage = "MECH"
            a.is_blocking = True
            a.can_postpone = False
            a.importance_level = "NORMAL"
            a.confirmed = True
            attrs.append(a)

        db.query.return_value.join.return_value.filter.return_value.all.return_value = attrs
        rec = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=5)
        assert rec is not None
        assert rec.stage_code == "FRAME"
        assert rec.confidence == 95.0  # >= 3 uses

    def test_confidence_lower_for_few_uses(self):
        db = MagicMock()
        attr = MagicMock()
        attr.assembly_stage = "MECH"
        attr.is_blocking = True
        attr.can_postpone = False
        attr.importance_level = "HIGH"
        attr.confirmed = True

        db.query.return_value.join.return_value.filter.return_value.all.return_value = [attr]
        rec = AssemblyAttrRecommender._match_from_history(db, material_id=1, current_bom_id=5)
        assert rec is not None
        assert rec.confidence < 95.0  # Only 1 use


# ─── recommend (优先级整合) ──────────────────────────────────

class TestRecommend:

    def test_returns_default_when_no_matches(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        material = _make_material(material_name="未知物料XYZ", category_id=None, default_supplier_id=None)
        bom_item = _make_bom_item()

        rec = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=1)
        assert rec is not None
        assert rec.source == "DEFAULT"
        assert rec.stage_code == "MECH"

    def test_history_takes_priority_over_keyword(self):
        """历史数据置信度 95 > 关键词 70"""
        db = MagicMock()
        # 历史数据返回 FRAME
        attr = MagicMock()
        attr.assembly_stage = "FRAME"
        attr.is_blocking = True
        attr.can_postpone = False
        attr.importance_level = "NORMAL"
        attr.confirmed = True
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [attr, attr, attr]
        # 无分类映射
        db.query.return_value.filter.return_value.first.return_value = None

        material = _make_material(material_name="伺服驱动器（电气）", category_id=None)
        bom_item = _make_bom_item()

        rec = AssemblyAttrRecommender.recommend(db, bom_item, material, current_bom_id=5)
        # 历史 (FRAME, 95%) 应优先于关键词 (ELECTRIC, 70%)
        assert rec.source == "HISTORY"
        assert rec.stage_code == "FRAME"


# ─── batch_recommend ─────────────────────────────────────────

class TestBatchRecommend:

    def test_empty_bom_items_returns_empty(self):
        db = MagicMock()
        result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[])
        assert result == {}

    def test_skips_items_without_material(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        bom_item = _make_bom_item(bom_item_id=1, material_id=99)
        result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[bom_item])
        assert result == {}

    def test_returns_recommendations_for_valid_items(self):
        db = MagicMock()
        material = _make_material(material_name="铝型材框架")
        # Material query
        db.query.return_value.filter.return_value.first.return_value = material
        # history attrs (empty)
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        bom_item = _make_bom_item(bom_item_id=1)
        result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[bom_item])
        assert 1 in result
        assert isinstance(result[1], AssemblyAttrRecommendation)
