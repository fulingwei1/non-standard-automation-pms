# -*- coding: utf-8 -*-
"""Tests for assembly_attr_recommender.py"""
from unittest.mock import MagicMock, patch

from app.services.assembly_attr_recommender import (
    AssemblyAttrRecommender,
    AssemblyAttrRecommendation,
)


class TestRecommend:
    def setup_method(self):
        self.db = MagicMock()

    @patch.object(AssemblyAttrRecommender, '_match_from_history', return_value=None)
    @patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=None)
    @patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=None)
    @patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=None)
    def test_default_recommendation(self, *mocks):
        bom_item = MagicMock()
        material = MagicMock(id=1)
        result = AssemblyAttrRecommender.recommend(self.db, bom_item, material, 1)
        assert result.source == "DEFAULT"
        assert result.confidence == 0.0

    @patch.object(AssemblyAttrRecommender, '_match_from_history')
    @patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=None)
    @patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=None)
    @patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=None)
    def test_history_wins(self, *mocks):
        history_rec = AssemblyAttrRecommendation("FRAME", True, False, confidence=95.0, source="HISTORY", reason="test")
        mocks[3].return_value = history_rec  # _match_from_history is last due to decorator order
        bom_item = MagicMock()
        material = MagicMock(id=1)
        result = AssemblyAttrRecommender.recommend(self.db, bom_item, material, 1)
        assert result.source == "HISTORY"


class TestMatchFromKeywords:
    def test_frame_keyword(self):
        material = MagicMock(material_name="铝型材 2080")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is not None
        assert result.stage_code == "FRAME"
        assert result.confidence == 70.0

    def test_electric_keyword(self):
        material = MagicMock(material_name="伺服驱动器")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result.stage_code == "ELECTRIC"

    def test_no_match(self):
        material = MagicMock(material_name="随机名称XYZ")
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is None

    def test_no_name(self):
        material = MagicMock(material_name=None)
        result = AssemblyAttrRecommender._match_from_keywords(material)
        assert result is None


class TestMatchFromCategory:
    def test_with_mapping(self):
        db = MagicMock()
        material = MagicMock(category_id=1, category=MagicMock(name="机械件"))
        mapping = MagicMock(stage_code="MECH", is_blocking=True, can_postpone=False, importance_level="HIGH")
        db.query.return_value.filter.return_value.first.return_value = mapping
        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result.stage_code == "MECH"
        assert result.confidence == 90.0

    def test_no_category(self):
        db = MagicMock()
        material = MagicMock(category_id=None)
        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result is None


class TestInferFromSupplier:
    def test_machining_supplier(self):
        db = MagicMock()
        material = MagicMock(default_supplier_id=1)
        supplier = MagicMock(supplier_type="MACHINING")
        db.query.return_value.filter.return_value.first.return_value = supplier
        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result.stage_code == "MECH"
        assert result.is_blocking is True

    def test_no_supplier(self):
        db = MagicMock()
        material = MagicMock(default_supplier_id=None)
        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result is None


class TestBatchRecommend:
    def test_batch(self):
        db = MagicMock()
        material = MagicMock(id=1, material_name="气缸 SC50", category_id=None, default_supplier_id=None)
        db.query.return_value.filter.return_value.first.return_value = material
        item = MagicMock(id=1, material_id=1)
        result = AssemblyAttrRecommender.batch_recommend(db, 1, [item])
        assert 1 in result
