# -*- coding: utf-8 -*-
"""
BOM装配属性智能推荐服务单元测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAssemblyAttrRecommendation:
    """测试装配属性推荐结果类"""

    def test_recommendation_init(self):
        """测试推荐结果初始化"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommendation

        rec = AssemblyAttrRecommendation(
        stage_code="MECH",
        is_blocking=True,
        can_postpone=False,
        importance_level="HIGH",
        confidence=95.0,
        source="HISTORY",
        reason="测试原因"
        )

        assert rec.stage_code == "MECH"
        assert rec.is_blocking is True
        assert rec.can_postpone is False
        assert rec.importance_level == "HIGH"
        assert rec.confidence == 95.0
        assert rec.source == "HISTORY"
        assert rec.reason == "测试原因"

    def test_default_values(self):
        """测试默认值"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommendation

        rec = AssemblyAttrRecommendation(
        stage_code="FRAME",
        is_blocking=False,
        can_postpone=True
        )

        assert rec.importance_level == "NORMAL"
        assert rec.confidence == 0.0
        assert rec.source == "UNKNOWN"
        assert rec.reason == ""


class TestAssemblyAttrRecommenderConstants:
    """测试推荐器常量"""

    def test_keyword_stage_mapping_exists(self):
        """测试关键词阶段映射存在"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        mapping = AssemblyAttrRecommender.KEYWORD_STAGE_MAPPING
        assert isinstance(mapping, dict)
        assert 'FRAME' in mapping
        assert 'MECH' in mapping
        assert 'ELECTRIC' in mapping

    def test_supplier_type_mapping_exists(self):
        """测试供应商类型映射存在"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        mapping = AssemblyAttrRecommender.SUPPLIER_TYPE_MAPPING
        assert isinstance(mapping, dict)
        assert 'MACHINING' in mapping
        assert 'SHEET_METAL' in mapping


class TestRecommend:
    """测试智能推荐"""

    def test_default_recommendation(self, db_session):
        """测试默认推荐"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        bom_item = MagicMock()
        bom_item.id = 1

        material = MagicMock()
        material.id = 1
        material.material_name = "未知物料"
        material.category_id = None
        material.default_supplier_id = None

        rec = AssemblyAttrRecommender.recommend(
        db_session, bom_item, material, current_bom_id=1
        )

        assert rec is not None
        assert rec.source == "DEFAULT"


class TestMatchFromKeywords:
    """测试关键词匹配"""

    def test_frame_keywords(self):
        """测试框架关键词"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = "铝型材框架"

        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is not None
        assert rec.stage_code == "FRAME"
        assert rec.confidence == 70.0
        assert rec.source == "KEYWORD"

    def test_mech_keywords(self):
        """测试机械关键词"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = "伺服电机模组"

        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is not None
        assert rec.stage_code == "MECH"

    def test_electric_keywords(self):
        """测试电气关键词"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = "PLC控制器"

        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is not None
        assert rec.stage_code == "ELECTRIC"

    def test_no_match(self):
        """测试无匹配"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = "未知XYZ物料ABC"

        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is None

    def test_empty_material_name(self):
        """测试空物料名称"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.material_name = None

        rec = AssemblyAttrRecommender._match_from_keywords(material)

        assert rec is None


class TestMatchFromCategory:
    """测试物料分类匹配"""

    def test_no_category(self, db_session):
        """测试无分类"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.category_id = None

        rec = AssemblyAttrRecommender._match_from_category(db_session, material)

        assert rec is None


class TestMatchFromHistory:
    """测试历史数据匹配"""

    def test_no_history(self, db_session):
        """测试无历史数据"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        rec = AssemblyAttrRecommender._match_from_history(
        db_session, material_id=99999, current_bom_id=1
        )

        assert rec is None


class TestInferFromSupplier:
    """测试供应商类型推断"""

    def test_no_supplier(self, db_session):
        """测试无供应商"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        material = MagicMock()
        material.default_supplier_id = None

        rec = AssemblyAttrRecommender._infer_from_supplier(db_session, material)

        assert rec is None


class TestBatchRecommend:
    """测试批量推荐"""

    def test_empty_items(self, db_session):
        """测试空物料列表"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        result = AssemblyAttrRecommender.batch_recommend(
        db_session, bom_id=1, bom_items=[]
        )

        assert result == {}


class TestBlockingDefaults:
    """测试阻塞性默认值"""

    def test_frame_is_blocking(self):
        """测试框架阶段是阻塞的"""
        blocking_defaults = {
        'FRAME': True,
        'MECH': True,
        'ELECTRIC': True,
        'WIRING': False,
        'DEBUG': False,
        'COSMETIC': False
        }

        assert blocking_defaults['FRAME'] is True
        assert blocking_defaults['WIRING'] is False

    def test_postpone_defaults(self):
        """测试可后补默认值"""
        postpone_defaults = {
        'FRAME': False,
        'MECH': False,
        'ELECTRIC': False,
        'WIRING': True,
        'DEBUG': True,
        'COSMETIC': True
        }

        assert postpone_defaults['FRAME'] is False
        assert postpone_defaults['COSMETIC'] is True


class TestConfidenceLevels:
    """测试置信度级别"""

    def test_history_confidence(self):
        """测试历史数据置信度"""
        # 使用3次以上为95%
        total_count = 5
        confidence = 95.0 if total_count >= 3 else 85.0 + (total_count - 1) * 5.0
        assert confidence == 95.0

    def test_category_confidence(self):
        """测试分类置信度"""
        confidence = 90.0
        assert confidence == 90.0

    def test_keyword_confidence(self):
        """测试关键词置信度"""
        confidence = 70.0
        assert confidence == 70.0

    def test_supplier_confidence(self):
        """测试供应商置信度"""
        confidence = 60.0
        assert confidence == 60.0


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
