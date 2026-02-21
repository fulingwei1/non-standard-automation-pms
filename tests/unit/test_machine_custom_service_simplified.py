# -*- coding: utf-8 -*-
"""
MachineCustomService 单元测试 (简化版本)

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import datetime

from app.services.machine_custom.service import MachineCustomService, DOC_TYPE_PERMISSION_MAP


class TestMachineCustomService(unittest.TestCase):
    """测试 MachineCustomService"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = MachineCustomService(self.mock_db)
        
        # 创建mock的机台对象
        self.mock_machine = MagicMock()
        self.mock_machine.id = 1
        self.mock_machine.machine_code = "MC001"
        self.mock_machine.machine_name = "测试机台"
        self.mock_machine.machine_no = "MN001"
        self.mock_machine.project_id = 100
        self.mock_machine.progress_pct = Decimal("0")
        
        # 创建mock的用户对象
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"


    # ========== update_machine_progress 测试 ==========

    @patch('app.services.machine_service.ProjectAggregationService')
    @patch('app.utils.db_helpers.save_obj')
    def test_update_machine_progress_success(self, mock_save_obj, mock_aggregation_service_class):
        """测试成功更新机台进度"""
        mock_aggregation_service = MagicMock()
        mock_aggregation_service_class.return_value = mock_aggregation_service
        
        new_progress = Decimal("75.5")
        
        result = self.service.update_machine_progress(self.mock_machine, new_progress)
        
        self.assertEqual(self.mock_machine.progress_pct, new_progress)
        mock_save_obj.assert_called_once_with(self.mock_db, self.mock_machine)
        mock_aggregation_service_class.assert_called_once_with(self.mock_db)
        mock_aggregation_service.update_project_aggregation.assert_called_once_with(100)
        self.assertEqual(result, self.mock_machine)


    # ========== get_machine_bom_list 测试 ==========

    def test_get_machine_bom_list_success(self):
        """测试成功获取BOM列表"""
        mock_bom1 = MagicMock()
        mock_bom1.id = 1
        mock_bom1.bom_no = "BOM001"
        mock_bom1.bom_name = "主BOM"
        mock_bom1.version = "V1.0"
        mock_bom1.is_latest = True
        mock_bom1.status = "APPROVED"
        mock_bom1.total_items = 50
        mock_bom1.total_amount = Decimal("10000.50")
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_bom1]
        
        result = self.service.get_machine_bom_list(1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["bom_no"], "BOM001")
        self.assertEqual(result[0]["total_amount"], 10000.50)

    def test_get_machine_bom_list_empty(self):
        """测试空BOM列表"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []
        
        result = self.service.get_machine_bom_list(1)
        
        self.assertEqual(result, [])


    # ========== check_document_permission 测试 ==========

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_has_permission(self, mock_check_permission):
        """测试有权限的情况"""
        mock_check_permission.return_value = True
        
        result = self.service.check_document_permission(self.mock_user, "CIRCUIT_DIAGRAM")
        
        self.assertTrue(result)
        mock_check_permission.assert_called_once_with(
            self.mock_user, 
            "machine:doc_circuit", 
            self.mock_db
        )

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_no_permission(self, mock_check_permission):
        """测试无权限的情况"""
        mock_check_permission.return_value = False
        
        result = self.service.check_document_permission(self.mock_user, "PLC_PROGRAM")
        
        self.assertFalse(result)


    # ========== get_service_history 测试 ==========

    @patch('app.common.query_filters.apply_pagination')
    def test_get_service_history_success(self, mock_apply_pagination):
        """测试成功获取服务历史"""
        mock_record1 = MagicMock()
        mock_record1.id = 1
        mock_record1.record_no = "SR001"
        mock_record1.service_type = "MAINTENANCE"
        mock_record1.service_date = datetime(2024, 1, 15)
        mock_record1.service_content = "定期保养"
        mock_record1.service_result = "正常"
        mock_record1.issues_found = None
        mock_record1.solution_provided = None
        mock_record1.duration_hours = Decimal("2.5")
        mock_record1.service_engineer_name = "工程师A"
        mock_record1.customer_satisfaction = 5
        mock_record1.customer_feedback = "很满意"
        mock_record1.location = "客户现场"
        mock_record1.created_at = datetime(2024, 1, 15, 10, 0)
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = [mock_record1]
        
        result = self.service.get_service_history(self.mock_machine, page=1, page_size=20)
        
        self.assertEqual(result["machine_id"], 1)
        self.assertEqual(result["machine_no"], "MN001")
        self.assertEqual(result["summary"]["total_records"], 1)
        self.assertEqual(result["summary"]["total_service_hours"], 2.5)
        self.assertEqual(result["summary"]["avg_satisfaction"], 5.0)
        self.assertEqual(len(result["items"]), 1)

    @patch('app.common.query_filters.apply_pagination')
    def test_get_service_history_empty(self, mock_apply_pagination):
        """测试空服务历史"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 0
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = []
        
        result = self.service.get_service_history(self.mock_machine)
        
        self.assertEqual(result["summary"]["total_records"], 0)
        self.assertEqual(result["summary"]["total_service_hours"], 0)
        self.assertIsNone(result["summary"]["avg_satisfaction"])


class TestDocTypePermissionMap(unittest.TestCase):
    """测试文档类型权限映射"""

    def test_all_doc_types_mapped(self):
        """测试所有定义的文档类型都有权限映射"""
        expected_types = [
            "CIRCUIT_DIAGRAM", "PLC_PROGRAM", "LABELWORK_PROGRAM",
            "VISION_PROGRAM", "MOTION_PROGRAM", "ROBOT_PROGRAM",
            "OPERATION_MANUAL", "DRAWING", "BOM_DOCUMENT",
            "FAT_DOCUMENT", "SAT_DOCUMENT", "OTHER"
        ]
        
        for doc_type in expected_types:
            self.assertIn(doc_type, DOC_TYPE_PERMISSION_MAP)

    def test_permission_codes_format(self):
        """测试权限代码格式正确"""
        for doc_type, perm_code in DOC_TYPE_PERMISSION_MAP.items():
            self.assertTrue(perm_code.startswith("machine:doc_"))


if __name__ == "__main__":
    unittest.main()
