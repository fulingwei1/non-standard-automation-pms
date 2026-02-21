# -*- coding: utf-8 -*-
"""
BOM装配属性服务增强单元测试
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

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
from app.services.bom_attributes.bom_attributes_service import BomAttributesService


class TestBomAttributesService(unittest.TestCase):
    """BOM装配属性服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = BomAttributesService(self.mock_db)

    def tearDown(self):
        """测试后清理"""
        self.mock_db.reset_mock()

    # ==================== get_bom_assembly_attrs 测试 ====================

    def test_get_bom_assembly_attrs_success(self):
        """测试成功获取BOM装配属性列表"""
        # Mock BomHeader
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom.id = 1
        
        # Mock BomItemAssemblyAttrs
        mock_attr = MagicMock(spec=BomItemAssemblyAttrs)
        mock_attr.id = 1
        mock_attr.bom_id = 1
        mock_attr.bom_item_id = 10
        mock_attr.assembly_stage = "MECH"
        mock_attr.importance_level = "NORMAL"
        mock_attr.stage_order = 1
        mock_attr.is_blocking = True
        
        # Mock BomItem
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        mock_bom_item.quantity = 5.0
        
        # Mock Material
        mock_material = MagicMock(spec=Material)
        mock_material.id = 100
        mock_material.code = "MAT001"
        mock_material.name = "测试物料"
        
        # Mock AssemblyStage
        mock_stage = MagicMock(spec=AssemblyStage)
        mock_stage.stage_code = "MECH"
        mock_stage.stage_name = "机械装配"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            # 设置查询链
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_attr]
            mock_query.first.side_effect = [mock_bom_item, mock_material, mock_stage]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.get_bom_assembly_attrs(1)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].material_code, "MAT001")
            self.assertEqual(result[0].material_name, "测试物料")
            self.assertEqual(result[0].required_qty, 5.0)
            self.assertEqual(result[0].stage_name, "机械装配")

    def test_get_bom_assembly_attrs_with_stage_filter(self):
        """测试带阶段过滤的获取"""
        mock_bom = MagicMock(spec=BomHeader)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = []
            
            self.mock_db.query.return_value = mock_query
            
            self.service.get_bom_assembly_attrs(1, stage_code="ELEC")
            
            # 验证过滤条件被调用
            self.assertTrue(mock_query.filter.called)

    def test_get_bom_assembly_attrs_with_blocking_filter(self):
        """测试带阻塞属性过滤的获取"""
        mock_bom = MagicMock(spec=BomHeader)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = []
            
            self.mock_db.query.return_value = mock_query
            
            self.service.get_bom_assembly_attrs(1, is_blocking=True)
            
            self.assertTrue(mock_query.filter.called)

    def test_get_bom_assembly_attrs_bom_not_found(self):
        """测试BOM不存在时抛出异常"""
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', side_effect=HTTPException(status_code=404)):
            with self.assertRaises(HTTPException):
                self.service.get_bom_assembly_attrs(999)

    def test_get_bom_assembly_attrs_no_material(self):
        """测试物料不存在的情况"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_attr = MagicMock(spec=BomItemAssemblyAttrs)
        mock_attr.bom_item_id = 10
        mock_attr.assembly_stage = "MECH"
        mock_attr.importance_level = "NORMAL"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_attr]
            mock_query.first.return_value = None  # 没有 BomItem
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.get_bom_assembly_attrs(1)
            self.assertEqual(len(result), 1)

    # ==================== batch_set_assembly_attrs 测试 ====================

    def test_batch_set_assembly_attrs_create_new(self):
        """测试批量创建新属性"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_item = MagicMock()
        mock_item.bom_id = 1
        mock_item.bom_item_id = 10
        mock_item.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "MECH"
        }
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # 不存在
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.batch_set_assembly_attrs(1, [mock_item])
            
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["updated"], 0)
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()

    def test_batch_set_assembly_attrs_update_existing(self):
        """测试批量更新已存在属性"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_item = MagicMock()
        mock_item.bom_id = 1
        mock_item.bom_item_id = 10
        mock_item.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "ELEC"
        }
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_existing
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.batch_set_assembly_attrs(1, [mock_item])
            
            self.assertEqual(result["created"], 0)
            self.assertEqual(result["updated"], 1)
            self.mock_db.commit.assert_called_once()

    def test_batch_set_assembly_attrs_mixed(self):
        """测试批量混合创建和更新"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_item1 = MagicMock()
        mock_item1.bom_id = 1
        mock_item1.bom_item_id = 10
        mock_item1.model_dump.return_value = {"bom_id": 1, "bom_item_id": 10}
        
        mock_item2 = MagicMock()
        mock_item2.bom_id = 1
        mock_item2.bom_item_id = 20
        mock_item2.model_dump.return_value = {"bom_id": 1, "bom_item_id": 20}
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.side_effect = [None, mock_existing]  # 第一个不存在，第二个存在
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.batch_set_assembly_attrs(1, [mock_item1, mock_item2])
            
            self.assertEqual(result["created"], 1)
            self.assertEqual(result["updated"], 1)

    def test_batch_set_assembly_attrs_skip_mismatched_bom(self):
        """测试跳过不匹配的BOM ID"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_item = MagicMock()
        mock_item.bom_id = 999  # 不匹配
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            result = self.service.batch_set_assembly_attrs(1, [mock_item])
            
            self.assertEqual(result["created"], 0)
            self.assertEqual(result["updated"], 0)

    # ==================== update_assembly_attr 测试 ====================

    def test_update_assembly_attr_success(self):
        """测试成功更新单个属性"""
        mock_attr = MagicMock(spec=BomItemAssemblyAttrs)
        mock_attr.id = 1
        mock_attr.assembly_stage = "MECH"
        mock_attr.importance_level = "NORMAL"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_attr):
            update_data = {"assembly_stage": "ELEC", "is_blocking": False}
            
            result = self.service.update_assembly_attr(1, update_data)
            
            self.assertEqual(mock_attr.assembly_stage, "ELEC")
            self.assertEqual(mock_attr.is_blocking, False)
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(mock_attr)

    def test_update_assembly_attr_not_found(self):
        """测试属性不存在时抛出异常"""
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', side_effect=HTTPException(status_code=404)):
            with self.assertRaises(HTTPException):
                self.service.update_assembly_attr(999, {})

    def test_update_assembly_attr_empty_data(self):
        """测试空更新数据"""
        mock_attr = MagicMock(spec=BomItemAssemblyAttrs)
        mock_attr.assembly_stage = "MECH"
        mock_attr.importance_level = "NORMAL"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_attr):
            result = self.service.update_assembly_attr(1, {})
            
            self.mock_db.commit.assert_called_once()

    # ==================== auto_assign_assembly_attrs 测试 ====================

    def test_auto_assign_assembly_attrs_with_mapping(self):
        """测试基于分类映射自动分配"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        
        mock_material = MagicMock(spec=Material)
        mock_material.id = 100
        mock_material.category_id = 1
        
        mock_mapping = MagicMock(spec=CategoryStageMapping)
        mock_mapping.stage_code = "ELEC"
        mock_mapping.is_blocking = False
        mock_mapping.can_postpone = True
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [None, mock_material, mock_mapping]  # 不存在existing，有material和mapping
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1)
            
            self.assertEqual(result["assigned"], 1)
            self.assertEqual(result["skipped"], 0)
            self.mock_db.add.assert_called_once()

    def test_auto_assign_assembly_attrs_without_mapping_use_default(self):
        """测试无映射时使用默认值"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        
        mock_material = MagicMock(spec=Material)
        mock_material.id = 100
        mock_material.category_id = 1
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [None, mock_material, None]  # 无mapping
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1)
            
            self.assertEqual(result["assigned"], 1)
            # 验证使用了默认值 MECH
            call_args = self.mock_db.add.call_args[0][0]
            self.assertEqual(call_args.assembly_stage, "MECH")

    def test_auto_assign_assembly_attrs_skip_existing_without_overwrite(self):
        """测试不覆盖已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.return_value = mock_existing  # 已存在
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1, overwrite=False)
            
            self.assertEqual(result["assigned"], 0)
            self.assertEqual(result["skipped"], 1)

    def test_auto_assign_assembly_attrs_overwrite_existing(self):
        """测试覆盖已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = 1
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        mock_mapping = MagicMock(spec=CategoryStageMapping)
        mock_mapping.stage_code = "ELEC"
        mock_mapping.is_blocking = True
        mock_mapping.can_postpone = False
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_existing, mock_material, mock_mapping]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1, overwrite=True)
            
            self.assertEqual(result["assigned"], 1)
            self.assertEqual(mock_existing.assembly_stage, "ELEC")

    def test_auto_assign_assembly_attrs_skip_no_material(self):
        """测试跳过无物料的BOM项"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [None, None]  # 无existing，无material
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1)
            
            self.assertEqual(result["skipped"], 1)

    def test_auto_assign_assembly_attrs_skip_no_category(self):
        """测试跳过无分类的物料"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = None
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [None, mock_material]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.auto_assign_assembly_attrs(1)
            
            self.assertEqual(result["skipped"], 1)

    # ==================== get_assembly_attr_recommendations 测试 ====================

    def test_get_assembly_attr_recommendations_success(self):
        """测试成功获取推荐"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        
        mock_material = MagicMock(spec=Material)
        mock_material.code = "MAT001"
        mock_material.name = "测试物料"
        
        mock_rec = MagicMock()
        mock_rec.stage_code = "ELEC"
        mock_rec.is_blocking = True
        mock_rec.can_postpone = False
        mock_rec.importance_level = "HIGH"
        mock_rec.confidence = 0.95
        mock_rec.source = "HISTORY"
        mock_rec.reason = "历史数据推荐"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={10: mock_rec}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = mock_material
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.get_assembly_attr_recommendations(1)
                
                self.assertEqual(result["total"], 1)
                self.assertEqual(len(result["recommendations"]), 1)
                self.assertEqual(result["recommendations"][0]["recommended_stage"], "ELEC")
                self.assertEqual(result["recommendations"][0]["confidence"], 0.95)

    def test_get_assembly_attr_recommendations_no_material(self):
        """测试无物料时跳过"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = None  # 无material
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.get_assembly_attr_recommendations(1)
                
                self.assertEqual(result["total"], 0)

    # ==================== smart_recommend_assembly_attrs 测试 ====================

    def test_smart_recommend_assembly_attrs_create_new(self):
        """测试智能推荐创建新属性"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        
        mock_rec = MagicMock()
        mock_rec.stage_code = "ELEC"
        mock_rec.is_blocking = True
        mock_rec.can_postpone = False
        mock_rec.importance_level = "HIGH"
        mock_rec.source = "HISTORY"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={10: mock_rec}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = None  # 不存在
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1)
                
                self.assertEqual(result["assigned"], 1)
                self.assertEqual(result["recommendation_stats"]["HISTORY"], 1)
                self.mock_db.add.assert_called_once()

    def test_smart_recommend_assembly_attrs_with_user_id(self):
        """测试带用户ID的智能推荐"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        
        mock_rec = MagicMock()
        mock_rec.stage_code = "MECH"
        mock_rec.is_blocking = True
        mock_rec.can_postpone = False
        mock_rec.importance_level = "NORMAL"
        mock_rec.source = "CATEGORY"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={10: mock_rec}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = None
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1, user_id=123)
                
                # 验证 created_by 被设置
                call_args = self.mock_db.add.call_args[0][0]
                self.assertEqual(call_args.created_by, 123)

    def test_smart_recommend_assembly_attrs_skip_existing(self):
        """测试跳过已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = mock_existing
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1, overwrite=False)
                
                self.assertEqual(result["skipped"], 1)

    def test_smart_recommend_assembly_attrs_overwrite(self):
        """测试覆盖已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        mock_rec = MagicMock()
        mock_rec.stage_code = "SOFT"
        mock_rec.is_blocking = False
        mock_rec.can_postpone = True
        mock_rec.importance_level = "LOW"
        mock_rec.source = "KEYWORD"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={10: mock_rec}):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = mock_existing
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1, overwrite=True)
                
                self.assertEqual(result["assigned"], 1)
                self.assertEqual(mock_existing.assembly_stage, "SOFT")
                self.assertEqual(mock_existing.setting_source, "KEYWORD")

    def test_smart_recommend_assembly_attrs_skip_no_recommendation(self):
        """测试跳过无推荐结果的项"""
        mock_bom = MagicMock(spec=BomHeader)
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value={}):  # 空推荐
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_bom_item]
                mock_query.first.return_value = None
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1)
                
                self.assertEqual(result["skipped"], 1)

    def test_smart_recommend_assembly_attrs_multiple_sources(self):
        """测试多种推荐来源统计"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_items = [MagicMock(spec=BomItem) for _ in range(3)]
        for i, item in enumerate(mock_items):
            item.id = i + 1
        
        mock_recs = {}
        sources = ["HISTORY", "CATEGORY", "KEYWORD"]
        for i, item in enumerate(mock_items):
            rec = MagicMock()
            rec.stage_code = "MECH"
            rec.is_blocking = True
            rec.can_postpone = False
            rec.importance_level = "NORMAL"
            rec.source = sources[i]
            mock_recs[item.id] = rec
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend', return_value=mock_recs):
                mock_query = MagicMock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = mock_items
                mock_query.first.return_value = None
                
                self.mock_db.query.return_value = mock_query
                
                result = self.service.smart_recommend_assembly_attrs(1)
                
                self.assertEqual(result["assigned"], 3)
                self.assertEqual(result["recommendation_stats"]["HISTORY"], 1)
                self.assertEqual(result["recommendation_stats"]["CATEGORY"], 1)
                self.assertEqual(result["recommendation_stats"]["KEYWORD"], 1)

    # ==================== apply_assembly_template 测试 ====================

    def test_apply_assembly_template_success(self):
        """测试成功应用模板"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.id = 1
        mock_template.stage_config = {
            "ELEC": {"stage": "ELEC", "blocking": True, "postpone": False}
        }
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_bom_item.id = 10
        mock_bom_item.material_id = 100
        
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = 1
        
        mock_category = MagicMock(spec=MaterialCategory)
        mock_category.code = "ELEC"
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_template, mock_material, mock_category, None]  # template, material, category, no existing
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.apply_assembly_template(1, 1)
            
            self.assertEqual(result["applied"], 1)
            self.mock_db.add.assert_called_once()

    def test_apply_assembly_template_not_found(self):
        """测试模板不存在"""
        mock_bom = MagicMock(spec=BomHeader)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # 模板不存在
            
            self.mock_db.query.return_value = mock_query
            
            with self.assertRaises(HTTPException) as context:
                self.service.apply_assembly_template(1, 999)
            
            self.assertEqual(context.exception.status_code, 404)

    def test_apply_assembly_template_empty_config(self):
        """测试模板配置为空"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.stage_config = None
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_template
            
            self.mock_db.query.return_value = mock_query
            
            with self.assertRaises(HTTPException) as context:
                self.service.apply_assembly_template(1, 1)
            
            self.assertEqual(context.exception.status_code, 400)

    def test_apply_assembly_template_skip_no_material(self):
        """测试跳过无物料的项"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.stage_config = {"ELEC": {"stage": "ELEC"}}
        
        mock_bom_item = MagicMock(spec=BomItem)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_template, None]  # 无material
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.apply_assembly_template(1, 1)
            
            self.assertEqual(result["applied"], 0)

    def test_apply_assembly_template_skip_no_match(self):
        """测试跳过无匹配配置的项"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.stage_config = {"ELEC": {"stage": "ELEC"}}
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = 1
        
        mock_category = MagicMock(spec=MaterialCategory)
        mock_category.code = "MECH"  # 不匹配
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_template, mock_material, mock_category]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.apply_assembly_template(1, 1)
            
            self.assertEqual(result["applied"], 0)

    def test_apply_assembly_template_skip_existing_without_overwrite(self):
        """测试不覆盖已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.stage_config = {"ELEC": {"stage": "ELEC"}}
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = 1
        
        mock_category = MagicMock(spec=MaterialCategory)
        mock_category.code = "ELEC"
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_template, mock_material, mock_category, mock_existing]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.apply_assembly_template(1, 1, overwrite=False)
            
            self.assertEqual(result["applied"], 0)

    def test_apply_assembly_template_overwrite_existing(self):
        """测试覆盖已存在的配置"""
        mock_bom = MagicMock(spec=BomHeader)
        
        mock_template = MagicMock(spec=AssemblyTemplate)
        mock_template.stage_config = {
            "ELEC": {"stage": "SOFT", "blocking": False, "postpone": True}
        }
        
        mock_bom_item = MagicMock(spec=BomItem)
        mock_material = MagicMock(spec=Material)
        mock_material.category_id = 1
        
        mock_category = MagicMock(spec=MaterialCategory)
        mock_category.code = "ELEC"
        
        mock_existing = MagicMock(spec=BomItemAssemblyAttrs)
        
        with patch('app.services.bom_attributes.bom_attributes_service.get_or_404', return_value=mock_bom):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [mock_bom_item]
            mock_query.first.side_effect = [mock_template, mock_material, mock_category, mock_existing]
            
            self.mock_db.query.return_value = mock_query
            
            result = self.service.apply_assembly_template(1, 1, overwrite=True)
            
            self.assertEqual(result["applied"], 1)
            self.assertEqual(mock_existing.assembly_stage, "SOFT")
            self.assertEqual(mock_existing.is_blocking, False)


if __name__ == '__main__':
    unittest.main()
