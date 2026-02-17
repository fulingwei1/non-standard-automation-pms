# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：BOM装配属性智能推荐服务
Coverage target: app/services/assembly_attr_recommender.py

分支覆盖：
1. _match_from_keywords — 每个阶段关键词、空名称、无匹配
2. _match_from_category — category_id 空/有无映射
3. _match_from_history — 历史统计多数决定逻辑
4. _infer_from_supplier — 各供应商类型、无供应商
5. recommend — 置信度最高优先
6. batch_recommend — 批量推荐
7. AssemblyAttrRecommendation — 属性初始化
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.assembly_attr_recommender import (
    AssemblyAttrRecommender,
    AssemblyAttrRecommendation,
)


# ─────────────────────────────────────────────────
# AssemblyAttrRecommendation 数据类
# ─────────────────────────────────────────────────

class TestAssemblyAttrRecommendation:

    def test_all_attributes_set(self):
        rec = AssemblyAttrRecommendation(
            stage_code="MECH",
            is_blocking=True,
            can_postpone=False,
            importance_level="HIGH",
            confidence=90.0,
            source="HISTORY",
            reason="历史匹配",
        )
        assert rec.stage_code == "MECH"
        assert rec.is_blocking is True
        assert rec.can_postpone is False
        assert rec.importance_level == "HIGH"
        assert rec.confidence == 90.0
        assert rec.source == "HISTORY"
        assert rec.reason == "历史匹配"

    def test_default_importance_level(self):
        rec = AssemblyAttrRecommendation("FRAME", True, False)
        assert rec.importance_level == "NORMAL"
        assert rec.confidence == 0.0
        assert rec.source == "UNKNOWN"


# ─────────────────────────────────────────────────
# _match_from_keywords — 每个阶段
# ─────────────────────────────────────────────────

class TestMatchFromKeywords:

    def _make_material(self, name):
        m = MagicMock(); m.material_name = name; return m

    def test_frame_keyword_铝型材(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("铝型材 2080"))
        assert result.stage_code == "FRAME"
        assert result.is_blocking is True
        assert result.can_postpone is False

    def test_frame_keyword_钣金(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("钣金件 #12"))
        assert result.stage_code == "FRAME"

    def test_mech_keyword_气缸(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("标准气缸 SMC"))
        assert result.stage_code == "MECH"
        assert result.is_blocking is True

    def test_mech_keyword_导轨(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("直线导轨 20mm"))
        assert result.stage_code == "MECH"

    def test_electric_keyword_伺服(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("伺服电机 400W"))
        assert result.stage_code == "ELECTRIC"
        assert result.is_blocking is True

    def test_electric_keyword_PLC(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("西门子PLC S7-1200"))
        assert result.stage_code == "ELECTRIC"

    def test_wiring_keyword_线缆(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("屏蔽线缆 2x0.5mm"))
        assert result.stage_code == "WIRING"
        assert result.is_blocking is False
        assert result.can_postpone is True

    def test_wiring_keyword_扎带(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("尼龙扎带 3x200"))
        assert result.stage_code == "WIRING"

    def test_debug_keyword_治具(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("定位治具 A型"))
        assert result.stage_code == "DEBUG"
        assert result.can_postpone is True

    def test_cosmetic_keyword_铭牌(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("设备铭牌 50x30"))
        assert result.stage_code == "COSMETIC"
        assert result.is_blocking is False
        assert result.can_postpone is True

    def test_no_keyword_match_returns_none(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("XYZ未知物料001"))
        assert result is None

    def test_none_name_returns_none(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material(None))
        assert result is None

    def test_confidence_is_70(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("铝型材"))
        assert result.confidence == 70.0

    def test_source_is_keyword(self):
        result = AssemblyAttrRecommender._match_from_keywords(self._make_material("气缸"))
        assert result.source == "KEYWORD"


# ─────────────────────────────────────────────────
# _match_from_category
# ─────────────────────────────────────────────────

