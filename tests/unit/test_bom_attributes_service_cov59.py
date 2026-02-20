# -*- coding: utf-8 -*-
"""
BOM装配属性服务单元测试
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.bom_attributes import BomAttributesService
from app.models import (
    BomHeader,
    BomItem,
    BomItemAssemblyAttrs,
    Material,
    AssemblyStage,
    CategoryStageMapping,
    AssemblyTemplate,
    MaterialCategory,
)


class TestBomAttributesService(unittest.TestCase):
    """BOM装配属性服务测试"""

    def setUp(self):
        """测试前置"""
        self.db = MagicMock()
        self.service = BomAttributesService(self.db)

    def test_get_bom_assembly_attrs_basic(self):
        """测试获取BOM装配属性列表 - 基础场景"""
        # Mock数据
        bom = BomHeader(id=1, bom_code="BOM001")
        attr1 = BomItemAssemblyAttrs(
            id=1,
            bom_id=1,
            bom_item_id=10,
            assembly_stage="MECH",
            stage_order=1,
            is_blocking=True
        )
        bom_item = BomItem(id=10, material_id=100, quantity=5)
        material = Material(id=100, code="MAT001", name="物料A")
        stage = AssemblyStage(stage_code="MECH", stage_name="机械装配")

        # Mock数据库查询
        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.all.return_value = [attr1]

            self.db.query.side_effect = [
                query_mock,  # BomItemAssemblyAttrs查询
                MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=bom_item)))),  # BomItem
                MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=material)))),  # Material
                MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=stage)))),  # Stage
            ]

            result = self.service.get_bom_assembly_attrs(1)

            self.assertEqual(len(result), 1)
            self.db.query.assert_called()

    def test_get_bom_assembly_attrs_with_filters(self):
        """测试获取BOM装配属性列表 - 带筛选条件"""
        bom = BomHeader(id=1, bom_code="BOM001")

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.all.return_value = []

            self.db.query.return_value = query_mock

            result = self.service.get_bom_assembly_attrs(1, stage_code="MECH", is_blocking=True)

            # 验证筛选条件被应用
            self.assertEqual(query_mock.filter.call_count, 3)  # bom_id + stage_code + is_blocking

    def test_batch_set_assembly_attrs_create(self):
        """测试批量设置装配属性 - 新建场景"""
        bom = BomHeader(id=1, bom_code="BOM001")
        item_data = MagicMock()
        item_data.bom_id = 1
        item_data.bom_item_id = 10
        item_data.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "MECH"
        }

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.first.return_value = None  # 不存在，新建

            self.db.query.return_value = query_mock

            result = self.service.batch_set_assembly_attrs(1, [item_data])

            self.assertEqual(result["created"], 1)
            self.assertEqual(result["updated"], 0)
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_batch_set_assembly_attrs_update(self):
        """测试批量设置装配属性 - 更新场景"""
        bom = BomHeader(id=1, bom_code="BOM001")
        existing_attr = BomItemAssemblyAttrs(id=1, bom_item_id=10, assembly_stage="ELEC")
        item_data = MagicMock()
        item_data.bom_id = 1
        item_data.bom_item_id = 10
        item_data.model_dump.return_value = {
            "bom_id": 1,
            "bom_item_id": 10,
            "assembly_stage": "MECH"
        }

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            query_mock = MagicMock()
            query_mock.filter.return_value = query_mock
            query_mock.first.return_value = existing_attr  # 已存在，更新

            self.db.query.return_value = query_mock

            result = self.service.batch_set_assembly_attrs(1, [item_data])

            self.assertEqual(result["created"], 0)
            self.assertEqual(result["updated"], 1)
            self.db.commit.assert_called_once()

    def test_update_assembly_attr(self):
        """测试更新单个装配属性"""
        attr = BomItemAssemblyAttrs(id=1, assembly_stage="ELEC", is_blocking=True)

        with patch('app.utils.db_helpers.get_or_404', return_value=attr):
            update_data = {"assembly_stage": "MECH", "is_blocking": False}

            result = self.service.update_assembly_attr(1, update_data)

            self.assertEqual(attr.assembly_stage, "MECH")
            self.assertEqual(attr.is_blocking, False)
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(attr)

    def test_auto_assign_assembly_attrs_with_mapping(self):
        """测试自动分配装配属性 - 有映射配置"""
        bom = BomHeader(id=1, bom_code="BOM001")
        bom_item = BomItem(id=10, bom_id=1, material_id=100)
        material = Material(id=100, code="MAT001", category_id=5)
        mapping = CategoryStageMapping(
            category_id=5,
            stage_code="ELEC",
            is_blocking=True,
            can_postpone=False
        )

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            # Mock查询链
            bom_items_query = MagicMock()
            bom_items_query.filter.return_value = bom_items_query
            bom_items_query.all.return_value = [bom_item]

            existing_query = MagicMock()
            existing_query.filter.return_value = existing_query
            existing_query.first.return_value = None  # 不存在

            material_query = MagicMock()
            material_query.filter.return_value = material_query
            material_query.first.return_value = material

            mapping_query = MagicMock()
            mapping_query.filter.return_value = mapping_query
            mapping_query.first.return_value = mapping

            self.db.query.side_effect = [
                bom_items_query,  # 获取BOM明细
                existing_query,   # 检查已存在
                material_query,   # 获取物料
                mapping_query,    # 获取映射配置
            ]

            result = self.service.auto_assign_assembly_attrs(1, overwrite=False)

            self.assertEqual(result["assigned"], 1)
            self.assertEqual(result["skipped"], 0)
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()

    def test_auto_assign_assembly_attrs_default(self):
        """测试自动分配装配属性 - 使用默认值"""
        bom = BomHeader(id=1, bom_code="BOM001")
        bom_item = BomItem(id=10, bom_id=1, material_id=100)
        material = Material(id=100, code="MAT001", category_id=5)

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            bom_items_query = MagicMock()
            bom_items_query.filter.return_value = bom_items_query
            bom_items_query.all.return_value = [bom_item]

            existing_query = MagicMock()
            existing_query.filter.return_value = existing_query
            existing_query.first.return_value = None

            material_query = MagicMock()
            material_query.filter.return_value = material_query
            material_query.first.return_value = material

            mapping_query = MagicMock()
            mapping_query.filter.return_value = mapping_query
            mapping_query.first.return_value = None  # 无映射配置

            self.db.query.side_effect = [
                bom_items_query,
                existing_query,
                material_query,
                mapping_query,
            ]

            result = self.service.auto_assign_assembly_attrs(1, overwrite=False)

            self.assertEqual(result["assigned"], 1)
            # 验证使用了默认值MECH
            call_args = self.db.add.call_args[0][0]
            self.assertEqual(call_args.assembly_stage, "MECH")

    def test_get_assembly_attr_recommendations(self):
        """测试获取装配属性推荐结果"""
        bom = BomHeader(id=1, bom_code="BOM001")
        bom_item = BomItem(id=10, material_id=100)
        material = Material(id=100, code="MAT001", name="物料A")

        # Mock推荐器
        mock_rec = MagicMock()
        mock_rec.stage_code = "MECH"
        mock_rec.is_blocking = True
        mock_rec.can_postpone = False
        mock_rec.importance_level = "HIGH"
        mock_rec.confidence = 0.9
        mock_rec.source = "HISTORY"
        mock_rec.reason = "基于历史数据"

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend') as mock_batch:
                mock_batch.return_value = {10: mock_rec}

                bom_items_query = MagicMock()
                bom_items_query.filter.return_value = bom_items_query
                bom_items_query.all.return_value = [bom_item]

                material_query = MagicMock()
                material_query.filter.return_value = material_query
                material_query.first.return_value = material

                self.db.query.side_effect = [
                    bom_items_query,
                    material_query,
                ]

                result = self.service.get_assembly_attr_recommendations(1)

                self.assertEqual(result["total"], 1)
                self.assertEqual(len(result["recommendations"]), 1)
                self.assertEqual(result["recommendations"][0]["recommended_stage"], "MECH")

    def test_smart_recommend_assembly_attrs(self):
        """测试智能推荐装配属性"""
        bom = BomHeader(id=1, bom_code="BOM001")
        bom_item = BomItem(id=10, bom_id=1, material_id=100)

        mock_rec = MagicMock()
        mock_rec.stage_code = "ELEC"
        mock_rec.is_blocking = False
        mock_rec.can_postpone = True
        mock_rec.importance_level = "NORMAL"
        mock_rec.source = "CATEGORY"

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            with patch('app.services.assembly_attr_recommender.AssemblyAttrRecommender.batch_recommend') as mock_batch:
                mock_batch.return_value = {10: mock_rec}

                bom_items_query = MagicMock()
                bom_items_query.filter.return_value = bom_items_query
                bom_items_query.all.return_value = [bom_item]

                existing_query = MagicMock()
                existing_query.filter.return_value = existing_query
                existing_query.first.return_value = None

                self.db.query.side_effect = [
                    bom_items_query,
                    existing_query,
                ]

                result = self.service.smart_recommend_assembly_attrs(1, overwrite=False, user_id=1)

                self.assertEqual(result["assigned"], 1)
                self.assertEqual(result["skipped"], 0)
                self.assertEqual(result["recommendation_stats"]["CATEGORY"], 1)
                self.db.add.assert_called_once()
                self.db.commit.assert_called_once()

    def test_apply_assembly_template(self):
        """测试套用装配模板"""
        bom = BomHeader(id=1, bom_code="BOM001")
        template = AssemblyTemplate(
            id=1,
            template_name="标准模板",
            stage_config={
                "ELECTRONICS": {"stage": "ELEC", "blocking": True, "postpone": False}
            }
        )
        bom_item = BomItem(id=10, bom_id=1, material_id=100)
        material = Material(id=100, code="MAT001", category_id=5)
        category = MaterialCategory(id=5, code="ELECTRONICS", name="电子元件")

        with patch('app.utils.db_helpers.get_or_404', return_value=bom):
            template_query = MagicMock()
            template_query.filter.return_value = template_query
            template_query.first.return_value = template

            bom_items_query = MagicMock()
            bom_items_query.filter.return_value = bom_items_query
            bom_items_query.all.return_value = [bom_item]

            material_query = MagicMock()
            material_query.filter.return_value = material_query
            material_query.first.return_value = material

            category_query = MagicMock()
            category_query.filter.return_value = category_query
            category_query.first.return_value = category

            existing_query = MagicMock()
            existing_query.filter.return_value = existing_query
            existing_query.first.return_value = None

            self.db.query.side_effect = [
                template_query,
                bom_items_query,
                material_query,
                category_query,
                existing_query,
            ]

            result = self.service.apply_assembly_template(1, 1, overwrite=False)

            self.assertEqual(result["applied"], 1)
            self.db.add.assert_called_once()
            self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
