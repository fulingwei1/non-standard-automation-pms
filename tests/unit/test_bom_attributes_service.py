# -*- coding: utf-8 -*-
"""
BOM装配属性服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 所有测试必须通过
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException

from app.models import (
    AssemblyStage,
    AssemblyTemplate,
    BomHeader,
    BomItem,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    Material,
    MaterialCategory,
)
from app.schemas.assembly_kit import BomItemAssemblyAttrsResponse
from app.services.bom_attributes.bom_attributes_service import BomAttributesService


class TestBomAttributesService(unittest.TestCase):
    """测试BomAttributesService核心方法"""

    def setUp(self):
        """每个测试前的初始化"""
        self.mock_db = MagicMock()
        self.service = BomAttributesService(db=self.mock_db)

    # ========== get_bom_assembly_attrs() 测试 ==========

    def test_get_bom_assembly_attrs_basic(self):
        """测试基本的BOM装配属性获取"""
        # Mock BOM存在
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        # Mock装配属性
        mock_attr = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            importance_level="NORMAL",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            created_at=datetime.now(),
        )
        
        # Mock BOM明细
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        # Mock物料
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        
        # Mock阶段
        mock_stage = AssemblyStage(
            stage_code="MECH",
            stage_name="机械装配",
        )
        
        # 配置数据库mock
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            # Mock query链
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_attr]
            mock_query.first.side_effect = [mock_bom_item, mock_material, mock_stage]
            
            # 执行测试
            result = self.service.get_bom_assembly_attrs(bom_id=1)
            
            # 验证
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].assembly_stage, "MECH")
            self.assertEqual(result[0].material_code, "MAT-001")
            self.assertEqual(result[0].material_name, "测试物料")
            self.assertEqual(result[0].stage_name, "机械装配")
            self.assertEqual(result[0].required_qty, Decimal("2.0"))

    def test_get_bom_assembly_attrs_with_stage_filter(self):
        """测试按阶段过滤"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_attr = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="ELEC",
            importance_level="HIGH",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_attr]
            mock_query.first.side_effect = [None, None, None]  # 没有关联数据
            
            result = self.service.get_bom_assembly_attrs(bom_id=1, stage_code="ELEC")
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].assembly_stage, "ELEC")

    def test_get_bom_assembly_attrs_with_blocking_filter(self):
        """测试按阻塞性过滤"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_attr = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            importance_level="CRITICAL",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_attr]
            mock_query.first.side_effect = [None, None, None]
            
            result = self.service.get_bom_assembly_attrs(bom_id=1, is_blocking=True)
            
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0].is_blocking)

    def test_get_bom_assembly_attrs_bom_not_found(self):
        """测试BOM不存在的情况"""
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.side_effect = HTTPException(status_code=404, detail="BOM不存在")
            
            with self.assertRaises(HTTPException):
                self.service.get_bom_assembly_attrs(bom_id=999)

    # ========== batch_set_assembly_attrs() 测试 ==========

    def test_batch_set_assembly_attrs_create_new(self):
        """测试批量创建新属性"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        # Mock请求数据
        mock_item = Mock()
        mock_item.bom_id = 1
        mock_item.bom_item_id = 10
        mock_item.assembly_stage = "MECH"
        mock_item.is_blocking = True
        mock_item.can_postpone = False
        mock_item.importance_level = "HIGH"
        mock_item.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "MECH",
            "is_blocking": True,
            "can_postpone": False,
            "importance_level": "HIGH",
        }
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            # Mock查询结果：不存在
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            
            result = self.service.batch_set_assembly_attrs(bom_id=1, items=[mock_item])
            
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["updated"], 0)
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()

    def test_batch_set_assembly_attrs_update_existing(self):
        """测试批量更新已有属性"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        # Mock已存在的属性
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=False,
            can_postpone=True,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        # Mock请求数据
        mock_item = Mock()
        mock_item.bom_id = 1
        mock_item.bom_item_id = 10
        mock_item.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "ELEC",
            "is_blocking": True,
        }
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            # Mock查询结果：存在
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_existing
            
            result = self.service.batch_set_assembly_attrs(bom_id=1, items=[mock_item])
            
            self.assertEqual(result["created"], 0)
            self.assertEqual(result["updated"], 1)
            self.assertEqual(mock_existing.assembly_stage, "ELEC")
            self.assertTrue(mock_existing.is_blocking)
            self.mock_db.commit.assert_called_once()

    def test_batch_set_assembly_attrs_skip_wrong_bom(self):
        """测试跳过不匹配的BOM ID"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_item = Mock()
        mock_item.bom_id = 2  # 不匹配
        mock_item.bom_item_id = 10
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            result = self.service.batch_set_assembly_attrs(bom_id=1, items=[mock_item])
            
            self.assertEqual(result["created"], 0)
            self.assertEqual(result["updated"], 0)

    # ========== update_assembly_attr() 测试 ==========

    def test_update_assembly_attr_success(self):
        """测试成功更新装配属性"""
        mock_attr = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=False,
            can_postpone=True,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_attr
            
            update_data = {
                "assembly_stage": "ELEC",
                "is_blocking": True,
                "importance_level": "CRITICAL",
            }
            
            result = self.service.update_assembly_attr(attr_id=1, update_data=update_data)
            
            self.assertEqual(mock_attr.assembly_stage, "ELEC")
            self.assertTrue(mock_attr.is_blocking)
            self.assertEqual(mock_attr.importance_level, "CRITICAL")
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(mock_attr)

    def test_update_assembly_attr_not_found(self):
        """测试更新不存在的属性"""
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.side_effect = HTTPException(status_code=404, detail="装配属性不存在")
            
            with self.assertRaises(HTTPException):
                self.service.update_assembly_attr(attr_id=999, update_data={})

    # ========== auto_assign_assembly_attrs() 测试 ==========

    def test_auto_assign_assembly_attrs_with_mapping(self):
        """测试基于物料分类映射自动分配"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        # Mock BOM明细
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        # Mock物料
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        # Mock分类映射
        mock_mapping = CategoryStageMapping(
            id=1,
            category_id=5,
            stage_code="ELEC",
            is_blocking=True,
            can_postpone=False,
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            # 配置query mock
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = None  # 不存在
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == CategoryStageMapping:
                    mock_query.first.return_value = mock_mapping
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.auto_assign_assembly_attrs(bom_id=1, overwrite=False)
            
            self.assertEqual(result["assigned"], 1)
            self.assertEqual(result["skipped"], 0)
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()

    def test_auto_assign_assembly_attrs_default_stage(self):
        """测试使用默认阶段（无映射配置）"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = None
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == CategoryStageMapping:
                    mock_query.first.return_value = None  # 无映射
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.auto_assign_assembly_attrs(bom_id=1, overwrite=False)
            
            self.assertEqual(result["assigned"], 1)
            self.assertEqual(result["skipped"], 0)
            
            # 验证使用默认值
            call_args = self.mock_db.add.call_args[0][0]
            self.assertEqual(call_args.assembly_stage, "MECH")
            self.assertTrue(call_args.is_blocking)
            self.assertFalse(call_args.can_postpone)

    def test_auto_assign_assembly_attrs_skip_existing(self):
        """测试跳过已有配置（不覆盖）"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = mock_existing
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.auto_assign_assembly_attrs(bom_id=1, overwrite=False)
            
            self.assertEqual(result["assigned"], 0)
            self.assertEqual(result["skipped"], 1)

    def test_auto_assign_assembly_attrs_with_overwrite(self):
        """测试覆盖已有配置"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=False,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        mock_mapping = CategoryStageMapping(
            id=1,
            category_id=5,
            stage_code="ELEC",
            is_blocking=True,
            can_postpone=True,
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = mock_existing
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == CategoryStageMapping:
                    mock_query.first.return_value = mock_mapping
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.auto_assign_assembly_attrs(bom_id=1, overwrite=True)
            
            self.assertEqual(result["assigned"], 1)
            self.assertEqual(result["skipped"], 0)
            self.assertEqual(mock_existing.assembly_stage, "ELEC")
            self.assertTrue(mock_existing.is_blocking)
            self.assertTrue(mock_existing.can_postpone)

    def test_auto_assign_assembly_attrs_skip_no_material(self):
        """测试跳过无物料信息的明细"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = None
                elif model == Material:
                    mock_query.first.return_value = None  # 无物料
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.auto_assign_assembly_attrs(bom_id=1, overwrite=False)
            
            self.assertEqual(result["assigned"], 0)
            self.assertEqual(result["skipped"], 1)

    # ========== get_assembly_attr_recommendations() 测试 ==========

    def test_get_assembly_attr_recommendations_success(self):
        """测试获取装配属性推荐"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Material(
            id=100,
            material_code="MAT-001",
            material_name="测试物料",
        )
        
        # Mock推荐结果
        mock_recommendation = Mock()
        mock_recommendation.stage_code = "ELEC"
        mock_recommendation.is_blocking = True
        mock_recommendation.can_postpone = False
        mock_recommendation.importance_level = "HIGH"
        mock_recommendation.confidence = 0.85
        mock_recommendation.source = "HISTORY"
        mock_recommendation.reason = "基于历史数据推荐"
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            with patch("app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend") as mock_batch_recommend:
                mock_batch_recommend.return_value = {10: mock_recommendation}
                
                def query_side_effect(model):
                    mock_query = MagicMock()
                    mock_query.filter.return_value = mock_query
                    
                    if model == BomItem:
                        mock_query.all.return_value = [mock_bom_item]
                    elif model == Material:
                        mock_query.first.return_value = mock_material
                    
                    return mock_query
                
                self.mock_db.query.side_effect = query_side_effect
                
                result = self.service.get_assembly_attr_recommendations(bom_id=1)
                
                self.assertEqual(result["total"], 1)
                self.assertEqual(len(result["recommendations"]), 1)
                rec = result["recommendations"][0]
                self.assertEqual(rec["bom_item_id"], 10)
                self.assertEqual(rec["material_code"], "MAT-001")
                self.assertEqual(rec["recommended_stage"], "ELEC")
                self.assertTrue(rec["recommended_blocking"])
                self.assertEqual(rec["confidence"], 0.85)
                self.assertEqual(rec["source"], "HISTORY")

    # ========== smart_recommend_assembly_attrs() 测试 ==========

    def test_smart_recommend_assembly_attrs_success(self):
        """测试智能推荐并应用"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_recommendation = Mock()
        mock_recommendation.stage_code = "ELEC"
        mock_recommendation.is_blocking = True
        mock_recommendation.can_postpone = False
        mock_recommendation.importance_level = "HIGH"
        mock_recommendation.source = "CATEGORY"
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            with patch("app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend") as mock_batch_recommend:
                mock_batch_recommend.return_value = {10: mock_recommendation}
                
                def query_side_effect(model):
                    mock_query = MagicMock()
                    mock_query.filter.return_value = mock_query
                    
                    if model == BomItem:
                        mock_query.all.return_value = [mock_bom_item]
                    elif model == BomItemAssemblyAttrs:
                        mock_query.first.return_value = None  # 不存在
                    
                    return mock_query
                
                self.mock_db.query.side_effect = query_side_effect
                
                result = self.service.smart_recommend_assembly_attrs(
                    bom_id=1,
                    overwrite=False,
                    user_id=1
                )
                
                self.assertEqual(result["assigned"], 1)
                self.assertEqual(result["skipped"], 0)
                self.assertEqual(result["recommendation_stats"]["CATEGORY"], 1)
                
                # 验证创建的属性
                call_args = self.mock_db.add.call_args[0][0]
                self.assertEqual(call_args.assembly_stage, "ELEC")
                self.assertTrue(call_args.is_blocking)
                self.assertEqual(call_args.setting_source, "CATEGORY")
                self.assertEqual(call_args.created_by, 1)

    def test_smart_recommend_assembly_attrs_skip_existing(self):
        """测试智能推荐跳过已有配置"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            with patch("app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend") as mock_batch_recommend:
                mock_batch_recommend.return_value = {}
                
                def query_side_effect(model):
                    mock_query = MagicMock()
                    mock_query.filter.return_value = mock_query
                    
                    if model == BomItem:
                        mock_query.all.return_value = [mock_bom_item]
                    elif model == BomItemAssemblyAttrs:
                        mock_query.first.return_value = mock_existing
                    
                    return mock_query
                
                self.mock_db.query.side_effect = query_side_effect
                
                result = self.service.smart_recommend_assembly_attrs(
                    bom_id=1,
                    overwrite=False
                )
                
                self.assertEqual(result["assigned"], 0)
                self.assertEqual(result["skipped"], 1)

    def test_smart_recommend_assembly_attrs_update_with_overwrite(self):
        """测试智能推荐覆盖已有配置"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=False,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        mock_recommendation = Mock()
        mock_recommendation.stage_code = "ELEC"
        mock_recommendation.is_blocking = True
        mock_recommendation.can_postpone = True
        mock_recommendation.importance_level = "CRITICAL"
        mock_recommendation.source = "KEYWORD"
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            with patch("app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend") as mock_batch_recommend:
                mock_batch_recommend.return_value = {10: mock_recommendation}
                
                def query_side_effect(model):
                    mock_query = MagicMock()
                    mock_query.filter.return_value = mock_query
                    
                    if model == BomItem:
                        mock_query.all.return_value = [mock_bom_item]
                    elif model == BomItemAssemblyAttrs:
                        mock_query.first.return_value = mock_existing
                    
                    return mock_query
                
                self.mock_db.query.side_effect = query_side_effect
                
                result = self.service.smart_recommend_assembly_attrs(
                    bom_id=1,
                    overwrite=True
                )
                
                self.assertEqual(result["assigned"], 1)
                self.assertEqual(result["skipped"], 0)
                self.assertEqual(mock_existing.assembly_stage, "ELEC")
                self.assertTrue(mock_existing.is_blocking)
                self.assertEqual(mock_existing.setting_source, "KEYWORD")

    # ========== apply_assembly_template() 测试 ==========

    def test_apply_assembly_template_success(self):
        """测试成功套用模板"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_template = AssemblyTemplate(
            id=1,
            template_code="TPL-001",
            template_name="测试模板",
            stage_config={
                "ELECTRONIC": {
                    "stage": "ELEC",
                    "blocking": True,
                    "postpone": False,
                }
            },
        )
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        mock_category = MaterialCategory(
            id=5,
            category_code="ELECTRONIC",
            category_name="电子元器件",
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == AssemblyTemplate:
                    mock_query.first.return_value = mock_template
                elif model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == MaterialCategory:
                    mock_query.first.return_value = mock_category
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = None  # 不存在
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.apply_assembly_template(
                bom_id=1,
                template_id=1,
                overwrite=False
            )
            
            self.assertEqual(result["applied"], 1)
            
            # 验证创建的属性
            call_args = self.mock_db.add.call_args[0][0]
            self.assertEqual(call_args.assembly_stage, "ELEC")
            self.assertTrue(call_args.is_blocking)
            self.assertFalse(call_args.can_postpone)

    def test_apply_assembly_template_not_found(self):
        """测试模板不存在"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # 模板不存在
            
            with self.assertRaises(HTTPException) as context:
                self.service.apply_assembly_template(
                    bom_id=1,
                    template_id=999,
                    overwrite=False
                )
            
            self.assertEqual(context.exception.status_code, 404)
            self.assertIn("模板不存在", context.exception.detail)

    def test_apply_assembly_template_empty_config(self):
        """测试模板配置为空"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_template = AssemblyTemplate(
            id=1,
            template_code="TPL-001",
            template_name="测试模板",
            stage_config=None,  # 配置为空
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            mock_query = MagicMock()
            self.mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_template
            
            with self.assertRaises(HTTPException) as context:
                self.service.apply_assembly_template(
                    bom_id=1,
                    template_id=1,
                    overwrite=False
                )
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("模板配置为空", context.exception.detail)

    def test_apply_assembly_template_skip_no_match(self):
        """测试跳过未匹配模板的物料"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_template = AssemblyTemplate(
            id=1,
            template_code="TPL-001",
            template_name="测试模板",
            stage_config={
                "MECHANICAL": {
                    "stage": "MECH",
                    "blocking": True,
                    "postpone": False,
                }
            },
        )
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        mock_category = MaterialCategory(
            id=5,
            category_code="ELECTRONIC",  # 不匹配模板
            category_name="电子元器件",
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == AssemblyTemplate:
                    mock_query.first.return_value = mock_template
                elif model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == MaterialCategory:
                    mock_query.first.return_value = mock_category
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.apply_assembly_template(
                bom_id=1,
                template_id=1,
                overwrite=False
            )
            
            self.assertEqual(result["applied"], 0)

    def test_apply_assembly_template_skip_existing(self):
        """测试模板应用跳过已有配置"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_template = AssemblyTemplate(
            id=1,
            template_code="TPL-001",
            template_name="测试模板",
            stage_config={
                "ELECTRONIC": {
                    "stage": "ELEC",
                    "blocking": True,
                    "postpone": False,
                }
            },
        )
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        mock_category = MaterialCategory(
            id=5,
            category_code="ELECTRONIC",
            category_name="电子元器件",
        )
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=True,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == AssemblyTemplate:
                    mock_query.first.return_value = mock_template
                elif model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == MaterialCategory:
                    mock_query.first.return_value = mock_category
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = mock_existing
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.apply_assembly_template(
                bom_id=1,
                template_id=1,
                overwrite=False
            )
            
            self.assertEqual(result["applied"], 0)

    def test_apply_assembly_template_with_overwrite(self):
        """测试模板应用覆盖已有配置"""
        mock_bom = BomHeader(id=1, bom_no="BOM-001", bom_name="测试BOM")
        
        mock_template = AssemblyTemplate(
            id=1,
            template_code="TPL-001",
            template_name="测试模板",
            stage_config={
                "ELECTRONIC": {
                    "stage": "ELEC",
                    "blocking": True,
                    "postpone": False,
                }
            },
        )
        
        mock_bom_item = BomItem(
            id=10,
            bom_id=1,
            material_id=100,
            quantity=Decimal("2.0"),
        )
        
        mock_material = Mock()
        mock_material.id = 100
        mock_material.material_code = "MAT-001"
        mock_material.material_name = "测试物料"
        mock_material.category_id = 5
        
        mock_category = MaterialCategory(
            id=5,
            category_code="ELECTRONIC",
            category_name="电子元器件",
        )
        
        mock_existing = BomItemAssemblyAttrs(
            id=1,
            bom_item_id=10,
            bom_id=1,
            assembly_stage="MECH",
            is_blocking=False,
            can_postpone=False,
            has_substitute=False,
            stage_order=0,
            importance_level="NORMAL",
            created_at=datetime.now(),
        )
        
        with patch("app.services.bom_attributes.bom_attributes_service.get_or_404") as mock_get_or_404:
            mock_get_or_404.return_value = mock_bom
            
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                
                if model == AssemblyTemplate:
                    mock_query.first.return_value = mock_template
                elif model == BomItem:
                    mock_query.all.return_value = [mock_bom_item]
                elif model == Material:
                    mock_query.first.return_value = mock_material
                elif model == MaterialCategory:
                    mock_query.first.return_value = mock_category
                elif model == BomItemAssemblyAttrs:
                    mock_query.first.return_value = mock_existing
                
                return mock_query
            
            self.mock_db.query.side_effect = query_side_effect
            
            result = self.service.apply_assembly_template(
                bom_id=1,
                template_id=1,
                overwrite=True
            )
            
            self.assertEqual(result["applied"], 1)
            self.assertEqual(mock_existing.assembly_stage, "ELEC")
            self.assertTrue(mock_existing.is_blocking)
            self.assertFalse(mock_existing.can_postpone)


if __name__ == "__main__":
    unittest.main()