class TestMatchFromCategory:

    def test_no_category_id_returns_none(self):
        db = MagicMock()
        material = MagicMock(); material.category_id = None
        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result is None

    def test_no_mapping_found_returns_none(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        material = MagicMock(); material.category_id = 1
        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result is None

    def test_mapping_found_returns_recommendation(self):
        db = MagicMock()
        mapping = MagicMock()
        mapping.stage_code = "ELECTRIC"
        mapping.is_blocking = True
        mapping.can_postpone = False
        mapping.importance_level = "HIGH"
        db.query.return_value.filter.return_value.first.return_value = mapping

        material = MagicMock()
        material.category_id = 2
        material.category = MagicMock(); material.category.name = "电气元件"

        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result is not None
        assert result.stage_code == "ELECTRIC"
        assert result.confidence == 90.0
        assert result.source == "CATEGORY"

    def test_mapping_without_importance_level_defaults_normal(self):
        db = MagicMock()
        mapping = MagicMock()
        mapping.stage_code = "MECH"
        mapping.is_blocking = True
        mapping.can_postpone = False
        mapping.importance_level = None
        db.query.return_value.filter.return_value.first.return_value = mapping

        material = MagicMock()
        material.category_id = 3
        material.category = None

        result = AssemblyAttrRecommender._match_from_category(db, material)
        assert result.importance_level == "NORMAL"


# ─────────────────────────────────────────────────
# _infer_from_supplier
# ─────────────────────────────────────────────────

class TestInferFromSupplier:

    def test_no_default_supplier_returns_none(self):
        db = MagicMock()
        material = MagicMock(); material.default_supplier_id = None
        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result is None

    def test_supplier_not_found_returns_none(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        material = MagicMock(); material.default_supplier_id = 1
        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result is None

    def test_supplier_type_not_in_mapping_returns_none(self):
        db = MagicMock()
        supplier = MagicMock(); supplier.supplier_type = "UNKNOWN_TYPE"
        db.query.return_value.filter.return_value.first.return_value = supplier
        material = MagicMock(); material.default_supplier_id = 1
        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result is None

    def test_machining_supplier_maps_to_mech(self):
        db = MagicMock()
        supplier = MagicMock(); supplier.supplier_type = "MACHINING"
        db.query.return_value.filter.return_value.first.return_value = supplier
        material = MagicMock(); material.default_supplier_id = 1

        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result.stage_code == "MECH"
        assert result.is_blocking is True
        assert result.confidence == 60.0
        assert result.source == "SUPPLIER"

    def test_sheet_metal_supplier_maps_to_frame(self):
        db = MagicMock()
        supplier = MagicMock(); supplier.supplier_type = "SHEET_METAL"
        db.query.return_value.filter.return_value.first.return_value = supplier
        material = MagicMock(); material.default_supplier_id = 1

        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result.stage_code == "FRAME"
        assert result.is_blocking is True

    def test_standard_supplier_not_blocking(self):
        db = MagicMock()
        supplier = MagicMock(); supplier.supplier_type = "STANDARD"
        db.query.return_value.filter.return_value.first.return_value = supplier
        material = MagicMock(); material.default_supplier_id = 1

        result = AssemblyAttrRecommender._infer_from_supplier(db, material)
        assert result.is_blocking is False
        assert result.can_postpone is True  # not blocking → can postpone


# ─────────────────────────────────────────────────
# recommend — 优先级与默认值
# ─────────────────────────────────────────────────

class TestRecommend:

    def setup_method(self):
        self.db = MagicMock()

    def test_all_none_returns_default(self):
        with patch.object(AssemblyAttrRecommender, '_match_from_history', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=None):
            result = AssemblyAttrRecommender.recommend(self.db, MagicMock(), MagicMock(), 1)
        assert result.source == "DEFAULT"
        assert result.stage_code == "MECH"

    def test_history_95_beats_category_90(self):
        history = AssemblyAttrRecommendation("FRAME", True, False, confidence=95.0, source="HISTORY", reason="")
        category = AssemblyAttrRecommendation("ELECTRIC", True, False, confidence=90.0, source="CATEGORY", reason="")

        with patch.object(AssemblyAttrRecommender, '_match_from_history', return_value=history), \
             patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=category), \
             patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=None):
            result = AssemblyAttrRecommender.recommend(self.db, MagicMock(), MagicMock(), 1)
        assert result.source == "HISTORY"

    def test_keyword_70_beats_supplier_60(self):
        keyword = AssemblyAttrRecommendation("MECH", True, False, confidence=70.0, source="KEYWORD", reason="")
        supplier = AssemblyAttrRecommendation("FRAME", True, False, confidence=60.0, source="SUPPLIER", reason="")

        with patch.object(AssemblyAttrRecommender, '_match_from_history', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=keyword), \
             patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=supplier):
            result = AssemblyAttrRecommender.recommend(self.db, MagicMock(), MagicMock(), 1)
        assert result.source == "KEYWORD"

    def test_single_recommendation_returned_directly(self):
        only_rec = AssemblyAttrRecommendation("WIRING", False, True, confidence=70.0, source="KEYWORD", reason="")

        with patch.object(AssemblyAttrRecommender, '_match_from_history', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_category', return_value=None), \
             patch.object(AssemblyAttrRecommender, '_match_from_keywords', return_value=only_rec), \
             patch.object(AssemblyAttrRecommender, '_infer_from_supplier', return_value=None):
            result = AssemblyAttrRecommender.recommend(self.db, MagicMock(), MagicMock(), 1)
        assert result.stage_code == "WIRING"


# ─────────────────────────────────────────────────
# batch_recommend
# ─────────────────────────────────────────────────

class TestBatchRecommend:

    def test_batch_skips_items_without_material(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None  # no material

        bom_item = MagicMock(); bom_item.id = 1; bom_item.material_id = 99
        result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[bom_item])
        assert result == {}

    def test_batch_returns_mapping_by_bom_item_id(self):
        db = MagicMock()
        material = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = material

        bom_item = MagicMock(); bom_item.id = 5; bom_item.material_id = 1

        rec = AssemblyAttrRecommendation("MECH", True, False, confidence=70.0, source="KEYWORD", reason="")
        with patch.object(AssemblyAttrRecommender, 'recommend', return_value=rec):
            result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[bom_item])

        assert 5 in result
        assert result[5].stage_code == "MECH"

    def test_batch_empty_items(self):
        db = MagicMock()
        result = AssemblyAttrRecommender.batch_recommend(db, bom_id=1, bom_items=[])
        assert result == {}
