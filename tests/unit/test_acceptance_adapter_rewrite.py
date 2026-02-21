# -*- coding: utf-8 -*-
"""
验收单审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.approval_engine.adapters.acceptance import AcceptanceOrderApprovalAdapter
from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem, AcceptanceTemplate
from app.models.approval import ApprovalInstance
from app.models.project import Project, Machine


class TestAcceptanceAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = AcceptanceOrderApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取验收单实体"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        mock_order.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_order)
        self.db.query.assert_called_once_with(AcceptanceOrder)

    def test_get_entity_not_found(self):
        """测试获取不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础验收单数据"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-001",
            acceptance_type="FAT",
            overall_result="PASSED",
            total_items=10,
            passed_items=10,
            failed_items=0,
            pass_rate=100.0
        )

        # 设置查询返回
        self._setup_query_returns(mock_order)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["order_no"], "FAT-2024-001")
        self.assertEqual(result["acceptance_type"], "FAT")
        self.assertEqual(result["overall_result"], "PASSED")
        self.assertEqual(result["status"], "DRAFT")
        
        # 验证统计字段
        self.assertEqual(result["total_items"], 10)
        self.assertEqual(result["passed_items"], 10)
        self.assertEqual(result["failed_items"], 0)
        self.assertEqual(result["pass_rate"], 100.0)
        
        # 验证标记字段
        self.assertFalse(result["has_critical_failure"])
        self.assertFalse(result["is_officially_completed"])

    def test_get_entity_data_with_project(self):
        """测试获取包含项目信息的验收单数据"""
        mock_order = self._create_mock_order(
            order_no="SAT-2024-001",
            acceptance_type="SAT",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "测试项目"
        mock_project.status = "IN_PROGRESS"

        # 设置多个查询返回
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

        # 验证项目信息被正确包含
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["project_status"], "IN_PROGRESS")

    def test_get_entity_data_with_machine(self):
        """测试获取包含设备信息的验收单数据"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-002",
            machine_id=20
        )

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

        # 验证设备信息
        self.assertEqual(result["machine_code"], "MCH-001")
        self.assertEqual(result["machine_name"], "测试设备")

    def test_get_entity_data_with_template(self):
        """测试获取包含模板信息的验收单数据"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-003",
            template_id=5
        )

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

        # 验证模板信息
        self.assertEqual(result["template_name"], "标准验收模板")
        self.assertEqual(result["template_code"], "TPL-001")
        self.assertEqual(result["equipment_type"], "设备A")

    def test_get_entity_data_with_critical_failure(self):
        """测试检测关键项不合格"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-004",
            overall_result="FAILED",
            total_items=10,
            passed_items=8,
            failed_items=2
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == AcceptanceOrderItem:
                # 模拟有1个关键项不合格
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证关键项不合格标记
        self.assertTrue(result["has_critical_failure"])
        self.assertEqual(result["failed_items"], 2)

    def test_get_entity_data_no_critical_failure(self):
        """测试没有关键项不合格"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-005",
            failed_items=0
        )

        self._setup_query_returns(mock_order)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证没有关键项不合格
        self.assertFalse(result["has_critical_failure"])

    def test_get_entity_data_with_dates(self):
        """测试包含日期字段的数据"""
        planned_date = datetime(2024, 1, 10, 10, 0, 0)
        start_date = datetime(2024, 1, 11, 9, 0, 0)
        end_date = datetime(2024, 1, 11, 17, 0, 0)

        mock_order = self._create_mock_order(
            order_no="SAT-2024-002",
            planned_date=planned_date,
            actual_start_date=start_date,
            actual_end_date=end_date
        )

        self._setup_query_returns(mock_order)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期被转换为ISO格式
        self.assertEqual(result["planned_date"], planned_date.isoformat())
        self.assertEqual(result["actual_start_date"], start_date.isoformat())
        self.assertEqual(result["actual_end_date"], end_date.isoformat())

    def test_get_entity_data_not_found(self):
        """测试获取不存在验收单的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_order = self._create_mock_order(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_submit(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_order.status, "PENDING_APPROVAL")
        self.db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_fat_passed(self):
        """测试FAT验收通过审批"""
        mock_order = self._create_mock_order(
            acceptance_type="FAT",
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # FAT通过 -> COMPLETED
        self.assertEqual(mock_order.status, "COMPLETED")
        self.db.flush.assert_called_once()

    def test_on_approved_fat_conditional(self):
        """测试FAT有条件通过审批"""
        mock_order = self._create_mock_order(
            acceptance_type="FAT",
            overall_result="CONDITIONAL"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # FAT有条件通过 -> CONDITIONAL_APPROVED
        self.assertEqual(mock_order.status, "CONDITIONAL_APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_fat_failed(self):
        """测试FAT不合格审批通过（状态只设置为APPROVED）"""
        mock_order = self._create_mock_order(
            acceptance_type="FAT",
            overall_result="FAILED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # 其他结果 -> APPROVED（默认）
        self.assertEqual(mock_order.status, "APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_sat_passed(self):
        """测试SAT验收通过审批"""
        mock_order = self._create_mock_order(
            acceptance_type="SAT",
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # SAT通过 -> COMPLETED
        self.assertEqual(mock_order.status, "COMPLETED")
        self.db.flush.assert_called_once()

    def test_on_approved_sat_conditional(self):
        """测试SAT有条件通过审批"""
        mock_order = self._create_mock_order(
            acceptance_type="SAT",
            overall_result="CONDITIONAL"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # SAT有条件通过 -> CONDITIONAL_APPROVED
        self.assertEqual(mock_order.status, "CONDITIONAL_APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_final_passed(self):
        """测试终验收通过审批"""
        mock_order = self._create_mock_order(
            acceptance_type="FINAL",
            overall_result="PASSED"
        )
        mock_order.is_officially_completed = False
        mock_order.officially_completed_at = None

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('app.services.approval_engine.adapters.acceptance.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            self.adapter.on_approved(self.entity_id, self.instance)

            # 终验收通过 -> COMPLETED + 正式完成标记
            self.assertEqual(mock_order.status, "COMPLETED")
            self.assertTrue(mock_order.is_officially_completed)
            self.assertEqual(mock_order.officially_completed_at, mock_now)
            self.db.flush.assert_called_once()

    def test_on_approved_final_conditional(self):
        """测试终验收有条件通过（不设置正式完成）"""
        mock_order = self._create_mock_order(
            acceptance_type="FINAL",
            overall_result="CONDITIONAL"
        )
        mock_order.is_officially_completed = False

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # 终验收有条件通过 -> APPROVED（代码中FINAL只处理PASSED情况）
        self.assertEqual(mock_order.status, "APPROVED")
        self.assertFalse(mock_order.is_officially_completed)
        self.db.flush.assert_called_once()

    def test_on_approved_unknown_type(self):
        """测试未知验收类型"""
        mock_order = self._create_mock_order(
            acceptance_type="UNKNOWN",
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_approved(self.entity_id, self.instance)

        # 未知类型只设置为APPROVED
        self.assertEqual(mock_order.status, "APPROVED")
        self.db.flush.assert_called_once()

    def test_on_approved_order_not_found(self):
        """测试审批通过不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改为REJECTED
        self.assertEqual(mock_order.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_order_not_found(self):
        """测试驳回不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复为DRAFT
        self.assertEqual(mock_order.status, "DRAFT")
        self.db.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self):
        """测试撤回不存在的验收单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== generate_title() 测试 ==========

    def test_generate_title_fat_passed(self):
        """测试生成FAT合格标题"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-001",
            acceptance_type="FAT",
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "出厂验收审批 - FAT-2024-001")

    def test_generate_title_sat_conditional(self):
        """测试生成SAT有条件通过标题"""
        mock_order = self._create_mock_order(
            order_no="SAT-2024-002",
            acceptance_type="SAT",
            overall_result="CONDITIONAL"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "现场验收审批 - SAT-2024-002 [有条件通过]")

    def test_generate_title_final_failed(self):
        """测试生成终验收不合格标题"""
        mock_order = self._create_mock_order(
            order_no="FINAL-2024-003",
            acceptance_type="FINAL",
            overall_result="FAILED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "终验收审批 - FINAL-2024-003 [不合格]")

    def test_generate_title_unknown_type(self):
        """测试生成未知类型的标题"""
        mock_order = self._create_mock_order(
            order_no="TEST-2024-001",
            acceptance_type="CUSTOM",
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        # 未知类型直接使用原始类型名
        self.assertEqual(title, "CUSTOM审批 - TEST-2024-001")

    def test_generate_title_order_not_found(self):
        """测试生成不存在验收单的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, f"验收单审批 - {self.entity_id}")

    # ========== generate_summary() 测试 ==========

    def test_generate_summary_basic(self):
        """测试生成基础摘要"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-001",
            acceptance_type="FAT",
            overall_result="PASSED",
            pass_rate=100.0,
            passed_items=10,
            total_items=10,
            failed_items=0,
            location="工厂车间"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证摘要包含关键信息
        self.assertIn("FAT-2024-001", summary)
        self.assertIn("FAT", summary)
        self.assertIn("合格", summary)
        self.assertIn("100.0%", summary)
        self.assertIn("10/10项通过", summary)
        self.assertIn("工厂车间", summary)

    def test_generate_summary_with_failed_items(self):
        """测试生成包含不合格项的摘要"""
        mock_order = self._create_mock_order(
            order_no="SAT-2024-002",
            acceptance_type="SAT",
            overall_result="CONDITIONAL",
            pass_rate=90.0,
            passed_items=9,
            total_items=10,
            failed_items=1,
            location="客户现场"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证包含不合格项信息
        self.assertIn("有条件通过", summary)
        self.assertIn("90.0%", summary)
        self.assertIn("不合格: 1项", summary)

    def test_generate_summary_with_project(self):
        """测试生成包含项目的摘要"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-003",
            acceptance_type="FAT",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "测试项目A"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证包含项目名称
        self.assertIn("项目: 测试项目A", summary)

    def test_generate_summary_with_machine(self):
        """测试生成包含设备的摘要"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-004",
            acceptance_type="FAT",
            machine_id=20
        )

        mock_machine = MagicMock(spec=Machine)
        mock_machine.machine_code = "MCH-001"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Machine:
                mock_query.filter.return_value.first.return_value = mock_machine
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证包含设备编号
        self.assertIn("设备: MCH-001", summary)

    def test_generate_summary_machine_without_code(self):
        """测试设备没有machine_code属性"""
        mock_order = self._create_mock_order(
            order_no="FAT-2024-005",
            acceptance_type="FAT",
            machine_id=20
        )

        mock_machine = MagicMock(spec=Machine)
        # 删除machine_code属性
        del mock_machine.machine_code

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Machine:
                mock_query.filter.return_value.first.return_value = mock_machine
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证摘要不包含设备信息（hasattr检查失败）
        self.assertNotIn("设备:", summary)

    def test_generate_summary_order_not_found(self):
        """测试生成不存在验收单的摘要"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        summary = self.adapter.generate_summary(self.entity_id)

        # 应返回空字符串
        self.assertEqual(summary, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=10,
            failed_items=0,
            na_items=0,
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_order = self._create_mock_order(
            status="REJECTED",
            project_id=1,
            acceptance_type="SAT",
            total_items=5,
            passed_items=5,
            failed_items=0,
            na_items=0,
            overall_result="PASSED"
        )
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
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_missing_project(self):
        """测试缺少项目关联"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请关联项目")

    def test_validate_submit_missing_acceptance_type(self):
        """测试缺少验收类型"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请选择验收类型")

    def test_validate_submit_no_items(self):
        """测试没有检查项"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=0
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "验收单至少需要一项检查内容")

    def test_validate_submit_incomplete_checks(self):
        """测试检查未完成"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=5,
            failed_items=2,
            na_items=1
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        # 10 - (5+2+1) = 2项未检查
        self.assertIn("还有 2 项未检查", error)

    def test_validate_submit_missing_overall_result(self):
        """测试缺少验收结论"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=10,
            failed_items=0,
            na_items=0,
            overall_result=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写验收结论（合格/不合格/有条件通过）")

    def test_validate_submit_conditional_without_conditions(self):
        """测试有条件通过但未填写条件"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=10,
            failed_items=0,
            na_items=0,
            overall_result="CONDITIONAL",
            conditions=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "有条件通过必须说明具体条件")

    def test_validate_submit_conditional_with_empty_conditions(self):
        """测试有条件通过但条件为空字符串"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=10,
            failed_items=0,
            na_items=0,
            overall_result="CONDITIONAL",
            conditions=""
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "有条件通过必须说明具体条件")

    def test_validate_submit_passed_with_failed_items(self):
        """测试判定合格但有不合格项"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=8,
            failed_items=2,
            na_items=0,
            overall_result="PASSED"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "存在不合格项，不能判定为合格")

    def test_validate_submit_conditional_with_conditions(self):
        """测试有条件通过且填写了条件"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            project_id=1,
            acceptance_type="FAT",
            total_items=10,
            passed_items=9,
            failed_items=1,
            na_items=0,
            overall_result="CONDITIONAL",
            conditions="需在3天内修复问题项"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    # ========== get_cc_user_ids() 测试 ==========

    def test_get_cc_user_ids_order_not_found(self):
        """测试获取不存在验收单的抄送人"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        cc_users = self.adapter.get_cc_user_ids(self.entity_id)

        # 应返回空列表
        self.assertEqual(cc_users, [])

    def test_get_cc_user_ids_with_project_manager(self):
        """测试获取包含项目经理的抄送人"""
        mock_order = self._create_mock_order(
            acceptance_type="FAT",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        # Mock基类方法
        with patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 应包含项目经理和质量部负责人
            self.assertIn(100, cc_users)  # 项目经理
            self.assertIn(200, cc_users)  # 质量部负责人

    def test_get_cc_user_ids_sat_with_sales(self):
        """测试SAT类型添加销售负责人"""
        mock_order = self._create_mock_order(
            acceptance_type="SAT",
            project_id=10
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock基类方法
        with patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]), \
             patch.object(AcceptanceOrderApprovalAdapter, 'get_project_sales_user_id', return_value=300):
            
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 应包含销售负责人
            self.assertIn(300, cc_users)

    def test_get_cc_user_ids_fat_no_sales(self):
        """测试FAT类型不添加销售负责人"""
        mock_order = self._create_mock_order(
            acceptance_type="FAT",
            project_id=10
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock基类方法
        with patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]), \
             patch.object(AcceptanceOrderApprovalAdapter, 'get_project_sales_user_id', return_value=300):
            
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # FAT不应包含销售负责人
            self.assertNotIn(300, cc_users)

    def test_get_cc_user_ids_deduplication(self):
        """测试抄送人去重"""
        mock_order = self._create_mock_order(
            acceptance_type="SAT",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        # 模拟重复的用户ID
        with patch.object(AcceptanceOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[100, 200]), \
             patch.object(AcceptanceOrderApprovalAdapter, 'get_project_sales_user_id', return_value=100):
            
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 验证去重
            self.assertEqual(len(cc_users), len(set(cc_users)))
            self.assertEqual(cc_users.count(100), 1)

    # ========== 辅助方法 ==========

    def _create_mock_order(self, **kwargs):
        """创建模拟验收单对象"""
        mock_order = MagicMock(spec=AcceptanceOrder)
        
        # 设置默认值
        defaults = {
            'id': self.entity_id,
            'order_no': 'TEST-001',
            'acceptance_type': 'FAT',
            'status': 'DRAFT',
            'overall_result': 'PASSED',
            'total_items': 10,
            'passed_items': 10,
            'failed_items': 0,
            'na_items': 0,
            'pass_rate': 100.0,
            'project_id': None,
            'machine_id': None,
            'template_id': None,
            'planned_date': None,
            'actual_start_date': None,
            'actual_end_date': None,
            'location': None,
            'conclusion': None,
            'conditions': None,
            'created_by': 1,
            'is_officially_completed': False,
        }
        
        # 合并自定义值
        defaults.update(kwargs)
        
        # 设置属性
        for key, value in defaults.items():
            setattr(mock_order, key, value)
        
        return mock_order

    def _setup_query_returns(self, mock_order):
        """设置基础查询返回"""
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == AcceptanceOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == AcceptanceOrderItem:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(AcceptanceOrderApprovalAdapter.entity_type, "ACCEPTANCE_ORDER")


if __name__ == '__main__':
    unittest.main()
