# -*- coding: utf-8 -*-
"""
BOM装配属性智能推荐服务单元测试
覆盖: app/services/assembly_attr_recommender.py
"""
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def make_material(
    material_id=1,
    material_name="铝型材导轨",
    category_id=None,
    default_supplier_id=None,
):
    m = MagicMock()
    m.id = material_id
    m.material_name = material_name
    m.category_id = category_id
    m.default_supplier_id = default_supplier_id
    return m


def make_bom_item(bom_item_id=1, material_id=1):
    b = MagicMock()
    b.id = bom_item_id
    b.material_id = material_id
    return b


# ─── _match_from_keywords ─────────────────────────────────────────────────────

class TestMatchFromKeywords:
    def test_no_material_name_returns_none(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name=None)
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is None

    def test_frame_keyword_match(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="铝型材连接件")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "FRAME"
        assert result.confidence == 70.0
        assert result.source == "KEYWORD"
        assert result.is_blocking is True

    def test_electric_keyword_match(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="伺服电机驱动器")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code in ["ELECTRIC", "MECH"]

    def test_wiring_keyword_match(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="线缆扎带组件")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "WIRING"
        assert result.is_blocking is False
        assert result.can_postpone is True

    def test_debug_keyword_match(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="调试工装夹具")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "DEBUG"

    def test_no_keyword_returns_none(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="未分类零件XYZ")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is None

    def test_cosmetic_keyword(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(material_name="铭牌警示标识")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "COSMETIC"
        assert result.can_postpone is True


# ─── _match_from_category ─────────────────────────────────────────────────────

class TestMatchFromCategory:
    def test_no_category_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(category_id=None)
        result = AssemblyAttrRecommender._match_from_category(mock_db, material)
        assert result is None

    def test_no_mapping_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(category_id=5)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = AssemblyAttrRecommender._match_from_category(mock_db, material)
        assert result is None

    def test_returns_category_recommendation(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(category_id=3)
        material.category = MagicMock()
        material.category.name = "电气元件"

        mapping = MagicMock()
        mapping.stage_code = "ELECTRIC"
        mapping.is_blocking = True
        mapping.can_postpone = False
        mapping.importance_level = "HIGH"
        mock_db.query.return_value.filter.return_value.first.return_value = mapping

        result = AssemblyAttrRecommender._match_from_category(mock_db, material)
        assert result is not None
        assert result.stage_code == "ELECTRIC"
        assert result.confidence == 90.0
        assert result.source == "CATEGORY"


# ─── _match_from_history ──────────────────────────────────────────────────────

class TestMatchFromHistory:
    def test_no_history_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = AssemblyAttrRecommender._match_from_history(mock_db, 1, 100)
        assert result is None

    def test_single_history_item(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        attr = MagicMock()
        attr.assembly_stage = "FRAME"
        attr.is_blocking = True
        attr.can_postpone = False
        attr.importance_level = "HIGH"
        attr.confirmed = True

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [attr]

        result = AssemblyAttrRecommender._match_from_history(mock_db, 1, 100)
        assert result is not None
        assert result.stage_code == "FRAME"
        assert result.source == "HISTORY"
        # 1 history item → confidence=85
        assert result.confidence == 85.0

    def test_three_or_more_history_items(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        attrs = []
        for _ in range(3):
            attr = MagicMock()
            attr.assembly_stage = "MECH"
            attr.is_blocking = True
            attr.can_postpone = False
            attr.importance_level = "NORMAL"
            attr.confirmed = True
            attrs.append(attr)

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = attrs

        result = AssemblyAttrRecommender._match_from_history(mock_db, 1, 100)
        assert result is not None
        assert result.confidence == 95.0


# ─── _infer_from_supplier ─────────────────────────────────────────────────────

class TestInferFromSupplier:
    def test_no_supplier_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(default_supplier_id=None)
        result = AssemblyAttrRecommender._infer_from_supplier(mock_db, material)
        assert result is None

    def test_supplier_not_found_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(default_supplier_id=5)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = AssemblyAttrRecommender._infer_from_supplier(mock_db, material)
        assert result is None

    def test_unknown_supplier_type_returns_none(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(default_supplier_id=5)
        supplier = MagicMock()
        supplier.supplier_type = "UNKNOWN_TYPE"
        mock_db.query.return_value.filter.return_value.first.return_value = supplier
        result = AssemblyAttrRecommender._infer_from_supplier(mock_db, material)
        assert result is None

    def test_machining_supplier_type(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        material = make_material(default_supplier_id=5)
        supplier = MagicMock()
        supplier.supplier_type = "MACHINING"
        mock_db.query.return_value.filter.return_value.first.return_value = supplier
        result = AssemblyAttrRecommender._infer_from_supplier(mock_db, material)
        assert result is not None
        assert result.stage_code == "MECH"
        assert result.is_blocking is True
        assert result.confidence == 60.0
        assert result.source == "SUPPLIER"


# ─── recommend (integration) ──────────────────────────────────────────────────

class TestRecommend:
    def test_keyword_match_used_when_no_history_or_category(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = make_material(material_name="铝型材框架", category_id=None, default_supplier_id=None)
        bom_item = make_bom_item()

        # No history, no category mapping, no supplier
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(mock_db, bom_item, material, 100)
        assert result is not None
        assert result.source in ["KEYWORD", "DEFAULT"]

    def test_default_returned_when_no_match(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = make_material(material_name="未知物料XYZ", category_id=None, default_supplier_id=None)
        bom_item = make_bom_item()

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(mock_db, bom_item, material, 100)
        assert result is not None
        assert result.source == "DEFAULT"

    def test_history_preferred_over_keyword(self, mock_db):
        """历史记录置信度95%高于关键词70%，应优先使用"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = make_material(material_name="铝型材", category_id=None, default_supplier_id=None)
        bom_item = make_bom_item()

        # History says MECH (3 times = confidence 95)
        attrs = []
        for _ in range(3):
            attr = MagicMock()
            attr.assembly_stage = "MECH"
            attr.is_blocking = True
            attr.can_postpone = False
            attr.importance_level = "NORMAL"
            attr.confirmed = True
            attrs.append(attr)

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = attrs
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.recommend(mock_db, bom_item, material, 100)
        assert result.source == "HISTORY"
        assert result.confidence == 95.0


# ─── batch_recommend ──────────────────────────────────────────────────────────

class TestBatchRecommend:
    def test_skips_items_without_material(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        bom_item = make_bom_item(material_id=999)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AssemblyAttrRecommender.batch_recommend(mock_db, bom_id=1, bom_items=[bom_item])
        assert result == {}

    def test_returns_recommendations_for_valid_items(self, mock_db):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        bom_item = make_bom_item(material_id=1)
        material = make_material(material_name="铭牌标识", category_id=None, default_supplier_id=None)

        mock_db.query.return_value.filter.return_value.first.return_value = material
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = AssemblyAttrRecommender.batch_recommend(mock_db, bom_id=1, bom_items=[bom_item])
        assert bom_item.id in result
