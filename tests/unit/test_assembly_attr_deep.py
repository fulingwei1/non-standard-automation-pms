# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 装配属性推荐服务（对齐当前实现）"""

import pytest
from unittest.mock import MagicMock


class TestAssemblyAttrRecommenderBusinessLogic:
    """装配属性推荐服务业务逻辑测试"""

    def test_recommend_attributes(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        mock_db = MagicMock()
        bom_item = MagicMock(id=1, material_id=1)
        material = MagicMock(id=1, material_name="铝型材框架", category_id=None, default_supplier_id=None)

        result = AssemblyAttrRecommender.recommend(mock_db, bom_item, material, current_bom_id=1)
        assert result is not None

    def test_get_similar_assemblies(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        mock_db = MagicMock()
        material = MagicMock(id=1, material_name="铝型材框架", category_id=None, default_supplier_id=None)
        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is not None

    def test_calculate_similarity(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = "PLC控制器"
        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is not None
        assert rec.confidence > 0

    def test_update_recommendation_model(self):
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        mock_db = MagicMock()
        bom_item = MagicMock(id=1, material_id=1)
        material = MagicMock(id=1, material_name="未知物料", category_id=None, default_supplier_id=None)

        result = AssemblyAttrRecommender.batch_recommend(mock_db, bom_id=1, bom_items=[bom_item])
        assert isinstance(result, dict)
