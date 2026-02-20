# -*- coding: utf-8 -*-
"""
验收单审批适配器单元测试
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.approval_engine.adapters.acceptance import AcceptanceOrderApprovalAdapter
from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem, AcceptanceTemplate
from app.models.approval import ApprovalInstance
from app.models.project import Project, Machine


class TestAcceptanceOrderApprovalAdapter(unittest.TestCase):
    """验收单审批适配器测试类"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = AcceptanceOrderApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    def tearDown(self):
        """测试清理"""
        self.db.reset_mock()

    # ==================== get_entity 测试 ====================

    def test_get_entity_success(self):
        """测试成功获取验收单实体"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_order)
        self.db.query.assert_called_once_with(AcceptanceOrder)

    def test_get_entity_not_found(self):
        """测试获取不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ==================== get_entity_data 测试 ====================

    def test_get_entity_data_basic(self):
        """测试获取基础验收单数据"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = 1
        mock_order.order_no = "FAT-2024-001"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "DRAFT"
        mock_order.overall_result = "PASSED"
        mock_order.total_items = 10
        mock_order.passed_items = 10
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.pass_rate = 100.0
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.template_id = None
        mock_order.planned_date = None
        mock_order.actual_start_date = None
        mock_order.actual_end_date = None
        mock_order.location = "工厂车间"
        mock_order.conclusion = "合格"
        mock_order.conditions = None
        mock_order.created_by = 1
        mock_order.is_officially_completed = False

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertEqual(result["order_no"], "FAT-2024-001")
        self.assertEqual(result["acceptance_type"], "FAT")
        self.assertEqual(result["overall_result"], "PASSED")
        self.assertEqual(result["total_items"], 10)
        self.assertEqual(result["passed_items"], 10)
        self.assertEqual(result["pass_rate"], 100.0)
        self.assertFalse(result["has_critical_failure"])

    def test_get_entity_data_with_project(self):
        """测试获取包含项目信息的验收单数据"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = 1
        mock_order.order_no = "SAT-2024-002"
        mock_order.acceptance_type = "SAT"
        mock_order.status = "DRAFT"
        mock_order.overall_result = "PASSED"
        mock_order.total_items = 5
        mock_order.passed_items = 5
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.pass_rate = 100.0
        mock_order.project_id = 10
        mock_order.machine_id = None
        mock_order.template_id = None
        mock_order.planned_date = None
        mock_order.actual_start_date = None
        mock_order.actual_end_date = None
        mock_order.location = "客户现场"
        mock_order.conclusion = "合格"
        mock_order.conditions = None
        mock_order.created_by = 1
        mock_order.is_officially_completed = False

        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ-2024-001"
        mock_project.project_name = "测试项目"
        mock_project.status = "IN_PROGRESS"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            elif model == AcceptanceOrderItem:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertEqual(result["project_code"], "PRJ-2024-001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["project_status"], "IN_PROGRESS")

    def test_get_entity_data_with_machine(self):
        """测试获取包含设备信息的验收单数据"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = 1
        mock_order.order_no = "FAT-2024-003"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "DRAFT"
        mock_order.overall_result = "PASSED"
        mock_order.total_items = 8
        mock_order.passed_items = 8
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.pass_rate = 100.0
        mock_order.project_id = None
        mock_order.machine_id = 20
        mock_order.template_id = None
        mock_order.planned_date = None
        mock_order.actual_start_date = None
        mock_order.actual_end_date = None
        mock_order.location = "工厂"
        mock_order.conclusion = "合格"
        mock_order.conditions = None
        mock_order.created_by = 1
        mock_order.is_officially_completed = False

        mock_machine = MagicMock(spec=Machine)
        mock_machine.machine_code = "MCH-001"
        mock_machine.machine_name = "测试设备"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Machine:
                mock_query.filter.return_value.first.return_value = mock_machine
            elif model == AcceptanceOrderItem:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertEqual(result["machine_code"], "MCH-001")
        self.assertEqual(result["machine_name"], "测试设备")

    def test_get_entity_data_with_critical_failure(self):
        """测试获取有关键项不合格的验收单数据"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = 1
        mock_order.order_no = "FAT-2024-004"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "DRAFT"
        mock_order.overall_result = "FAILED"
        mock_order.total_items = 10
        mock_order.passed_items = 8
        mock_order.failed_items = 2
        mock_order.na_items = 0
        mock_order.pass_rate = 80.0
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.template_id = None
        mock_order.planned_date = None
        mock_order.actual_start_date = None
        mock_order.actual_end_date = None
        mock_order.location = "工厂"
        mock_order.conclusion = "不合格"
        mock_order.conditions = None
        mock_order.created_by = 1
        mock_order.is_officially_completed = False

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == AcceptanceOrderItem:
                mock_query.filter.return_value.count.return_value = 1  # 1个关键项不合格
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertTrue(result["has_critical_failure"])
        self.assertEqual(result["failed_items"], 2)

    def test_get_entity_data_not_found(self):
        """测试获取不存在验收单的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertEqual(result, {})

    def test_get_entity_data_with_template(self):
        """测试获取包含模板信息的验收单数据"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = 1
        mock_order.order_no = "FAT-2024-005"
        mock_order.acceptance_type = "FAT"
        mock_order.status = "DRAFT"
        mock_order.overall_result = "PASSED"
        mock_order.total_items = 15
        mock_order.passed_items = 15
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.pass_rate = 100.0
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.template_id = 5
        mock_order.planned_date = None
        mock_order.actual_start_date = None
        mock_order.actual_end_date = None
        mock_order.location = "工厂"
        mock_order.conclusion = "合格"
        mock_order.conditions = None
        mock_order.created_by = 1
        mock_order.is_officially_completed = False

        mock_template = MagicMock(spec=AcceptanceTemplate)
        mock_template.template_name = "标准验收模板"
        mock_template.template_code = "TPL-001"
        mock_template.equipment_type = "设备A"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == AcceptanceTemplate:
                mock_query.filter.return_value.first.return_value = mock_template
            elif model == AcceptanceOrderItem:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        self.assertEqual(result["template_name"], "标准验收模板")
        self.assertEqual(result["template_code"], "TPL-001")
        self.assertEqual(result["equipment_type"], "设备A")

    # ==================== on_submit 测试 ====================

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_submit(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "PENDING_APPROVAL")
        self.db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        self.db.flush.assert_not_called()

    # ==================== on_approved 测试 ====================

    def test_on_approved_fat_passed(self):
        """测试FAT验收通过审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "COMPLETED")
        self.db.flush.assert_called_once()

    def test_on_approved_fat_conditional(self):
        """测试FAT有条件通过审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "CONDITIONAL"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "CONDITIONAL_APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_sat_passed(self):
        """测试SAT验收通过审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "SAT"
        mock_order.overall_result = "PASSED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "COMPLETED")
        self.db.flush.assert_called_once()

    def test_on_approved_sat_conditional(self):
        """测试SAT有条件通过审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "SAT"
        mock_order.overall_result = "CONDITIONAL"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "CONDITIONAL_APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_final_passed(self):
        """测试终验收通过审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "FINAL"
        mock_order.overall_result = "PASSED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('app.services.approval_engine.adapters.acceptance.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            self.adapter.on_approved(self.entity_id, self.instance)

            self.assertEqual(mock_order.status, "COMPLETED")
            self.assertTrue(mock_order.is_officially_completed)
            self.assertEqual(mock_order.officially_completed_at, mock_now)
            self.db.flush.assert_called_once()

    def test_on_approved_order_not_found(self):
        """测试审批通过不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        self.db.flush.assert_not_called()

    # ==================== on_rejected 测试 ====================

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_rejected(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_order_not_found(self):
        """测试驳回不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        self.db.flush.assert_not_called()

    # ==================== on_withdrawn 测试 ====================

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        self.assertEqual(mock_order.status, "DRAFT")
        self.db.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self):
        """测试撤回不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        self.db.flush.assert_not_called()

    # ==================== generate_title 测试 ====================

    def test_generate_title_fat_passed(self):
        """测试生成FAT合格验收单标题"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "FAT-2024-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "出厂验收审批 - FAT-2024-001")

    def test_generate_title_sat_conditional(self):
        """测试生成SAT有条件通过标题"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "SAT-2024-002"
        mock_order.acceptance_type = "SAT"
        mock_order.overall_result = "CONDITIONAL"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "现场验收审批 - SAT-2024-002 [有条件通过]")

    def test_generate_title_final_failed(self):
        """测试生成终验收不合格标题"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "FINAL-2024-003"
        mock_order.acceptance_type = "FINAL"
        mock_order.overall_result = "FAILED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "终验收审批 - FINAL-2024-003 [不合格]")

    def test_generate_title_order_not_found(self):
        """测试生成不存在验收单的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "验收单审批 - 1")

    # ==================== generate_summary 测试 ====================

    def test_generate_summary_basic(self):
        """测试生成基础摘要"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "FAT-2024-001"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.pass_rate = 100.0
        mock_order.passed_items = 10
        mock_order.total_items = 10
        mock_order.failed_items = 0
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.location = "工厂"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        summary = self.adapter.generate_summary(self.entity_id)

        self.assertIn("FAT-2024-001", summary)
        self.assertIn("FAT", summary)
        self.assertIn("合格", summary)
        self.assertIn("100.0%", summary)
        self.assertIn("10/10项通过", summary)
        self.assertIn("工厂", summary)

    def test_generate_summary_with_failed_items(self):
        """测试生成包含不合格项的摘要"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "SAT-2024-002"
        mock_order.acceptance_type = "SAT"
        mock_order.overall_result = "CONDITIONAL"
        mock_order.pass_rate = 90.0
        mock_order.passed_items = 9
        mock_order.total_items = 10
        mock_order.failed_items = 1
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.location = "客户现场"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        summary = self.adapter.generate_summary(self.entity_id)

        self.assertIn("有条件通过", summary)
        self.assertIn("90.0%", summary)
        self.assertIn("不合格: 1项", summary)

    def test_generate_summary_with_project_and_machine(self):
        """测试生成包含项目和设备的摘要"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.order_no = "FAT-2024-003"
        mock_order.acceptance_type = "FAT"
        mock_order.overall_result = "PASSED"
        mock_order.pass_rate = 100.0
        mock_order.passed_items = 8
        mock_order.total_items = 8
        mock_order.failed_items = 0
        mock_order.project_id = 10
        mock_order.machine_id = 20
        mock_order.location = "工厂"

        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "测试项目"

        mock_machine = MagicMock(spec=Machine)
        mock_machine.machine_code = "MCH-001"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            elif model == Machine:
                mock_query.filter.return_value.first.return_value = mock_machine
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        self.assertIn("项目: 测试项目", summary)
        self.assertIn("设备: MCH-001", summary)

    def test_generate_summary_order_not_found(self):
        """测试生成不存在验收单的摘要"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        summary = self.adapter.generate_summary(self.entity_id)

        self.assertEqual(summary, "")

    # ==================== validate_submit 测试 ====================

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 10
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.overall_result = "PASSED"
        mock_order.conditions = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "REJECTED"
        mock_order.project_id = 1
        mock_order.acceptance_type = "SAT"
        mock_order.total_items = 5
        mock_order.passed_items = 5
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.overall_result = "PASSED"
        mock_order.conditions = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_submit_order_not_found(self):
        """测试验证不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "验收单不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效状态下提交"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "PENDING_APPROVAL"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_missing_project(self):
        """测试缺少项目关联"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请关联项目")

    def test_validate_submit_missing_acceptance_type(self):
        """测试缺少验收类型"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请选择验收类型")

    def test_validate_submit_no_items(self):
        """测试没有检查项"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 0
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "验收单至少需要一项检查内容")

    def test_validate_submit_incomplete_checks(self):
        """测试检查未完成"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 5
        mock_order.failed_items = 2
        mock_order.na_items = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("还有 2 项未检查", error)

    def test_validate_submit_missing_overall_result(self):
        """测试缺少验收结论"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 10
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.overall_result = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写验收结论（合格/不合格/有条件通过）")

    def test_validate_submit_conditional_without_conditions(self):
        """测试有条件通过但未填写条件"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 10
        mock_order.failed_items = 0
        mock_order.na_items = 0
        mock_order.overall_result = "CONDITIONAL"
        mock_order.conditions = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "有条件通过必须说明具体条件")

    def test_validate_submit_passed_with_failed_items(self):
        """测试判定合格但有不合格项"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 8
        mock_order.failed_items = 2
        mock_order.na_items = 0
        mock_order.overall_result = "PASSED"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "存在不合格项，不能判定为合格")

    def test_validate_submit_conditional_with_conditions(self):
        """测试有条件通过且填写了条件"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.status = "DRAFT"
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.total_items = 10
        mock_order.passed_items = 9
        mock_order.failed_items = 1
        mock_order.na_items = 0
        mock_order.overall_result = "CONDITIONAL"
        mock_order.conditions = "需在3天内修复问题项"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    # ==================== get_cc_user_ids 测试 ====================

    def test_get_cc_user_ids_basic(self):
        """测试获取基础抄送人列表"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock 基类方法
        with patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[100]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            self.assertIn(100, cc_users)

    def test_get_cc_user_ids_order_not_found(self):
        """测试获取不存在验收单的抄送人"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        cc_users = self.adapter.get_cc_user_ids(self.entity_id)

        self.assertEqual(cc_users, [])


if __name__ == '__main__':
    unittest.main()
